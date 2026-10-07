"""Chunked exact development-query ground truth for L2 and angular data."""

from __future__ import annotations

from typing import Literal

import numpy as np
from scipy.spatial.distance import cdist

Metric = Literal["l2", "angular"]


def exact_top_k(
    base: np.ndarray,
    queries: np.ndarray,
    k: int,
    *,
    metric: Metric,
    query_batch: int = 8,
    base_batch: int = 10_000,
) -> tuple[np.ndarray, np.ndarray]:
    """Return exact float64 top-k identities and distances with stable ID ties."""

    base = np.asarray(base)
    queries = np.asarray(queries)
    if base.ndim != 2 or queries.ndim != 2 or base.shape[1] != queries.shape[1]:
        raise ValueError("base and queries must be dimension-compatible matrices")
    if not 0 < k <= len(base):
        raise ValueError("k must lie in [1, len(base)]")
    if metric not in {"l2", "angular"}:
        raise ValueError("metric must be l2 or angular")
    if query_batch <= 0 or base_batch <= 0:
        raise ValueError("batch sizes must be positive")

    labels = np.empty((len(queries), k), dtype=np.int64)
    distances = np.empty((len(queries), k), dtype=np.float64)
    for query_start in range(0, len(queries), query_batch):
        query_stop = min(query_start + query_batch, len(queries))
        query_block = np.asarray(queries[query_start:query_stop], dtype=np.float64)
        best_distances = np.full((len(query_block), k), np.inf, dtype=np.float64)
        best_labels = np.full((len(query_block), k), -1, dtype=np.int64)
        for base_start in range(0, len(base), base_batch):
            base_stop = min(base_start + base_batch, len(base))
            base_block = np.asarray(base[base_start:base_stop], dtype=np.float64)
            if metric == "l2":
                block_distances = cdist(query_block, base_block, metric="sqeuclidean")
            else:
                block_distances = 1.0 - query_block @ base_block.T
            block_labels = np.broadcast_to(
                np.arange(base_start, base_stop, dtype=np.int64), block_distances.shape
            )
            merged_distances = np.concatenate([best_distances, block_distances], axis=1)
            merged_labels = np.concatenate([best_labels, block_labels], axis=1)
            for row in range(len(query_block)):
                candidates = np.argpartition(merged_distances[row], k - 1)[:k]
                order = np.lexsort(
                    (merged_labels[row, candidates], merged_distances[row, candidates])
                )
                chosen = candidates[order]
                best_distances[row] = merged_distances[row, chosen]
                best_labels[row] = merged_labels[row, chosen]
        labels[query_start:query_stop] = best_labels
        distances[query_start:query_stop] = best_distances
    return labels, distances
