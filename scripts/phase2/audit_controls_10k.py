#!/usr/bin/env python
"""Audit specificity-control matching on sealed 10K construction subsets."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import hnswlib
import numpy as np
import pandas as pd
import psutil
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))
sys.path.insert(0, str(REPO))

from narhnsw.controls import (  # noqa: E402
    geometry_safe_random_selection,
    shuffled_resistance_selection,
)
from narhnsw.ggr import geometry_guarded_resistance_selection  # noqa: E402

from scripts.experiments.run_phase2_selector_audit import (  # noqa: E402
    local_scheme_a,
    sha256,
)


def load_construction(manifest: dict, count: int) -> tuple[np.ndarray, bool]:
    source = REPO / manifest["local_path"]
    if sha256(source) != manifest["sha256"]:
        raise ValueError(f"dataset checksum mismatch: {manifest['name']}")
    with h5py.File(source, "r") as handle:
        points = np.asarray(handle["train"][:count], dtype=np.float32)
    angular = str(manifest["distance"]).startswith("angular")
    if angular:
        norms = np.linalg.norm(points, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("angular construction data contain a zero vector")
        points /= norms
    return points, angular


def terminal_changes(base: tuple[int, ...], selected: tuple[int, ...]) -> int:
    return len(set(selected) - set(base))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("raw output directory exists and will not be overwritten")
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    rows: list[dict] = []
    receipts = []
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    started = time.perf_counter()

    for dataset_index, manifest_name in enumerate(config["datasets"]):
        manifest_path = REPO / manifest_name
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        points, angular = load_construction(manifest, config["construction_vectors"])
        index = hnswlib.Index(space="cosine" if angular else "l2", dim=points.shape[1])
        index.init_index(
            max_elements=len(points),
            M=config["M"],
            ef_construction=config["ef_construction"],
            random_seed=config["build_seed"],
        )
        index.set_num_threads(config["threads"])
        build_started = time.perf_counter()
        index.add_items(points, np.arange(len(points)))
        build_seconds = time.perf_counter() - build_started
        index.set_ef(config["candidate_ef_search"])
        labels, _ = index.knn_query(points, k=config["candidate_count"] + 1)
        candidates_by_center = np.empty(
            (len(points), config["candidate_count"]), dtype=np.int64
        )
        for node, labels_row in enumerate(labels):
            filtered = labels_row[labels_row != node][: config["candidate_count"]]
            if len(filtered) != config["candidate_count"]:
                raise RuntimeError("candidate query returned too few distinct labels")
            candidates_by_center[node] = filtered
        rng = np.random.default_rng(config["build_seed"])
        centers = np.sort(
            rng.choice(len(points), size=config["audited_centers"], replace=False)
        )
        audit_started = time.perf_counter()
        for center in centers:
            candidates = candidates_by_center[center]
            leverage = local_scheme_a(points, int(center), candidates, candidates_by_center)
            selection_kwargs = {
                "epsilon": config["epsilon"],
                "geometry_tolerance": config["geometry_tolerance"],
            }
            ggr = geometry_guarded_resistance_selection(
                points[center],
                points[candidates],
                leverage,
                config["M"],
                leverage_tolerance=config["leverage_tolerance"],
                **selection_kwargs,
            )
            seed_offset = dataset_index * 1_000_000 + int(center)
            random_control = geometry_safe_random_selection(
                points[center],
                points[candidates],
                config["M"],
                requested_swaps=len(ggr.swaps),
                seed=config["geometry_safe_random_seed"] + seed_offset,
                **selection_kwargs,
            )
            shuffled = shuffled_resistance_selection(
                points[center],
                points[candidates],
                leverage,
                config["M"],
                seed=config["shuffled_resistance_seed"] + seed_offset,
                leverage_tolerance=config["leverage_tolerance"],
                **selection_kwargs,
            )
            methods = {
                "ggr": ggr,
                "geometry_safe_random": random_control,
                "shuffled_resistance": shuffled.selection,
            }
            for method, result in methods.items():
                chosen = np.asarray(result.selected, dtype=np.int64)
                rows.append(
                    {
                        "dataset": manifest["name"],
                        "center": int(center),
                        "method": method,
                        "candidate_count": len(candidates),
                        "requested_swap_steps": len(ggr.swaps),
                        "actual_swap_steps": len(result.swaps),
                        "swap_budget_matched": len(result.swaps) == len(ggr.swaps),
                        "terminal_changed_edges": terminal_changes(
                            result.geometry_selected, result.selected
                        ),
                        "geometry_base": result.geometry_base,
                        "geometry_final": result.geometry_final,
                        "geometry_delta": result.geometry_final - result.geometry_base,
                        "true_frozen_leverage_total": float(leverage[chosen].sum()),
                        "termination": result.termination,
                        "layer": 0,
                        "selected_targets": json.dumps(
                            [int(candidates[item]) for item in result.selected]
                        ),
                    }
                )
        receipts.append(
            {
                "dataset": manifest["name"],
                "sha256": manifest["sha256"],
                "build_seconds": build_seconds,
                "audit_seconds": time.perf_counter() - audit_started,
            }
        )
        peak_rss = max(peak_rss, process.memory_info().rss)

    frame = pd.DataFrame(rows)
    summary = (
        frame.groupby(["dataset", "method"])
        .agg(
            centers=("center", "size"),
            centers_changed=("terminal_changed_edges", lambda values: int((values > 0).sum())),
            requested_swap_steps=("requested_swap_steps", "sum"),
            actual_swap_steps=("actual_swap_steps", "sum"),
            swap_budget_match_fraction=("swap_budget_matched", "mean"),
            terminal_changed_edges=("terminal_changed_edges", "sum"),
            geometry_delta_min=("geometry_delta", "min"),
            geometry_delta_total=("geometry_delta", "sum"),
            true_frozen_leverage_total=("true_frozen_leverage_total", "sum"),
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
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "formal_test_members_accessed": False,
        "control_seeds": {
            "geometry_safe_random": config["geometry_safe_random_seed"],
            "shuffled_resistance": config["shuffled_resistance_seed"],
        },
        "receipts": receipts,
        "peak_rss_bytes": peak_rss,
        "total_seconds": time.perf_counter() - started,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
