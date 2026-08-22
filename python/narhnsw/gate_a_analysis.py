"""Frozen Gate-A pairing, matched-recall, bootstrap, and treatment utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

QUERY_KEY = ["dataset", "method", "build_seed", "control_seed", "ef_search", "query_id"]
PAIR_KEY = ["dataset", "build_seed", "ef_search", "query_id"]


@dataclass(frozen=True)
class MatchedRecallCost:
    target_recall: float
    quantile: float
    ef_search: int | None
    observed_recall: float | None
    ndc_cost: float | None


def collapse_latency_rounds(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated latency rounds while asserting algorithmic fields agree."""

    required = set(QUERY_KEY) | {
        "latency_round",
        "recall_at_10",
        "ndc",
        "visited_nodes",
        "candidate_queue_pushes",
        "candidate_queue_pops",
        "latency_ns",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing query columns: {sorted(missing)}")
    if frame.duplicated(QUERY_KEY + ["latency_round"]).any():
        raise ValueError("duplicate query/latency-round key")
    algorithmic = [
        "recall_at_10",
        "ndc",
        "visited_nodes",
        "candidate_queue_pushes",
        "candidate_queue_pops",
    ]
    variation = frame.groupby(QUERY_KEY, dropna=False)[algorithmic].nunique(dropna=False)
    if (variation > 1).any().any():
        raise ValueError("algorithmic query fields differ across latency rounds")
    collapsed = (
        frame.groupby(QUERY_KEY, dropna=False)
        .agg(
            recall_at_10=("recall_at_10", "first"),
            full_recall=("full_recall", "first"),
            ndc=("ndc", "first"),
            visited_nodes=("visited_nodes", "first"),
            candidate_queue_pushes=("candidate_queue_pushes", "first"),
            candidate_queue_pops=("candidate_queue_pops", "first"),
            latency_ns=("latency_ns", "median"),
            latency_rounds=("latency_round", "size"),
        )
        .reset_index()
    )
    return collapsed


def validate_method_pairing(
    frame: pd.DataFrame, expected_methods: set[str], expected_queries: int
) -> None:
    """Require every dataset/build/ef/query cell to contain the expected methods."""

    observed = frame.groupby(PAIR_KEY, dropna=False)["method"].agg(lambda x: set(x))
    if not observed.map(lambda methods: methods == expected_methods).all():
        raise ValueError("method pairing is incomplete or contains unexpected methods")
    counts = frame.groupby(["dataset", "method", "build_seed", "ef_search"], dropna=False)[
        "query_id"
    ].nunique()
    if not (counts == expected_queries).all():
        raise ValueError("query IDs are incomplete within a method build")


def curve_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate an un-interpolated Recall/NDC/latency curve."""

    grouping = ["dataset", "method", "build_seed", "control_seed", "ef_search"]
    return (
        frame.groupby(grouping, dropna=False)
        .agg(
            queries=("query_id", "size"),
            mean_recall=("recall_at_10", "mean"),
            full_recall_fraction=("full_recall", "mean"),
            mean_ndc=("ndc", "mean"),
            p50_ndc=("ndc", lambda values: float(np.quantile(values, 0.50))),
            p95_ndc=("ndc", lambda values: float(np.quantile(values, 0.95))),
            p99_ndc=("ndc", lambda values: float(np.quantile(values, 0.99))),
            mean_latency_ns=("latency_ns", "mean"),
            p50_latency_ns=("latency_ns", lambda values: float(np.quantile(values, 0.50))),
            p95_latency_ns=("latency_ns", lambda values: float(np.quantile(values, 0.95))),
            p99_latency_ns=("latency_ns", lambda values: float(np.quantile(values, 0.99))),
        )
        .reset_index()
    )


def matched_recall_cost(
    curve: pd.DataFrame, *, target_recall: float, quantile: float
) -> MatchedRecallCost:
    """Choose the observed sufficient ef with minimum requested NDC quantile."""

    if not 0 < target_recall <= 1 or not 0 < quantile < 1:
        raise ValueError("recall and quantile targets are outside their domains")
    column = f"p{int(round(100 * quantile)):02d}_ndc"
    if column not in curve:
        raise ValueError(f"curve does not contain {column}")
    sufficient = curve[curve["mean_recall"] >= target_recall].copy()
    if sufficient.empty:
        return MatchedRecallCost(target_recall, quantile, None, None, None)
    chosen = sufficient.sort_values([column, "ef_search"], kind="stable").iloc[0]
    return MatchedRecallCost(
        target_recall=target_recall,
        quantile=quantile,
        ef_search=int(chosen["ef_search"]),
        observed_recall=float(chosen["mean_recall"]),
        ndc_cost=float(chosen[column]),
    )


def paired_query_bootstrap(
    left: np.ndarray,
    right: np.ndarray,
    *,
    statistic: str,
    replicates: int,
    seed: int,
) -> dict[str, float]:
    """Bootstrap a paired left-minus-right mean or recomputed quantile difference."""

    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    if left.shape != right.shape or left.ndim != 1 or len(left) == 0:
        raise ValueError("paired inputs must be nonempty equal-length vectors")
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if statistic == "mean":
        def evaluate(a: np.ndarray, b: np.ndarray) -> float:
            return float(np.mean(a) - np.mean(b))

    elif statistic.startswith("q"):
        quantile = float(statistic[1:])
        if not 0 < quantile < 1:
            raise ValueError("bootstrap quantile is outside (0, 1)")

        def evaluate(a: np.ndarray, b: np.ndarray) -> float:
            return float(np.quantile(a, quantile) - np.quantile(b, quantile))

    else:
        raise ValueError("statistic must be mean or q<probability>")
    rng = np.random.default_rng(seed)
    values = np.empty(replicates, dtype=np.float64)
    for replicate in range(replicates):
        sample = rng.integers(0, len(left), size=len(left))
        values[replicate] = evaluate(left[sample], right[sample])
    return {
        "estimate": evaluate(left, right),
        "lower_95": float(np.quantile(values, 0.025)),
        "upper_95": float(np.quantile(values, 0.975)),
    }


def realized_treatment(
    geometry_edges: set[tuple[int, int]], method_edges: set[tuple[int, int]]
) -> dict[str, float | int]:
    """Compare final directed and undirected support treatment against Geometry."""

    directed_union = geometry_edges | method_edges
    directed_intersection = geometry_edges & method_edges
    geometry_support = {tuple(sorted(edge)) for edge in geometry_edges}
    method_support = {tuple(sorted(edge)) for edge in method_edges}
    changed_sources = {
        source for source, _ in geometry_edges ^ method_edges
    }
    return {
        "added_directed_edges": len(method_edges - geometry_edges),
        "removed_directed_edges": len(geometry_edges - method_edges),
        "changed_sources": len(changed_sources),
        "directed_jaccard": len(directed_intersection) / len(directed_union),
        "support_jaccard": len(geometry_support & method_support)
        / len(geometry_support | method_support),
    }
