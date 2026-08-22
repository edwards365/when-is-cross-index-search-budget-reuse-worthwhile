"""Instrumented reference beam search over an exported proximity graph."""

from __future__ import annotations

import heapq

import numpy as np


def _squared_l2_float32(left: np.ndarray, right: np.ndarray) -> float:
    total = np.float32(0.0)
    for left_value, right_value in zip(left, right, strict=True):
        difference = np.float32(left_value - right_value)
        total = np.float32(total + np.float32(difference * difference))
    return float(total)


def ordered_beam_search(
    points: np.ndarray,
    neighbors: list[list[int]],
    query: np.ndarray,
    entrypoint: int,
    *,
    k: int,
    ef: int,
) -> tuple[np.ndarray, int, int]:
    """Replay hnswlib's bare-bone layer-0 search in stored neighbor order."""

    if ef < k:
        raise ValueError("ef must be at least k")
    points = np.asarray(points, dtype=np.float32)
    query = np.asarray(query, dtype=np.float32)
    if len(neighbors) != len(points) or not 0 <= entrypoint < len(points):
        raise ValueError("invalid ordered graph or entrypoint")
    entry_distance = _squared_l2_float32(points[entrypoint], query)
    distance_calls = 1
    expanded = 0
    candidates: list[tuple[float, int]] = [(entry_distance, entrypoint)]
    best: list[tuple[float, int]] = [(-entry_distance, entrypoint)]
    visited = {entrypoint}
    lower_bound = entry_distance
    while candidates:
        candidate_distance, node = candidates[0]
        if candidate_distance > lower_bound:
            break
        heapq.heappop(candidates)
        expanded += 1
        for neighbor in neighbors[node]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            distance = _squared_l2_float32(points[neighbor], query)
            distance_calls += 1
            if len(best) < ef or lower_bound > distance:
                heapq.heappush(candidates, (distance, neighbor))
                heapq.heappush(best, (-distance, neighbor))
                if len(best) > ef:
                    heapq.heappop(best)
                lower_bound = -best[0][0]
    ordered = sorted([(-distance, node) for distance, node in best])[:k]
    return np.array([node for _, node in ordered], dtype=np.int64), distance_calls, expanded


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
