#!/usr/bin/env python3
"""Build the sealed-development SIFT Gate-A preliminary matched-recall report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from narhnsw.gate_a_analysis import (
    collapse_latency_rounds,
    curve_summary,
    matched_recall_cost,
)

METHODS = ("original", "geometry", "ggr_0")
CONTROLS = ("geometry_safe_random", "shuffled_resistance")
BUILD_SEEDS = (7, 17, 29)
CONTROL_SEEDS = (101, 211, 307)
EF_VALUES = {10, 20, 40, 60, 80, 100, 120, 160, 200}


def run_name(method: str, build_seed: int, control_seed: int | None = None) -> str:
    suffix = f"-c{control_seed}" if control_seed is not None else ""
    return f"sift_100k-{method}-b{build_seed}{suffix}"


def load_run(raw: Path, name: str, *, add_midpoints: bool) -> pd.DataFrame:
    metadata = json.loads((raw / name / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("status") != "complete":
        raise ValueError(f"{name}: run is not complete")
    if metadata.get("formal_test_members_accessed") is not False:
        raise ValueError(f"{name}: formal test access audit failed")
    parts = [pd.read_csv(raw / name / "queries.csv")]
    if add_midpoints:
        midpoint_metadata = json.loads(
            (raw / f"{name}-midpoints" / "metadata.json").read_text(encoding="utf-8")
        )
        if midpoint_metadata.get("status") != "complete":
            raise ValueError(f"{name}-midpoints: run is not complete")
        if midpoint_metadata.get("formal_test_members_accessed") is not False:
            raise ValueError(f"{name}-midpoints: formal test access audit failed")
        parts.append(pd.read_csv(raw / f"{name}-midpoints" / "queries.csv"))
    frame = collapse_latency_rounds(pd.concat(parts, ignore_index=True))
    observed = set(frame["ef_search"].unique())
    if observed != EF_VALUES:
        raise ValueError(f"{name}: unexpected ef values {sorted(observed)}")
    counts = frame.groupby("ef_search")["query_id"].nunique()
    if not (counts == 1000).all():
        raise ValueError(f"{name}: incomplete query IDs")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("results/gate_a/raw"))
    parser.add_argument("--output", type=Path, default=Path("results/gate_a/derived"))
    args = parser.parse_args()

    frames: list[pd.DataFrame] = []
    expected_names: list[str] = []
    for build_seed in BUILD_SEEDS:
        for method in METHODS:
            name = run_name(method, build_seed)
            expected_names.append(name)
            frames.append(load_run(args.raw, name, add_midpoints=build_seed == 7))
        for method in CONTROLS:
            for control_seed in CONTROL_SEEDS:
                name = run_name(method, build_seed, control_seed)
                expected_names.append(name)
                frames.append(
                    load_run(
                        args.raw,
                        name,
                        add_midpoints=build_seed == 7 and control_seed == 101,
                    )
                )

    frame = pd.concat(frames, ignore_index=True)
    curve = curve_summary(frame)
    rows: list[dict[str, object]] = []
    specifications = ((0.95, 0.50), (0.95, 0.95), (0.95, 0.99), (0.99, 0.95))
    keys = ["method", "build_seed", "control_seed"]
    for key, group in curve.groupby(keys, dropna=False):
        method, build_seed, control_seed = key
        for target_recall, quantile in specifications:
            result = matched_recall_cost(group, target_recall=target_recall, quantile=quantile)
            rows.append(
                {
                    "dataset": "sift_100k",
                    "method": method,
                    "build_seed": int(build_seed),
                    "control_seed": None if pd.isna(control_seed) else int(control_seed),
                    "target_recall": target_recall,
                    "ndc_quantile": quantile,
                    "ef_search": result.ef_search,
                    "observed_recall": result.observed_recall,
                    "ndc_cost": result.ndc_cost,
                }
            )
    matched = pd.DataFrame(rows)

    primary = matched[(matched.target_recall == 0.95) & (matched.ndc_quantile == 0.95)]
    geometry = primary[primary.method == "geometry"].set_index("build_seed")
    ggr = primary[primary.method == "ggr_0"].set_index("build_seed")
    improvements = 100 * (geometry.ndc_cost - ggr.ndc_cost) / geometry.ndc_cost
    comparisons: dict[str, dict[str, float]] = {}
    for build_seed in BUILD_SEEDS:
        build = primary[primary.build_seed == build_seed]
        ggr_cost = float(build[build.method == "ggr_0"].ndc_cost.iloc[0])
        baselines = {
            "geometry": float(build[build.method == "geometry"].ndc_cost.iloc[0]),
            "original": float(build[build.method == "original"].ndc_cost.iloc[0]),
            "geometry_safe_random_mean": float(
                build[build.method == "geometry_safe_random"].ndc_cost.mean()
            ),
            "shuffled_resistance_mean": float(
                build[build.method == "shuffled_resistance"].ndc_cost.mean()
            ),
        }
        comparisons[str(build_seed)] = {
            name: 100 * (cost - ggr_cost) / cost for name, cost in baselines.items()
        }
    summary = {
        "scope": "sealed-development SIFT only; not a final Gate-A verdict",
        "formal_test_members_accessed": False,
        "expected_main_runs": len(expected_names),
        "complete_main_runs": len(expected_names),
        "ef_values": sorted(EF_VALUES),
        "primary": "p95 NDC at mean recall >= 0.95, observed sufficient ef only",
        "ggr_vs_geometry_improvement_percent_by_build": {
            str(seed): float(improvements.loc[seed]) for seed in BUILD_SEEDS
        },
        "ggr_vs_geometry_improvement_percent_mean": float(improvements.mean()),
        "ggr_vs_geometry_improvement_positive_builds": int((improvements > 0).sum()),
        "ggr_vs_geometry_improvement_ge_1pct_builds": int((improvements >= 1).sum()),
        "ggr_improvement_percent_vs_primary_baselines_by_build": comparisons,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    curve.to_csv(args.output / "sift_100k-gate-a-curve.csv", index=False)
    matched.to_csv(args.output / "sift_100k-gate-a-matched-recall.csv", index=False)
    (args.output / "sift_100k-gate-a-preliminary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
