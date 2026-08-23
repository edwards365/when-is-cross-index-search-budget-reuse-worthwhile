#!/usr/bin/env python3
"""Freeze Gate A from completed, sealed-development run artifacts.

The script is intentionally data-only: it never opens an HDF5 dataset and only reads
completed metadata/query/edge artifacts produced by the preregistered runners.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from narhnsw.gate_a_analysis import collapse_latency_rounds, curve_summary

DATASETS = ("sift_100k", "glove100_100k", "arxiv_nomic_100k")
BUILD_SEEDS = (7, 17, 29)
CONTROL_SEEDS = (101, 211, 307)
CORE_METHODS = ("original", "geometry", "ggr_0")
CONTROL_METHODS = ("geometry_safe_random", "shuffled_resistance")
TARGET_RECALL = 0.95
FINAL_LABEL = "RESISTANCE_SPECIFICITY_NOT_ESTABLISHED"


def expected_runs(dataset: str) -> list[tuple[str, str, int, int | None]]:
    rows: list[tuple[str, str, int, int | None]] = []
    for build_seed in BUILD_SEEDS:
        rows.extend(
            (f"{dataset}-{method}-b{build_seed}", method, build_seed, None)
            for method in CORE_METHODS
        )
        rows.extend(
            (
                f"{dataset}-{method}-b{build_seed}-c{control_seed}",
                method,
                build_seed,
                control_seed,
            )
            for method in CONTROL_METHODS
            for control_seed in CONTROL_SEEDS
        )
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _control_seed(value: object) -> int | None:
    return None if pd.isna(value) else int(value)


def load_dataset(raw: Path, dataset: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    frames: list[pd.DataFrame] = []
    run_records: list[dict[str, object]] = []
    for run_id, method, build_seed, control_seed in expected_runs(dataset):
        directories = [raw / run_id]
        supplement = raw / f"{run_id}-midpoints"
        if supplement.is_dir():
            directories.append(supplement)
        for directory in directories:
            metadata_path = directory / "metadata.json"
            query_path = directory / "queries.csv"
            edge_path = directory / "edges.csv"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("status") != "complete":
                raise ValueError(f"{directory.name}: incomplete")
            if metadata.get("formal_test_members_accessed") is not False:
                raise ValueError(f"{directory.name}: formal-test firewall failed")
            if set(metadata.get("accessed_hdf5_members", [])) != {"train"}:
                raise ValueError(f"{directory.name}: unexpected HDF5 member access")
            frame = collapse_latency_rounds(pd.read_csv(query_path))
            if frame.query_id.nunique() != 1000:
                raise ValueError(f"{directory.name}: expected 1,000 development queries")
            if set(frame.method) != {method} or set(frame.build_seed) != {build_seed}:
                raise ValueError(f"{directory.name}: run-key mismatch")
            if control_seed is not None and set(frame.control_seed) != {control_seed}:
                raise ValueError(f"{directory.name}: control-seed mismatch")
            frames.append(frame)
            run_records.append(
                {
                    "run_id": directory.name,
                    "dataset": dataset,
                    "method": method,
                    "build_seed": build_seed,
                    "control_seed": control_seed,
                    "status": "complete",
                    "formal_test_members_accessed": False,
                    "ef_values": sorted(int(value) for value in frame.ef_search.unique()),
                    "build_seconds": float(metadata["build_seconds"]),
                    "treatment_seconds": float(metadata["treatment_seconds"]),
                    "checksums": {
                        "metadata.json": sha256(metadata_path),
                        "queries.csv": sha256(query_path),
                        "edges.csv": sha256(edge_path),
                    },
                }
            )
    queries = pd.concat(frames, ignore_index=True)
    duplicate = queries.duplicated(
        ["method", "build_seed", "control_seed", "ef_search", "query_id"]
    )
    if duplicate.any():
        raise ValueError(f"{dataset}: duplicate query evidence across main/supplement runs")
    return queries, run_records


def endpoint_rows(curve: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.Series] = []
    keys = ["dataset", "method", "build_seed", "control_seed"]
    for _, group in curve.groupby(keys, dropna=False):
        sufficient = group[group.mean_recall >= TARGET_RECALL]
        if sufficient.empty:
            row = group.sort_values("ef_search").iloc[-1].copy()
            row["endpoint_reachable"] = False
        else:
            row = sufficient.sort_values(["p95_ndc", "ef_search"], kind="stable").iloc[0].copy()
            row["endpoint_reachable"] = True
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def improvement(candidate: float, baseline: float) -> float:
    """Return cost improvement versus baseline; positive is favorable."""

    return 100.0 * (baseline - candidate) / baseline


def summarize_dataset(queries: pd.DataFrame, records: list[dict[str, object]]) -> dict[str, object]:
    curve = curve_summary(queries)
    endpoint = endpoint_rows(curve)
    dataset = str(curve.dataset.iloc[0])
    core = endpoint[endpoint.method.isin(["original", "geometry", "ggr_0"])]
    reachable = bool(core.endpoint_reachable.all())
    seed_rows: dict[str, object] = {}
    if reachable:
        for build_seed in BUILD_SEEDS:
            build = endpoint[endpoint.build_seed == build_seed]
            ggr = build[build.method == "ggr_0"].iloc[0]
            geometry = build[build.method == "geometry"].iloc[0]
            random_cost = float(build[build.method == "geometry_safe_random"].p95_ndc.mean())
            shuffled_cost = float(build[build.method == "shuffled_resistance"].p95_ndc.mean())
            seed_rows[str(build_seed)] = {
                "ggr_ef_search": int(ggr.ef_search),
                "ggr_mean_recall": float(ggr.mean_recall),
                "ggr_mean_ndc": float(ggr.mean_ndc),
                "ggr_p50_ndc": float(ggr.p50_ndc),
                "ggr_p95_ndc": float(ggr.p95_ndc),
                "ggr_p99_ndc": float(ggr.p99_ndc),
                "ggr_p50_latency_us": float(ggr.p50_latency_ns / 1000),
                "ggr_p95_latency_us": float(ggr.p95_latency_ns / 1000),
                "ggr_p99_latency_us": float(ggr.p99_latency_ns / 1000),
                "ggr_improvement_vs_geometry_p95_ndc_percent": improvement(
                    ggr.p95_ndc, geometry.p95_ndc
                ),
                "ggr_improvement_vs_random_mean_p95_ndc_percent": improvement(
                    ggr.p95_ndc, random_cost
                ),
                "ggr_improvement_vs_shuffled_mean_p95_ndc_percent": improvement(
                    ggr.p95_ndc, shuffled_cost
                ),
            }
        status = "PRIMARY_ENDPOINT_REACHABLE"
    else:
        seed_rows = {}
        status = "PRIMARY_ENDPOINT_UNREACHABLE_WITHIN_PREREGISTERED_GRID"
    max_grid = curve[curve.ef_search == curve.ef_search.max()]
    return {
        "dataset": dataset,
        "status": status,
        "complete_main_runs": sum("-midpoints" not in str(r["run_id"]) for r in records),
        "complete_supplement_runs": sum("-midpoints" in str(r["run_id"]) for r in records),
        "failed_runs": 0,
        "formal_test_members_accessed": False,
        "max_grid_mean_recall": {
            "min": float(max_grid.mean_recall.min()),
            "max": float(max_grid.mean_recall.max()),
        },
        "primary_by_build_seed": seed_rows,
        "build_seconds": {
            "median": float(np.median([float(r["build_seconds"]) for r in records])),
            "max": float(max(float(r["build_seconds"]) for r in records)),
        },
        "treatment_seconds": {
            "median": float(np.median([float(r["treatment_seconds"]) for r in records])),
            "max": float(max(float(r["treatment_seconds"]) for r in records)),
        },
    }


def final_decision(datasets: list[dict[str, object]]) -> str:
    successes = 0
    for dataset in datasets:
        seeds = list(dataset["primary_by_build_seed"].values())
        stable = sum(
            row["ggr_improvement_vs_geometry_p95_ndc_percent"] > 0
            and row["ggr_improvement_vs_random_mean_p95_ndc_percent"] > 0
            and row["ggr_improvement_vs_shuffled_mean_p95_ndc_percent"] > 0
            for row in seeds
        ) >= 2
        successes += int(stable)
    return "GGR_SPECIFICITY_SUPPORTED" if successes >= 2 else FINAL_LABEL


def render_report(summary: dict[str, object]) -> str:
    datasets = {row["dataset"]: row for row in summary["datasets"]}
    lines = [
        "# Gate A final frozen result",
        "",
        f"Final label: **{summary['final_label']}**.",
        "",
        "All 81 preregistered main runs completed without failure. SIFT used five",
        "triggered midpoint supplements and Arxiv used 27 uniform midpoint supplements;",
        "GloVe triggered none. Every audited artifact records only the `train` HDF5",
        "member and `formal_test_members_accessed=false`; formal test data remain sealed.",
        "",
        "| Dataset | Frozen endpoint status | GGR improvement vs Geometry by build seed |",
        "| --- | --- | --- |",
    ]
    for name in DATASETS:
        row = datasets[name]
        if row["primary_by_build_seed"]:
            effects = ", ".join(
                f"b{seed} {values['ggr_improvement_vs_geometry_p95_ndc_percent']:+.3f}%"
                for seed, values in row["primary_by_build_seed"].items()
            )
        else:
            effects = "undefined (Recall 0.95 unreachable)"
        lines.append(f"| {name} | {row['status']} | {effects} |")
    lines += [
        "",
        "Positive improvement is favorable. SIFT is weakly negative but seed directions are",
        "inconsistent and the result is not specific to resistance. Arxiv is consistently",
        "unfavorable to GGR versus Geometry and both matched negative controls. GloVe's",
        "primary endpoint is right-censored by the frozen efSearch grid and is neither a",
        "success nor a zero-effect result.",
        "",
        "The preregistered requirement—stable superiority over Geometry, matched random,",
        "and shuffled-resistance controls on at least two datasets and most seeds—is not",
        "met. The GGR development direction is frozen and receives no further tuning.",
        "Effective-resistance mathematics and engineering feasibility remain valid, but",
        "resistance-specific HNSW navigation or performance benefit is not established.",
        "",
        "Detailed p50/p95/p99 NDC, latency, Recall, build cost, run identities, and SHA-256",
        "evidence hashes are in `manifests/gate_a/gate_a_final.json`,",
        "`completed_run_matrix.json`, and `result_checksums.json`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("results/gate_a/raw"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("manifests/gate_a"))
    parser.add_argument("--report", type=Path, default=Path("reports/gate_a_final.md"))
    args = parser.parse_args()

    dataset_summaries: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    for dataset in DATASETS:
        queries, dataset_records = load_dataset(args.raw, dataset)
        dataset_summaries.append(summarize_dataset(queries, dataset_records))
        records.extend(dataset_records)
    summary = {
        "schema_version": 1,
        "gate": "G0",
        "primary_endpoint": "minimum observed p95 NDC at mean Recall@10 >= 0.95",
        "formal_test_members_accessed": False,
        "datasets": dataset_summaries,
        "final_label": final_decision(dataset_summaries),
        "old_direction_frozen": True,
    }
    if summary["final_label"] != FINAL_LABEL:
        raise ValueError("observed result unexpectedly conflicts with frozen stop rule")

    args.manifest_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    (args.manifest_dir / "gate_a_final.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.manifest_dir / "completed_run_matrix.json").write_text(
        json.dumps({"schema_version": 1, "runs": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksums = {
        str(record["run_id"]): record["checksums"]
        for record in records
    }
    (args.manifest_dir / "result_checksums.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": ["metadata.json", "queries.csv", "edges.csv"],
                "checksums": checksums,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    args.report.write_text(render_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
