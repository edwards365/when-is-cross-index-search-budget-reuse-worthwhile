"""Query-independent primitives for frozen Graph Gate E0 plan generation."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .mpcc_selectors import frozen_radii, progress_masks, unit_rows


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


def empirical_progress_masks_fast(
    center: NDArray[np.float64],
    candidates: NDArray[np.float64],
    local_neighbors: NDArray[np.float64],
    local_scale: float,
    samples: int,
    rng: np.random.Generator,
) -> tuple[NDArray[np.bool_], NDArray[np.float64], NDArray[np.int8]]:
    """Compute the frozen empirical-direction masks without repeating directions.

    The random-number consumption and result are identical to calling
    ``frozen_radii``, ``frozen_directions('empirical_direction', ...)`` and
    ``progress_masks``. Only the 64 unique direction dot products are evaluated.
    """

    radii, bins = frozen_radii(samples, rng)
    local_directions = unit_rows(np.asarray(local_neighbors, dtype=np.float64) - center)
    sampled_direction_ids = rng.integers(0, len(local_directions), samples)
    candidate_delta = np.asarray(candidates, dtype=np.float64) - center
    candidate_lengths = np.linalg.norm(candidate_delta, axis=1)
    candidate_directions = unit_rows(candidate_delta)
    thresholds = candidate_lengths[:, None] / (2.0 * local_scale * radii[None, :])
    cosine = candidate_directions @ local_directions.T
    masks = cosine[:, sampled_direction_ids] > thresholds
    return masks, radii, bins


def stable_mpcc_select(
    masks: NDArray[np.bool_],
    budget: int,
    distances: NDArray[np.float64],
    labels: NDArray[np.int64],
    backbone: tuple[int, ...] = (),
) -> tuple[int, ...]:
    """Greedy MPCC with the frozen gain/length/external-label tie break."""

    masks = np.asarray(masks, dtype=np.bool_)
    distances = np.asarray(distances, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    if masks.ndim != 2 or distances.shape != (len(masks),) or labels.shape != (len(masks),):
        raise ValueError("candidate masks, distances, and labels are inconsistent")
    if not 0 <= len(backbone) <= budget <= len(masks):
        raise ValueError("backbone and budget are inconsistent")
    if len(set(backbone)) != len(backbone) or any(not 0 <= item < len(masks) for item in backbone):
        raise ValueError("backbone contains an invalid candidate")
    covered = (
        np.logical_or.reduce(masks[list(backbone)], axis=0)
        if backbone
        else np.zeros(masks.shape[1], dtype=bool)
    )
    available = set(range(len(masks))) - set(backbone)
    added: list[int] = []
    while len(backbone) + len(added) < budget:
        winner = min(
            available,
            key=lambda index: (
                -int(np.count_nonzero(masks[index] & ~covered)),
                float(distances[index]),
                int(labels[index]),
            ),
        )
        added.append(winner)
        available.remove(winner)
        covered |= masks[winner]
    return backbone + tuple(added)


def reference_empirical_progress_masks(
    center: NDArray[np.float64],
    candidates: NDArray[np.float64],
    local_neighbors: NDArray[np.float64],
    local_scale: float,
    samples: int,
    rng: np.random.Generator,
) -> NDArray[np.bool_]:
    """Small-fixture reference retained for equivalence tests."""

    radii, _ = frozen_radii(samples, rng)
    local_displacements = np.asarray(local_neighbors, dtype=np.float64) - center
    local_directions = unit_rows(local_displacements)
    directions = local_directions[rng.integers(0, len(local_directions), samples)]
    return progress_masks(center, candidates, local_scale, directions, radii)
