#!/usr/bin/env python3
"""Run leakage-separated held-out evaluation of trace-gated controlled swaps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from narhnsw.controlled_swap import (
    apply_ordered_swaps,
    load_ordered_graph,
    select_controlled_swaps,
)
from narhnsw.search import ordered_beam_search


def parse_labels(value: str) -> set[int]:
    return {int(item) for item in value.split(";") if item}


def bootstrap_interval(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    indices = rng.integers(0, len(values), size=(5000, len(values)))
    means = values[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("scores", type=Path)
    parser.add_argument("failure_support", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--random-seed", type=int, default=313)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty result directory: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)

    points = np.loadtxt(args.fixture / "points.csv", delimiter=",", ndmin=2).astype(np.float32)
    neighbors = load_ordered_graph(args.fixture / "edges.csv", len(points))
    scores = pd.read_csv(args.scores)
    failure_support = pd.read_csv(args.failure_support)
    swaps = select_controlled_swaps(
        points, neighbors, scores, failure_support, random_seed=args.random_seed
    )
    swaps.to_csv(args.output / "swaps.csv", index=False)

    query_frame = pd.read_csv(args.fixture / "heldout_query_points.csv").set_index("query_id")
    query_columns = [column for column in query_frame.columns if column.startswith("x")]
    reference = pd.read_csv(args.fixture / "heldout_query_summary.csv")
    variants = {"original": neighbors}
    for variant, group in swaps.groupby("variant"):
        variants[variant] = apply_ordered_swaps(neighbors, group)

    rows: list[dict[str, object]] = []
    original_validations = 0
    for reference_row in reference.itertuples():
        query_id, ef = int(reference_row.query_id), int(reference_row.ef)
        query = query_frame.loc[query_id, query_columns].to_numpy(dtype=np.float32)
        truth = parse_labels(reference_row.ground_truth)
        for variant, graph in variants.items():
            labels, base_ndc, expanded = ordered_beam_search(
                points,
                graph,
                query,
                int(reference_row.base_entrypoint),
                k=10,
                ef=ef,
            )
            total_ndc = 1 + int(reference_row.upper_evaluations) + base_ndc
            observed = set(int(label) for label in labels)
            if variant == "original":
                if observed != parse_labels(reference_row.observed):
                    raise AssertionError("Python original labels disagree with C++ hnswlib")
                if total_ndc != int(reference_row.exact_ndc):
                    raise AssertionError("Python original NDC disagrees with C++ hnswlib")
                original_validations += 1
            rows.append(
                {
                    "variant": variant,
                    "query_id": query_id,
                    "ef": ef,
                    "recall": len(observed & truth) / 10,
                    "exact_ndc": total_ndc,
                    "base_expansions": expanded,
                }
            )
    query_results = pd.DataFrame(rows)
    query_results.to_csv(args.output / "heldout_query_results.csv", index=False)
    summary = (
        query_results.groupby(["variant", "ef"])
        .agg(
            mean_recall=("recall", "mean"),
            mean_exact_ndc=("exact_ndc", "mean"),
            p95_exact_ndc=("exact_ndc", lambda values: values.quantile(0.95)),
            queries_below_full_recall=("recall", lambda values: int((values < 1).sum())),
        )
        .reset_index()
    )
    rng = np.random.default_rng(991)
    comparisons: list[dict[str, object]] = []
    comparison_pairs = [
        (variant, "original") for variant in sorted(set(variants) - {"original"})
    ] + [
        ("trace_resistance", "geometry"),
        ("trace_resistance", "random"),
        ("trace_resistance", "resistance_only"),
    ]
    for ef in sorted(query_results["ef"].unique()):
        for variant, reference_variant in comparison_pairs:
            baseline = query_results[
                (query_results["variant"] == reference_variant)
                & (query_results["ef"] == ef)
            ].sort_values("query_id")
            changed = query_results[
                (query_results["variant"] == variant) & (query_results["ef"] == ef)
            ].sort_values("query_id")
            recall_difference = changed["recall"].to_numpy() - baseline["recall"].to_numpy()
            ndc_difference = changed["exact_ndc"].to_numpy() - baseline["exact_ndc"].to_numpy()
            recall_low, recall_high = bootstrap_interval(recall_difference, rng)
            ndc_low, ndc_high = bootstrap_interval(ndc_difference, rng)
            comparisons.append(
                {
                    "variant": variant,
                    "reference_variant": reference_variant,
                    "ef": ef,
                    "mean_recall_difference": float(recall_difference.mean()),
                    "recall_difference_ci_low": recall_low,
                    "recall_difference_ci_high": recall_high,
                    "mean_ndc_difference": float(ndc_difference.mean()),
                    "ndc_difference_ci_low": ndc_low,
                    "ndc_difference_ci_high": ndc_high,
                    "queries_with_recall_improvement": int((recall_difference > 0).sum()),
                    "queries_with_recall_regression": int((recall_difference < 0).sum()),
                    "queries_with_ndc_reduction": int((ndc_difference < 0).sum()),
                }
            )
    comparison_frame = pd.DataFrame(comparisons)
    summary.to_csv(args.output / "heldout_summary.csv", index=False)
    comparison_frame.to_csv(args.output / "paired_comparisons.csv", index=False)
    metadata = {
        "heldout_queries": int(reference["query_id"].nunique()),
        "searches_per_variant": len(reference),
        "original_cpp_python_exact_validations": original_validations,
        "directed_swaps_per_variant": int(swaps.groupby("variant").size().iloc[0]),
        "directed_swap_fraction": float(
            swaps.groupby("variant").size().iloc[0] / sum(map(len, neighbors))
        ),
        "all_common_deletions_reciprocal": bool(swaps["removed_was_reciprocal"].all()),
        "heldout_distribution": "independent_balanced_two_cloud_gaussian",
        "heldout_query_seed": 101,
        "random_control_seed": args.random_seed,
        "bootstrap_seed": 991,
        "bootstrap_replicates": 5000,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False))
    print(comparison_frame.to_string(index=False))
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
