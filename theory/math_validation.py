"""Small-graph numerical checks for the mathematical theory.

These routines are deliberately exact or dense and are only intended for graphs
small enough to audit.  Numerical agreement is evidence about the implementation,
not a substitute for a proof.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from itertools import combinations

import numpy as np

Edge = tuple[int, int, float]


def graph_matrices(n: int, edges: Sequence[Edge]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return oriented incidence B, diagonal conductance W, and L=BWB^T."""
    b = np.zeros((n, len(edges)), dtype=float)
    weights = np.empty(len(edges), dtype=float)
    for j, (u, v, weight) in enumerate(edges):
        if u == v or weight <= 0:
            raise ValueError("edges must join distinct vertices and have positive conductance")
        b[u, j], b[v, j] = 1.0, -1.0
        weights[j] = weight
    w = np.diag(weights)
    return b, w, b @ w @ b.T


def effective_resistance(n: int, edges: Sequence[Edge], u: int, v: int) -> float:
    """Compute b_uv^T L^+ b_uv for a connected positive-weight graph."""
    _, _, laplacian = graph_matrices(n, edges)
    contrast = np.zeros(n)
    contrast[u], contrast[v] = 1.0, -1.0
    return float(contrast @ np.linalg.pinv(laplacian, hermitian=True) @ contrast)


def projection_and_leverages(
    n: int, edges: Sequence[Edge]
) -> tuple[np.ndarray, np.ndarray]:
    """Return the weighted cut-space projector and its diagonal leverage scores."""
    b, w, laplacian = graph_matrices(n, edges)
    sqrt_w = np.diag(np.sqrt(np.diag(w)))
    projector = sqrt_w @ b.T @ np.linalg.pinv(laplacian, hermitian=True) @ b @ sqrt_w
    return projector, np.diag(projector).copy()


def path_edges(n: int, weight: float = 1.0) -> list[Edge]:
    return [(i, i + 1, weight) for i in range(n - 1)]


def cycle_edges(n: int, weight: float = 1.0) -> list[Edge]:
    return path_edges(n, weight) + [(n - 1, 0, weight)]


def complete_edges(n: int, weight: float = 1.0) -> list[Edge]:
    return [(u, v, weight) for u, v in combinations(range(n), 2)]


def double_clique_edges(size: int, bridge_weight: float = 1.0) -> list[Edge]:
    left = complete_edges(size)
    right = [(u + size, v + size, w) for u, v, w in complete_edges(size)]
    return left + right + [(size - 1, size, bridge_weight)]


def parallel_two_hop_edges(count: int) -> tuple[int, list[Edge]]:
    """A unit direct edge plus `count` internally disjoint unit two-hop paths."""
    paths = [
        edge
        for i in range(count)
        for edge in ((0, i + 2, 1.0), (i + 2, 1, 1.0))
    ]
    return count + 2, [(0, 1, 1.0)] + paths


def spanning_tree_marginals(n: int, edges: Sequence[Edge]) -> np.ndarray:
    """Enumerate weighted spanning trees and return exact edge inclusion probabilities."""
    totals = np.zeros(len(edges), dtype=float)
    partition = 0.0
    for subset in combinations(range(len(edges)), n - 1):
        parent = list(range(n))

        def find(x: int, current_parent: list[int] = parent) -> int:
            while current_parent[x] != x:
                current_parent[x] = current_parent[current_parent[x]]
                x = current_parent[x]
            return x

        valid = True
        tree_weight = 1.0
        for edge_index in subset:
            u, v, weight = edges[edge_index]
            ru, rv = find(u), find(v)
            if ru == rv:
                valid = False
                break
            parent[ru] = rv
            tree_weight *= weight
        if valid and len({find(i) for i in range(n)}) == 1:
            partition += tree_weight
            totals[list(subset)] += tree_weight
    if partition == 0:
        raise ValueError("graph is disconnected")
    return totals / partition


