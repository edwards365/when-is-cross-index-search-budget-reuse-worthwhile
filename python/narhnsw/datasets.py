"""Deterministic synthetic datasets and exact ground truth."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.datasets import make_swiss_roll
from sklearn.neighbors import NearestNeighbors


@dataclass(frozen=True)
class DatasetSplit:
    base: np.ndarray
    query: np.ndarray
    ground_truth: np.ndarray
    metric: str


def exact_ground_truth(base: np.ndarray, query: np.ndarray, k: int = 10) -> np.ndarray:
    model = NearestNeighbors(n_neighbors=k, algorithm="brute", metric="euclidean", n_jobs=1)
    model.fit(base)
    return model.kneighbors(query, return_distance=False).astype(np.int64)


def narrow_bridge(
    n: int, dim: int = 16, query_fraction: float = 0.1, seed: int = 0
) -> DatasetSplit:
    if n < 100 or dim < 2:
        raise ValueError("narrow_bridge requires n >= 100 and dim >= 2")
    rng = np.random.default_rng(seed)
    n_query = max(20, int(n * query_fraction))
    n_bridge = max(10, n // 50)
    n_cloud = n + n_query - n_bridge
    left_count = n_cloud // 2
    right_count = n_cloud - left_count
    left = rng.normal(0.0, 0.45, size=(left_count, dim))
    right = rng.normal(0.0, 0.45, size=(right_count, dim))
    left[:, 0] -= 3.0
    right[:, 0] += 3.0
    t = np.linspace(-2.6, 2.6, n_bridge)
    bridge = rng.normal(0.0, 0.04, size=(n_bridge, dim))
    bridge[:, 0] = t
    all_points = np.vstack([left, right, bridge]).astype(np.float32)
    permutation = rng.permutation(len(all_points))
    query = all_points[permutation[:n_query]] + rng.normal(0.0, 0.02, size=(n_query, dim)).astype(
        np.float32
    )
    base = all_points[permutation[n_query:]]
    return DatasetSplit(base, query, exact_ground_truth(base, query), "l2")


def gaussian_mixture(n: int, dim: int = 16, seed: int = 0) -> DatasetSplit:
    rng = np.random.default_rng(seed)
    centers = rng.normal(0, 3, size=(5, dim))
    labels = rng.integers(0, len(centers), size=n + max(20, n // 10))
    scales = np.linspace(0.15, 0.9, len(centers))
    points = centers[labels] + rng.normal(size=(len(labels), dim)) * scales[labels, None]
    points = points.astype(np.float32)
    base, query = points[:n], points[n:]
    return DatasetSplit(base, query, exact_ground_truth(base, query), "l2")


def swiss_roll(n: int, dim: int = 16, seed: int = 0) -> DatasetSplit:
    n_query = max(20, n // 10)
    points, _ = make_swiss_roll(n_samples=n + n_query, noise=0.05, random_state=seed)
    rng = np.random.default_rng(seed)
    projection = rng.normal(size=(3, dim)) / np.sqrt(3)
    embedded = (points @ projection).astype(np.float32)
    base, query = embedded[:n], embedded[n:]
    return DatasetSplit(base, query, exact_ground_truth(base, query), "l2")


GENERATORS = {
    "narrow_bridge": narrow_bridge,
    "gaussian_mixture": gaussian_mixture,
    "swiss_roll": swiss_roll,
}
