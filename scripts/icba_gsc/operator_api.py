"""Deterministic, proposal-only O4/O6 graph operators for the GSC pilot.

The API works on exported adjacency arrays and response scores supplied by the
proposal/validation roles. It never reads truth, certification, or evaluation
data and never mutates its input array.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np


def _check_graph(adjacency: np.ndarray) -> np.ndarray:
    graph = np.asarray(adjacency, dtype=bool)
    if graph.ndim != 2 or graph.shape[0] != graph.shape[1]:
        raise ValueError("adjacency must be square")
    if np.any(np.diag(graph)):
        raise ValueError("self-loops are forbidden")
    return graph


def rollback_graph(adjacency: np.ndarray) -> np.ndarray:
    """Return an isolated copy suitable for transactional rollback."""

    return _check_graph(adjacency).copy()


def response_weighted_prune(
    adjacency: np.ndarray,
    response_scores: Sequence[float],
    *,
    candidate_pools: Iterable[Sequence[int]] | None = None,
    critical_scores: Sequence[float] | None = None,
    backup_scores: Sequence[float] | None = None,
    intruder_penalty: float = 0.25,
) -> np.ndarray:
    """O4: choose a response-weighted candidate set at each node's old budget.

    Candidate pools and scores are proposal/validation inputs. Original degree
    budgets are retained exactly; ties end at the lowest node ID.
    """

    graph = _check_graph(adjacency)
    n = graph.shape[0]
    response = np.asarray(response_scores, dtype=float)
    if response.shape != (n,):
        raise ValueError("response_scores must have one value per node")
    critical = np.zeros(n, dtype=float) if critical_scores is None else np.asarray(critical_scores, dtype=float)
    backup = np.zeros(n, dtype=float) if backup_scores is None else np.asarray(backup_scores, dtype=float)
    if critical.shape != (n,) or backup.shape != (n,):
        raise ValueError("critical/backup scores must have one value per node")
    pools = list(candidate_pools) if candidate_pools is not None else [np.flatnonzero(graph[i]) for i in range(n)]
    if len(pools) != n:
        raise ValueError("candidate_pools must have one pool per node")
    repaired = np.zeros_like(graph, dtype=bool)
    for node in range(n):
        original = np.flatnonzero(graph[node]).astype(int)
        budget = len(original)
        pool = sorted({int(x) for x in pools[node] if 0 <= int(x) < n and int(x) != node})
        if len(pool) < budget:
            raise ValueError("candidate pool cannot satisfy original degree")
        scored = sorted(
            pool,
            key=lambda x: (
                -(response[x] - intruder_penalty * critical[x]),
                -critical[x],
                -backup[x],
                x,
            ),
        )
        repaired[node, scored[:budget]] = True
    if not np.array_equal(repaired.sum(axis=1), graph.sum(axis=1)):
        raise AssertionError("O4 changed per-node degree")
    return repaired


def response_aware_insertion_order(
    neighbors: Sequence[Sequence[int]],
    response_scores: Sequence[float],
    *,
    reorder_fraction: float = 0.05,
) -> list[list[int]]:
    """O6: deterministically reorder only a bounded prefix of each list."""

    if not 0.0 <= reorder_fraction <= 1.0:
        raise ValueError("reorder_fraction must be in [0,1]")
    response = np.asarray(response_scores, dtype=float)
    result: list[list[int]] = []
    for row in neighbors:
        original = [int(x) for x in row]
        if any(x < 0 or x >= len(response) for x in original):
            raise ValueError("neighbor ID out of range")
        count = min(len(original), int(math.ceil(len(original) * reorder_fraction)))
        prefix = sorted(original[:count], key=lambda x: (-response[x], x))
        result.append(prefix + original[count:])
    return result


def assert_same_degree(original: np.ndarray, candidate: np.ndarray) -> None:
    left = _check_graph(original)
    right = _check_graph(candidate)
    if left.shape != right.shape or not np.array_equal(left.sum(axis=1), right.sum(axis=1)):
        raise AssertionError("degree invariant failed")
