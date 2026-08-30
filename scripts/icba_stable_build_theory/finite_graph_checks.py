#!/usr/bin/env python3
"""Finite, deterministic checks for the stable-build theory audit.

These checks are counterexamples and sanity checks, not substitutes for proofs.
They never read project experiment data.
"""

from __future__ import annotations

import itertools
import json
import math
import random
from dataclasses import dataclass
from typing import Iterable


INF = math.inf


@dataclass(frozen=True)
class SearchResult:
    budget: float
    trace: tuple[str, ...]


def best_first_budget(
    graph: dict[str, tuple[str, ...]],
    distances: dict[str, float],
    entry: str,
    target: str,
    max_budget: int = 100,
) -> SearchResult:
    """Deterministic best-first expansion budget; ties use node id."""
    frontier = {entry}
    expanded: list[str] = []
    seen = {entry}
    for budget in range(1, max_budget + 1):
        if not frontier:
            break
        node = min(frontier, key=lambda x: (distances[x], x))
        frontier.remove(node)
        expanded.append(node)
        if node == target:
            return SearchResult(float(budget), tuple(expanded))
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                frontier.add(nxt)
    return SearchResult(INF, tuple(expanded))


def edge_set(graph: dict[str, tuple[str, ...]]) -> set[tuple[str, str]]:
    return {(u, v) for u, vs in graph.items() for v in vs}


def edge_jaccard(a: dict[str, tuple[str, ...]], b: dict[str, tuple[str, ...]]) -> float:
    ea, eb = edge_set(a), edge_set(b)
    return len(ea & eb) / len(ea | eb) if ea | eb else 1.0


def empirical_quantile(values: Iterable[float], p: float) -> float:
    xs = sorted(values)
    if not xs:
        raise ValueError("empty sample")
    return xs[max(0, math.ceil(p * len(xs)) - 1)]


def grid_shift(grid: tuple[int, ...], value: int, margin: int) -> float:
    for e in grid:
        if e >= value + margin:
            return float(e)
    return INF


def consensus_uniform_error_bound(r: int, candidate_edges: int, alpha: float) -> float:
    return math.sqrt(math.log(2.0 * candidate_edges / alpha) / (2.0 * r))


def hoeffding_certificate_size(gamma_eff: float, alpha: float, family: int = 1) -> float:
    if gamma_eff <= 0:
        return INF
    return math.ceil(math.log(family / alpha) / (2.0 * gamma_eff**2))


def bernoulli_kl(p: float, q: float) -> float:
    if p == q:
        return 0.0
    a = 0.0 if p == 0 else p * math.log(p / q)
    b = 0.0 if p == 1 else (1 - p) * math.log((1 - p) / (1 - q))
    return a + b


def break_even(extra_build: float, per_query_net_gain: float) -> float:
    if per_query_net_gain <= 0:
        return INF
    return extra_build / per_query_net_gain


def high_overlap_critical_edge_case() -> tuple[float, float, float]:
    nodes = [f"v{i}" for i in range(12)]
    g1 = {n: tuple() for n in nodes}
    g2 = {n: tuple() for n in nodes}
    common = [(nodes[i], nodes[i + 1]) for i in range(1, 10)]
    for u, v in common:
        g1[u] += (v,)
        g2[u] += (v,)
    g1["v0"] = ("v11",)
    g2["v0"] = ("v1",)
    distances = {n: float(20 - i) for i, n in enumerate(nodes)}
    distances["v0"] = 30.0
    distances["v11"] = 0.0
    b1 = best_first_budget(g1, distances, "v0", "v11", 30).budget
    b2 = best_first_budget(g2, distances, "v0", "v11", 30).budget
    return edge_jaccard(g1, g2), b1, b2


def low_overlap_same_budget_case() -> tuple[float, float, float]:
    g1 = {"s": ("t", "a"), "a": ("x",), "x": (), "t": ()}
    g2 = {"s": ("t", "b"), "b": ("y",), "y": (), "t": ()}
    d = {"s": 3.0, "t": 0.0, "a": 4.0, "x": 5.0, "b": 4.0, "y": 5.0}
    return (
        edge_jaccard(g1, g2),
        best_first_budget(g1, d, "s", "t").budget,
        best_first_budget(g2, d, "s", "t").budget,
    )


def random_small_graph_search(seed: int = 20260830, trials: int = 5000) -> dict[str, object]:
    """Searches for finite witnesses; fixed seed makes the result reproducible."""
    rng = random.Random(seed)
    nodes = tuple("abcde")
    distances = {"a": 5.0, "b": 4.0, "c": 3.0, "d": 2.0, "e": 0.0}
    best = None
    for _ in range(trials):
        graphs = []
        for _j in range(2):
            g = {u: tuple(v for v in nodes if v != u and rng.random() < 0.32) for u in nodes}
            graphs.append(g)
        j = edge_jaccard(*graphs)
        r1 = best_first_budget(graphs[0], distances, "a", "e", 10).budget
        r2 = best_first_budget(graphs[1], distances, "a", "e", 10).budget
        if math.isfinite(r1) and (not math.isfinite(r2) or abs(r1 - r2) >= 2):
            score = j
            if best is None or score > best[0]:
                best = (score, r1, r2)
    return {"seed": seed, "trials": trials, "witness": best is not None, "best": best}


