"""Query-independent primitives for frozen Graph Gate E0 plan generation."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def exact_local_neighbors(
    points: NDArray[np.float32] | NDArray[np.float64],
    neighbors: int = 64,
    *,
    block_size: int = 128,
) -> tuple[NDArray[np.int32], NDArray[np.float64]]:
    """Return exact nonself neighbors and the frozen 16th-neighbor scale.

    Columns are external labels in ascending order, so NumPy's stable sort gives
    the preregistered smaller-label tie break for exactly equal distances.
    """

    values = np.asarray(points, dtype=np.float64)
    if values.ndim != 2 or len(values) <= neighbors:
        raise ValueError("points must be a matrix with more rows than neighbors")
    if neighbors < 16 or block_size <= 0:
        raise ValueError("neighbors must be at least 16 and block_size positive")
    if not np.isfinite(values).all():
        raise ValueError("points must be finite")

    count = len(values)
    squared_norms = np.einsum("ij,ij->i", values, values)
    result = np.empty((count, neighbors), dtype=np.int32)
    scales = np.empty(count, dtype=np.float64)
    for start in range(0, count, block_size):
        stop = min(count, start + block_size)
        distances = (
            squared_norms[start:stop, None]
            + squared_norms[None, :]
            - 2.0 * (values[start:stop] @ values.T)
        )
        np.maximum(distances, 0.0, out=distances)
        distances[np.arange(stop - start), np.arange(start, stop)] = np.inf
        order = np.argsort(distances, axis=1, kind="stable")[:, :neighbors]
        result[start:stop] = order.astype(np.int32)
        scales[start:stop] = np.sqrt(distances[np.arange(stop - start), order[:, 15]])
    if np.any(scales <= np.finfo(np.float64).eps):
        raise ValueError("the frozen 16th-neighbor scale must be positive")
    return result, scales
