"""Instrumented reference beam search over an exported proximity graph."""

from __future__ import annotations

import heapq

import numpy as np


def beam_search(
    points: np.ndarray,
    adjacency: np.ndarray,
    query: np.ndarray,
    entrypoint: int,
    *,
    k: int,
    ef: int,
) -> tuple[np.ndarray, int, int]:
    """Return labels, exact distance-call count, and expanded-node count."""

    if ef < k:
        raise ValueError("ef must be at least k")
    points = np.asarray(points, dtype=np.float64)
    graph = np.asarray(adjacency, dtype=bool)
    query = np.asarray(query, dtype=np.float64)
    if graph.shape != (len(points), len(points)) or not 0 <= entrypoint < len(points):
        raise ValueError("invalid graph or entrypoint")

    entry_distance = float(np.sum(np.square(points[entrypoint] - query)))
    distance_calls = 1
    expanded = 0
    candidates: list[tuple[float, int]] = [(entry_distance, entrypoint)]
    best: list[tuple[float, int]] = [(-entry_distance, entrypoint)]
    visited = {entrypoint}
    while candidates:
        candidate_distance, node = heapq.heappop(candidates)
        worst_distance = -best[0][0]
        if len(best) >= ef and candidate_distance > worst_distance:
            break
        expanded += 1
        for neighbor in np.flatnonzero(graph[node]):
            neighbor = int(neighbor)
            if neighbor in visited:
                continue
            visited.add(neighbor)
            distance = float(np.sum(np.square(points[neighbor] - query)))
            distance_calls += 1
            if len(best) < ef or distance < -best[0][0]:
                heapq.heappush(candidates, (distance, neighbor))
                heapq.heappush(best, (-distance, neighbor))
                if len(best) > ef:
                    heapq.heappop(best)
    ordered = sorted([(-distance, node) for distance, node in best])[:k]
    return np.array([node for _, node in ordered], dtype=np.int64), distance_calls, expanded
