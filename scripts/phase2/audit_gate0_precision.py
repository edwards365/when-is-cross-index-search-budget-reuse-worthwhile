#!/usr/bin/env python
"""Audit epsilon-zero GGR precision without reading formal HDF5 test members."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from decimal import Decimal, localcontext
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

from narhnsw.ggr import geometry_guarded_resistance_selection  # noqa: E402

from scripts.experiments.run_phase2_selector_audit import (  # noqa: E402
    local_scheme_a,
    sha256,
)


def decimal_geometry_objective(
    center: np.ndarray,
    candidates: np.ndarray,
    selected: tuple[int, ...] | list[int],
    *,
    precision: int,
) -> Decimal:
    """Recompute the frozen Geometry objective with Decimal Cholesky arithmetic."""

    if not selected:
        return Decimal(0)
    with localcontext() as context:
        context.prec = precision
        center_d = [Decimal.from_float(float(value)) for value in center]
        candidate_d = [
            [Decimal.from_float(float(value)) for value in row] for row in candidates
        ]
        deltas = [
            [value - origin for value, origin in zip(row, center_d, strict=True)]
            for row in candidate_d
        ]
        distances = [sum(value * value for value in row).sqrt() for row in deltas]
        ordered_distances = sorted(distances)
        middle = len(ordered_distances) // 2
        if len(ordered_distances) % 2:
            rho = ordered_distances[middle]
        else:
            rho = (ordered_distances[middle - 1] + ordered_distances[middle]) / Decimal(2)
        directions = [
            [value / distance for value in row]
            for row, distance in zip(deltas, distances, strict=True)
        ]
        chosen = list(selected)
        size = len(chosen)
        gram = [[Decimal(0) for _ in range(size)] for _ in range(size)]
        for row_index, left in enumerate(chosen):
            for column_index, right in enumerate(chosen):
                dot = sum(
                    a * b
                    for a, b in zip(directions[left], directions[right], strict=True)
                )
                gram[row_index][column_index] = Decimal(4) * dot
                if row_index == column_index:
                    gram[row_index][column_index] += Decimal(1)
        lower = [[Decimal(0) for _ in range(size)] for _ in range(size)]
        for row in range(size):
            for column in range(row + 1):
                residual = gram[row][column] - sum(
                    lower[row][item] * lower[column][item] for item in range(column)
                )
                lower[row][column] = (
                    residual.sqrt()
                    if row == column
                    else residual / lower[column][column]
                )
        logdet = Decimal(2) * sum(lower[item][item].ln() for item in range(size))
        locality = sum((-(distances[item] / rho) ** 2).exp() for item in chosen)
        return +(logdet + locality)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("raw output directory exists and will not be overwritten")
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    process = psutil.Process()
    peak_rss = process.memory_info().rss
    center_rows: list[dict] = []
    swap_rows: list[dict] = []
    dataset_receipts = []
    total_started = time.perf_counter()

    for manifest_name in config["datasets"]:
        manifest_path = REPO / manifest_name
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        points, angular = load_construction(manifest, config["construction_vectors"])
        index = hnswlib.Index(space="cosine" if angular else "l2", dim=points.shape[1])
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
        construction_neighbors = np.empty(
            (len(points), config["candidate_count"]), dtype=np.int64
        )
        for node, row in enumerate(labels):
            filtered = row[row != node][: config["candidate_count"]]
            if len(filtered) != config["candidate_count"]:
                raise RuntimeError("candidate query returned too few distinct labels")
            construction_neighbors[node] = filtered
        rng = np.random.default_rng(config["seed"])
        centers = np.sort(
            rng.choice(len(points), size=config["audited_centers"], replace=False)
        )
        high_precision = set(
            int(item)
            for item in rng.choice(
                centers, size=config["high_precision_centers"], replace=False
            )
        )
        audit_started = time.perf_counter()
        for center in centers:
            candidates = construction_neighbors[center]
            leverage = local_scheme_a(points, int(center), candidates, construction_neighbors)
            for tolerance in config["geometry_tolerance_sweep"]:
                kwargs = dict(
                    epsilon=0.0,
                    geometry_tolerance=float(tolerance),
                    leverage_tolerance=config["leverage_tolerance"],
                )
                result = geometry_guarded_resistance_selection(
                    points[center], points[candidates], leverage, config["M"], **kwargs
                )
                repeated = geometry_guarded_resistance_selection(
                    points[center], points[candidates], leverage, config["M"], **kwargs
                )
                deterministic = result == repeated
                high_precision_delta = None
                classification = "not_sampled"
                if int(center) in high_precision:
                    base_decimal = decimal_geometry_objective(
                        points[center],
                        points[candidates],
                        result.geometry_selected,
                        precision=config["decimal_precision"],
                    )
                    final_decimal = decimal_geometry_objective(
                        points[center],
                        points[candidates],
                        result.selected,
                        precision=config["decimal_precision"],
                    )
                    high_precision_delta = float(final_decimal - base_decimal)
                    if final_decimal >= base_decimal:
                        classification = "strict_non_decrease"
                    elif result.geometry_final + result.geometry_allowance >= result.geometry_base:
                        classification = "mixed_tolerance_equivalent"
                    else:
                        classification = "invalid"
                center_rows.append(
                    {
                        "dataset": manifest["name"],
                        "center": int(center),
                        "candidate_count": len(candidates),
                        "geometry_tolerance": float(tolerance),
                        "geometry_allowance": result.geometry_allowance,
                        "swaps": len(result.swaps),
                        "geometry_base": result.geometry_base,
                        "geometry_final": result.geometry_final,
                        "geometry_delta": result.geometry_final - result.geometry_base,
                        "leverage_delta": result.leverage_final - result.leverage_initial,
                        "high_precision_delta": high_precision_delta,
                        "classification": classification,
                        "deterministic": deterministic,
                        "termination": result.termination,
                    }
                )
                selected = list(result.geometry_selected)
                for swap_index, swap in enumerate(result.swaps):
                    proposal = [item for item in selected if item != swap.outgoing]
                    proposal.append(swap.incoming)
                    proposal.sort()
                    hp_delta = None
                    if int(center) in high_precision:
                        before_hp = decimal_geometry_objective(
                            points[center],
                            points[candidates],
                            selected,
                            precision=config["decimal_precision"],
                        )
                        after_hp = decimal_geometry_objective(
                            points[center],
                            points[candidates],
                            proposal,
                            precision=config["decimal_precision"],
                        )
                        hp_delta = float(after_hp - before_hp)
                    swap_rows.append(
                        {
                            "dataset": manifest["name"],
                            "center": int(center),
                            "candidate_count": len(candidates),
                            "geometry_tolerance": float(tolerance),
                            "swap_index": swap_index,
                            "outgoing": swap.outgoing,
                            "incoming": swap.incoming,
                            "geometry_delta": swap.geometry_after - swap.geometry_before,
                            "high_precision_geometry_delta": hp_delta,
                            "leverage_delta": swap.leverage_after - swap.leverage_before,
                            "guard_margin": (
                                swap.geometry_after
                                - result.geometry_base
                                + result.geometry_allowance
                            ),
                        }
                    )
                    selected = proposal
        audit_seconds = time.perf_counter() - audit_started
        peak_rss = max(peak_rss, process.memory_info().rss)
        dataset_receipts.append(
            {
                "dataset": manifest["name"],
                "sha256": manifest["sha256"],
                "build_seconds": build_seconds,
                "audit_seconds": audit_seconds,
            }
        )

    centers_frame = pd.DataFrame(center_rows)
    swaps_frame = pd.DataFrame(swap_rows)
    summary = (
        centers_frame.groupby(["dataset", "geometry_tolerance"], dropna=False)
        .agg(
            audited_centers=("center", "count"),
            centers_with_swaps=("swaps", lambda values: int((values > 0).sum())),
            total_swaps=("swaps", "sum"),
            min_geometry_delta=("geometry_delta", "min"),
            median_geometry_delta=("geometry_delta", "median"),
            total_leverage_delta=("leverage_delta", "sum"),
            deterministic_fraction=("deterministic", "mean"),
        )
        .reset_index()
    )
    args.output.mkdir(parents=True)
    centers_frame.to_csv(args.output / "per_center.csv", index=False)
    swaps_frame.to_csv(args.output / "per_swap.csv", index=False)
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
        "dataset_receipts": dataset_receipts,
        "peak_rss_bytes": peak_rss,
        "total_seconds": time.perf_counter() - total_started,
        "final_hnsw_retention_available": config["final_hnsw_retention_available"],
        "final_hnsw_retention_blocker": config["final_hnsw_retention_blocker"],
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
