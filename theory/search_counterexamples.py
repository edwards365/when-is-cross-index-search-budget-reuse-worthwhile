"""Reproduce the finite counterexamples recorded in counterexamples.md."""

from __future__ import annotations

import json
from itertools import combinations

import numpy as np

from theory.math_validation import (
    diminishing_returns_violations,
    dynamic_leverage_objective,
    effective_resistance,
    graph_matrices,
    parallel_two_hop_edges,
    pure_greedy_path,
)


def find_dynamic_leverage_violation(max_n: int = 6) -> dict[str, object]:
    """Find a minimal unweighted example for the declared dynamic objective."""
    for n in range(3, max_n + 1):
        all_pairs = list(combinations(range(n), 2))
        for base_pairs in combinations(all_pairs, n - 1):
            base = [(u, v, 1.0) for u, v in base_pairs]
            if np.linalg.matrix_rank(graph_matrices(n, base)[2], tol=1e-9) != n - 1:
                continue
            missing = [pair for pair in all_pairs if pair not in base_pairs]
            for candidate_pairs in combinations(missing, min(3, len(missing))):
                candidates = [(u, v, 1.0) for u, v in candidate_pairs]
                def objective(
                    mask: int,
                    current_n: int = n,
                    current_base=base,
                    current_candidates=candidates,
                ) -> float:
                    return dynamic_leverage_objective(
                        current_n, current_base, current_candidates, mask
                    )

                violations = diminishing_returns_violations(len(candidates), objective)
                if violations:
                    a, b, v, delta_a, delta_b = violations[0]
                    return {
                        "n": n,
                        "base_edges": base,
                        "candidate_edges": candidates,
                        "a_mask": a,
                        "b_mask": b,
                        "added_candidate": v,
                        "delta_a": delta_a,
                        "delta_b": delta_b,
                    }
    raise RuntimeError("no violation found in search range")


def fixed_navigation_examples() -> dict[str, object]:
    high_coordinates = [[0.0, 0.0], [-1.0, 0.0], [1.0, 0.0], [2.0, 0.0]]
    high_edges = [(0, 1, 1.0), (0, 2, 1.0), (2, 3, 1.0)]

    n, low_edges = parallel_two_hop_edges(4)
    low_coordinates = [[0.0, 0.0], [2.0, 0.0]] + [[0.0, 10.0 + i] for i in range(4)]
    without_shortcut = {i: set() for i in range(n)}
    for u, v, _ in low_edges[1:]:
        without_shortcut[u].add(v)
        without_shortcut[v].add(u)
    with_shortcut = {u: set(vs) for u, vs in without_shortcut.items()}
    with_shortcut[0].add(1)
    with_shortcut[1].add(0)

    return {
        "high_resistance_no_navigation": {
            "coordinates": high_coordinates,
            "edges": high_edges,
            "query": [2.0, 0.0],
            "edge": [0, 1],
            "leverage": effective_resistance(4, high_edges, 0, 1),
            "distance_change": 3.0 - 2.0,
        },
        "low_resistance_high_navigation": {
            "coordinates": low_coordinates,
            "edges": low_edges,
            "query": [2.1, 0.0],
            "edge": [0, 1],
            "leverage": effective_resistance(n, low_edges, 0, 1),
            "path_without": pure_greedy_path(
                np.asarray(low_coordinates),
                without_shortcut,
                np.asarray([2.1, 0.0]),
                0,
            ),
            "path_with": pure_greedy_path(
                np.asarray(low_coordinates),
                with_shortcut,
                np.asarray([2.1, 0.0]),
                0,
            ),
        },
    }


if __name__ == "__main__":
    result = {
        **fixed_navigation_examples(),
        "dynamic": find_dynamic_leverage_violation(),
    }
    print(json.dumps(result, indent=2))
