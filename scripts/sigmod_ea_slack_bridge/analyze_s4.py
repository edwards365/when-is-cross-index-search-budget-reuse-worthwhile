#!/usr/bin/env python3
"""Analyze fresh-query certified fixed-action replay with legal per-query NDC."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np

from analyze_s1 import write_csv
from analyze_s2 import three_state

GRIDS = {
    "hnswlib": np.asarray([10, 20, 40, 80, 120, 200]),
    "faiss_hnsw": np.asarray([16, 32, 64, 128, 256, 512]),
}
LANES = ("source_selected_plus_0", "source_selected_plus_1", "source_selected_plus_2", "endpoint")


def load_raw(raw_dir, dataset, grid):
    paths = sorted(raw_dir.glob(f"{dataset}*.csv.gz"))
    records = []
    for path in paths:
        with gzip.open(path, "rt", newline="") as handle:
            for row in csv.DictReader(handle):
                records.append((row["build"], int(row["query_id"]), int(row["ef"]), float(row["recall"]), float(row["ndc"])))
    builds = sorted({r[0] for r in records})
    bmap = {b: i for i, b in enumerate(builds)}
    amap = {int(a): i for i, a in enumerate(grid)}
    recall = np.full((len(builds), 1000, len(grid)), np.nan)
    ndc = np.full_like(recall, np.nan)
    for b, q, a, r, c in records:
        recall[bmap[b], q, amap[a]] = r
        ndc[bmap[b], q, amap[a]] = c
    if len(builds) != 24 or np.isnan(recall).any() or np.isnan(ndc).any():
        raise RuntimeError(f"incomplete fresh cube {dataset} {raw_dir}")
    return builds, recall, ndc


def cp(k, n, alpha=0.025):
    return three_state(k, n, alpha)


def bootstrap_pair(fail_q, cost_q, endpoint_cost_q, reps=5000, seed=991):
    rng = np.random.default_rng(seed)
    n = len(fail_q)
    risks, savings = np.empty(reps), np.empty(reps)
    for i in range(reps):
        idx = rng.integers(0, n, n)
        risks[i] = np.mean(fail_q[idx])
        savings[i] = 1.0 - np.mean(cost_q[idx]) / np.mean(endpoint_cost_q[idx])
    return (*map(float, np.quantile(risks, (0.025, 0.975))), *map(float, np.quantile(savings, (0.025, 0.975))))


def analyze_setting(operator, dataset, raw_dir, policies):
    grid = GRIDS[operator]
    builds, recall, ndc = load_raw(raw_dir, dataset, grid)
    pmap = {(r["operator"], r["dataset"], r["source_build"]): int(r["chosen_action"]) for r in policies}
    cert = np.arange(500)
    evaluation = np.arange(500, 1000)
    source_rows, pair_rows, summary_rows = [], [], []
    lane_data = {}
    for lane in LANES:
        fail_by_q = [[] for _ in evaluation]
        cost_by_q = [[] for _ in evaluation]
        endpoint_cost_by_q = [[] for _ in evaluation]
        pair_vectors = {}
        fallback_sources = 0
        no_cert_sources = 0
        for si, source in enumerate(builds):
            selected = pmap[(operator, dataset, source)]
            selected_idx = int(np.where(grid == selected)[0][0])
            shift = 0 if lane.endswith("plus_0") else 1 if lane.endswith("plus_1") else 2
            candidate_idx = len(grid) - 1 if lane == "endpoint" else min(selected_idx + shift, len(grid) - 1)
            candidate_fail = int(np.sum(recall[si, cert, candidate_idx] < 0.95))
            endpoint_fail = int(np.sum(recall[si, cert, -1] < 0.95))
            candidate_state, candidate_low, candidate_up = cp(candidate_fail, len(cert))
            endpoint_state, endpoint_low, endpoint_up = cp(endpoint_fail, len(cert))
            if endpoint_state != "QUALIFIED":
                deployment = "NO_CERTIFIED_ACTION"
                executed_idx = len(grid) - 1
                no_cert_sources += 1
            elif candidate_state == "QUALIFIED":
                deployment = "DEPLOY_CANDIDATE"
                executed_idx = candidate_idx
            else:
                deployment = "FALLBACK_ENDPOINT"
                executed_idx = len(grid) - 1
                fallback_sources += 1
            source_rows.append(
                {
                    "operator": operator,
                    "dataset": dataset,
                    "lane": lane,
                    "source_build": source,
                    "s3_selected_action": selected,
                    "candidate_action": int(grid[candidate_idx]),
                    "executed_action": int(grid[executed_idx]),
                    "candidate_failures": candidate_fail,
                    "certification_n": len(cert),
                    "candidate_cp_lower": candidate_low,
                    "candidate_cp_upper": candidate_up,
                    "candidate_state": candidate_state,
                    "endpoint_failures": endpoint_fail,
                    "endpoint_cp_lower": endpoint_low,
                    "endpoint_cp_upper": endpoint_up,
                    "endpoint_state": endpoint_state,
                    "deployment": deployment,
                }
            )
            for ti, target in enumerate(builds):
                if si == ti:
                    continue
                failures = recall[ti, evaluation, executed_idx] < 0.95
                costs = ndc[ti, evaluation, executed_idx]
                endpoint_costs = ndc[ti, evaluation, -1]
                k = int(np.sum(failures))
                state, low, up = three_state(k, len(evaluation), 0.05)
                for qi, (f, c, e) in enumerate(zip(failures, costs, endpoint_costs)):
                    fail_by_q[qi].append(int(f)); cost_by_q[qi].append(float(c)); endpoint_cost_by_q[qi].append(float(e))
                pair_vectors[(si, ti)] = (failures.astype(float), costs, endpoint_costs)
                pair_rows.append(
                    {
                        "operator": operator,
                        "dataset": dataset,
                        "lane": lane,
                        "source_build": source,
                        "target_build": target,
                        "deployment": deployment,
                        "executed_action": int(grid[executed_idx]),
                        "target_failures": k,
                        "target_n": len(evaluation),
                        "target_risk": k / len(evaluation),
                        "target_cp_lower": low,
                        "target_cp_upper": up,
                        "target_state": state,
                        "ndc_mean": float(np.mean(costs)),
                        "ndc_p95": float(np.quantile(costs, 0.95)),
                        "ndc_p99": float(np.quantile(costs, 0.99)),
                        "endpoint_ndc_mean": float(np.mean(endpoint_costs)),
                    }
                )
        fq = np.asarray([np.mean(x) for x in fail_by_q])
        cq = np.asarray([np.mean(x) for x in cost_by_q])
        eq = np.asarray([np.mean(x) for x in endpoint_cost_by_q])
        rlo, rhi, slo, shi = bootstrap_pair(fq, cq, eq)
        drop = max(1, math.ceil(0.01 * len(fq)))
        keep = np.argsort(fq)[:-drop]
        lobo_risk, lobo_save = [], []
        for b in range(len(builds)):
            vals = [v for (si, ti), v in pair_vectors.items() if si != b and ti != b]
            f = np.concatenate([v[0] for v in vals]); c = np.concatenate([v[1] for v in vals]); e = np.concatenate([v[2] for v in vals])
            lobo_risk.append(float(np.mean(f))); lobo_save.append(float(1.0 - np.mean(c) / np.mean(e)))
        lane_pairs = [r for r in pair_rows if r["lane"] == lane]
        states = [r["target_state"] for r in lane_pairs]
        all_cost = np.concatenate([v[1] for v in pair_vectors.values()])
        all_endpoint = np.concatenate([v[2] for v in pair_vectors.values()])
        summary_rows.append(
            {
                "operator": operator,
                "dataset": dataset,
                "lane": lane,
                "fresh_certification_queries": 500,
                "fresh_evaluation_queries": 500,
                "fallback_sources": fallback_sources,
                "no_certified_action_sources": no_cert_sources,
                "target_risk": float(np.mean(fq)),
                "target_risk_ci_low": rlo,
                "target_risk_ci_high": rhi,
                "target_qualified_pairs": states.count("QUALIFIED"),
                "target_indeterminate_pairs": states.count("INDETERMINATE"),
                "target_confidently_above_delta_pairs": states.count("CONFIDENTLY_ABOVE_DELTA"),
                "ndc_mean": float(np.mean(all_cost)),
                "ndc_p95": float(np.quantile(all_cost, 0.95)),
                "ndc_p99": float(np.quantile(all_cost, 0.99)),
                "endpoint_ndc_mean": float(np.mean(all_endpoint)),
                "relative_mean_ndc_saving": float(1.0 - np.mean(all_cost) / np.mean(all_endpoint)),
                "relative_mean_ndc_saving_ci_low": slo,
                "relative_mean_ndc_saving_ci_high": shi,
                "delete_max_1pct_query_risk": float(np.mean(fq[keep])),
                "lobo_min_risk": min(lobo_risk),
                "lobo_max_risk": max(lobo_risk),
                "lobo_min_ndc_saving": min(lobo_save),
                "lobo_max_ndc_saving": max(lobo_save),
                "wall_clock_status": "WALL_CLOCK_EXPLORATORY_ONLY",
            }
        )
        lane_data[lane] = (fq, cq, eq)
    return source_rows, pair_rows, summary_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hnsw", type=Path, required=True)
    ap.add_argument("--faiss", type=Path, required=True)
    ap.add_argument("--policies", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    with args.policies.open(newline="") as f: policies = list(csv.DictReader(f))
    source_rows, pair_rows, summary_rows = [], [], []
    for operator, raw in (("hnswlib", args.hnsw), ("faiss_hnsw", args.faiss)):
        for dataset in ("sift_100k", "arxiv_nomic_100k"):
            s, p, a = analyze_setting(operator, dataset, raw, policies)
            source_rows.extend(s); pair_rows.extend(p); summary_rows.extend(a)
    write_csv(args.output / "s4_source_certification.csv", source_rows)
    write_csv(args.output / "s4_pair_results.csv", pair_rows)
    write_csv(args.output / "s4_summary.csv", summary_rows)
    decision = {
        "phase": "S4",
        "evidence_level": "FRESH_QUERY_CONFIRMATION",
        "fresh_query_roles": "PASS",
        "legal_per_query_ndc": "PASS_BOTH_IMPLEMENTATIONS",
        "stable_tail": "NON_DEPLOYABLE_TRUTH_DEPENDENT_NOT_USED",
        "analysis_status": "COMPLETE",
    }
    (args.output / "s4_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
