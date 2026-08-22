"""Degree-preserving reference rewiring for exported directed proximity graphs."""

from __future__ import annotations

from typing import Literal

import numpy as np

from .ggr import geometry_guarded_resistance_selection
from .graph import validate_adjacency
from .resistance import (
    edge_leverage_scores,
    effective_resistance_matrix,
    gaussian_weight_graph,
    greedy_neighbor_selection,
)

Variant = Literal[
    "original",
    "random",
    "distance",
    "geometry",
    "resistance",
    "resistance_direction",
    "ggr",
]


def two_hop_candidate_pool(adjacency: np.ndarray, node: int) -> np.ndarray:
    """Return unique one/two-hop candidates under union symmetrization."""

    graph = np.asarray(adjacency, dtype=bool)
    union = graph | graph.T
    one_hop = np.flatnonzero(union[node])
    candidates = set(int(item) for item in one_hop)
    for neighbor in one_hop:
        candidates.update(int(item) for item in np.flatnonzero(union[neighbor]))
    candidates.discard(node)
    return np.array(sorted(candidates), dtype=np.int64)


def _local_candidate_leverage(
    points: np.ndarray, adjacency: np.ndarray, center: int, candidates: np.ndarray
) -> np.ndarray:
    """Score candidate center edges in an explicitly augmented local graph.

    All center-to-candidate edges are inserted before resistance is computed. Existing
    candidate-to-candidate edges use union symmetrization. The star makes the local
    graph connected; scores are therefore standard resistance values on this stated
    augmented graph, not regularized resistance.
    """

    ids = np.concatenate([[center], candidates])
    local_adjacency = (adjacency[np.ix_(ids, ids)] | adjacency[np.ix_(ids, ids)].T).copy()
    local_adjacency[0, 1:] = True
    local_adjacency[1:, 0] = True
    np.fill_diagonal(local_adjacency, False)
    weights = gaussian_weight_graph(points[ids], local_adjacency)
    resistance = effective_resistance_matrix(weights)
    leverage = edge_leverage_scores(weights, resistance)
    return leverage[0, 1:]


def rewire_directed_graph(
    points: np.ndarray,
    adjacency: np.ndarray,
    variant: Variant,
    *,
    seed: int = 0,
    max_candidates: int = 32,
    epsilon: float = 0.0,
) -> tuple[np.ndarray, dict[str, int | float | str]]:
    """Re-select every node's outgoing list without changing per-node edge budgets.

    This reference operates on an exported bottom-layer graph and does not mutate an
    hnswlib index in place. Candidate scoring uses no queries or ground-truth labels.
    """

    points = np.asarray(points, dtype=np.float64)
    graph = np.asarray(adjacency, dtype=bool)
    validate_adjacency(graph)
    if graph.shape[0] != len(points):
        raise ValueError("point and graph sizes differ")
    supported = {
        "original",
        "random",
        "distance",
        "geometry",
        "resistance",
        "resistance_direction",
        "ggr",
    }
    if variant not in supported:
        raise ValueError(f"unsupported variant: {variant}")
    if variant == "original":
        return graph.copy(), {"variant": variant, "replaced_directed_edges": 0}

    rng = np.random.default_rng(seed)
    repaired = np.zeros_like(graph)
    replaced = 0
    accepted_swaps = 0
    geometry_loss = 0.0
    leverage_gain = 0.0
    for center in range(len(graph)):
        original = np.flatnonzero(graph[center])
        budget = len(original)
        if budget == 0:
            continue
        pool = two_hop_candidate_pool(graph, center)
        distances = np.linalg.norm(points[pool] - points[center], axis=1)
        if len(pool) > max_candidates:
            keep = set(int(item) for item in original)
            for item in pool[np.argsort(distances)]:
                if len(keep) >= max(max_candidates, budget):
                    break
                keep.add(int(item))
            pool = np.array(sorted(keep), dtype=np.int64)
            distances = np.linalg.norm(points[pool] - points[center], axis=1)
        if len(pool) < budget:
            raise RuntimeError("candidate pool cannot satisfy the original degree")

        if variant == "random":
            chosen = rng.choice(pool, size=budget, replace=False)
        elif variant == "distance":
            chosen = pool[np.argsort(distances)[:budget]]
        else:
            leverage = (
                _local_candidate_leverage(points, graph, center, pool)
                if variant in {"resistance", "resistance_direction", "ggr"}
                else np.zeros(len(pool))
            )
            if variant == "resistance":
                chosen = pool[np.argsort(-leverage, kind="stable")[:budget]]
            elif variant == "ggr":
                result = geometry_guarded_resistance_selection(
                    points[center], points[pool], leverage, budget, epsilon=epsilon
                )
                chosen = pool[np.asarray(result.selected, dtype=np.int64)]
                accepted_swaps += len(result.swaps)
                geometry_loss += result.geometry_star - result.geometry_final
                leverage_gain += result.leverage_final - result.leverage_initial
            else:
                alpha = 1.0 if variant == "resistance_direction" else 0.0
                beta = 1.0
                gamma = 1.0 if variant == "geometry" else 0.25
                selected, _ = greedy_neighbor_selection(
                    points[center],
                    points[pool],
                    leverage,
                    budget,
                    alpha=alpha,
                    beta=beta,
                    gamma=gamma,
                )
                chosen = pool[selected]
        repaired[center, chosen] = True
        replaced += len(set(int(item) for item in original) - set(int(item) for item in chosen))

    if not np.array_equal(repaired.sum(axis=1), graph.sum(axis=1)):
        raise AssertionError("rewiring changed a per-node degree budget")
    if repaired.sum() != graph.sum():
        raise AssertionError("rewiring changed the total directed edge budget")
    validate_adjacency(repaired, max_degree=int(graph.sum(axis=1).max(initial=0)))
    return repaired, {
        "variant": variant,
        "replaced_directed_edges": replaced,
        "accepted_swaps": accepted_swaps,
        "geometry_objective_loss": geometry_loss,
        "frozen_leverage_gain": leverage_gain,
        "epsilon": epsilon,
    }
