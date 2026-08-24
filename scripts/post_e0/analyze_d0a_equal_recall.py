#!/usr/bin/env python3
"""Observed-point equal-recall Pareto analysis for frozen Post-E0 Gate D0-A."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def means(path: Path, efs: list[int]) -> dict[int, tuple[float, float]]:
    recall = {ef: [] for ef in efs}
    ndc = {ef: [] for ef in efs}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if int(row["latency_round"]) != 0:
                continue
            ef = int(row["ef_search"])
            recall[ef].append(float(row["recall_at_10"]))
            ndc[ef].append(float(row["ndc"]))
    if any(len(recall[ef]) != 500 or len(ndc[ef]) != 500 for ef in efs):
        raise ValueError(f"incomplete query matrix {path}")
    return {ef: (float(np.mean(recall[ef])), float(np.mean(ndc[ef]))) for ef in efs}


def envelope(points: dict[int, tuple[float, float]], target: float) -> dict[str, Any]:
    eligible = [(ndc, ef, recall) for ef, (recall, ndc) in points.items() if recall >= target]
    if not eligible:
        return {"reachable": False, "ef": None, "recall": None, "ndc": None}
    ndc, ef, recall = min(eligible)
    return {"reachable": True, "ef": ef, "recall": recall, "ndc": ndc}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path("preregistration/post_e0_d0.yaml")
    )
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0a"))
    parser.add_argument("--report", type=Path, default=Path("reports/post_e0_equal_recall.md"))
    args = parser.parse_args()

    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_d0a_analysis":
        raise PermissionError("D0-A protocol is not frozen")
    firewall = protocol["firewall"]
    if (
        firewall["validation_dev_access"] != "forbidden"
        or firewall["formal_test_access"] != "forbidden"
        or firewall["new_graph_construction"] != "forbidden_in_d0a"
        or firewall["new_ef_points"] != "forbidden_in_d0a"
        or firewall["extrapolation"] != "forbidden"
    ):
        raise PermissionError("D0-A firewall changed")
    parent = json.loads(Path(protocol["parent_manifest"]).read_text(encoding="utf-8"))
    if parent["status"] != protocol["parent_e0_decision"] or parent["e1_authorized"]:
        raise ValueError("frozen E0 parent decision mismatch")
    matrix = json.loads((args.e0 / "graph_matrix_summary.json").read_text(encoding="utf-8"))
    if matrix["graphs"] != 117 or not matrix["all_temporary_indexes_deleted"]:
        raise ValueError("frozen E0 matrix incomplete")
    if args.output.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite D0-A output")
    args.output.mkdir(parents=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    gate = protocol["d0a"]
    datasets = list(gate["datasets"])
    seeds = [int(seed) for seed in gate["build_seeds"]]
    efs = [int(ef) for ef in gate["ef_search"]]
    methods = list(gate["methods"])
    primary = str(gate["primary"])
    all_points: dict[tuple[str, int, str], dict[int, tuple[float, float]]] = {}
    input_hashes: dict[str, str] = {}
    for dataset in datasets:
        for seed in seeds:
            run_id = f"{dataset}-b{seed}"
            for method in methods:
                path = args.e0 / "runs" / run_id / method / "query_metrics.csv.gz"
                all_points[(dataset, seed, method)] = means(path, efs)
                input_hashes[f"{run_id}/{method}"] = sha256(path)

    rows: list[dict[str, Any]] = []
    seed_decisions: dict[str, Any] = {}
    for dataset in datasets:
        dataset_seeds = []
        for seed in seeds:
            maximum = {
                method: max(recall for recall, _ in all_points[(dataset, seed, method)].values())
                for method in methods
            }
            highest_common = min(maximum.values())
            targets = [float(target) for target in gate["fixed_targets"] if target <= highest_common]
            targets.append(highest_common)
            targets = sorted(set(targets))
            target_passes = []
            for target in targets:
                costs = {
                    method: envelope(all_points[(dataset, seed, method)], target)
                    for method in methods
                }
                if not all(item["reachable"] for item in costs.values()):
                    raise RuntimeError("common-support target unexpectedly unreachable")
                primary_cost = float(costs[primary]["ndc"])
                original_cost = float(costs["original_algorithm4"]["ndc"])
                improvement = (original_cost - primary_cost) / original_cost
                target_pass = (
                    improvement >= 0.01
                    and primary_cost <= float(costs["geometry"]["ndc"])
                    and primary_cost < float(costs["geometry_backbone_random_R4"]["ndc"])
                    and primary_cost
                    < float(costs["geometry_backbone_mpcc_shuffled_R4"]["ndc"])
                )
                target_passes.append(target_pass)
                for method in methods:
                    item = costs[method]
                    rows.append(
                        {
                            "dataset": dataset,
                            "build_seed": seed,
                            "target_recall": target,
                            "target_role": "highest_common"
                            if target == highest_common
                            else "fixed",
                            "method": method,
                            "selected_ef": item["ef"],
                            "observed_recall": item["recall"],
                            "observed_ndc": item["ndc"],
                            "primary_improvement_vs_original": improvement
                            if method == primary
                            else "",
                            "target_pass": target_pass if method == primary else "",
                            "interpolation_used": False,
                            "extrapolation_used": False,
                        }
                    )
            seed_pass = bool(target_passes) and all(target_passes)
            dataset_seeds.append(
                {
                    "build_seed": seed,
                    "highest_common_recall": highest_common,
                    "evaluated_targets": targets,
                    "all_targets_pass": seed_pass,
                }
            )
        positive = sum(item["all_targets_pass"] for item in dataset_seeds)
        seed_decisions[dataset] = {
            "positive_seeds": positive,
            "dataset_pass": positive >= 2,
            "seeds": dataset_seeds,
        }

    passing_datasets = sum(item["dataset_pass"] for item in seed_decisions.values())
    passed = passing_datasets >= 2
    decision = {
        "schema_version": 1,
        "gate": "Post-E0 D0-A observed-point equal-recall Pareto",
        "status": "PASS_CONTINUE_D0" if passed else "FAIL_STOP",
        "label": "EQUAL_RECALL_EFFICIENCY_SIGNAL" if passed else gate["failure_label"],
        "next_action": "CONTINUE_D0_B" if passed else gate["failure_action"],
        "passing_datasets": passing_datasets,
        "required_passing_datasets": 2,
        "dataset_decisions": seed_decisions,
        "observed_ef_only": True,
        "interpolation_used": False,
        "extrapolation_used": False,
        "new_graphs_built": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
        "adaptive_tuning_performed": False,
        "parent_manifest_sha256": sha256(Path(protocol["parent_manifest"])),
        "protocol_sha256": sha256(args.protocol),
        "input_query_metric_sha256": input_hashes,
    }
    with (args.output / "equal_recall_points.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Post-E0 Gate D0-A: observed-point equal-recall Pareto",
        "",
        f"Decision: **{decision['status']} / {decision['label']}**.",
        "",
        "Only the six frozen E0 ef points were used. No interpolation, extrapolation, new graph, "
        "validation-dev, or formal-test access was permitted.",
        "",
        "| Dataset | Passing seeds | Dataset gate |",
        "|---|---:|:---:|",
    ]
    for dataset in datasets:
        item = seed_decisions[dataset]
        lines.append(
            f"| {dataset} | {item['positive_seeds']}/3 | "
            f"{'PASS' if item['dataset_pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            f"Overall passing datasets: {passing_datasets}/3; required: 2/3.",
            "",
            f"Next action: **{decision['next_action']}**.",
            "",
            "Machine-readable observed-point selections are in "
            "`results/post_e0/d0a/equal_recall_points.csv`; the full frozen decision and input "
            "hashes are in `results/post_e0/d0a/decision.json`.",
        ]
    )
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in decision.items() if key != "input_query_metric_sha256"}))


if __name__ == "__main__":
    main()
