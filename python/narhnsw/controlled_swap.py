"""Trace-gated, degree-preserving controlled swaps on an exported HNSW layer 0."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from narhnsw.resistance import (
    edge_leverage_scores,
    effective_resistance_matrix,
    gaussian_weight_graph,
)


def load_ordered_graph(path: str | Path, n_points: int) -> list[list[int]]:
    neighbors = [[] for _ in range(n_points)]
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            neighbors[int(row["source"])].append(int(row["target"]))
    return neighbors


def graph_to_adjacency(neighbors: list[list[int]]) -> np.ndarray:
    adjacency = np.zeros((len(neighbors), len(neighbors)), dtype=bool)
    for source, targets in enumerate(neighbors):
        adjacency[source, targets] = True
    return adjacency


def select_controlled_swaps(
    points: np.ndarray,
    neighbors: list[list[int]],
    scores: pd.DataFrame,
    failure_support: pd.DataFrame,
    *,
    random_seed: int,
) -> pd.DataFrame:
    """Select equal-budget trace, resistance, geometry, and random additions."""

    points = np.asarray(points, dtype=np.float64)
    adjacency = graph_to_adjacency(neighbors)
    trace_rows = failure_support[failure_support["orientation_progressive"]].copy()
    trace_rows = trace_rows.sort_values("scheme_b_gain", ascending=False)
    if trace_rows["edge_source"].duplicated().any():
        raise ValueError("controlled fixture requires one trace edge per source")
    sources = [int(value) for value in trace_rows["edge_source"]]
    trace_target = dict(
        zip(
            trace_rows["edge_source"].astype(int),
            trace_rows["edge_target"].astype(int),
            strict=True,
        )
    )

    rejected = scores[scores["decision"] != "accepted"]
    pools: defaultdict[int, dict[int, float]] = defaultdict(dict)
    for row in rejected.itertuples():
        left, right, gain = int(row.insertion_id), int(row.candidate_id), float(row.scheme_b_gain)
        pools[left][right] = max(gain, pools[left].get(right, -np.inf))
        pools[right][left] = max(gain, pools[right].get(left, -np.inf))

    union = adjacency | adjacency.T
    edge_distances = np.linalg.norm(points[:, None] - points[None, :], axis=-1)
    rho = float(np.median(edge_distances[np.triu(union, k=1)]))
    weights = gaussian_weight_graph(points, union, rho=rho)
    resistance = effective_resistance_matrix(weights)
    leverage = edge_leverage_scores(weights, resistance)
    removals: dict[int, tuple[int, float]] = {}
    for source in sources:
        choices: list[tuple[float, float, int]] = []
        for target in neighbors[source]:
            sensitivity = 0.0 if adjacency[target, source] else float(leverage[source, target])
            choices.append((sensitivity, -float(edge_distances[source, target]), target))
        sensitivity, _, target = min(choices)
        removals[source] = (target, sensitivity)

    rng = np.random.default_rng(random_seed)
    rows: list[dict[str, object]] = []
    for source in sources:
        available = sorted(
            target
            for target in pools[source]
            if target != source and not adjacency[source, target]
        )
        if not available or trace_target[source] not in available:
            raise ValueError(f"invalid rejected-candidate pool for source {source}")
        target_by_variant = {
            "trace_resistance": trace_target[source],
            "resistance_only": max(available, key=lambda target: (pools[source][target], -target)),
            "geometry": min(
                available,
                key=lambda target: (edge_distances[source, target], target),
            ),
            "random": int(rng.choice(available)),
        }
        removed, deletion_sensitivity = removals[source]
        for variant, target in target_by_variant.items():
            rows.append(
                {
                    "variant": variant,
                    "source": source,
                    "removed": removed,
                    "added": target,
                    "candidate_scheme_b_gain": pools[source][target],
                    "deletion_sensitivity": deletion_sensitivity,
                    "removed_was_reciprocal": bool(adjacency[removed, source]),
                    "rho": rho,
                }
            )
    return pd.DataFrame(rows)


def apply_ordered_swaps(
    neighbors: list[list[int]], swaps: pd.DataFrame
) -> list[list[int]]:
    repaired = [list(targets) for targets in neighbors]
    original_degrees = [len(targets) for targets in repaired]
    for row in swaps.itertuples():
        source, removed, added = int(row.source), int(row.removed), int(row.added)
        if removed not in repaired[source] or added in repaired[source] or source == added:
            raise ValueError("invalid directed swap")
        offset = repaired[source].index(removed)
        repaired[source][offset] = added
    if [len(targets) for targets in repaired] != original_degrees:
        raise AssertionError("controlled swaps changed a source degree")
    return repaired
