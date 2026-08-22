#!/usr/bin/env python3
"""Summarize offline insertion-time candidate scores."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def distribution(values: pd.Series) -> dict[str, float | int]:
    values = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    return {
        "count": int(len(values)),
        "finite_count": int(len(finite)),
        "infinite_count": int(np.isinf(values).sum()),
        "min": float(np.min(finite)) if len(finite) else math.nan,
        "median": float(np.median(finite)) if len(finite) else math.nan,
        "mean": float(np.mean(finite)) if len(finite) else math.nan,
        "p95": float(np.quantile(finite, 0.95)) if len(finite) else math.nan,
        "max": float(np.max(finite)) if len(finite) else math.nan,
    }


def summarize(frame: pd.DataFrame, cluster_split: int | None) -> dict[str, object]:
    accepted = frame[frame["decision"] == "accepted"]
    rejected = frame[frame["decision"] != "accepted"]
    insertion_ranges: list[float] = []
    insertion_correlations: list[float] = []
    matched_overlap = 0
    matched_total = 0
    blocker_comparisons = 0
    b_above_blocker_c = 0

    for _, group in frame.groupby("insertion_id"):
        values = group["scheme_a_tau"].to_numpy(dtype=float)
        insertion_ranges.append(float(np.max(values) - np.min(values)))
        if len(group) > 2:
            correlation = spearmanr(group["scheme_a_tau"], group["distance_to_new"]).statistic
            if np.isfinite(correlation):
                insertion_correlations.append(float(correlation))
        budget = int((group["decision"] == "accepted").sum())
        ranked = group.sort_values(
            ["scheme_a_tau", "candidate_id"], ascending=[False, True]
        ).head(budget)
        matched_overlap += int((ranked["decision"] == "accepted").sum())
        matched_total += budget
        accepted_c = {
            int(row.candidate_id): float(row.scheme_c_tau)
            for row in group.itertuples()
            if row.decision == "accepted"
        }
        for row in group.itertuples():
            if row.decision == "accepted" or pd.isna(row.blocker_id):
                continue
            blocker = int(row.blocker_id)
            if blocker not in accepted_c or not np.isfinite(row.scheme_b_gain):
                continue
            blocker_comparisons += 1
            b_above_blocker_c += int(float(row.scheme_b_gain) > accepted_c[blocker])

    summary: dict[str, object] = {
        "rows": len(frame),
        "decision_counts": frame["decision"].value_counts().to_dict(),
        "scheme_a_all": distribution(frame["scheme_a_tau"]),
        "scheme_a_accepted": distribution(accepted["scheme_a_tau"]),
        "scheme_a_rejected": distribution(rejected["scheme_a_tau"]),
        "scheme_b_rejected": distribution(rejected["scheme_b_gain"]),
        "scheme_b_connected_rate": float(rejected["scheme_b_connected"].mean()),
        "scheme_c_accepted": distribution(accepted["scheme_c_tau"]),
        "scheme_a_violations_above_1_plus_1e_4": int(
            (frame["scheme_a_tau"] > 1.0 + 1e-4).sum()
        ),
        "scheme_c_violations_above_1_plus_1e_4": int(
            (accepted["scheme_c_tau"] > 1.0 + 1e-4).sum()
        ),
        "scheme_a_per_insertion_range_median": float(np.median(insertion_ranges)),
        "scheme_a_per_insertion_range_p05": float(np.quantile(insertion_ranges, 0.05)),
        "scheme_a_distance_spearman_per_insertion_median": float(
            np.median(insertion_correlations)
        ),
        "scheme_a_matched_budget_accept_overlap_rate": matched_overlap / matched_total,
        "scheme_b_above_own_blocker_c_rate": b_above_blocker_c / blocker_comparisons,
        "scheme_b_blocker_comparisons": blocker_comparisons,
    }

    if cluster_split is not None:
        relevant = rejected[rejected["insertion_id"] >= cluster_split].copy()
        relevant["cross_cluster"] = relevant["candidate_id"] < cluster_split
        top_counts: dict[str, float] = {}
        for count in (1, 5, 10):
            top = (
                relevant.sort_values(
                    ["insertion_id", "scheme_b_gain", "candidate_id"],
                    ascending=[True, False, True],
                )
                .groupby("insertion_id")
                .head(count)
            )
            top_counts[f"top_{count}_cross_cluster_rate"] = float(top["cross_cluster"].mean())
        summary["cluster_split"] = cluster_split
        summary["rejected_cross_cluster_rate_after_split"] = float(
            relevant["cross_cluster"].mean()
        )
        summary["scheme_b_cross_cluster_top_rates"] = top_counts
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scores", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cluster-split", type=int)
    args = parser.parse_args()
    frame = pd.read_csv(args.scores)
    summary = summarize(frame, args.cluster_split)
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
