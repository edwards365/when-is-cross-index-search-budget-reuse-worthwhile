"""First-opportunity attribution of rejected HNSW insertion edges to query traces."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ATTRIBUTION_COLUMNS = [
    "insertion_id",
    "candidate_id",
    "scheme_b_gain",
    "scheme_b_rank_within_insertion",
    "trace_opportunity_count",
    "eligible_count",
    "progressive_eligible_count",
    "ground_truth_target_eligible_count",
    "missed_ground_truth_eligible_count",
    "high_ndc_eligible_count",
]


def _parse_labels(value: str) -> set[int]:
    return {int(item) for item in str(value).split(";") if item}


def _orientation_flags(
    *,
    expansion_event: int,
    target_visit_event: int | None,
    target_distance: float,
    source_distance: float,
    lower_bound: float,
    result_size: int,
    search_ef: int,
) -> tuple[bool, bool, bool]:
    """Return opportunity, queue eligibility, and strict query progress."""

    opportunity = target_visit_event is None or target_visit_event > expansion_event
    eligible = opportunity and (result_size < search_ef or target_distance < lower_bound)
    progressive = eligible and target_distance < source_distance
    return opportunity, eligible, progressive


def attribute_rejected_candidates(
    scores_path: str | Path, trace_directory: str | Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Attribute missing edges without claiming a full counterfactual search result."""

    trace_directory = Path(trace_directory)
    scores = pd.read_csv(scores_path)
    rejected = scores[scores["decision"] != "accepted"].copy().reset_index(drop=True)
    points = np.loadtxt(trace_directory / "points.csv", delimiter=",", ndmin=2)
    queries = pd.read_csv(trace_directory / "query_points.csv").set_index("query_id")
    query_columns = [column for column in queries.columns if column.startswith("x")]
    query_summary = pd.read_csv(trace_directory / "query_trace_summary.csv")
    events = pd.read_csv(trace_directory / "query_trace_events.csv")
    events = events[(events["phase"] == "base")]

    by_source: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in rejected.iterrows():
        center, candidate = int(row["insertion_id"]), int(row["candidate_id"])
        by_source[center].append((row_index, candidate))
        by_source[candidate].append((row_index, center))

    counter_names = [
        "trace_opportunity_count",
        "eligible_count",
        "progressive_eligible_count",
        "ground_truth_target_eligible_count",
        "missed_ground_truth_eligible_count",
        "high_ndc_eligible_count",
    ]
    counters = {name: np.zeros(len(rejected), dtype=np.int64) for name in counter_names}
    p95_ndc = query_summary.groupby("ef")["exact_ndc"].quantile(0.95).to_dict()
    covered_failure_queries: set[tuple[int, int]] = set()
    missed_support_orientations: list[tuple[object, ...]] = []

    summaries = query_summary.set_index(["query_id", "ef"])
    for (query_id, ef), trace in events.groupby(["query_id", "ef"], sort=False):
        query_id, ef = int(query_id), int(ef)
        summary = summaries.loc[(query_id, ef)]
        ground_truth = _parse_labels(summary["ground_truth"])
        observed = _parse_labels(summary["observed"])
        missed = ground_truth - observed
        query = queries.loc[query_id, query_columns].to_numpy(dtype=float)
        distances = np.sum(np.square(points - query), axis=1)
        visits: dict[int, int] = {}
        for event in trace.itertuples():
            if event.event == "entry":
                visits.setdefault(int(event.target), int(event.event_index))
            elif event.event in {"enqueued", "pruned"}:
                visits.setdefault(int(event.target), int(event.event_index))

        per_candidate: defaultdict[int, int] = defaultdict(int)
        for expansion in trace[trace["event"] == "expanded"].itertuples():
            source = int(expansion.source)
            for row_index, target in by_source.get(source, []):
                opportunity, eligible, progressive = _orientation_flags(
                    expansion_event=int(expansion.event_index),
                    target_visit_event=visits.get(target),
                    target_distance=float(distances[target]),
                    source_distance=float(expansion.distance_to_query),
                    lower_bound=float(expansion.lower_bound_before),
                    result_size=int(expansion.result_size_before),
                    search_ef=max(ef, 10),
                )
                mask = per_candidate[row_index]
                mask |= int(opportunity) << 0
                mask |= int(eligible) << 1
                mask |= int(progressive) << 2
                mask |= int(eligible and target in ground_truth) << 3
                mask |= int(eligible and target in missed) << 4
                mask |= int(eligible and float(summary["exact_ndc"]) >= p95_ndc[ef]) << 5
                per_candidate[row_index] = mask
                if eligible and target in missed:
                    missed_support_orientations.append(
                        (
                            row_index,
                            query_id,
                            ef,
                            source,
                            target,
                            float(expansion.distance_to_query),
                            float(distances[target]),
                            float(expansion.lower_bound_before),
                            int(expansion.result_size_before),
                            progressive,
                        )
                    )
        for row_index, candidate_mask in per_candidate.items():
            if candidate_mask & (1 << 4):
                covered_failure_queries.add((query_id, ef))
            for flag_index, name in enumerate(counter_names):
                counters[name][row_index] += int(bool(candidate_mask & (1 << flag_index)))

    attributed = rejected[["insertion_id", "candidate_id", "scheme_b_gain"]].copy()
    for name in counter_names:
        attributed[name] = counters[name]

    finite_b = attributed["scheme_b_gain"].replace([np.inf, -np.inf], np.nan)
    correlation = spearmanr(
        finite_b[finite_b.notna()],
        attributed.loc[finite_b.notna(), "progressive_eligible_count"],
    ).statistic
    rank = attributed.groupby("insertion_id")["scheme_b_gain"].rank(
        method="first", ascending=False
    )
    attributed["scheme_b_rank_within_insertion"] = rank.astype(int)
    support = pd.DataFrame(
        missed_support_orientations,
        columns=[
            "candidate_row",
            "query_id",
            "ef",
            "edge_source",
            "edge_target",
            "source_distance_to_query",
            "target_distance_to_query",
            "lower_bound_before",
            "result_size_before",
            "orientation_progressive",
        ],
    ).merge(
        attributed.reset_index(names="candidate_row"), on="candidate_row", how="left"
    )
    support = support.drop(columns=["candidate_row"]).sort_values(
        ["query_id", "ef", "scheme_b_rank_within_insertion", "scheme_b_gain"],
        ascending=[True, True, True, False],
    )
    progressive_failure_support = support[support["orientation_progressive"]]
    best_progressive_ranks = (
        progressive_failure_support.groupby(["query_id", "ef"])[
            "scheme_b_rank_within_insertion"
        ]
        .min()
        .to_dict()
    )
    missed_supported = attributed["missed_ground_truth_eligible_count"] > 0
    summary_result: dict[str, object] = {
        "rejected_candidates": len(attributed),
        "candidates_with_any_trace_opportunity": int(
            (attributed["trace_opportunity_count"] > 0).sum()
        ),
        "candidates_with_any_eligible_opportunity": int(
            (attributed["eligible_count"] > 0).sum()
        ),
        "candidates_with_any_progressive_eligible_opportunity": int(
            (attributed["progressive_eligible_count"] > 0).sum()
        ),
        "candidates_targeting_missed_ground_truth": int(
            missed_supported.sum()
        ),
        "missed_ground_truth_candidates_ranked_top_1": int(
            (missed_supported & (rank <= 1)).sum()
        ),
        "missed_ground_truth_candidates_ranked_top_5": int(
            (missed_supported & (rank <= 5)).sum()
        ),
        "missed_ground_truth_candidates_ranked_top_10": int(
            (missed_supported & (rank <= 10)).sum()
        ),
        "missed_ground_truth_candidate_query_pairs": int(
            attributed["missed_ground_truth_eligible_count"].sum()
        ),
        "failure_queries_with_at_least_one_supported_candidate": len(covered_failure_queries),
        "failure_queries_total": int((query_summary["recall"] < 1.0).sum()),
        "progressive_missed_ground_truth_orientations": int(
            support["orientation_progressive"].sum()
        ),
        "failure_queries_with_progressive_supported_candidate": len(best_progressive_ranks),
        "best_progressive_scheme_b_rank_by_failure_query": {
            f"{int(query_id)}@ef{int(ef)}": int(value)
            for (query_id, ef), value in best_progressive_ranks.items()
        },
        "scheme_b_progressive_count_spearman": (
            float(correlation) if math.isfinite(correlation) else None
        ),
        "top_1_per_insertion_progressive_support_rate": float(
            (attributed.loc[rank <= 1, "progressive_eligible_count"] > 0).mean()
        ),
        "top_5_per_insertion_progressive_support_rate": float(
            (attributed.loc[rank <= 5, "progressive_eligible_count"] > 0).mean()
        ),
        "all_candidate_progressive_support_rate": float(
            (attributed["progressive_eligible_count"] > 0).mean()
        ),
        "query_metrics_by_ef": {
            str(int(ef)): {
                "mean_recall": float(group["recall"].mean()),
                "queries_below_full_recall": int((group["recall"] < 1.0).sum()),
                "mean_exact_ndc": float(group["exact_ndc"].mean()),
                "p95_exact_ndc": float(group["exact_ndc"].quantile(0.95)),
                "mean_base_expansions": float(group["base_expansions"].mean()),
            }
            for ef, group in query_summary.groupby("ef")
        },
    }
    return attributed[ATTRIBUTION_COLUMNS], support, summary_result
