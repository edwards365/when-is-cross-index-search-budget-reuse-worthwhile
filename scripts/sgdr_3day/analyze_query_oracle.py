#!/usr/bin/env python3
"""Compute the frozen SGDR Gate-O query-selector oracle and fallback bounds."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def describe(values: list[float]) -> dict[str, float]:
    return {"mean": sum(values) / len(values), "p50": percentile(values, 0.50),
            "p95": percentile(values, 0.95), "p99": percentile(values, 0.99)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=Path("results/post_e0/d0ef"))
    parser.add_argument("--output", type=Path, default=Path("results/sgdr_3day/gate_o_query_oracle"))
    args = parser.parse_args()
    matrix = json.loads((args.matrix / "matrix_summary.json").read_text(encoding="utf-8"))
    if (matrix["status"] != "D0EF_COUNTERFACTUAL_MATRIX_COMPLETE"
            or not matrix["all_native_adjacency_checks_exact"]
            or not matrix["all_temporary_indexes_deleted"]
            or matrix["validation_dev_accessed"] or matrix["formal_test_members_accessed"]):
        raise ValueError("frozen D0-E/F input is incomplete or unsafe")
    args.output.mkdir(parents=True, exist_ok=False)
    summaries, break_even = [], []
    dataset_runs: dict[str, list[dict]] = defaultdict(list)
    for record in matrix["records"]:
        run_id, dataset = record["run_id"], record["dataset"]
        modes: dict[str, dict[tuple[int, int], tuple[float, float]]] = defaultdict(dict)
        with gzip.open(args.matrix / "runs" / run_id / "counterfactual.csv.gz",
                       "rt", encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["mode"] in ("original", "primary"):
                    modes[row["mode"]][(int(row["ef_search"]), int(row["query_id"]))] = (
                        float(row["recall"]), float(row["ndc"]))
        original, primary = modes["original"], modes["primary"]
        if len(original) != 3000 or original.keys() != primary.keys():
            raise ValueError(f"{run_id}: expected paired 500-query x 6-ef rows")
        oracle_cost, original_cost, savings, safe = [], [], [], 0
        for key, (o_recall, o_cost) in original.items():
            r_recall, r_cost = primary[key]
            use_r4 = r_recall >= o_recall
            chosen = r_cost if use_r4 else o_cost
            safe += use_r4
            original_cost.append(o_cost); oracle_cost.append(chosen)
            savings.append(max(0.0, o_cost - chosen))
        original_stats, oracle_stats = describe(original_cost), describe(oracle_cost)
        mean_improvement = 1.0 - oracle_stats["mean"] / original_stats["mean"]
        ranked = sorted(range(len(savings)), key=lambda i: savings[i], reverse=True)
        total_savings = sum(savings)
        top1_count = max(1, math.ceil(0.01 * len(savings)))
        top10_count = max(1, math.ceil(0.10 * len(savings)))
        kept = [i for i in range(len(savings)) if i not in set(ranked[:top1_count])]
        trimmed_improvement = 1.0 - sum(oracle_cost[i] for i in kept) / sum(original_cost[i] for i in kept)
        summary = {
            "run_id": run_id, "dataset": dataset, "build_seed": record["build_seed"],
            "pairs": len(original), "r4_safe_fraction": safe / len(original),
            "original": original_stats, "oracle": oracle_stats,
            "mean_ndc_improvement": mean_improvement,
            "p95_ndc_improvement": 1.0 - oracle_stats["p95"] / original_stats["p95"],
            "p99_ndc_improvement": 1.0 - oracle_stats["p99"] / original_stats["p99"],
            "top_1_percent_savings_share": sum(savings[i] for i in ranked[:top1_count]) / total_savings if total_savings else 0.0,
            "top_10_percent_savings_share": sum(savings[i] for i in ranked[:top10_count]) / total_savings if total_savings else 0.0,
            "trim_top_1_percent_mean_ndc_improvement": trimmed_improvement,
            "passes_primary_3_percent": mean_improvement >= 0.03,
            "passes_after_top_1_percent_trim": trimmed_improvement >= 0.03
        }
        summaries.append(summary); dataset_runs[dataset].append(summary)
        for ef in sorted({key[0] for key in original}):
            keys = [key for key in original if key[0] == ef]
            alpha = sum(primary[key][1] for key in keys) / sum(original[key][1] for key in keys)
            harmed = sum(primary[key][0] < original[key][0] for key in keys) / len(keys)
            for overhead in (0.0, 0.005, 0.01, 0.02):
                threshold = 1.0 - alpha - overhead
                break_even.append({"run_id": run_id, "dataset": dataset,
                    "build_seed": record["build_seed"], "ef_search": ef, "alpha": alpha,
                    "h": overhead, "maximum_fallback_fraction": threshold,
                    "actual_harmed_fraction": harmed, "break_even_possible": harmed < threshold})
    dataset_decisions = {}
    for dataset, runs in dataset_runs.items():
        passing = sum(x["passes_primary_3_percent"] and x["passes_after_top_1_percent_trim"] for x in runs)
        dataset_decisions[dataset] = {"passing_seeds": passing, "total_seeds": 3,
                                      "passes": passing >= 2}
    oracle_pass = sum(value["passes"] for value in dataset_decisions.values()) >= 2
    with (args.output / "run_summary.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["run_id", "dataset", "build_seed", "pairs", "r4_safe_fraction",
                  "mean_ndc_improvement", "p95_ndc_improvement", "p99_ndc_improvement",
                  "top_1_percent_savings_share", "top_10_percent_savings_share",
                  "trim_top_1_percent_mean_ndc_improvement", "passes_primary_3_percent",
                  "passes_after_top_1_percent_trim"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in summaries)
    with (args.output / "fallback_break_even.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(break_even[0])); writer.writeheader(); writer.writerows(break_even)
    result = {"status": "QUERY_ORACLE_PASS" if oracle_pass else "FAIL_ORACLE_UPPER_BOUND",
              "query_oracle_component_passes": oracle_pass, "datasets": dataset_decisions,
              "runs": summaries, "fallback_rows": len(break_even),
              "input_matrix_rows": matrix["rows"], "new_graphs_built": False,
              "new_ef_points": False, "validation_dev_accessed": False,
              "formal_test_members_accessed": False}
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "runs"}, sort_keys=True))


if __name__ == "__main__":
    main()
