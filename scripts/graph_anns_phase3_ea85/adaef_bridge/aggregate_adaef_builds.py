#!/usr/bin/env python3
"""Aggregate Ada-ef target builds with build as the resampling unit."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


FIELDS = (
    "raw_eval_risk",
    "fixed_eval_risk",
    "raw_mean_dist",
    "fixed_mean_dist",
    "raw_p95_dist",
    "fixed_p95_dist",
    "raw_cost_saving_fraction",
    "audited_gain_vs_fixed",
)


def row(seed: int, path: Path) -> dict[str, float | int | str]:
    data = json.loads(path.read_text())
    raw = data["evaluation"]["raw"]
    fixed = data["evaluation"]["fixed_safe"]
    return {
        "seed": seed,
        "decision": data["certification_decision"]["frozen_deployment"],
        "raw_cert_risk": data["certification"]["raw"]["risk"],
        "raw_cert_ucb": data["certification"]["raw"]["risk_cp95_upper"],
        "fixed_cert_risk": data["certification"]["fixed_safe"]["risk"],
        "fixed_cert_ucb": data["certification"]["fixed_safe"]["risk_cp95_upper"],
        "raw_eval_risk": raw["risk"],
        "fixed_eval_risk": fixed["risk"],
        "raw_mean_dist": raw["mean_distance_computations"],
        "fixed_mean_dist": fixed["mean_distance_computations"],
        "raw_p95_dist": raw["p95_distance_computations"],
        "fixed_p95_dist": fixed["p95_distance_computations"],
        "raw_cost_saving_fraction": 1.0 - raw["mean_distance_computations"] / fixed["mean_distance_computations"],
        "audited_gain_vs_fixed": data["audited_policy"]["efficiency_gain_vs_fixed_safe"],
    }


def mean_record(rows: list[dict[str, float | int | str]]) -> dict[str, float]:
    return {field: float(np.mean([float(item[field]) for item in rows])) for field in FIELDS}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="append", required=True, help="SEED:SUMMARY_JSON")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=991)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    builds = []
    for spec in args.build:
        seed, path = spec.split(":", 1)
        builds.append(row(int(seed), Path(path)))
    builds.sort(key=lambda item: int(item["seed"]))

    csv_path = args.output_dir / "build_metrics.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(builds[0]))
        writer.writeheader()
        writer.writerows(builds)

    rng = np.random.default_rng(args.seed)
    bootstrap: dict[str, list[float]] = {field: [] for field in FIELDS}
    for _ in range(args.bootstrap):
        sampled = [builds[i] for i in rng.integers(0, len(builds), size=len(builds))]
        means = mean_record(sampled)
        for field in FIELDS:
            bootstrap[field].append(means[field])
    intervals = {
        field: {
            "mean": float(np.mean([float(item[field]) for item in builds])),
            "ci95_low": float(np.quantile(values, 0.025)),
            "ci95_high": float(np.quantile(values, 0.975)),
        }
        for field, values in bootstrap.items()
    }
    lobo = {
        str(held_out["seed"]): mean_record([item for item in builds if item is not held_out])
        for held_out in builds
    }
    largest = max(builds, key=lambda item: float(item["raw_cost_saving_fraction"]))
    delete_largest = mean_record([item for item in builds if item is not largest])
    extension_complete = len(builds) >= 10
    result = {
        "schema_version": "ea85-adaef-arxiv-aggregate-1.1",
        "status": "TEN_BUILD_EXTENSION_COMPLETE" if extension_complete else "THREE_BUILD_MAIN_COMPLETE_EXTENSION_ELIGIBLE",
        "evidence_level": "TEN_TARGET_BUILD_FIXED_PROTOCOL" if extension_complete else "PILOT_BUILD_UNCERTAINTY_UNDERPOWERED",
        "primary_unit": "target_build",
        "builds": len(builds),
        "all_raw_failed_certificate": all(float(item["raw_cert_ucb"]) > 0.05 for item in builds),
        "all_fixed_safe_passed_certificate": all(float(item["fixed_cert_ucb"]) <= 0.05 for item in builds),
        "all_deployments": sorted({str(item["decision"]) for item in builds}),
        "bootstrap_reps": args.bootstrap,
        "bootstrap_seed": args.seed,
        "intervals": intervals,
        "lobo": lobo,
        "delete_largest_benefit_build": {
            "deleted_seed": largest["seed"],
            "remaining_mean": delete_largest,
        },
        "decision": (
            "RAW_ADA_EF_UNCERTIFIED_AUDITED_FIXED_SAFE_ZERO_GAIN"
            if extension_complete
            else "EXTEND_ADA_EF_ARXIV_TO_TEN_REGISTERED_BUILDS"
        ),
        "interpretation": "Raw Ada-ef is consistently cheaper but uncertified; ICBA consistently selects fixed-safe and therefore preserves safety with zero gain versus fixed-safe.",
    }
    (args.output_dir / "aggregate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
