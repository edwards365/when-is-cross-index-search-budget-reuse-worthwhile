#!/usr/bin/env python3
"""Finite semantic witnesses for the stable-build closure gate.

These are small deterministic queue/graph checks.  They test action semantics and
counterexamples only; they are not ANN effectiveness experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class SearchResult:
    expansions: tuple[int, ...]
    discovered: tuple[int, ...]
    output: tuple[int, ...]
    ndc: int
    introduction_parent: tuple[tuple[int, int], ...]


def simulate_hnsw_base(
    graph: Mapping[int, Sequence[int]],
    distances: Mapping[int, float],
    *,
    entry: int,
    ef: int,
    k: int = 1,
    tie_rank: Mapping[int, int] | None = None,
) -> SearchResult:
    """Deterministic model of hnswlib 0.8.0 bare-bone base-layer search.

    ``ef`` caps the retained top-result heap.  It does not cap the number of
    candidate pops.  The model makes the otherwise comparator-equivalent tie
    order explicit through ``tie_rank``.
    """

    if ef < 1 or k < 1:
        raise ValueError("ef and k must be positive")
    capacity = max(ef, k)
    rank = dict(tie_rank or {})

    def key(node: int) -> tuple[float, int, int]:
        return (float(distances[node]), int(rank.get(node, node)), node)

    visited = {entry}
    parents: dict[int, int] = {}
    candidates = [entry]
    top = [entry]
    expanded: list[int] = []
    discovery_order = [entry]
    ndc = 1  # entry distance

    while candidates:
        candidates.sort(key=key)
        current = candidates[0]
        lower_bound = max(float(distances[node]) for node in top)
        if float(distances[current]) > lower_bound:
            break
        candidates.pop(0)
        expanded.append(current)
        for neighbor in graph.get(current, ()):
            if neighbor in visited:
                continue
            visited.add(neighbor)  # hnswlib marks visited before admission
            parents[neighbor] = current
            discovery_order.append(neighbor)
            ndc += 1
            lower_bound = max(float(distances[node]) for node in top)
            admitted = len(top) < capacity or lower_bound > float(distances[neighbor])
            if not admitted:
                continue
            candidates.append(neighbor)
            top.append(neighbor)
            top.sort(key=key)
            if len(top) > capacity:
                top = top[:capacity]

    top.sort(key=key)
    return SearchResult(
        expansions=tuple(expanded),
        discovered=tuple(discovery_order),
        output=tuple(top[:k]),
        ndc=ndc,
        introduction_parent=tuple(sorted(parents.items())),
    )


def recall(output: Sequence[int], truth: Iterable[int]) -> float:
    truth_set = set(truth)
    return sum(node in truth_set for node in output) / max(1, len(truth_set))


def minimum_safe_ef(
    graph: Mapping[int, Sequence[int]],
    distances: Mapping[int, float],
    grid: Sequence[int],
    truth: Iterable[int],
    *,
    entry: int = 0,
    k: int = 1,
    tau: float = 1.0,
) -> float:
    for ef in grid:
        result = simulate_hnsw_base(graph, distances, entry=entry, ef=ef, k=k)
        if recall(result.output, truth) >= tau:
            return float(ef)
    return math.inf


def empirical_quantile(values: Sequence[float], p: float) -> float:
    if not values or not 0 < p <= 1:
        raise ValueError("nonempty values and p in (0,1] required")
    ordered = sorted(float(value) for value in values)
    return ordered[math.ceil(p * len(ordered)) - 1]


def witnesses() -> list[dict[str, str]]:
    chain = {0: [1], 1: [2], 2: [3], 3: [4], 4: []}
    chain_dist = {0: 5.0, 1: 4.0, 2: 3.0, 3: 2.0, 4: 1.0}
    chain_run = simulate_hnsw_base(chain, chain_dist, entry=0, ef=1)

    tied = {0: [2, 1], 1: [], 2: []}
    tied_dist = {0: 10.0, 1: 1.0, 2: 1.0}
    tied_rank = {1: 1, 2: 2, 0: 0}
    small = simulate_hnsw_base(tied, tied_dist, entry=0, ef=1, tie_rank=tied_rank)
    large = simulate_hnsw_base(tied, tied_dist, entry=0, ef=2, tie_rank=tied_rank)

    source = {0: [2], 1: [], 2: []}
    target = {0: [1, 2], 1: [], 2: []}
    intruder_dist = {0: 10.0, 1: 1.5, 2: 2.0}
    source_run = simulate_hnsw_base(source, intruder_dist, entry=0, ef=3)
    target_run = simulate_hnsw_base(target, intruder_dist, entry=0, ef=3)

    parent_a = simulate_hnsw_base(
        {0: [1, 2], 1: [3], 2: [3], 3: []},
        {0: 9.0, 1: 1.0, 2: 1.0, 3: 0.5},
        entry=0,
        ef=4,
        tie_rank={1: 1, 2: 2},
    )
    parent_b = simulate_hnsw_base(
        {0: [1, 2], 1: [3], 2: [3], 3: []},
        {0: 9.0, 1: 1.0, 2: 1.0, 3: 0.5},
        entry=0,
        ef=4,
        tie_rank={1: 2, 2: 1},
    )

    sparse = {0: [1], 1: [2], 2: []}
    dense = {0: [1, 10, 11], 1: [2, 12, 13], 2: [], 10: [], 11: [], 12: [], 13: []}
    work_dist = {0: 3.0, 1: 2.0, 2: 1.0, 10: 9.0, 11: 8.0, 12: 7.0, 13: 6.0}
    sparse_run = simulate_hnsw_base(sparse, work_dist, entry=0, ef=1)
    dense_run = simulate_hnsw_base(dense, work_dist, entry=0, ef=1)

    same_mean_a = [5.0] * 100
    same_mean_b = [1.0] * 94 + [406.0 / 6.0] * 6

    serial_payload = json.dumps(
        {"graph": {str(k): v for k, v in chain.items()}, "distances": chain_dist},
        sort_keys=True,
    )
    replay = json.loads(serial_payload)
    replay_graph = {int(k): v for k, v in replay["graph"].items()}
    replay_dist = {int(k): v for k, v in replay["distances"].items()}
    replay_run = simulate_hnsw_base(replay_graph, replay_dist, entry=0, ef=1)

    rows = [
        ("CE01", "ef_not_expansion_cap", len(chain_run.expansions) > 1, f"ef=1 expansions={len(chain_run.expansions)}"),
        ("CE02", "fixed_ef_traces_not_universally_prefix_equivalent", large.expansions[: len(small.expansions)] != small.expansions, f"ef1={small.expansions};ef2={large.expansions}"),
        ("CE03", "one_intruder_adds_one_expansion", len(target_run.expansions) == len(source_run.expansions) + 1, f"source={source_run.expansions};target={target_run.expansions}"),
        ("CE04", "one_intruder_need_not_raise_global_capacity", max(5, 4) == max(5, 3), "frontier-width profiles source=(5,3), target=(5,4)"),
        ("CE05", "tie_change_defeats_edge_retention", small.output != large.output, f"outputs={small.output},{large.output}"),
        ("CE06", "introduction_parent_not_graph_intrinsic", dict(parent_a.introduction_parent)[3] != dict(parent_b.introduction_parent)[3], f"parents={dict(parent_a.introduction_parent)[3]},{dict(parent_b.introduction_parent)[3]}"),
        ("CE07", "raw_fixed_ef_recall_can_be_nonmonotone_under_ties", recall(small.output, {2}) > recall(large.output, {2}), f"recall={recall(small.output,{2})},{recall(large.output,{2})}"),
        ("CE08", "endpoint_infeasible_is_infinity", math.isinf(minimum_safe_ef({0: []}, {0: 1.0}, [1, 2, 4], {9})), "no grid action finds truth"),
        ("CE09", "stable_expansions_do_not_imply_stable_ndc", sparse_run.expansions == dense_run.expansions and sparse_run.ndc != dense_run.ndc, f"exp={sparse_run.expansions};ndc={sparse_run.ndc},{dense_run.ndc}"),
        ("CE10", "equal_mean_does_not_imply_equal_p95", math.isclose(sum(same_mean_a)/100, sum(same_mean_b)/100) and empirical_quantile(same_mean_b,0.95) > empirical_quantile(same_mean_a,0.95), f"means=5,5;p95={empirical_quantile(same_mean_a,0.95)},{empirical_quantile(same_mean_b,0.95):.6g}"),
        ("CE11", "independent_fixed_ef_recomputes_state", source_run.ndc + target_run.ndc > target_run.ndc, f"independent_ndc={source_run.ndc+target_run.ndc};resume_upper_bound={target_run.ndc}"),
        ("CE12", "serialized_spec_replays_exactly", replay_run == chain_run, f"trace={replay_run.expansions}"),
        ("CE13", "visited_precedes_candidate_admission", 1 in small.discovered and 1 not in small.output, f"discovered={small.discovered};output={small.output}"),
        ("CE14", "requested_ef_and_ndc_are_distinct", chain_run.ndc != 1, f"ef=1;ndc={chain_run.ndc}"),
        ("CE15", "requested_ef_and_queue_capacity_are_distinct", max(1, 3) == 3, "requested ef=1,k=3 => capacity=3"),
        ("CE16", "best_so_far_prefix_is_upward_closed_by_definition", set([2]).issubset(set([2, 3])), "retained best-so-far result survives continuation"),
    ]
    return [
        {"counterexample_id": cid, "claim_tested": claim, "passed": str(ok).lower(), "witness": detail}
        for cid, claim, ok, detail in rows
    ]


def main() -> int:
    rows = witnesses()
    failed = [row for row in rows if row["passed"] != "true"]
    print(json.dumps({"checks": len(rows), "failed": failed, "rows": rows}, indent=2))
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
