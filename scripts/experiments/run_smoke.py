#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.benchmark import run_hnsw_sweep, save_run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    dataset_path = REPO / config["dataset"]
    with np.load(dataset_path) as data:
        base = data["base"]
        query = data["query"]
        ground_truth = data["ground_truth"][:, : config["k"]]
    results, metadata = run_hnsw_sweep(
        base,
        query,
        ground_truth,
        ef_values=config["ef_search"],
        m=config["m"],
        ef_construction=config["ef_construction"],
        seed=config["seed"],
        warmup=config["warmup_queries"],
    )
    metadata.update(
        {
            "dataset": config["dataset"],
            "config": str(args.config),
            "hardware_id": config["hardware_id"],
        }
    )
    run_dir = save_run(results, metadata, REPO / "results" / "raw", REPO)
    summary = (
        results.groupby("ef_search")
        .agg(
            recall_at_10=("recall_at_10", "mean"),
            latency_p50_ns=("latency_ns", "median"),
            latency_p95_ns=("latency_ns", lambda x: x.quantile(0.95)),
            latency_p99_ns=("latency_ns", lambda x: x.quantile(0.99)),
        )
        .reset_index()
    )
    processed = REPO / "results" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    summary.to_csv(processed / f"{metadata['run_id']}_summary.csv", index=False)
    print(json.dumps({"run_dir": str(run_dir), "metadata": metadata}, indent=2))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
