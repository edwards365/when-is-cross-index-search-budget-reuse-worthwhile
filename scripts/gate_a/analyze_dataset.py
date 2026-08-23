#!/usr/bin/env python3
"""Analyze one frozen Gate-A dataset and determine preregistered midpoint triggers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from narhnsw.gate_a_analysis import collapse_latency_rounds, curve_summary, matched_recall_cost

BUILD_SEEDS = (7, 17, 29)
CONTROL_SEEDS = (101, 211, 307)
CORE_METHODS = ("original", "geometry", "ggr_0")
CONTROL_METHODS = ("geometry_safe_random", "shuffled_resistance")
BASE_EF = (10, 20, 40, 80, 120, 200)
MIDPOINTS = (15, 30, 60, 100, 160)


def run_id(dataset: str, method: str, build_seed: int, control_seed: int | None) -> str:
    suffix = f"-c{control_seed}" if control_seed is not None else ""
    return f"{dataset}-{method}-b{build_seed}{suffix}"


def expected_runs(dataset: str) -> list[tuple[str, str, int, int | None]]:
    rows = []
    for build_seed in BUILD_SEEDS:
        rows.extend(
            (run_id(dataset, method, build_seed, None), method, build_seed, None)
            for method in CORE_METHODS
        )
        rows.extend(
            (run_id(dataset, method, build_seed, control_seed), method, build_seed, control_seed)
            for method in CONTROL_METHODS
            for control_seed in CONTROL_SEEDS
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--raw", type=Path, default=Path("results/gate_a/raw"))
    parser.add_argument("--output", type=Path, default=Path("results/gate_a/derived"))
    args = parser.parse_args()

    frames = []
    for name, method, build_seed, control_seed in expected_runs(args.dataset):
        directory = args.raw / name
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        if metadata.get("status") != "complete":
            raise ValueError(f"{name}: incomplete")
        if metadata.get("formal_test_members_accessed") is not False:
            raise ValueError(f"{name}: formal test access audit failed")
        frame = collapse_latency_rounds(pd.read_csv(directory / "queries.csv"))
        if len(frame) != len(BASE_EF) * 1000 or frame.query_id.nunique() != 1000:
            raise ValueError(f"{name}: incomplete base-grid queries")
        if set(frame.ef_search.unique()) != set(BASE_EF):
            raise ValueError(f"{name}: base ef grid differs from frozen protocol")
        if (
            set(frame.method) != {method}
            or set(frame.build_seed) != {build_seed}
            or (control_seed is not None and set(frame.control_seed) != {control_seed})
        ):
            raise ValueError(f"{name}: run-key mismatch")
        frames.append(frame)

    queries = pd.concat(frames, ignore_index=True)
    curve = curve_summary(queries)
    triggered: list[int] = []
    trigger_evidence = []
    for low, high, midpoint in zip(BASE_EF[:-1], BASE_EF[1:], MIDPOINTS, strict=True):
        low_curve = curve[curve.ef_search == low].set_index(
            ["method", "build_seed", "control_seed"]
        )
        high_curve = curve[curve.ef_search == high].set_index(
            ["method", "build_seed", "control_seed"]
        )
        thresholds = []
        for threshold in (0.95, 0.99):
            crossed = (low_curve.mean_recall < threshold) & (
                high_curve.mean_recall >= threshold
            )
            if crossed.any():
                thresholds.append(threshold)
        if thresholds:
            triggered.append(midpoint)
        trigger_evidence.append(
            {
                "low_ef": low,
                "high_ef": high,
                "midpoint": midpoint,
                "crossed_thresholds": thresholds,
                "low_recall_min": float(low_curve.mean_recall.min()),
                "low_recall_max": float(low_curve.mean_recall.max()),
                "high_recall_min": float(high_curve.mean_recall.min()),
                "high_recall_max": float(high_curve.mean_recall.max()),
            }
        )

    matched_rows = []
    for key, group in curve.groupby(["method", "build_seed", "control_seed"], dropna=False):
        method, build_seed, control_seed = key
        for target, quantile in ((0.95, 0.50), (0.95, 0.95), (0.95, 0.99), (0.99, 0.95)):
            cost = matched_recall_cost(group, target_recall=target, quantile=quantile)
            matched_rows.append(
                {
                    "dataset": args.dataset,
                    "method": method,
                    "build_seed": int(build_seed),
                    "control_seed": None if pd.isna(control_seed) else int(control_seed),
                    "target_recall": target,
                    "ndc_quantile": quantile,
                    "ef_search": cost.ef_search,
                    "observed_recall": cost.observed_recall,
                    "ndc_cost": cost.ndc_cost,
                }
            )
    matched = pd.DataFrame(matched_rows)
    args.output.mkdir(parents=True, exist_ok=True)
    curve.to_csv(args.output / f"{args.dataset}-gate-a-curve.csv", index=False)
    matched.to_csv(args.output / f"{args.dataset}-gate-a-matched-recall.csv", index=False)
    summary = {
        "dataset": args.dataset,
        "complete_main_runs": 27,
        "formal_test_members_accessed": False,
        "triggered_midpoints": triggered,
        "trigger_evidence": trigger_evidence,
    }
    (args.output / f"{args.dataset}-gate-a-base-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    config_path = Path("configs/gate_a/gate_a_100k.yaml")
    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    midpoint_runs = []
    for name, method, build_seed, control_seed in expected_runs(args.dataset):
        midpoint_runs.append(
            {
                "run_id": f"{name}-midpoints",
                "dataset": args.dataset,
                "method": method,
                "build_seed": build_seed,
                "control_seed": control_seed,
                "config_sha256": config_hash,
                "status": "pending",
            }
        )
    midpoint_matrix = {
        "config_sha256": config_hash,
        "purpose": "uniform triggered midpoint supplement",
        "ef_values": triggered,
        "runs": midpoint_runs,
    }
    (args.output / f"{args.dataset}-midpoint-matrix.json").write_text(
        json.dumps(midpoint_matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
