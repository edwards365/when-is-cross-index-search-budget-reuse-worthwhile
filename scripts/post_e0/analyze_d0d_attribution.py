#!/usr/bin/env python3
"""Attribute frozen D0-D first divergences to scale, proxy tail, and edge origin."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from narhnsw.mpcc_selectors import frozen_radii, unit_rows


def read_matrix(path: Path) -> np.ndarray:
    with path.open("rb") as stream:
        rows, columns = struct.unpack("<QQ", stream.read(16))
        values = np.fromfile(stream, dtype="<f4")
    if values.size != rows * columns:
        raise ValueError(f"invalid matrix {path}")
    return values.reshape(rows, columns)


def read_mapping(path: Path, points: int) -> np.ndarray:
    data = np.loadtxt(path, delimiter=",", skiprows=1, dtype=np.int64)
    if data.shape != (points, 2) or not np.array_equal(data[:, 0], np.arange(points)):
        raise ValueError(f"invalid mapping {path}")
    return data[:, 1]


def read_plan(path: Path) -> set[tuple[int, int]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return {(int(row["source"]), int(row["target"])) for row in csv.DictReader(stream)}


def read_adjacency(path: Path, points: int) -> list[np.ndarray]:
    values: list[list[int]] = [[] for _ in range(points)]
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            values[int(row["source"])].append(int(row["target"]))
    return [np.asarray(items, dtype=np.int32) for items in values]


def nearest_proxy_state_distance(
    query: np.ndarray,
    center: np.ndarray,
    local_points: np.ndarray,
    local_scale: float,
    event_seed: int,
    samples: int,
) -> float:
    rng = np.random.default_rng(event_seed)
    radii, _ = frozen_radii(samples, rng)
    directions = unit_rows(np.asarray(local_points, dtype=np.float64) - center)
    direction_ids = rng.integers(0, len(directions), samples)
    state = (np.asarray(query, dtype=np.float64) - center) / local_scale
    dot = directions @ state
    squared = np.dot(state, state) + radii * radii - 2.0 * radii * dot[direction_ids]
    return float(np.sqrt(np.maximum(squared.min(), 0.0)))


def progress_count(
    query: np.ndarray,
    source: int,
    adjacency: list[np.ndarray],
    mapping: np.ndarray,
    vectors: np.ndarray,
) -> int:
    neighbors = adjacency[source]
    if not len(neighbors):
        return 0
    source_vector = np.asarray(vectors[mapping[source]], dtype=np.float64)
    source_distance = np.linalg.norm(np.asarray(query, dtype=np.float64) - source_vector)
    neighbor_vectors = np.asarray(vectors[mapping[neighbors]], dtype=np.float64)
    distances = np.linalg.norm(neighbor_vectors - query, axis=1)
    return int(np.count_nonzero(distances < source_distance))


def origin(
    source: int,
    target: int,
    original_plan: set[tuple[int, int]],
    primary_plan: set[tuple[int, int]],
) -> str:
    if (source, target) in original_plan:
        return "SOURCE_SELECTION_CHANGED" if (source, target) not in primary_plan else "REVERSE_PRUNING"
    if (target, source) in original_plan:
        return "RECIPROCAL_FROM_CHANGED_SELECTION" if (target, source) not in primary_plan else "REVERSE_PRUNING"
    return "UNRESOLVED_EDGE_ORIGIN"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--protocol", type=Path, default=Path("preregistration/post_e0_d0_dfg.yaml")
    )
    parser.add_argument("--trace", type=Path, default=Path("results/post_e0/d0d"))
    parser.add_argument("--e0", type=Path, default=Path("results/gb_mpcc/e0"))
    parser.add_argument("--output", type=Path, default=Path("results/post_e0/d0d_attribution"))
    parser.add_argument("--report", type=Path, default=Path("reports/post_e0_first_divergence.md"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    if protocol["firewall"]["formal_test_access"] != "forbidden":
        raise PermissionError("D0-D firewall open")
    matrix = json.loads((args.trace / "matrix_summary.json").read_text(encoding="utf-8"))
    if (
        matrix["status"] != "D0D_TRACE_MATRIX_COMPLETE"
        or not matrix["all_reconstructions_exact_e0"]
        or not matrix["all_temporary_indexes_deleted"]
    ):
        raise ValueError("D0-D trace matrix incomplete")
    if args.output.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite D0-D attribution")
    args.output.mkdir(parents=True)

    train_manifest = json.loads(Path("results/gb_mpcc/r0_inputs/manifest.json").read_text())
    train = {item["dataset"]: item for item in train_manifest["inputs"]}
    search_manifest = json.loads((args.e0 / "search_inputs" / "manifest.json").read_text())
    search = {item["dataset"]: item for item in search_manifest["datasets"]}
    samples = 2048
    thresholds = protocol["d0d_first_divergence"]["classification_thresholds"]
    enriched: list[dict[str, Any]] = []
    run_summaries = []

    for dataset in protocol["matrix"]["datasets"]:
        record = train[dataset]
        vectors = np.memmap(
            record["path"],
            dtype=np.float32,
            mode="r",
            shape=(int(record["points"]), int(record["dimensions"])),
        )
        queries = read_matrix(Path(search[dataset]["queries"]))
        cache = np.load(args.e0 / "local_neighbors" / f"{dataset}.npz")
        neighbor_ids = cache["neighbor_external_labels"]
        local_scales = cache["local_scales"]
        for seed in protocol["matrix"]["build_seeds"]:
            run_id = f"{dataset}-b{seed}"
            mapping = read_mapping(
                Path("results/gb_mpcc/r0_candidates") / run_id / "internal_to_external.csv",
                10000,
            )
            original_plan = read_plan(args.e0 / "audits" / f"{run_id}-original-plan.csv")
            primary_plan = read_plan(
                args.e0 / "plans" / run_id / "geometry_backbone_mpcc_R4.csv"
            )
            original_adjacency = read_adjacency(
                args.e0 / "runs" / run_id / "original_algorithm4" / "layer0_edges.csv.gz",
                10000,
            )
            primary_adjacency = read_adjacency(
                args.e0
                / "runs"
                / run_id
                / "geometry_backbone_mpcc_R4"
                / "layer0_edges.csv.gz",
                10000,
            )
            rows = []
            with gzip.open(
                args.trace / "runs" / run_id / "first_divergence.csv.gz",
                "rt",
                encoding="utf-8",
                newline="",
            ) as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                source = int(row["absent_source_internal"])
                target = int(row["absent_target_internal"])
                if source < 0 or target < 0:
                    raise ValueError(f"{run_id}: missing first Original-only edge")
                external_source = int(mapping[source])
                query = queries[int(row["query_id"])]
                center = np.asarray(vectors[external_source], dtype=np.float64)
                scale = float(local_scales[external_source])
                normalized_radius = float(np.linalg.norm(query - center) / scale)
                proxy_distance = nearest_proxy_state_distance(
                    query,
                    center,
                    vectors[neighbor_ids[external_source]],
                    scale,
                    202608240000 + int(seed) * 1000003 + external_source,
                    samples,
                )
                original_progress = progress_count(
                    query, source, original_adjacency, mapping, vectors
                )
                primary_progress = progress_count(
                    query, source, primary_adjacency, mapping, vectors
                )
                item = dict(row)
                item.update(
                    edge_origin=origin(source, target, original_plan, primary_plan),
                    normalized_radius=normalized_radius,
                    nearest_proxy_state_distance=proxy_distance,
                    original_effective_progress_edges=original_progress,
                    primary_effective_progress_edges=primary_progress,
                    effective_progress_edge_advantage=original_progress - primary_progress,
                )
                enriched.append(item)
            run_summaries.append({"run_id": run_id, "rows": len(rows)})
        del vectors

    by_run: dict[str, list[dict[str, Any]]] = {}
    for row in enriched:
        by_run.setdefault(row["run_id"], []).append(row)
    for run_id, rows in by_run.items():
        tail = float(
            np.quantile(
                [float(row["nearest_proxy_state_distance"]) for row in rows],
                thresholds["proxy_tail_nearest_state_quantile"],
            )
        )
        for row in rows:
            row["proxy_tail_threshold"] = tail
            if row["edge_origin"] in {
                "RECIPROCAL_FROM_CHANGED_SELECTION",
                "REVERSE_PRUNING",
            }:
                classification = "RECIPROCAL_PRUNING_DAMAGE"
            elif float(row["normalized_radius"]) <= thresholds[
                "near_target_normalized_radius_max"
            ]:
                classification = "NEAR_TARGET_DAMAGE"
            elif float(row["nearest_proxy_state_distance"]) >= tail:
                classification = "PROXY_TAIL_FAILURE"
            elif int(row["effective_progress_edge_advantage"]) >= thresholds[
                "redundancy_original_effective_progress_edge_advantage_minimum"
            ]:
                classification = "REDUNDANCY_LOSS"
            elif int(row["first_queue_divergence"]) >= 0:
                classification = "QUEUE_ORDER_EFFECT"
            elif row["target_expanded_original"] == "1":
                classification = "GLOBAL_PATH_EFFECT"
            else:
                classification = "UNATTRIBUTED"
            row["classification"] = classification

    output_csv = args.output / "first_divergence_attribution.csv.gz"
    with gzip.open(output_csv, "wt", encoding="utf-8", newline="", compresslevel=6) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(enriched[0]))
        writer.writeheader()
        writer.writerows(enriched)
    summary: dict[str, Any] = {
        "status": "D0D_ATTRIBUTION_COMPLETE",
        "rows": len(enriched),
        "classification_counts": dict(Counter(row["classification"] for row in enriched)),
        "edge_origin_counts": dict(Counter(row["edge_origin"] for row in enriched)),
        "strict_progress_fraction": float(
            np.mean([row["strict_progress"] == "1" for row in enriched])
        ),
        "beam_admissible_fraction": float(
            np.mean([row["beam_admissible"] == "1" for row in enriched])
        ),
        "target_is_direct_missed_truth_fraction": float(
            np.mean([row["target_is_missed_true_top10"] == "1" for row in enriched])
        ),
        "per_run": [],
        "classification_is_diagnostic_not_causal_proof": True,
        "new_graphs_built_for_attribution": False,
        "validation_dev_accessed": False,
        "formal_test_members_accessed": False,
    }
    for run_id, rows in sorted(by_run.items()):
        summary["per_run"].append(
            {
                "run_id": run_id,
                "rows": len(rows),
                "classification_counts": dict(Counter(row["classification"] for row in rows)),
                "edge_origin_counts": dict(Counter(row["edge_origin"] for row in rows)),
                "mean_normalized_radius": float(
                    np.mean([float(row["normalized_radius"]) for row in rows])
                ),
                "mean_proxy_distance": float(
                    np.mean([float(row["nearest_proxy_state_distance"]) for row in rows])
                ),
            }
        )
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Post-E0 D0-D first-divergence attribution",
        "",
        f"Rows: {len(enriched)} harmed query-ef pairs across 9 frozen graph pairs.",
        "",
        "| Diagnostic class | Count | Fraction |",
        "|---|---:|---:|",
    ]
    for label, count in Counter(row["classification"] for row in enriched).most_common():
        lines.append(f"| {label} | {count} | {count / len(enriched):.4f} |")
    lines.extend(
        [
            "",
            "Classification follows the preregistered exclusive precedence and is a diagnostic "
            "partition, not a causal proof. Counterfactual D0-E and add-back D0-F are still required.",
            "",
            "No new ef point, validation-dev member, or formal-test member was accessed. Temporary "
            "indexes used for exact trace reconstruction were deleted before this analysis.",
        ]
    )
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "per_run"}))


if __name__ == "__main__":
    main()