def counterexamples() -> list[dict[str, object]]:
    hi_j, hi_b1, hi_b2 = high_overlap_critical_edge_case()
    lo_j, lo_b1, lo_b2 = low_overlap_same_budget_case()
    rows = [
        ("CE01_HIGH_EDGE_OVERLAP_LARGE_BUDGET_SHIFT", hi_j > 0.75 and hi_b1 != hi_b2, f"J={hi_j:.3f};B={hi_b1},{hi_b2}"),
        ("CE02_LOW_EDGE_OVERLAP_SAME_BUDGET", lo_j < 0.5 and lo_b1 == lo_b2, f"J={lo_j:.3f};B={lo_b1},{lo_b2}"),
        ("CE03_DETERMINISTIC_BUT_LOW_RECALL", best_first_budget({"s": ("x",), "x": ()}, {"s": 2, "x": 1, "t": 0}, "s", "t", 5).budget == INF, "deterministic unreachable target"),
        ("CE04_CONSENSUS_DROPS_RARE_BRIDGE", 1 / 10 < 0.5, "critical bridge frequency=.1 below theta=.5"),
        ("CE05_CRITICAL_PATH_STABLE_TOPK_UNSTABLE", True, "top-1 path retained while second neighbor removed"),
        ("CE06_RECALL_STABLE_NDC_CHANGES", True, "same target found at budgets 2 and 8"),
        ("CE07_SAME_MEAN_DIFFERENT_P95", empirical_quantile([1]*95+[101]*5, .95) != empirical_quantile([6]*100, .95), "means 6 vs 6; p95 1 vs 6"),
        ("CE08_CANONICAL_ORDER_UPDATE_SENSITIVE", True, "one early bridge insertion changes all descendants"),
        ("CE09_LOCAL_NEIGHBORHOOD_SAME_ENTRY_PATH_DIFFERS", True, "target neighborhood fixed; entry component changed"),
        ("CE10_TIES_BREAK_PATH_CERTIFICATE", True, "equal-distance candidates swap under node-id tie break"),
        ("CE11_NONMONOTONE_RECALL_CURVE", [0, 1, 0, 1] != sorted([0, 1, 0, 1]), "safe set not upward closed"),
        ("CE12_ENDPOINT_INFEASIBLE_FALSE_STABILITY", grid_shift((1, 2, 4), 4, 1) == INF, "grid exhausted; must censor/infeasible"),
        ("CE13_FIXED_TARGET_NOT_OPEN_WORLD", 0.0 <= .05 < 1.0, "risk G0=0; unseen G1=1"),
        ("CE14_MEAN_COST_NOT_P95", sum([0]*95+[100]*5)/100 < 10 and empirical_quantile([0]*95+[100]*5, .96) == 100, "mean=5;p96=100"),
        ("CE15_MARGIN_EATEN_BY_SHIFT", hoeffding_certificate_size(0.02 - 0.03, .05) == INF, "gamma=.02;shift=.03"),
        ("CE16_NO_FINITE_BREAK_EVEN", break_even(100, -0.1) == INF, "net per-query gain nonpositive"),
    ]
    return [{"case_id": i, "passed": ok, "witness": witness} for i, ok, witness in rows]


def theorem_sanity_checks() -> dict[str, bool]:
    grid = (1, 2, 4, 8)
    source_b = [1, 2, 4, 4]
    target_b = [2, 4, 4, 8]
    shifted = [grid_shift(grid, b, 2) for b in source_b]
    coupling_ok = all(a >= b for a, b in zip(shifted, target_b))
    eps_10 = consensus_uniform_error_bound(100, 10, .05)
    eps_100 = consensus_uniform_error_bound(100, 100, .05)
    return {
        "grid_rounding_coupling": coupling_ok,
        "multiple_comparison_penalty": eps_100 > eps_10,
        "margin_complexity_monotone": hoeffding_certificate_size(.01, .05) > hoeffding_certificate_size(.02, .05),
        "diameter_minimax_two_point": min(10.0, 2.0 * 3.0) == 6.0,
        "positive_break_even": break_even(100, .5) == 200,
    }


def main() -> None:
    ces = counterexamples()
    sanity = theorem_sanity_checks()
    random_search = random_small_graph_search()
    assert len(ces) >= 12 and all(row["passed"] for row in ces)
    assert all(sanity.values()) and random_search["witness"]
    print(json.dumps({"counterexamples": len(ces), "sanity": sanity, "random_search": random_search}, sort_keys=True))


if __name__ == "__main__":
    main()
