#!/usr/bin/env python3
"""Analyze the preregistered fresh-query/new-build TCP confirmation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from phase3_baselines import constant_policy, first_passing_action, source_global_action
from phase3_simultaneous_fallback import CONFIDENCE, choose_policy, simultaneous_pass
from tcp_hm9_tc import (
    GRID, LIMIT, TARGET, bootstrap, execute, history_max, load_grid, recall_values,
    risk_stats, stable_tail_actions,
)

SOURCE_SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131]
TARGET_SEEDS = [2381, 2503, 2633]


def result_row(seed: int, method: str, selected: str, cert: pd.DataFrame,
               evaluation: pd.DataFrame, simultaneous_ucb: float | None = None) -> dict:
    failures, n, risk, ucb = risk_stats(cert)
    recall = recall_values(evaluation)
    return {
        "seed": seed, "method": method, "selected_policy": selected,
        "cert_n": n, "cert_failures": failures, "cert_risk": risk,
        "cert_cp95_ucb": ucb, "selected_simultaneous_ucb": simultaneous_ucb,
        "eval_risk": float((recall < TARGET).mean()),
        "mean_recall": float(recall.mean()),
        "mean_dists": float(evaluation.dists.mean()),
        "p50_dists": float(evaluation.dists.quantile(.50)),
        "p95_dists": float(evaluation.dists.quantile(.95)),
        "p99_dists": float(evaluation.dists.quantile(.99)),
        "abstain_rate": float(evaluation.abstain.mean()) if "abstain" in evaluation else 0.0,
    }


def append_queries(records: list[dict], seed: int, method: str,
                   evaluation: pd.DataFrame) -> None:
    for qid, (distance, recall) in enumerate(zip(evaluation.dists, recall_values(evaluation))):
        records.append({"seed": seed, "qid": qid, "method": method,
                        "dists": float(distance), "recall": float(recall)})


def shift_actions(actions, rungs: int):
    shifted = actions.copy()
    if rungs == 0:
        return shifted
    for _ in range(rungs):
        finite = ~pd.isna(shifted) & (shifted != float("inf"))
        mapping = {int(GRID[i]): int(GRID[min(i + 1, len(GRID) - 1)])
                   for i in range(len(GRID))}
        shifted[finite] = [mapping[int(value)] for value in shifted[finite]]
    return shifted


def graded(candidate_cert: pd.DataFrame, candidate_eval: pd.DataFrame,
           fixed_cert: pd.DataFrame, fixed_eval: pd.DataFrame,
           endpoint_cert: pd.DataFrame, endpoint_eval: pd.DataFrame,
           candidate_name: str = "TCP_HM9_TC",
           ) -> tuple[str, pd.DataFrame, pd.DataFrame, float]:
    candidate_check = simultaneous_pass(candidate_cert)
    fixed_check = simultaneous_pass(fixed_cert)
    endpoint_check = simultaneous_pass(endpoint_cert)
    selected = choose_policy(candidate_check[0], fixed_check[0], endpoint_check[0])
    if selected == "INVALID_NO_CERTIFIED_ACTION":
        raise RuntimeError("no simultaneously certified action")
    cert = {candidate_name: candidate_cert,
            "SOURCE_GLOBAL_FIXED": fixed_cert, "FIXED_ENDPOINT": endpoint_cert}
    evaluation = {candidate_name: candidate_eval,
                  "SOURCE_GLOBAL_FIXED": fixed_eval, "FIXED_ENDPOINT": endpoint_eval}
    check = {candidate_name: candidate_check,
             "SOURCE_GLOBAL_FIXED": fixed_check, "FIXED_ENDPOINT": endpoint_check}
    return selected, cert[selected], evaluation[selected], check[selected][4]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid-root", required=True, type=Path)
    parser.add_argument("--darth-root", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target-seeds", nargs="+", type=int, default=TARGET_SEEDS)
    parser.add_argument("--tcp-rung-shift", type=int, choices=[0, 1], default=0)
    args = parser.parse_args()

    target_seeds = args.target_seeds
    all_seeds = SOURCE_SEEDS + target_seeds
    cert_grids = {s: load_grid(args.grid_root / f"seed_{s}", "cert") for s in all_seeds}
    eval_grids = {s: load_grid(args.grid_root / f"seed_{s}", "eval") for s in all_seeds}
    cert_actions = history_max([stable_tail_actions(cert_grids[s]) for s in SOURCE_SEEDS])
    eval_actions = history_max([stable_tail_actions(eval_grids[s]) for s in SOURCE_SEEDS])
    cert_actions = shift_actions(cert_actions, args.tcp_rung_shift)
    eval_actions = shift_actions(eval_actions, args.tcp_rung_shift)
    tcp_policy_name = "TCP_HM9_TC_R1" if args.tcp_rung_shift == 1 else "TCP_HM9_TC"
    tcp_method_name = f"{tcp_policy_name}_GRADED"
    source_ef = source_global_action([cert_grids[s] for s in SOURCE_SEEDS])
    summaries, query_records = [], []

    for target in target_seeds:
        endpoint_cert = constant_policy(cert_grids[target], 200, 0, 500)
        endpoint_eval = constant_policy(eval_grids[target], 200)
        fixed_cert = constant_policy(cert_grids[target], source_ef, 0, 500)
        fixed_eval = constant_policy(eval_grids[target], source_ef)

        tcp_cert = execute(cert_grids[target], cert_actions)
        tcp_eval = execute(eval_grids[target], eval_actions)
        tcp_selected, tcp_deployed_cert, tcp_deployed_eval, tcp_ucb = graded(
            tcp_cert, tcp_eval, fixed_cert, fixed_eval, endpoint_cert, endpoint_eval,
            candidate_name=tcp_policy_name)

        target_ef = first_passing_action(cert_grids[target], 0, 250)
        target_cert = constant_policy(cert_grids[target], target_ef, 250, 500)
        target_eval = constant_policy(eval_grids[target], target_ef)
        target_ok = risk_stats(target_cert)[3] <= LIMIT
        target_deployed_cert = target_cert if target_ok else endpoint_cert
        target_deployed_eval = target_eval if target_ok else endpoint_eval
        target_selected = f"EF_{target_ef}" if target_ok else "FIXED_ENDPOINT"

        source_ok = risk_stats(fixed_cert)[3] <= LIMIT
        source_deployed_cert = fixed_cert if source_ok else endpoint_cert
        source_deployed_eval = fixed_eval if source_ok else endpoint_eval
        source_selected = f"EF_{source_ef}" if source_ok else "FIXED_ENDPOINT"

        darth_cert = pd.read_csv(args.darth_root / f"seed_{target}" / "darth_cert_500.txt")
        darth_eval = pd.read_csv(args.darth_root / f"seed_{target}" / "darth_eval_1000.txt")
        darth_selected_raw, darth_deployed_cert, darth_deployed_eval, darth_ucb = graded(
            darth_cert, darth_eval, fixed_cert, fixed_eval, endpoint_cert, endpoint_eval,
            candidate_name="DARTH_SOURCE_1103")
        darth_selected = darth_selected_raw

        methods = [
            ("FIXED_ENDPOINT", "EF_200", endpoint_cert, endpoint_eval, None),
            ("SOURCE_GLOBAL_FIXED_DEPLOYED", source_selected, source_deployed_cert, source_deployed_eval, None),
            ("TARGET_ONLY_GLOBAL_DEPLOYED", target_selected, target_deployed_cert, target_deployed_eval, None),
            ("DARTH_SOURCE_1103_GRADED", darth_selected, darth_deployed_cert, darth_deployed_eval, darth_ucb),
            (tcp_method_name, tcp_selected, tcp_deployed_cert, tcp_deployed_eval, tcp_ucb),
        ]
        for method, selected, cert, evaluation, simultaneous_ucb in methods:
            summaries.append(result_row(target, method, selected, cert, evaluation, simultaneous_ucb))
            append_queries(query_records, target, method, evaluation)

    args.output.mkdir(parents=True, exist_ok=False)
    summary = pd.DataFrame(summaries)
    query = pd.DataFrame(query_records)
    summary.to_csv(args.output / "per_build_summary.csv", index=False)
    query.to_csv(args.output / "per_query.csv.gz", index=False, compression="gzip")
    pooled = query.groupby("method").agg(
        queries=("qid", "count"), mean_dists=("dists", "mean"),
        p50_dists=("dists", lambda x: x.quantile(.50)),
        p95_dists=("dists", lambda x: x.quantile(.95)),
        p99_dists=("dists", lambda x: x.quantile(.99)),
        eval_risk=("recall", lambda x: (x < TARGET).mean()),
        mean_recall=("recall", "mean"),
    ).reset_index()
    pooled.to_csv(args.output / "pooled_summary.csv", index=False)

    baseline_names = ["SOURCE_GLOBAL_FIXED_DEPLOYED", "TARGET_ONLY_GLOBAL_DEPLOYED",
                      "DARTH_SOURCE_1103_GRADED"]
    best = pooled[pooled.method.isin(baseline_names)].sort_values("mean_dists").iloc[0]
    tcp = pooled[pooled.method == tcp_method_name].iloc[0]
    comparison = bootstrap(query, tcp_method_name, str(best.method))
    pivot = query.pivot(index=["seed", "qid"], columns="method", values="dists")
    build_diff = pivot[tcp_method_name].sub(pivot[str(best.method)]).groupby(level=0).mean()
    decision = {
        "dataset": args.dataset,
        "source_builds": SOURCE_SEEDS, "prospective_target_builds": target_seeds,
        "tcp_policy": tcp_policy_name,
        "source_global_fixed_ef": source_ef,
        "best_deployable_baseline": str(best.method),
        "tcp_selection_counts": {str(k): int(v) for k, v in summary[summary.method == tcp_method_name].selected_policy.value_counts().items()},
        "darth_selection_counts": {str(k): int(v) for k, v in summary[summary.method == "DARTH_SOURCE_1103_GRADED"].selected_policy.value_counts().items()},
        "mean_gain_fraction": float((best.mean_dists - tcp.mean_dists) / best.mean_dists),
        "mean_recall_difference": float(tcp.mean_recall - best.mean_recall),
        "p95_ratio": float(tcp.p95_dists / best.p95_dists),
        "p99_ratio_diagnostic": float(tcp.p99_dists / best.p99_dists),
        "bootstrap": comparison,
        "lobo_mean_differences": {str(int(s)): float(build_diff.drop(s).mean()) for s in build_diff.index},
        "safety_gate": bool((summary[summary.method == tcp_method_name].selected_simultaneous_ucb <= LIMIT).all()),
        "mean_gate": bool(comparison["ci95"][1] < 0),
        "materiality_5pct": bool((best.mean_dists - tcp.mean_dists) / best.mean_dists >= .05),
        "recall_noninferiority_minus_0p001": bool(tcp.mean_recall - best.mean_recall >= -.001),
        "p95_noninferiority_5pct": bool(tcp.p95_dists / best.p95_dists <= 1.05),
        "lobo_direction_gate": bool((build_diff.drop(build_diff.index[0]).mean() < 0) and
                                    (build_diff.drop(build_diff.index[1]).mean() < 0) and
                                    (build_diff.drop(build_diff.index[2]).mean() < 0)),
        "formal_build_distribution_certificate": False,
        "simultaneous_confidence": CONFIDENCE,
    }
    decision["prospective_primary_gate"] = bool(decision["safety_gate"] and decision["mean_gate"] and
                                                decision["materiality_5pct"] and
                                                decision["recall_noninferiority_minus_0p001"] and
                                                decision["p95_noninferiority_5pct"] and
                                                decision["lobo_direction_gate"])
    (args.output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
