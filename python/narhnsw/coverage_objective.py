"""Frozen-state hard and smooth coverage objectives for GB-MPCC."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray


def normalized_weights(weights: Sequence[float] | None, states: int) -> NDArray[np.float64]:
    if states <= 0:
        raise ValueError("states must be positive")
    if weights is None:
        return np.full(states, 1.0 / states, dtype=np.float64)
    result = np.asarray(weights, dtype=np.float64)
    if result.shape != (states,) or np.any(result < 0) or not np.isfinite(result).all():
        raise ValueError("weights must be finite, nonnegative, and match the state count")
    total = float(result.sum())
    if total <= 0:
        raise ValueError("weights must have positive total mass")
    return result / total


def hard_coverage(
    masks: NDArray[np.bool_], selected: Iterable[int], weights: Sequence[float] | None = None
) -> float:
    masks = np.asarray(masks, dtype=np.bool_)
    if masks.ndim != 2:
        raise ValueError("masks must have shape (candidates, states)")
    chosen = tuple(selected)
    if not chosen:
        return 0.0
    if min(chosen) < 0 or max(chosen) >= masks.shape[0]:
        raise IndexError("selected candidate is outside the mask matrix")
    covered = np.logical_or.reduce(masks[list(chosen)], axis=0)
    return float(covered @ normalized_weights(weights, masks.shape[1]))


def smooth_scores(margins: NDArray[np.float64], tau: float) -> NDArray[np.float64]:
    if tau <= 0:
        raise ValueError("tau must be positive")
    return np.clip(np.asarray(margins, dtype=np.float64) / tau, 0.0, 1.0)


def smooth_coverage(
    scores: NDArray[np.float64], selected: Iterable[int], weights: Sequence[float] | None = None
) -> float:
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 2 or np.any(scores < 0) or np.any(scores > 1):
        raise ValueError("scores must have shape (candidates, states) and lie in [0, 1]")
    chosen = tuple(selected)
    if not chosen:
        return 0.0
    if min(chosen) < 0 or max(chosen) >= scores.shape[0]:
        raise IndexError("selected candidate is outside the score matrix")
    covered = np.max(scores[list(chosen)], axis=0)
    return float(covered @ normalized_weights(weights, scores.shape[1]))


def incremental_hard_coverage(
    masks: NDArray[np.bool_],
    backbone: Iterable[int],
    added: Iterable[int],
    weights: Sequence[float] | None = None,
) -> float:
    backbone = tuple(backbone)
    added = tuple(added)
    return hard_coverage(masks, backbone + added, weights) - hard_coverage(
        masks, backbone, weights
    )


def greedy_incremental_hard_coverage(
    masks: NDArray[np.bool_],
    backbone: Iterable[int],
    candidates: Iterable[int],
    budget: int,
    weights: Sequence[float] | None = None,
) -> tuple[int, ...]:
    """Deterministic cardinality-constrained marginal-coverage greedy selector."""

    if budget < 0:
        raise ValueError("budget must be nonnegative")
    backbone = tuple(backbone)
    available = sorted(set(candidates) - set(backbone))
    chosen: list[int] = []
    for _ in range(min(budget, len(available))):
        gains = [
            (
                incremental_hard_coverage(masks, backbone, chosen + [candidate], weights)
                - incremental_hard_coverage(masks, backbone, chosen, weights),
                candidate,
            )
            for candidate in available
        ]
        _, winner = max(gains, key=lambda item: (item[0], -item[1]))
        chosen.append(winner)
        available.remove(winner)
    return tuple(chosen)
