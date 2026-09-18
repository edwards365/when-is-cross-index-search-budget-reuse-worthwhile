#!/usr/bin/env python3
"""Replay graph-only query-cluster intervals from compact per-query records."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "graph_only_query_clusters.csv"
OUTPUT = ROOT / "graph_only_marginal_intervals.csv"
REGISTRY = ROOT / "w6_audit" / "graph_only_registry.csv"
REPLICATES = 5000
SEED = 991


def interval(values: np.ndarray, indices: np.ndarray) -> tuple[float, float, float]:
    draws = values[indices].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(values.mean()), float(low), float(high)


def main() -> None:
    rows = list(csv.DictReader(INPUT.open(encoding="utf-8")))
    registry = {
        (row["operator"], row["dataset"]): row
        for row in csv.DictReader(REGISTRY.open(encoding="utf-8"))
        if row["operator"] != "Vamana-style"
    }
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault((row["implementation"], row["dataset"]), []).append(row)

    output: list[dict[str, object]] = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda row: int(row["query_id"]))
        if len(group) != 750 or len({int(row["query_id"]) for row in group}) != 750:
            raise AssertionError(f"expected 750 unique query clusters for {key}")
        absolute = np.asarray([float(row["absolute_pair_mean"]) for row in group])
        reference = np.asarray([float(row["reference_pair_mean"]) for row in group])
        increment = np.asarray([float(row["increment_pair_mean"]) for row in group])
        if not np.allclose(absolute - reference, increment, rtol=0, atol=1e-15):
            raise AssertionError(f"risk decomposition mismatch for {key}")
        rng = np.random.default_rng(SEED)
        indices = rng.integers(0, len(group), (REPLICATES, len(group)))
        absolute_stats = interval(absolute, indices)
        reference_stats = interval(reference, indices)
        increment_stats = interval(increment, indices)
        frozen = registry[key]
        expected = (
            float(frozen["incremental_risk"]),
            float(frozen["ci_low"]),
            float(frozen["ci_high"]),
        )
        if not np.allclose(increment_stats, expected, rtol=0, atol=1e-15):
            raise AssertionError(f"increment interval no longer matches frozen registry for {key}")
        output.append({
            "implementation": key[0],
            "dataset": key[1],
            "queries": len(group),
            "directed_pairs_per_query": int(group[0]["directed_pairs"]),
            "bootstrap_replicates": REPLICATES,
            "seed": SEED,
            "absolute_risk": absolute_stats[0],
            "absolute_ci_low": absolute_stats[1],
            "absolute_ci_high": absolute_stats[2],
            "reference_risk": reference_stats[0],
            "reference_ci_low": reference_stats[1],
            "reference_ci_high": reference_stats[2],
            "incremental_risk": increment_stats[0],
            "incremental_ci_low": increment_stats[1],
            "incremental_ci_high": increment_stats[2],
        })

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(f"Wrote {len(output)} graph-only interval rows to {OUTPUT.name}.")


if __name__ == "__main__":
    main()
