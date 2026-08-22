"""Query-independent Geometry-Guarded Resistance (GGR) selection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .resistance import direction_coverage, greedy_neighbor_selection


@dataclass(frozen=True)
class GGRSwap:
    """One accepted one-for-one exchange in candidate-index coordinates."""

    outgoing: int
    incoming: int
    geometry_before: float
    geometry_after: float
    leverage_before: float
    leverage_after: float


@dataclass(frozen=True)
class GGRResult:
    """Complete deterministic selection result and its audit trace."""

    selected: tuple[int, ...]
    geometry_selected: tuple[int, ...]
    geometry_star: float
    geometry_final: float
    leverage_initial: float
    leverage_final: float
    epsilon: float
    tolerance: float
    termination: str
    swaps: tuple[GGRSwap, ...]


def geometry_objective(
    center: np.ndarray,
    candidates: np.ndarray,
    selected: list[int] | tuple[int, ...] | np.ndarray,
    *,
    beta: float = 1.0,
    gamma: float = 1.0,
    sigma: float = 0.5,
    rho: float | None = None,
) -> float:
    """Evaluate the exact Geometry-only set objective used by the greedy baseline."""

    center = np.asarray(center, dtype=np.float64)
    candidates = np.asarray(candidates, dtype=np.float64)
    chosen = np.asarray(selected, dtype=np.int64)
    if candidates.ndim != 2 or candidates.shape[1:] != center.shape:
        raise ValueError("candidate dimensions must match center")
    if chosen.ndim != 1 or np.any(chosen < 0) or np.any(chosen >= len(candidates)):
        raise ValueError("selected contains an invalid candidate index")
    if len(np.unique(chosen)) != len(chosen):
        raise ValueError("selected candidate indices must be unique")
    if min(beta, gamma) < 0 or sigma <= 0:
        raise ValueError("coefficients must be nonnegative and sigma positive")
    if len(candidates) == 0:
        return 0.0

    delta = candidates - center
    distances = np.linalg.norm(delta, axis=1)
    if np.any(distances <= np.finfo(float).eps):
        raise ValueError("candidate equal to center would have undefined direction")
    if rho is None:
        rho = float(np.median(distances))
    if not np.isfinite(rho) or rho <= 0:
        raise ValueError("rho must be positive")
    if not np.isfinite(beta) or not np.isfinite(gamma) or not np.isfinite(sigma):
        raise ValueError("coefficients must be finite")

    directions = delta / distances[:, None]
    locality = np.exp(-np.square(distances / rho))
    return float(
        beta * direction_coverage(directions[chosen], sigma)
        + gamma * locality[chosen].sum()
    )


def geometry_guarded_resistance_selection(
    center: np.ndarray,
    candidates: np.ndarray,
    leverage: np.ndarray,
    budget: int,
    *,
    epsilon: float = 0.0,
    tolerance: float = 1e-12,
    max_swaps: int | None = None,
    beta: float = 1.0,
    gamma: float = 1.0,
    sigma: float = 0.5,
    rho: float | None = None,
) -> GGRResult:
    """Improve frozen leverage subject to a Geometry-only objective floor.

    This API deliberately accepts no query, trace, failure label, or ground truth.
    Candidate leverages are treated as immutable input throughout the exchange loop.
    """

    candidates = np.asarray(candidates, dtype=np.float64)
    leverage = np.asarray(leverage, dtype=np.float64)
    if leverage.shape != (len(candidates),):
        raise ValueError("leverage must be one value per candidate")
    if np.any(~np.isfinite(leverage)) or np.any(leverage < 0):
        raise ValueError("leverage must be finite and nonnegative")
    if not 0 <= budget <= len(candidates):
        raise ValueError("budget is outside the candidate set")
    if not np.isfinite(epsilon) or not 0 <= epsilon < 1:
        raise ValueError("epsilon must lie in [0, 1)")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    if len(candidates) == 0:
        return GGRResult(
            selected=(),
            geometry_selected=(),
            geometry_star=0.0,
            geometry_final=0.0,
            leverage_initial=0.0,
            leverage_final=0.0,
            epsilon=epsilon,
            tolerance=tolerance,
            termination="local_optimum",
            swaps=(),
        )

    if rho is None and len(candidates):
        distances = np.linalg.norm(candidates - np.asarray(center, dtype=np.float64), axis=1)
        rho = float(np.median(distances))

    geometry_selected, _ = greedy_neighbor_selection(
        center,
        candidates,
        np.zeros(len(candidates), dtype=np.float64),
        budget,
        alpha=0.0,
        beta=beta,
        gamma=gamma,
        sigma=sigma,
        rho=rho,
    )
    geometry_star = geometry_objective(
        center,
        candidates,
        geometry_selected,
        beta=beta,
        gamma=gamma,
        sigma=sigma,
        rho=rho,
    )
    threshold = (1.0 - epsilon) * geometry_star
    selected = list(geometry_selected)
    leverage_total = float(leverage[selected].sum())
    geometry_total = geometry_star
    if max_swaps is None:
        max_swaps = budget * (len(candidates) - budget)
    if max_swaps < 0:
        raise ValueError("max_swaps must be nonnegative")

    swaps: list[GGRSwap] = []
    termination = "local_optimum"
    for _ in range(max_swaps):
        selected_set = set(selected)
        feasible: list[tuple[float, float, int, int, list[int]]] = []
        for outgoing in sorted(selected_set):
            for incoming in range(len(candidates)):
                if incoming in selected_set:
                    continue
                leverage_gain = float(leverage[incoming] - leverage[outgoing])
                if leverage_gain <= tolerance:
                    continue
                proposal = [item for item in selected if item != outgoing]
                proposal.append(incoming)
                proposal.sort()
                proposal_geometry = geometry_objective(
                    center,
                    candidates,
                    proposal,
                    beta=beta,
                    gamma=gamma,
                    sigma=sigma,
                    rho=rho,
                )
                if proposal_geometry + tolerance >= threshold:
                    feasible.append(
                        (leverage_gain, proposal_geometry, -outgoing, -incoming, proposal)
                    )
        if not feasible:
            break
        leverage_gain, proposal_geometry, neg_outgoing, neg_incoming, proposal = max(feasible)
        outgoing = -neg_outgoing
        incoming = -neg_incoming
        new_leverage = leverage_total + leverage_gain
        swaps.append(
            GGRSwap(
                outgoing=outgoing,
                incoming=incoming,
                geometry_before=geometry_total,
                geometry_after=proposal_geometry,
                leverage_before=leverage_total,
                leverage_after=new_leverage,
            )
        )
        selected = proposal
        geometry_total = proposal_geometry
        leverage_total = new_leverage
    else:
        termination = "max_swaps"

    return GGRResult(
        selected=tuple(selected),
        geometry_selected=tuple(geometry_selected),
        geometry_star=geometry_star,
        geometry_final=geometry_total,
        leverage_initial=float(leverage[geometry_selected].sum()),
        leverage_final=leverage_total,
        epsilon=epsilon,
        tolerance=tolerance,
        termination=termination,
        swaps=tuple(swaps),
    )
