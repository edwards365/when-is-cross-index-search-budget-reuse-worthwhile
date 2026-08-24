#!/usr/bin/env python3
"""Frozen Post-E0 D0-B safe/harmed query decomposition."""

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


FIELDS = ["recall_at_10", "ndc", "base_expansions", "traversal_hops"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path, efs: list[int]) -> dict[str, np.ndarray]:
    values = {field: [] for field in FIELDS}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if int(row["latency_round"]) == 0:
                for field in FIELDS:
                    values[field].append(float(row[field]))
    expected = len(efs) * 500
    if any(len(items) != expected for items in values.values()):
        raise ValueError(f"incomplete query metrics: {path}")
    return {field: np.asarray(items).reshape(len(efs), 500) for field, items in values.items()}


def describe(values: np.ndarray) -> dict[str, float | None]:
    if not len(values):
        return {"mean": None, "p50": None, "p95": None, "p99": None}
    return {
        "mean": float(values.mean()),
        "p50": float(np.quantile(values, 0.50)),
        "p95": float(np.quantile(values, 0.95)),
        "p99": float(np.quantile(values, 0.99)),
    }


def bootstrap_query_means(
    per_query: np.ndarray, replicates: int, generator: np.random.Generator
) -> tuple[float, float]:
    draws = np.empty(replicates, dtype=np.float64)
    for replicate in range(replicates):
        sample = generator.integers(0, len(per_query), size=len(per_query))
        draws[replicate] = per_query[sample].mean()
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return float(lower), float(upper)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path("preregistration/post_e0_d0b.yaml")
    )
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0b"))
    parser.add_argument(
        "--report", type=Path, default=Path("reports/post_e0_safe_harmed_queries.md")
    )
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_d0b_analysis":
        raise PermissionError("D0-B protocol is not frozen")
    firewall = protocol["firewall"]
    if (
        firewall["new_ef_points"] != "forbidden"
        or firewall["new_graph_construction"] != "forbidden"
        or firewall["validation_dev_access"] != "forbidden"
        or firewall["formal_test_access"] != "forbidden"
    ):
        raise PermissionError("D0-B firewall changed")
    parent = json.loads(Path(protocol["parent_manifest"]).read_text(encoding="utf-8"))
    if parent["status"] != protocol["parent_d0a_decision"]:
        raise ValueError("D0-A parent did not authorize D0-B")
    if args.output.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite D0-B output")
    args.output.mkdir(parents=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    analysis = protocol["analysis"]
    datasets = list(analysis["datasets"])
    seeds = [int(seed) for seed in analysis["build_seeds"]]
    efs = [int(ef) for ef in analysis["ef_search"]]
    original_name = str(analysis["original"])
    primary_name = str(analysis["primary"])
    generator = np.random.default_rng(int(analysis["bootstrap_seed"]))
    rows: list[dict[str, Any]] = []
    seed_decisions: dict[str, Any] = {}
    input_hashes: dict[str, str] = {}

    for dataset in datasets:
        seed_results = []
        for seed in seeds:
            run_id = f"{dataset}-b{seed}"
            paths = {
                "original": args.e0 / "runs" / run_id / original_name / "query_metrics.csv.gz",
                "primary": args.e0 / "runs" / run_id / primary_name / "query_metrics.csv.gz",
            }
            for role, path in paths.items():
                input_hashes[f"{run_id}/{role}"] = sha256(path)
            original = load(paths["original"], efs)
            primary = load(paths["primary"], efs)
            recall_delta = primary["recall_at_10"] - original["recall_at_10"]
            ndc_improvement = original["ndc"] - primary["ndc"]
            safe = recall_delta >= 0
            harmed = ~safe
            positive_safe_efs = 0
            for ef_index, ef in enumerate(efs):
                for group_name, mask in (("safe", safe[ef_index]), ("harmed", harmed[ef_index])):
                    delta = ndc_improvement[ef_index][mask]
                    recall = recall_delta[ef_index][mask]
                    row = {
                        "dataset": dataset,
                        "build_seed": seed,
                        "ef_search": ef,
                        "group": group_name,
                        "queries": int(mask.sum()),
                        "query_fraction": float(mask.mean()),
                        "mean_recall_difference": float(recall.mean()) if len(recall) else None,
                        "mean_ndc_improvement": float(delta.mean()) if len(delta) else None,
                        "ndc_improvement_p50": float(np.quantile(delta, 0.50))
                        if len(delta)
                        else None,
                        "primary_ndc_p50": float(np.quantile(primary["ndc"][ef_index][mask], 0.50))
                        if mask.any()
                        else None,
                        "primary_ndc_p95": float(np.quantile(primary["ndc"][ef_index][mask], 0.95))
                        if mask.any()
                        else None,
                        "primary_ndc_p99": float(np.quantile(primary["ndc"][ef_index][mask], 0.99))
                        if mask.any()
                        else None,
                        "mean_primary_base_expansions": float(
                            primary["base_expansions"][ef_index][mask].mean()
                        )
                        if mask.any()
                        else None,
                        "mean_primary_traversal_hops": float(
                            primary["traversal_hops"][ef_index][mask].mean()
                        )
                        if mask.any()
                        else None,
                    }
                    rows.append(row)
                if safe[ef_index].any() and ndc_improvement[ef_index][safe[ef_index]].mean() > 0:
                    positive_safe_efs += 1

            per_query_safe = []
            for query_id in range(500):
                mask = safe[:, query_id]
                if mask.any():
                    per_query_safe.append(float(ndc_improvement[:, query_id][mask].mean()))
            per_query_safe_array = np.asarray(per_query_safe)
            lower, upper = bootstrap_query_means(
                per_query_safe_array, int(analysis["bootstrap_replicates"]), generator
            )
            mean_safe = float(ndc_improvement[safe].mean())
            median_safe_query = float(np.median(per_query_safe_array))
            seed_pass = mean_safe > 0 and median_safe_query > 0 and positive_safe_efs >= 4
            seed_results.append(
                {
                    "build_seed": seed,
                    "safe_query_ef_fraction": float(safe.mean()),
                    "harmed_query_ef_fraction": float(harmed.mean()),
                    "mean_safe_ndc_improvement": mean_safe,
                    "median_per_query_safe_ndc_improvement": median_safe_query,
                    "safe_ndc_improvement_ci95": [lower, upper],
                    "positive_safe_ef_points": positive_safe_efs,
                    "seed_pass": seed_pass,
                }
            )
        positive_seeds = sum(item["seed_pass"] for item in seed_results)
        seed_decisions[dataset] = {
            "positive_seeds": positive_seeds,
            "dataset_pass": positive_seeds >= 2,
            "seeds": seed_results,
        }

    passing_datasets = sum(item["dataset_pass"] for item in seed_decisions.values())
    passed = passing_datasets >= 2
    decision = {
        "schema_version": 1,
        "gate": "Post-E0 D0-B safe/harmed query decomposition",
        "status": "PASS_CONTINUE_D0" if passed else "FAIL_STOP",
        "label": "SAFE_QUERY_EFFICIENCY_SIGNAL" if passed else analysis["failure_label"],
        "next_action": analysis["pass_action"] if passed else analysis["failure_action"],
        "passing_datasets": passing_datasets,
        "required_passing_datasets": 2,
        "dataset_decisions": seed_decisions,
        "unavailable_existing_artifacts": protocol["known_artifact_boundary"][
            "unavailable_without_trace_replay"
        ],
        "unavailable_fields_not_substituted": True,
        "new_ef_points": False,
        "new_graphs_built": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
        "adaptive_tuning_performed": False,
        "protocol_sha256": sha256(args.protocol),
        "parent_manifest_sha256": sha256(Path(protocol["parent_manifest"])),
        "input_query_metric_sha256": input_hashes,
    }
    with (args.output / "safe_harmed_by_ef.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Post-E0 Gate D0-B: safe/harmed query decomposition",
        "",
        f"Decision: **{decision['status']} / {decision['label']}**.",
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
            "Safe/harmed status is paired by query and existing ef. Positive NDC improvement means "
            "Original used more distance computations than R4. The bootstrap resamples query IDs "
            "within each build seed; ef points are not treated as independent repetitions.",
            "",
            "Candidate enqueue counts and terminal frontier states were not retained by E0 and "
            "were not replaced with proxy fields. Obtaining them requires a separately frozen "
            "trace replay in D0-D; no graph was rebuilt for D0-B.",
            "",
            f"Next action: **{decision['next_action']}**.",
        ]
    )
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in decision.items() if key != "input_query_metric_sha256"}))


if __name__ == "__main__":
    main()
