#!/usr/bin/env python3
"""Query-independent GB-MPCC spherical-cap capacity audit.

Only the HDF5 ``train`` member is opened. Exact base-to-base neighbors provide a
conservative, reproducible proxy candidate pool before candidate-replay code exists.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
from scipy.special import betainc

DATASETS = {
    "sift_100k": (Path("data/raw/sift-128-euclidean.hdf5"), False),
    "glove100_100k": (Path("data/raw/glove-100-angular.hdf5"), True),
    "arxiv_nomic_100k": (Path("data/raw/arxiv-nomic-768-normalized.hdf5"), True),
}
RHO_BINS = {"near": (0.75, 1.25), "medium": (1.25, 2.5), "far": (2.5, 5.0)}


def exact_neighbors(
    vectors: np.ndarray, center_ids: np.ndarray, k: int
) -> tuple[np.ndarray, np.ndarray]:
    norms = np.einsum("ij,ij->i", vectors, vectors)
    neighbor_ids = np.empty((len(center_ids), k), dtype=np.int64)
    neighbor_distances = np.empty((len(center_ids), k), dtype=np.float64)
    for row, center_id in enumerate(center_ids):
        center = vectors[center_id]
        squared = norms + norms[center_id] - 2.0 * (vectors @ center)
        squared[center_id] = np.inf
        indices = np.argpartition(squared, k)[:k]
        indices = indices[np.argsort(squared[indices], kind="stable")]
        neighbor_ids[row] = indices
        neighbor_distances[row] = np.sqrt(np.maximum(squared[indices], 0.0))
    return neighbor_ids, neighbor_distances


def local_dimension(distances: np.ndarray, k: int = 20) -> float:
    positive = distances[:k][distances[:k] > 0]
    if len(positive) < k:
        return float("nan")
    denominator = float(np.sum(np.log(positive[-1] / positive[:-1])))
    return float((k - 1) / denominator) if denominator > 0 else float("inf")


def state_radii(rng: np.random.Generator, samples: int) -> tuple[np.ndarray, np.ndarray]:
    counts = [samples // 3, samples // 3, samples - 2 * (samples // 3)]
    radii = []
    labels = []
    for count, (label, (low, high)) in zip(counts, RHO_BINS.items(), strict=True):
        radii.append(rng.uniform(low, high, count))
        labels.extend([label] * count)
    return np.concatenate(radii), np.asarray(labels)


def unit_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, np.finfo(np.float64).tiny)


def state_directions(
    model: str, displacements: np.ndarray, samples: int, rng: np.random.Generator
) -> np.ndarray:
    ambient = displacements.shape[1]
    if model == "empirical_direction":
        directions = unit_rows(displacements)
        return directions[rng.integers(0, len(directions), samples)]
    if model == "local_pca":
        centered = displacements - displacements.mean(axis=0, keepdims=True)
        _, singular, right = np.linalg.svd(centered, full_matrices=False)
        energy = np.cumsum(singular * singular)
        components = int(np.searchsorted(energy, 0.90 * energy[-1]) + 1)
        components = min(32, max(1, components))
        coefficients = rng.normal(size=(samples, components))
        return unit_rows(coefficients @ right[:components])
    if model == "isotropic_sphere":
        return unit_rows(rng.normal(size=(samples, ambient)))
    raise ValueError(f"unknown direction model: {model}")


def analytic_union_bound(thresholds: np.ndarray, dimension: int) -> np.ndarray:
    clipped = np.clip(thresholds, 0.0, 1.0)
    masses = 0.5 * betainc(
        (dimension - 1.0) / 2.0, 0.5, 1.0 - clipped * clipped
    )
    masses[thresholds >= 1.0] = 0.0
    return np.minimum(1.0, masses.sum(axis=0))


def audit_dataset(
    dataset: str,
    path: Path,
    normalized: bool,
    centers: int,
    samples: int,
    seed: int,
) -> dict[str, object]:
    with h5py.File(path, "r") as source:
        vectors = np.asarray(source["train"][:100000], dtype=np.float64)
    if normalized:
        vectors = unit_rows(vectors)
    rng = np.random.default_rng(seed)
    center_ids = np.sort(rng.choice(len(vectors), size=centers, replace=False))
    neighbor_ids, neighbor_distances = exact_neighbors(vectors, center_ids, 64)
    rows: list[dict[str, object]] = []
    for row, center_id in enumerate(center_ids):
        displacements = vectors[neighbor_ids[row]] - vectors[center_id]
        scale = float(neighbor_distances[row, 15])
        candidate_displacements = displacements[:32]
        candidate_lengths = np.linalg.norm(candidate_displacements, axis=1)
        candidate_directions = unit_rows(candidate_displacements)
        scaled_lengths = candidate_lengths / scale
        lid = local_dimension(neighbor_distances[row])
        cap_dimension = max(2, int(round(lid))) if np.isfinite(lid) else vectors.shape[1]
        radii, bin_labels = state_radii(rng, samples)
        thresholds = scaled_lengths[:, None] / (2.0 * radii[None, :])
        analytic = analytic_union_bound(thresholds, cap_dimension)
        model_coverage: dict[str, np.ndarray] = {}
        for model in ("empirical_direction", "local_pca", "isotropic_sphere"):
            directions = state_directions(model, displacements, samples, rng)
            masks = candidate_directions @ directions.T > thresholds
            model_coverage[model] = np.any(masks, axis=0)
        for bin_name in RHO_BINS:
            selected = bin_labels == bin_name
            rows.append(
                {
                    "center_id": int(center_id),
                    "rho_bin": bin_name,
                    "local_dimension": lid,
                    "cap_dimension_rounded": cap_dimension,
                    "analytic_isotropic_union_bound": float(np.mean(analytic[selected])),
                    **{
                        f"{model}_coverage": float(np.mean(coverage[selected]))
                        for model, coverage in model_coverage.items()
                    },
                }
            )
    summaries: dict[str, object] = {}
    for bin_name in RHO_BINS:
        selected = [row for row in rows if row["rho_bin"] == bin_name]
        summaries[bin_name] = {
            field: {
                "median": float(np.median([float(row[field]) for row in selected])),
                "p10": float(np.quantile([float(row[field]) for row in selected], 0.10)),
                "p90": float(np.quantile([float(row[field]) for row in selected], 0.90)),
            }
            for field in (
                "analytic_isotropic_union_bound",
                "empirical_direction_coverage",
                "local_pca_coverage",
                "isotropic_sphere_coverage",
            )
        }
    empirical_nondegenerate = sum(
        0.05 <= summaries[bin_name]["empirical_direction_coverage"]["median"] <= 0.95
        for bin_name in RHO_BINS
    ) >= 1
    return {
        "dataset": dataset,
        "dimensions": int(vectors.shape[1]),
        "base_vectors": int(vectors.shape[0]),
        "sampled_centers": centers,
        "candidate_proxy": "exact 32-nearest base neighbors",
        "local_state_neighbors": 64,
        "state_samples_per_center": samples,
        "accessed_hdf5_members": ["train"],
        "formal_test_members_accessed": False,
        "local_dimension": {
            "median": float(np.nanmedian([float(row["local_dimension"]) for row in rows])),
            "p10": float(np.nanquantile([float(row["local_dimension"]) for row in rows], 0.10)),
            "p90": float(np.nanquantile([float(row["local_dimension"]) for row in rows], 0.90)),
        },
        "rho_bins": summaries,
        "empirical_direction_nondegenerate": empirical_nondegenerate,
        "node_rows": rows,
    }


def render_report(result: dict[str, object]) -> str:
    lines = [
        "# GB-MPCC capacity audit",
        "",
        "Scope: query-independent T0 audit over `train[:100000]` only. Formal HDF5",
        "`test`, `neighbors`, and `distances` were not accessed. Exact 32-nearest base",
        "neighbors are a pre-replay proxy candidate pool, not claimed to equal HNSW's",
        "insertion-time Algorithm 4 pool.",
        "",
        "| Dataset | LID median | Scale | Isotropic analytic UB | Empirical coverage "
        "| Local-PCA coverage | Isotropic MC |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for dataset in result["datasets"]:
        for bin_name, values in dataset["rho_bins"].items():
            lines.append(
                f"| {dataset['dataset']} | {dataset['local_dimension']['median']:.2f} | "
                f"{bin_name} | {values['analytic_isotropic_union_bound']['median']:.4f} | "
                f"{values['empirical_direction_coverage']['median']:.4f} | "
                f"{values['local_pca_coverage']['median']:.4f} | "
                f"{values['isotropic_sphere_coverage']['median']:.4f} |"
            )
    lines += [
        "",
        f"Frozen T0 capacity status: **{result['capacity_status']}**.",
        "",
        "The 0.05/0.95 non-degeneracy interval and isotropic 0.05 stop threshold were",
        "fixed before this run. Capacity alone cannot establish Algorithm 4 difference,",
        "proxy transfer to routing states, or search performance.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--centers", type=int, default=64)
    parser.add_argument("--samples", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/t0_capacity.json"))
    parser.add_argument("--report", type=Path, default=Path("reports/capacity_audit.md"))
    args = parser.parse_args()
    if args.centers <= 0 or args.samples <= 0:
        raise ValueError("centers and samples must be positive")
    datasets = [
        audit_dataset(name, path, normalized, args.centers, args.samples, args.seed + index)
        for index, (name, (path, normalized)) in enumerate(DATASETS.items())
    ]
    nondegenerate = sum(bool(dataset["empirical_direction_nondegenerate"]) for dataset in datasets)
    result = {
        "schema_version": 1,
        "seed": args.seed,
        "formal_test_members_accessed": False,
        "datasets": datasets,
        "capacity_status": (
            "QUERY_INDEPENDENT_CAPACITY_NONDEGENERATE_ON_AT_LEAST_TWO_DATASETS"
            if nondegenerate >= 2
            else "OBJECTIVE_DEGENERATE"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(render_report(result), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "datasets"}, indent=2))


if __name__ == "__main__":
    main()
