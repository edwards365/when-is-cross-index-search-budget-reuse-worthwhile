"""Resistance-specific negative controls for Geometry-guarded selection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ggr import (
    GGRResult,
    geometry_guarded_resistance_selection,
    geometry_objective,
)
from .resistance import greedy_neighbor_selection


@dataclass(frozen=True)
class GeometrySafeRandomSwap:
    """One query-free random exchange satisfying the frozen Geometry floor."""

    outgoing: int
    incoming: int
    geometry_before: float
    geometry_after: float


@dataclass(frozen=True)
class GeometrySafeRandomResult:
    """Random-control terminal set and its complete feasibility trace."""

    selected: tuple[int, ...]
    geometry_selected: tuple[int, ...]
    geometry_base: float
    geometry_final: float
    epsilon: float
    geometry_tolerance: float
    geometry_allowance: float
    requested_swaps: int
    termination: str
    swaps: tuple[GeometrySafeRandomSwap, ...]


@dataclass(frozen=True)
class ShuffledResistanceResult:
    """GGR output after a within-pool permutation of frozen leverage scores."""

    permutation: tuple[int, ...]
    selection: GGRResult


def geometry_safe_random_selection(
    center: np.ndarray,
    candidates: np.ndarray,
    budget: int,
    *,
    requested_swaps: int,
    seed: int,
    epsilon: float = 0.0,
    geometry_tolerance: float = 1e-12,
    beta: float = 1.0,
    gamma: float = 1.0,
    sigma: float = 0.5,
    rho: float | None = None,
) -> GeometrySafeRandomResult:
    """Randomly choose feasible swaps while matching a requested GGR swap budget.

    The control sees no leverage, query, trace, or ground truth. It samples uniformly
    from the sorted set of as-yet-unvisited one-swap Geometry-feasible terminal sets.
    Avoiding revisits prevents inverse swaps from inflating treatment strength.
    """

    center = np.asarray(center, dtype=np.float64)
    candidates = np.asarray(candidates, dtype=np.float64)
    if not 0 <= budget <= len(candidates):
        raise ValueError("budget is outside the candidate set")
    if requested_swaps < 0:
        raise ValueError("requested_swaps must be nonnegative")
    if not np.isfinite(epsilon) or not 0 <= epsilon < 1:
        raise ValueError("epsilon must lie in [0, 1)")
    if not np.isfinite(geometry_tolerance) or geometry_tolerance < 0:
        raise ValueError("geometry_tolerance must be finite and nonnegative")
    if rho is None and len(candidates):
        distances = np.linalg.norm(candidates - center, axis=1)
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
    geometry_base = geometry_objective(
        center,
        candidates,
        geometry_selected,
        beta=beta,
        gamma=gamma,
        sigma=sigma,
        rho=rho,
    )
    allowance = geometry_tolerance * (1.0 + abs(geometry_base))
    threshold = (1.0 - epsilon) * geometry_base
    selected = sorted(int(item) for item in geometry_selected)
    geometry_total = geometry_base
    visited = {tuple(selected)}
    swaps: list[GeometrySafeRandomSwap] = []
    rng = np.random.default_rng(seed)

    for _ in range(requested_swaps):
        selected_set = set(selected)
        feasible: list[tuple[int, int, float, list[int]]] = []
        for outgoing in sorted(selected_set):
            for incoming in range(len(candidates)):
                if incoming in selected_set:
                    continue
                proposal = sorted((selected_set - {outgoing}) | {incoming})
                if tuple(proposal) in visited:
                    continue
                proposal_geometry = geometry_objective(
                    center,
                    candidates,
                    proposal,
                    beta=beta,
                    gamma=gamma,
                    sigma=sigma,
                    rho=rho,
                )
                if proposal_geometry + allowance >= threshold:
                    feasible.append((outgoing, incoming, proposal_geometry, proposal))
        if not feasible:
            termination = "feasible_set_exhausted"
            break
        outgoing, incoming, proposal_geometry, proposal = feasible[
            int(rng.integers(len(feasible)))
        ]
        swaps.append(
            GeometrySafeRandomSwap(
                outgoing=outgoing,
                incoming=incoming,
                geometry_before=geometry_total,
                geometry_after=proposal_geometry,
            )
        )
        selected = proposal
        geometry_total = proposal_geometry
        visited.add(tuple(selected))
    else:
        termination = "matched_swap_budget"

    return GeometrySafeRandomResult(
        selected=tuple(selected),
        geometry_selected=tuple(int(item) for item in geometry_selected),
        geometry_base=geometry_base,
        geometry_final=geometry_total,
        epsilon=epsilon,
        geometry_tolerance=geometry_tolerance,
        geometry_allowance=allowance,
        requested_swaps=requested_swaps,
        termination=termination,
        swaps=tuple(swaps),
    )


def shuffled_resistance_selection(
    center: np.ndarray,
    candidates: np.ndarray,
    leverage: np.ndarray,
    budget: int,
    *,
    seed: int,
    epsilon: float = 0.0,
    geometry_tolerance: float = 1e-12,
    leverage_tolerance: float = 1e-12,
) -> ShuffledResistanceResult:
    """Permute leverage identities within one local pool, then run unchanged GGR."""

    leverage = np.asarray(leverage, dtype=np.float64)
    if leverage.shape != (len(candidates),):
        raise ValueError("leverage must be one value per candidate")
    permutation = np.random.default_rng(seed).permutation(len(leverage))
    selection = geometry_guarded_resistance_selection(
        center,
        candidates,
        leverage[permutation],
        budget,
        epsilon=epsilon,
        geometry_tolerance=geometry_tolerance,
        leverage_tolerance=leverage_tolerance,
    )
    return ShuffledResistanceResult(
        permutation=tuple(int(item) for item in permutation), selection=selection
    )
