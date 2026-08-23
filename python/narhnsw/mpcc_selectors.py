"""Deterministic state generation and R0 selector baselines for GB-MPCC."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .coverage_objective import greedy_incremental_hard_coverage

RHO_BINS = ((0.75, 1.25), (1.25, 2.5), (2.5, 5.0))


def unit_rows(values: NDArray[np.float64]) -> NDArray[np.float64]:
    values = np.asarray(values, dtype=np.float64)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    if np.any(norms <= np.finfo(np.float64).eps):
        raise ValueError("zero displacement has no direction")
    return values / norms


def frozen_radii(samples: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    if samples < 3:
        raise ValueError("at least three state samples are required")
    counts = (samples // 3, samples // 3, samples - 2 * (samples // 3))
    radii = []
    labels = []
    for label, (count, (low, high)) in enumerate(zip(counts, RHO_BINS, strict=True)):
        radii.append(rng.uniform(low, high, count))
        labels.extend([label] * count)
    return np.concatenate(radii), np.asarray(labels, dtype=np.int8)


def frozen_directions(
    model: str,
    local_displacements: NDArray[np.float64],
    samples: int,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    local_displacements = np.asarray(local_displacements, dtype=np.float64)
    local = unit_rows(local_displacements)
    if model == "empirical_direction":
        return local[rng.integers(0, len(local), samples)]
    if model == "local_pca":
        centered = local_displacements - local_displacements.mean(axis=0, keepdims=True)
        _, singular, right = np.linalg.svd(centered, full_matrices=False)
        energy = np.cumsum(singular * singular)
        components = int(np.searchsorted(energy, 0.90 * energy[-1]) + 1)
        components = min(32, max(1, components))
        return unit_rows(rng.normal(size=(samples, components)) @ right[:components])
    if model == "isotropic_sphere":
        return unit_rows(rng.normal(size=(samples, local.shape[1])))
    raise ValueError(f"unknown state model: {model}")


def progress_masks(
    center: NDArray[np.float64],
    candidates: NDArray[np.float64],
    local_scale: float,
    directions: NDArray[np.float64],
    radii: NDArray[np.float64],
    *,
    eta: float = 0.0,
) -> NDArray[np.bool_]:
    if local_scale <= 0 or not 0 <= eta < 1:
        raise ValueError("invalid local scale or eta")
    delta = np.asarray(candidates, dtype=np.float64) - np.asarray(center, dtype=np.float64)
    lengths = np.linalg.norm(delta, axis=1)
    candidate_directions = unit_rows(delta)
    scaled = lengths / local_scale
    thresholds = scaled[:, None] / (2.0 * radii[None, :])
    if eta:
        thresholds += (2.0 * eta - eta * eta) * radii[None, :] / (2.0 * scaled[:, None])
    return candidate_directions @ np.asarray(directions, dtype=np.float64).T > thresholds


def maxmin_angle_select(
    center: NDArray[np.float64],
    candidates: NDArray[np.float64],
    labels: NDArray[np.int64],
    budget: int,
) -> tuple[int, ...]:
    delta = np.asarray(candidates, dtype=np.float64) - np.asarray(center, dtype=np.float64)
    lengths = np.linalg.norm(delta, axis=1)
    directions = unit_rows(delta)
    remaining = set(range(len(candidates)))
    selected: list[int] = []
    while len(selected) < budget:
        if not selected:
            winner = min(remaining, key=lambda i: (lengths[i], int(labels[i])))
        else:
            winner = min(
                remaining,
                key=lambda i: (
                    float(np.max(directions[selected] @ directions[i])),
                    lengths[i],
                    int(labels[i]),
                ),
            )
        selected.append(winner)
        remaining.remove(winner)
    return tuple(selected)


def length_aware_angle_select(
    center: NDArray[np.float64],
    candidates: NDArray[np.float64],
    labels: NDArray[np.int64],
    budget: int,
) -> tuple[int, ...]:
    delta = np.asarray(candidates, dtype=np.float64) - np.asarray(center, dtype=np.float64)
    lengths = np.linalg.norm(delta, axis=1)
    directions = unit_rows(delta)
    remaining = set(range(len(candidates)))
    selected: list[int] = []
    while len(selected) < budget:
        if not selected:
            winner = min(remaining, key=lambda i: (lengths[i], int(labels[i])))
        else:
            def key(index: int) -> tuple[float, float, int]:
                cosine = directions[selected] @ directions[index]
                margin = cosine - lengths[selected] / (2.0 * lengths[index])
                return float(np.max(np.maximum(margin, 0.0))), lengths[index], int(labels[index])

            winner = min(remaining, key=key)
        selected.append(winner)
        remaining.remove(winner)
    return tuple(selected)


def mpcc_select(
    masks: NDArray[np.bool_], budget: int, backbone: tuple[int, ...] = ()
) -> tuple[int, ...]:
    added = greedy_incremental_hard_coverage(
        masks, backbone, range(len(masks)), max(0, budget - len(backbone))
    )
    return tuple(backbone) + tuple(added)


def shuffled_mpcc_select(
    masks: NDArray[np.bool_], budget: int, rng: np.random.Generator
) -> tuple[int, ...]:
    permutation = rng.permutation(len(masks))
    return mpcc_select(masks[permutation], budget)
