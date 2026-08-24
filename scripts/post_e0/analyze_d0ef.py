#!/usr/bin/env python3
"""Analyze frozen D0-E/F curves with an outcome-blind conservative aggregation rule."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

BUDGETS = {"addback_0p0": 0.0, "addback_0p01": 0.01, "addback_0p025": 0.025,
           "addback_0p05": 0.05, "addback_0p1": 0.10, "addback_0p15": 0.15,
           "addback_0p2": 0.20, "addback_0p25": 0.25}


def load_run(path: Path) -> dict[str, dict[tuple[int, int], tuple[float, float]]]:
    modes: dict[str, dict[tuple[int, int], tuple[float, float]]] = defaultdict(dict)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            modes[row["mode"]][(int(row["ef_search"]), int(row["query_id"]))] = (
                float(row["recall"]), float(row["ndc"]))
    return modes


def metrics(modes: dict[str, dict[tuple[int, int], tuple[float, float]]], mode: str) -> dict[str, Any]:
    original, primary, candidate = modes["original"], modes["primary"], modes[mode]
    harmed = [key for key in original if original[key][0] > primary[key][0]]
    recall_loss = sum(original[key][0] - primary[key][0] for key in harmed)
    recall_recovered = sum(candidate[key][0] - primary[key][0] for key in harmed)
    primary_ndc_gain = sum(original[key][1] - primary[key][1] for key in harmed)
    retained_ndc_gain = sum(original[key][1] - candidate[key][1] for key in harmed)
    return {
        "harmed_query_ef_pairs": len(harmed),
        "recall_loss": recall_loss,
        "recall_recovered": recall_recovered,
        "recall_loss_recovery": recall_recovered / recall_loss if recall_loss else None,
        "primary_ndc_improvement": primary_ndc_gain,
        "retained_primary_ndc_improvement": (
            retained_ndc_gain / primary_ndc_gain if primary_ndc_gain > 0 else None),
        "mean_recall": sum(value[0] for value in candidate.values()) / len(candidate),
        "mean_ndc": sum(value[1] for value in candidate.values()) / len(candidate),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/post_e0_d0_dfg.yaml"))
    parser.add_argument("--input", type=Path, default=Path("results/post_e0/d0ef"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0ef_analysis"))
    parser.add_argument("--manifest", type=Path, default=Path("manifests/post_e0_d0f_decision.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/post_e0_d0ef.md"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    matrix = json.loads((args.input / "matrix_summary.json").read_text(encoding="utf-8"))
    if (matrix["status"] != "D0EF_COUNTERFACTUAL_MATRIX_COMPLETE"
            or not matrix["all_native_adjacency_checks_exact"]
            or not matrix["all_temporary_indexes_deleted"]
            or matrix["validation_dev_accessed"] or matrix["formal_test_members_accessed"]):
        raise ValueError("D0-E/F matrix incomplete or unsafe")
    gate = protocol["d0f_oracle_addback"]["local_repairability"]
    min_recovery = float(gate["minimum_recall_loss_recovery"])
    min_retained = float(gate["minimum_retained_primary_ndc_improvement"])
    max_budget = float(gate["maximum_addback_fraction"])
    args.output.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    run_pass: dict[str, bool] = {}
    d0e: list[dict[str, Any]] = []
    for record in matrix["records"]:
        run_id, dataset = record["run_id"], record["dataset"]
        modes = load_run(args.input / "runs" / run_id / "counterfactual.csv.gz")
        if modes["addback_0p0"] != modes["primary"]:
            raise ValueError(f"{run_id}: zero add-back differs from Primary")
        qualifying = []
        for mode, budget in BUDGETS.items():
            value = metrics(modes, mode)
            passed = (budget <= max_budget and value["recall_loss_recovery"] is not None
                      and value["recall_loss_recovery"] >= min_recovery
                      and value["retained_primary_ndc_improvement"] is not None
                      and value["retained_primary_ndc_improvement"] >= min_retained)
            row = {"run_id": run_id, "dataset": dataset, "build_seed": record["build_seed"],
                   "mode": mode, "budget_fraction": budget, "passes_thresholds": passed, **value}
            rows.append(row)
            if passed:
                qualifying.append(budget)
        run_pass[run_id] = bool(qualifying)
        for mode in ("intersection", "union"):
            d0e.append({"run_id": run_id, "dataset": dataset, "build_seed": record["build_seed"],
                        "mode": mode, **metrics(modes, mode)})
    curve_path = args.output / "addback_curves.csv"
    with curve_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (args.output / "d0e_counterfactuals.json").write_text(
        json.dumps(d0e, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    datasets = {}
    for dataset in protocol["matrix"]["datasets"]:
        ids = [f"{dataset}-b{seed}" for seed in protocol["matrix"]["build_seeds"]]
        count = sum(run_pass[run_id] for run_id in ids)
        datasets[dataset] = {"passing_seeds": count, "total_seeds": 3,
                             "passes_two_of_three": count >= 2}
    passed = all(value["passes_two_of_three"] for value in datasets.values())
    decision = protocol["d0f_oracle_addback"]["pass_label"] if passed else protocol["d0f_oracle_addback"]["fail_label"]
    manifest = {
        "status": decision, "aggregation_rule": "all_datasets_at_least_two_of_three_seeds",
        "aggregation_rule_scope": "conservative_operational_rule_frozen_before_curve_inspection",
        "thresholds": {"maximum_addback_fraction": max_budget,
                       "minimum_recall_loss_recovery": min_recovery,
                       "minimum_retained_primary_ndc_improvement": min_retained},
        "datasets": datasets, "runs": run_pass, "matrix_rows": matrix["rows"],
        "oracle_query_supervision_diagnostic_only": True,
        "causal_claim_scope": "diagnostic_not_algorithmic",
        "new_ef_points": False, "validation_dev_accessed": False,
        "formal_test_members_accessed": False, "bep_implemented": False,
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = ["# Post-E0 D0-E/F counterfactual and oracle add-back result", "",
              f"Machine decision: `{decision}`.", "",
              "The decision uses the frozen 25%/80%/50% thresholds. Conservatively, each dataset "
              "must pass in at least two of three build seeds; this operational aggregation rule was "
              "committed before inspecting the generated curves.", "", "| Dataset | Passing seeds | Decision |",
              "|---|---:|---|" ]
    for dataset, value in datasets.items():
        report.append(f"| {dataset} | {value['passing_seeds']}/3 | {'PASS' if value['passes_two_of_three'] else 'FAIL'} |")
    report += ["", "These are oracle-supervised diagnostic counterfactuals, not a deployable algorithm "
               "and not evidence that E0 passed. No validation-dev or formal-test members were accessed.", ""]
    args.report.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