def sampled_spanning_tree_frequencies(
    n: int, edges: Sequence[Edge], samples: int, seed: int = 0
) -> np.ndarray:
    """Sample from the exact small-graph weighted-tree distribution."""
    trees: list[tuple[int, ...]] = []
    weights: list[float] = []
    for subset in combinations(range(len(edges)), n - 1):
        chosen = [edges[i] for i in subset]
        if np.linalg.matrix_rank(graph_matrices(n, chosen)[2], tol=1e-9) != n - 1:
            continue
        trees.append(subset)
        weights.append(float(np.prod([edges[i][2] for i in subset])))
    probabilities = np.asarray(weights) / np.sum(weights)
    rng = np.random.default_rng(seed)
    counts = np.zeros(len(edges))
    for tree_index in rng.choice(len(trees), size=samples, p=probabilities):
        counts[list(trees[tree_index])] += 1
    return counts / samples


def direction_logdet(vectors: np.ndarray, selected: Iterable[int], sigma: float = 1.0) -> float:
    """Evaluate log det(I + sigma^-2 sum z z^T) with normalized rows z."""
    chosen = list(selected)
    if not chosen:
        return 0.0
    z = np.asarray(vectors, dtype=float)[chosen]
    norms = np.linalg.norm(z, axis=1)
    if np.any(norms == 0) or sigma <= 0:
        raise ValueError("directions must be nonzero and sigma positive")
    z = z / norms[:, None]
    gram = z @ z.T / sigma**2
    sign, value = np.linalg.slogdet(np.eye(len(chosen)) + gram)
    if sign <= 0:
        raise FloatingPointError("regularized Gram matrix must be positive definite")
    return float(value)


def frozen_objective(
    vectors: np.ndarray,
    selected: Iterable[int],
    leverage: np.ndarray,
    locality: np.ndarray,
    coefficients: tuple[float, float, float],
    sigma: float = 1.0,
) -> float:
    chosen = list(selected)
    alpha, beta, gamma = coefficients
    return float(
        alpha * np.sum(leverage[chosen])
        + beta * direction_logdet(vectors, chosen, sigma)
        + gamma * np.sum(locality[chosen])
    )


def diminishing_returns_violations(
    ground_size: int, objective
) -> list[tuple[int, int, int, float, float]]:
    """Exhaustively return (A-mask, B-mask, v, Delta_A, Delta_B) violations."""
    violations = []
    for a_mask in range(1 << ground_size):
        for b_mask in range(1 << ground_size):
            if a_mask & ~b_mask:
                continue
            for v in range(ground_size):
                bit = 1 << v
                if b_mask & bit:
                    continue
                delta_a = objective(a_mask | bit) - objective(a_mask)
                delta_b = objective(b_mask | bit) - objective(b_mask)
                if delta_a + 1e-10 < delta_b:
                    violations.append((a_mask, b_mask, v, delta_a, delta_b))
    return violations


def dynamic_leverage_objective(
    n: int, base_edges: Sequence[Edge], candidates: Sequence[Edge], selected_mask: int
) -> float:
    """One explicit dynamic set function: sum current leverages of selected new edges."""
    selected = [i for i in range(len(candidates)) if selected_mask & (1 << i)]
    augmented = list(base_edges) + [candidates[i] for i in selected]
    _, scores = projection_and_leverages(n, augmented)
    offset = len(base_edges)
    return float(np.sum(scores[offset:]))


def pure_greedy_path(
    coordinates: np.ndarray, adjacency: dict[int, set[int]], query: np.ndarray, start: int
) -> list[int]:
    """Run strict pure greedy search with deterministic index tie-breaking."""
    path = [start]
    while True:
        current = path[-1]
        current_distance = float(np.linalg.norm(coordinates[current] - query))
        improving = [
            v
            for v in adjacency.get(current, set())
            if float(np.linalg.norm(coordinates[v] - query)) < current_distance
        ]
        if not improving:
            return path
        next_vertex = min(improving, key=lambda v: (np.linalg.norm(coordinates[v] - query), v))
        if next_vertex in path:
            raise RuntimeError("strict distance decrease should prevent cycles")
        path.append(next_vertex)
