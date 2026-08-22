#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def bootstrap_mean(
    values: np.ndarray, seed: int = 20260822, rounds: int = 2000
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(rounds, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(samples, [0.025, 0.975]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    runs = sorted((repo / "results" / "raw").glob("*/queries.csv"), key=lambda p: p.stat().st_mtime)
    if not runs:
        raise SystemExit("no raw smoke run found")
    frame = pd.read_csv(runs[-1])
    rows = []
    for ef, group in frame.groupby("ef_search"):
        lo, hi = bootstrap_mean(group.recall_at_10.to_numpy())
        rows.append(
            {
                "ef_search": ef,
                "recall_mean": group.recall_at_10.mean(),
                "recall_ci95_low": lo,
                "recall_ci95_high": hi,
                "latency_p50_us": group.latency_ns.median() / 1e3,
                "latency_p95_us": group.latency_ns.quantile(0.95) / 1e3,
                "latency_p99_us": group.latency_ns.quantile(0.99) / 1e3,
            }
        )
    analysis = pd.DataFrame(rows)
    output = repo / "results" / "processed" / "latest_smoke_analysis.csv"
    analysis.to_csv(output, index=False)
    print(analysis.to_string(index=False))
    if args.write_report:
        metadata = json.loads((runs[-1].parent / "metadata.json").read_text(encoding="utf-8"))
        report = (
            "# Baseline smoke report\n\n"
            "This is a Tier-0 correctness and pipeline result, not evidence for H1 or H2. "
            "Timing is single-threaded but not CPU-affinity controlled.\n\n"
        )
        report += (
            f"Run ID: `{metadata['run_id']}`; dataset: `{metadata['dataset']}`; "
            f"build: {metadata['build_seconds']:.4f} s.\n\n"
        )
        report += "```text\n" + analysis.to_string(index=False) + "\n```\n"
        (repo / "reports" / "baseline_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
