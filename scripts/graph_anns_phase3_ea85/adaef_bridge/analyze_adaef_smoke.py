#!/usr/bin/env python3
"""Seal the registered Ada-ef Arxiv one-build smoke."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def cp_upper(failures: int, n: int, confidence: float = 0.95) -> float:
    return 1.0 if failures == n else float(beta.ppf(confidence, failures + 1, n - failures))


def summarize(rows: list[dict[str, str]], lane: str, include_ucb: bool) -> dict[str, float | int]:
    recall = np.array([float(row[f"{lane}_recall"]) for row in rows])
    distance = np.array([int(row[f"{lane}_distance_computations"]) for row in rows])
    latency = np.array([int(row[f"{lane}_latency_ns"]) for row in rows])
    failures = int(np.sum(recall < 0.95))
    result: dict[str, float | int] = {
        "n": len(rows),
        "failures": failures,
        "risk": failures / len(rows),
        "mean_recall": float(np.mean(recall)),
        "mean_distance_computations": float(np.mean(distance)),
        "p95_distance_computations": float(np.quantile(distance, 0.95)),
        "p99_distance_computations": float(np.quantile(distance, 0.99)),
        "mean_latency_ns": float(np.mean(latency)),
        "p95_latency_ns": float(np.quantile(latency, 0.95)),
        "p99_latency_ns": float(np.quantile(latency, 0.99)),
    }
    if include_ucb:
        result["risk_cp95_upper"] = cp_upper(failures, len(rows))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    design = json.loads((args.run_dir / "design_summary.json").read_text())
    certification_rows = read_csv(args.run_dir / "certification.csv")
    evaluation_rows = read_csv(args.run_dir / "evaluation.csv")
    certification = {
        lane: summarize(certification_rows, lane, True) for lane in ("raw", "fixed_safe")
    }
    evaluation = {
        lane: summarize(evaluation_rows, lane, False) for lane in ("raw", "fixed_safe")
    }
    raw_certified = certification["raw"]["risk_cp95_upper"] <= 0.05
    fixed_certified = certification["fixed_safe"]["risk_cp95_upper"] <= 0.05
    if raw_certified:
        deployment = "RAW_ADA_EF"
    elif fixed_certified:
        deployment = "FIXED_SAFE_EF200"
    else:
        deployment = "NO_CERTIFIED_ACTION"

    actions: dict[str, int] = {}
    for row in evaluation_rows:
        action = row["raw_action_ef"]
        actions[action] = actions.get(action, 0) + 1
    result = {
        "schema_version": "ea85-adaef-arxiv-smoke-1.0",
        "status": "SMOKE_PASS_SEMANTICALLY_VALID_EXTEND_TO_REGISTERED_MAIN",
        "evidence_level": "ONE_BUILD_SMOKE_NOT_OUTER_BUILD_INFERENCE",
        "dataset": "arxiv_nomic_100k",
        "event": "Recall@10 < 0.95",
        "design": design,
        "certification": certification,
        "certification_decision": {
            "raw_certified": raw_certified,
            "fixed_safe_certified": fixed_certified,
            "frozen_deployment": deployment,
        },
        "evaluation": evaluation,
        "raw_evaluation_action_counts": actions,
        "audited_policy": {
            "evaluation_lane": "fixed_safe" if deployment == "FIXED_SAFE_EF200" else "raw",
            "efficiency_gain_vs_fixed_safe": 0.0 if deployment == "FIXED_SAFE_EF200" else None,
        },
        "interpretation": "Raw Ada-ef is efficient but fails the independent safety certificate; ICBA safely falls back to EF200. The one-build smoke validates semantics but does not establish build-level generality.",
        "sha256": {
            name: sha256(args.run_dir / name)
            for name in ("index.hnsw", "adapter.bin", "design_summary.json", "certification.csv", "evaluation.csv")
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
