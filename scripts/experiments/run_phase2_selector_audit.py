#!/usr/bin/env python
"""Run a construction-only GGR structural audit without opening formal test data."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import hnswlib
import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.ggr import geometry_guarded_resistance_selection  # noqa: E402
from narhnsw.resistance import (  # noqa: E402
    edge_leverage_scores,
    effective_resistance_matrix,
    gaussian_weight_graph,
)


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def local_scheme_a(
    points: np.ndarray,
    center: int,
    candidates: np.ndarray,
    construction_neighbors: np.ndarray,
) -> np.ndarray:
    ids = np.concatenate([[center], candidates])
    positions = {int(node): offset for offset, node in enumerate(ids)}
    adjacency = np.zeros((len(ids), len(ids)), dtype=bool)
    for source_offset, source in enumerate(ids):
        for target in construction_neighbors[int(source)]:
            target_offset = positions.get(int(target))
            if target_offset is not None and target_offset != source_offset:
                adjacency[source_offset, target_offset] = True
    adjacency |= adjacency.T
    adjacency[0, 1:] = True
    adjacency[1:, 0] = True
    weights = gaussian_weight_graph(points[ids], adjacency)
    return edge_leverage_scores(weights, effective_resistance_matrix(weights))[0, 1:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("raw output directory already exists and will not be overwritten")
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    manifest_path = REPO / config["manifest"]
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    source_path = REPO / manifest["local_path"]
    if sha256(source_path) != manifest["sha256"]:
        raise ValueError("dataset checksum does not match the frozen manifest")

    started = time.perf_counter()
    with h5py.File(source_path, "r") as handle:
        train = handle["train"]
        if train.shape[1] != manifest["dimensions"]:
            raise ValueError("construction-vector dimension mismatch")
        points = np.asarray(train[: config["construction_vectors"]], dtype=np.float32)
    load_seconds = time.perf_counter() - started

    index = hnswlib.Index(space="l2", dim=points.shape[1])
    index.init_index(
        max_elements=len(points),
        M=config["M"],
        ef_construction=config["ef_construction"],
        random_seed=config["seed"],
    )
    index.set_num_threads(config["threads"])
    build_started = time.perf_counter()
    index.add_items(points, np.arange(len(points)))
    build_seconds = time.perf_counter() - build_started
    index.set_ef(config["candidate_ef_search"])
    labels, _ = index.knn_query(points, k=config["candidate_count"] + 1)
    construction_neighbors = np.empty((len(points), config["candidate_count"]), dtype=int)
    for node, row in enumerate(labels):
        filtered = row[row != node][: config["candidate_count"]]
        if len(filtered) != config["candidate_count"]:
            raise RuntimeError("candidate query did not return enough distinct non-self labels")
        construction_neighbors[node] = filtered

    rng = np.random.default_rng(config["seed"])
    centers = np.sort(
        rng.choice(len(points), size=config["audited_centers"], replace=False)
    )
    rows: list[dict[str, float | int | str]] = []
    audit_started = time.perf_counter()
    for center in centers:
        candidates = construction_neighbors[center]
        leverage = local_scheme_a(points, int(center), candidates, construction_neighbors)
        for epsilon in config["epsilon_candidates"]:
            result = geometry_guarded_resistance_selection(
                points[center],
                points[candidates],
                leverage,
                config["M"],
                epsilon=epsilon,
                tolerance=config["objective_tolerance"],
            )
            rows.append(
                {
                    "center": int(center),
                    "epsilon": float(epsilon),
                    "swaps": len(result.swaps),
                    "geometry_star": result.geometry_star,
                    "geometry_final": result.geometry_final,
                    "geometry_relative_loss": (
                        0.0
                        if result.geometry_star == 0
                        else (result.geometry_star - result.geometry_final) / result.geometry_star
                    ),
                    "leverage_initial": result.leverage_initial,
                    "leverage_final": result.leverage_final,
                    "leverage_gain": result.leverage_final - result.leverage_initial,
                    "termination": result.termination,
                }
            )
    audit_seconds = time.perf_counter() - audit_started
    frame = pd.DataFrame(rows)
    summary = (
        frame.groupby("epsilon")
        .agg(
            centers=("center", "count"),
            centers_with_swaps=("swaps", lambda values: int((values > 0).sum())),
            total_swaps=("swaps", "sum"),
            mean_geometry_relative_loss=("geometry_relative_loss", "mean"),
            max_geometry_relative_loss=("geometry_relative_loss", "max"),
            mean_leverage_gain=("leverage_gain", "mean"),
            max_leverage_gain=("leverage_gain", "max"),
        )
        .reset_index()
    )
    args.output.mkdir(parents=True)
    frame.to_csv(args.output / "per_center.csv", index=False)
    summary.to_csv(args.output / "summary.csv", index=False)
    (args.output / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    metadata = {
        "run_id": config["run_id"],
        "status": "development_structural_audit_not_search_performance",
        "formal_test_members_accessed": False,
        "dataset_sha256": manifest["sha256"],
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "load_seconds": load_seconds,
        "build_seconds": build_seconds,
        "audit_seconds": audit_seconds,
        "rows": len(frame),
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
