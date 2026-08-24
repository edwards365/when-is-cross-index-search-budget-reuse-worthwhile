"""Exact small-graph resistance and local neighbor-selection reference code.

This module intentionally favors explicit numerical checks over scalability. It is
the ground-truth implementation for candidate pools of roughly 32--64 vertices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.sparse.csgraph import connected_components

DisconnectedPolicy = Literal["infinite", "component"]


@dataclass(frozen=True)
class CandidateScore:
    index: int
    leverage: float
    direction_gain: float
    locality: float
    total_gain: float


def _validate_adjacency(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=np.float64)
    if weights.ndim != 2 or weights.shape[0] != weights.shape[1]:
        raise ValueError("weights must be a square matrix")
    if not np.all(np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("weights must be finite and nonnegative")
    if not np.allclose(weights, weights.T, atol=1e-12):
        raise ValueError("standard effective resistance requires symmetric weights")
    weights = weights.copy()
    np.fill_diagonal(weights, 0.0)
    return weights


def effective_resistance_matrix(
    weights: np.ndarray,
    *,
    disconnected: DisconnectedPolicy = "infinite",
    rcond: float = 1e-12,
) -> np.ndarray:
    """Return exact Moore--Penrose effective resistances for a small graph.

    Cross-component values are infinity. ``component`` currently has the same
    cross-component semantics but documents that each block was solved separately.
    No Laplacian regularization is silently applied.
    """

    if disconnected not in {"infinite", "component"}:
        raise ValueError(f"unsupported disconnected policy: {disconnected}")
    weights = _validate_adjacency(weights)
    # Pass the exact support graph. SciPy's dense weighted-graph conversion can
    # otherwise treat very small but nonzero conductances as absent edges.
    n_components, labels = connected_components(weights > 0, directed=False)
    result = np.full(weights.shape, np.inf, dtype=np.float64)
    np.fill_diagonal(result, 0.0)

    for component in range(n_components):
        ids = np.flatnonzero(labels == component)
        if len(ids) == 1:
            continue
        block = weights[np.ix_(ids, ids)]
        laplacian = np.diag(block.sum(axis=1)) - block
        # Ground the final vertex instead of repeatedly diagonalizing the
        # singular Laplacian.  For a connected weighted graph, the inverse of
        # any grounded Laplacian gives exactly the same pairwise effective
        # resistances as the Moore--Penrose inverse.  This formulation also
        # avoids a Windows SciPy/LAPACK native crash observed on a valid Gate-A
        # candidate graph.
        grounded = laplacian[:-1, :-1]
        if not np.all(np.isfinite(grounded)):
            raise ValueError("grounded Laplacian must be finite")
        condition = np.linalg.cond(grounded)
        if not np.isfinite(condition) or condition * rcond >= 1.0:
            raise np.linalg.LinAlgError("grounded Laplacian is numerically singular")
        grounded_inverse = np.linalg.solve(grounded, np.eye(len(grounded)))
        grounded_inverse = 0.5 * (grounded_inverse + grounded_inverse.T)
        diag = np.diag(grounded_inverse)
        resistance = np.zeros_like(laplacian)
        resistance[:-1, :-1] = diag[:, None] + diag[None, :] - 2.0 * grounded_inverse
        resistance[:-1, -1] = diag
        resistance[-1, :-1] = diag
        resistance[np.abs(resistance) < 100 * np.finfo(float).eps] = 0.0
        result[np.ix_(ids, ids)] = resistance
    return result


def edge_leverage_scores(weights: np.ndarray, resistance: np.ndarray | None = None) -> np.ndarray:
    """Compute tau_e = w_e R_eff(e) for every existing undirected edge."""

    weights = _validate_adjacency(weights)
    if resistance is None:
        resistance = effective_resistance_matrix(weights)
    resistance = np.asarray(resistance, dtype=np.float64)
    leverage = np.zeros_like(weights)
    mask = weights > 0
    leverage[mask] = weights[mask] * resistance[mask]
    return leverage


def gaussian_weight_graph(
    points: np.ndarray,
    adjacency: np.ndarray,
    *,
    rho: float | None = None,
) -> np.ndarray:
    """Turn a symmetric boolean adjacency into Gaussian distance weights."""

    points = np.asarray(points, dtype=np.float64)
    adjacency = np.asarray(adjacency, dtype=bool)
    if adjacency.shape != (len(points), len(points)):
        raise ValueError("adjacency shape must match points")
    adjacency = adjacency | adjacency.T
    np.fill_diagonal(adjacency, False)
    distances = np.linalg.norm(points[:, None] - points[None, :], axis=-1)
    observed = distances[adjacency]
    if rho is None:
        rho = float(np.median(observed)) if observed.size else 1.0
    if not np.isfinite(rho) or rho <= 0:
        raise ValueError("rho must be positive")
    weights = np.exp(-np.square(distances / rho)) * adjacency
    np.fill_diagonal(weights, 0.0)
    return weights


def direction_coverage(directions: np.ndarray, sigma: float = 0.5) -> float:
    """Return log det(I + sigma^-2 Z Z^T) using a stable signed log determinant."""

    directions = np.asarray(directions, dtype=np.float64)
    if directions.ndim != 2:
        raise ValueError("directions must be a matrix with one row per selected edge")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    if len(directions) == 0:
        return 0.0
    sign, value = np.linalg.slogdet(
        np.eye(len(directions)) + (directions @ directions.T) / sigma**2
    )
    if sign <= 0:
        raise FloatingPointError("direction Gram matrix is not positive definite")
    return float(value)


def _logdet_direction_gain(
    selected: list[np.ndarray], candidate: np.ndarray, sigma: float
) -> float:
    """Stable marginal log-det using slogdet on tiny candidate sets."""

    def objective(rows: list[np.ndarray]) -> float:
        if not rows:
            return 0.0
        return direction_coverage(np.stack(rows), sigma)

    return objective([*selected, candidate]) - objective(selected)


def greedy_neighbor_selection(
    center: np.ndarray,
    candidates: np.ndarray,
    leverage: np.ndarray,
    budget: int,
    *,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
    sigma: float = 0.5,
    rho: float | None = None,
    labels: np.ndarray | None = None,
) -> tuple[list[int], list[CandidateScore]]:
    """Greedily maximize nonnegative leverage, direction log-det, and locality.

    The leverage values are frozen before selection. Under nonnegative coefficients,
    this is a normalized monotone submodular objective; the guarantee concerns only
    this local candidate-selection problem.
    """

    center = np.asarray(center, dtype=np.float64)
    candidates = np.asarray(candidates, dtype=np.float64)
    leverage = np.asarray(leverage, dtype=np.float64)
    external_labels = None if labels is None else np.asarray(labels, dtype=np.int64)
    if candidates.ndim != 2 or candidates.shape[1:] != center.shape:
        raise ValueError("candidate dimensions must match center")
    if leverage.shape != (len(candidates),) or np.any(leverage < 0):
        raise ValueError("leverage must be one nonnegative value per candidate")
    if external_labels is not None and external_labels.shape != (len(candidates),):
        raise ValueError("labels must contain one external label per candidate")
    if not 0 <= budget <= len(candidates):
        raise ValueError("budget is outside the candidate set")
    if min(alpha, beta, gamma) < 0 or sigma <= 0:
        raise ValueError("coefficients must be nonnegative and sigma positive")

    delta = candidates - center
    distances = np.linalg.norm(delta, axis=1)
    nonzero = distances > np.finfo(float).eps
    if not np.all(nonzero):
        raise ValueError("candidate equal to center would have undefined direction")
    directions = delta / distances[:, None]
    if rho is None:
        rho = float(np.median(distances))
    if rho <= 0:
        raise ValueError("rho must be positive")
    locality = np.exp(-np.square(distances / rho))

    remaining = set(range(len(candidates)))
    selected: list[int] = []
    selected_directions: list[np.ndarray] = []
    trace: list[CandidateScore] = []
    for _ in range(budget):
        choices: list[CandidateScore] = []
        for index in sorted(remaining):
            direction_gain = _logdet_direction_gain(selected_directions, directions[index], sigma)
            total = alpha * leverage[index] + beta * direction_gain + gamma * locality[index]
            choices.append(
                CandidateScore(
                    index=index,
                    leverage=float(leverage[index]),
                    direction_gain=direction_gain,
                    locality=float(locality[index]),
                    total_gain=float(total),
                )
            )
        if external_labels is None:
            winner = max(choices, key=lambda item: (item.total_gain, -item.index))
        else:
            winner = max(
                choices,
                key=lambda item: (
                    item.total_gain,
                    -float(distances[item.index]),
                    -int(external_labels[item.index]),
                ),
            )
        selected.append(winner.index)
        selected_directions.append(directions[winner.index])
        remaining.remove(winner.index)
        trace.append(winner)
    return selected, trace
