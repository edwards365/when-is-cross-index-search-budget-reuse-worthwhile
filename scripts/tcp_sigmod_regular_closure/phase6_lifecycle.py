#!/usr/bin/env python3
"""Hardware-independent prospective lifecycle accounting for Phase 5 outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from .phase3_baselines import constant_policy, first_passing_action, source_global_action
    from .phase5_analyze import SOURCE_SEEDS, TARGET_SEEDS, graded
    from .tcp_hm9_tc import execute, history_max, load_grid, stable_tail_actions
except ImportError:  # direct script execution
    from phase3_baselines import constant_policy, first_passing_action, source_global_action
    from phase5_analyze import SOURCE_SEEDS, TARGET_SEEDS, graded
    from tcp_hm9_tc import execute, history_max, load_grid, stable_tail_actions

EF_GRID = [10, 20, 40, 80, 120, 160, 200]
LIFETIMES = [1_000, 10_000, 100_000, 1_000_000, 10_000_000]
BASE_SIZE = 100_000


def break_even(overhead_a: float, per_query_a: float,
               overhead_b: float, per_query_b: float) -> float | None:
    """First non-negative N where A is no more expensive than B."""
    saving = per_query_b - per_query_a
    if saving <= 0:
        return None
    return max(0.0, (overhead_a - overhead_b) / saving)


def work(frame: pd.DataFrame) -> float:
    return float(frame.dists.sum())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-root", required=True, type=Path)
    parser.add_argument("--darth-root", required=True, type=Path)
    parser.add_argument("--analysis-root", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    cert_grids = {s: load_grid(args.grid_root / f"seed_{s}", "cert")
                  for s in SOURCE_SEEDS + TARGET_SEEDS}
    eval_grids = {s: load_grid(args.grid_root / f"seed_{s}", "eval")
                  for s in SOURCE_SEEDS + TARGET_SEEDS}
    cert_actions = history_max([stable_tail_actions(cert_grids[s]) for s in SOURCE_SEEDS])
    eval_actions = history_max([stable_tail_actions(eval_grids[s]) for s in SOURCE_SEEDS])
    source_ef = source_global_action([cert_grids[s] for s in SOURCE_SEEDS])
    source_profile = {
        role: sum(work(frame) for seed in SOURCE_SEEDS
                  for frame in load_grid(args.grid_root / f"seed_{seed}", role).values())
        for role in ("cert", "eval")
    }

    records: list[dict] = []
    for seed in TARGET_SEEDS:
        endpoint_cert = constant_policy(cert_grids[seed], 200, 0, 500)
        endpoint_eval = constant_policy(eval_grids[seed], 200)
        fixed_cert = constant_policy(cert_grids[seed], source_ef, 0, 500)
        fixed_eval = constant_policy(eval_grids[seed], source_ef)

        tcp_cert = execute(cert_grids[seed], cert_actions)
        tcp_eval = execute(eval_grids[seed], eval_actions)
        tcp_selected, _, tcp_deployed_eval, _ = graded(
            tcp_cert, tcp_eval, fixed_cert, fixed_eval, endpoint_cert, endpoint_eval)

        target_ef = first_passing_action(cert_grids[seed], 0, 250)
        target_cert = constant_policy(cert_grids[seed], target_ef, 250, 500)
        target_eval = constant_policy(eval_grids[seed], target_ef)
        target_selection = sum(work(constant_policy(cert_grids[seed], ef, 0, 250))
                               for ef in EF_GRID)

        darth_cert = pd.read_csv(args.darth_root / f"seed_{seed}" / "darth_cert_500.txt")
        darth_eval = pd.read_csv(args.darth_root / f"seed_{seed}" / "darth_eval_1000.txt")
        darth_selected, _, darth_deployed_eval, _ = graded(
            darth_cert, darth_eval, fixed_cert, fixed_eval, endpoint_cert, endpoint_eval)

        methods = {
            "FIXED_ENDPOINT": (work(endpoint_cert), endpoint_eval),
            "SOURCE_GLOBAL_FIXED_DEPLOYED": (work(fixed_cert), fixed_eval),
            "TARGET_ONLY_GLOBAL_DEPLOYED": (target_selection + work(target_cert), target_eval),
            # Candidate certification is followed by fixed-policy certification when DARTH rejects.
            "DARTH_SOURCE_1103_GRADED": (
                work(darth_cert) + (work(fixed_cert) if darth_selected != "DARTH_SOURCE_1103" else 0.0),
                darth_deployed_eval,
            ),
            # TCP was accepted on all prospective targets; no fallback certification was consumed.
            "TCP_HM9_TC_GRADED": (work(tcp_cert), tcp_deployed_eval),
        }
        for method, (overhead, evaluation) in methods.items():
            mean_search = float(evaluation.dists.mean())
            records.append({
                "dataset": args.dataset, "seed": seed, "method": method,
                "selected_policy": tcp_selected if method == "TCP_HM9_TC_GRADED" else (
                    darth_selected if method == "DARTH_SOURCE_1103_GRADED" else "see_phase5_summary"),
                "target_labels": 500,
                "target_selection_search_dists": target_selection if method == "TARGET_ONLY_GLOBAL_DEPLOYED" else 0.0,
                "certification_search_dists": overhead - (target_selection if method == "TARGET_ONLY_GLOBAL_DEPLOYED" else 0.0),
                "one_time_target_search_dists": overhead,
                "production_mean_search_dists": mean_search,
            })

    per_build = pd.DataFrame(records)
    pooled = per_build.groupby("method", as_index=False).agg(
        target_labels=("target_labels", "mean"),
        one_time_target_search_dists=("one_time_target_search_dists", "mean"),
        production_mean_search_dists=("production_mean_search_dists", "mean"),
    )
    # TCP's per-query History-Max cache is a real offline cost. Source-global
    # selection uses only the source certification role; TCP additionally uses
    # the cached production-query role. Exact truth is counted as one exhaustive
    # base scan per source-labelled query, independent of the number of builds.
    source_setup = {
        "FIXED_ENDPOINT": 0.0,
        "SOURCE_GLOBAL_FIXED_DEPLOYED": source_profile["cert"] + 500 * BASE_SIZE,
        "TARGET_ONLY_GLOBAL_DEPLOYED": 0.0,
        "TCP_HM9_TC_GRADED": source_profile["cert"] + source_profile["eval"] + 1500 * BASE_SIZE,
        # The frozen comparator's model-training/feature construction cost was
        # not instrumented, so a complete lifecycle total would be misleading.
        "DARTH_SOURCE_1103_GRADED": float("nan"),
    }
    pooled["offline_source_history_dists"] = pooled.method.map(source_setup)
    pooled["complete_one_time_dists"] = (
        pooled.one_time_target_search_dists + pooled.offline_source_history_dists)
    rows = []
    for _, row in pooled.iterrows():
        for n in LIFETIMES:
            rows.append({
                "dataset": args.dataset, "method": row.method, "production_queries": n,
                "target_labels": int(row.target_labels),
                "one_time_target_search_dists": float(row.one_time_target_search_dists),
                "production_search_dists": float(n * row.production_mean_search_dists),
                "total_search_dists": float(row.one_time_target_search_dists + n * row.production_mean_search_dists),
                "complete_cached_workload_dists": (
                    float(row.complete_one_time_dists + n * row.production_mean_search_dists)
                    if pd.notna(row.complete_one_time_dists) else None),
                "scope": "TARGET_INCREMENTAL_AND_COMPLETE_CACHED_WORKLOAD_DISTANCE_COMPUTATIONS",
            })
    lifecycle = pd.DataFrame(rows)

    tcp = pooled[pooled.method == "TCP_HM9_TC_GRADED"].iloc[0]
    comparisons = []
    for _, other in pooled[pooled.method != "TCP_HM9_TC_GRADED"].iterrows():
        comparisons.append({
            "dataset": args.dataset,
            "comparison": f"TCP_HM9_TC_GRADED_minus_{other.method}",
            "break_even_queries": break_even(
                float(tcp.one_time_target_search_dists), float(tcp.production_mean_search_dists),
                float(other.one_time_target_search_dists), float(other.production_mean_search_dists)),
            "production_mean_gain_fraction": float(
                (other.production_mean_search_dists - tcp.production_mean_search_dists) /
                other.production_mean_search_dists),
            "complete_cached_workload_break_even_queries": (
                break_even(float(tcp.complete_one_time_dists), float(tcp.production_mean_search_dists),
                           float(other.complete_one_time_dists), float(other.production_mean_search_dists))
                if pd.notna(other.complete_one_time_dists) else None),
            "complete_comparison_status": (
                "ESTIMATED" if pd.notna(other.complete_one_time_dists)
                else "NOT_ESTIMABLE_DARTH_TRAINING_AND_FEATURE_COST_MISSING"),
        })
    comparison = pd.DataFrame(comparisons)
    decision = json.loads((args.analysis_root / "decision.json").read_text())
    at_100k = lifecycle[lifecycle.production_queries == 100_000]
    tcp_100k = float(at_100k[at_100k.method == "TCP_HM9_TC_GRADED"].complete_cached_workload_dists.iloc[0])
    complete_baselines = at_100k[
        at_100k.method.isin(["FIXED_ENDPOINT", "SOURCE_GLOBAL_FIXED_DEPLOYED",
                             "TARGET_ONLY_GLOBAL_DEPLOYED"])]
    best_100k = float(complete_baselines.complete_cached_workload_dists.min())
    complete_gain_100k = (best_100k - tcp_100k) / best_100k
    seal = {
        "dataset": args.dataset,
        "accounting_scope": "DISTANCE_COMPUTATIONS_AND_EQUAL_TARGET_LABEL_COUNTS",
        "common_costs_excluded_from_differences": [
            "target_index_rebuild", "target_certification_truth_generation"
        ],
        "source_history_truth_cost": "INCLUDED_AS_EXHAUSTIVE_BASE_SCAN_LOWER_BOUND",
        "wall_clock_status": "NOT_USED_FOR_PRIMARY_COST_CLAIM",
        "offline_source_profile_search_dists": source_profile,
        "source_truth_distance_lower_bound": 1500 * BASE_SIZE,
        "complete_cost_gain_at_n100k": complete_gain_100k,
        "complete_cost_gate_n100k_gain_at_least_5pct": bool(complete_gain_100k >= .05),
        "strict_quality_preserving_gate": bool(decision["prospective_primary_gate"]),
        "sla_risk_constrained_efficiency_track": bool(
            decision["safety_gate"] and decision["mean_gate"] and
            decision["materiality_5pct"] and decision["p95_noninferiority_5pct"] and
            decision["lobo_direction_gate"]),
        "mean_recall_difference": decision["mean_recall_difference"],
        "interpretation": "RISK_COST_TRADEOFF_SUPPORTED_BUT_RECALL_FIDELITY_GATE_FAILED",
    }

    args.output.mkdir(parents=True, exist_ok=False)
    per_build.to_csv(args.output / "per_build_cost.csv", index=False)
    lifecycle.to_csv(args.output / "lifecycle_cost.csv", index=False)
    comparison.to_csv(args.output / "break_even.csv", index=False)
    (args.output / "decision.json").write_text(json.dumps(seal, indent=2) + "\n")
    print(json.dumps(seal, indent=2))


if __name__ == "__main__":
    main()
