#!/usr/bin/env python3
"""Train the preregistered 11-feature DARTH regressor without target leakage."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import lightgbm as lgb
import pandas as pd


FEATURES = [
    "step",
    "dists",
    "inserts",
    "first_nn_dist",
    "nn_dist",
    "furthest_dist",
    "avg_dist",
    "variance",
    "percentile_25",
    "percentile_50",
    "percentile_75",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--expected-queries", type=int, default=2000)
    args = parser.parse_args()

    usecols = ["qid", *FEATURES, "r"]
    frame = pd.read_csv(args.input, usecols=usecols)
    if frame.empty:
        raise ValueError("training observation table is empty")
    if frame[usecols].isna().any().any():
        raise ValueError("training observation table contains missing values")
    qids = sorted(int(value) for value in frame["qid"].unique())
    expected = list(range(args.expected_queries))
    if qids != expected:
        raise ValueError("training qids differ from the frozen contiguous source role")
    if ((frame["r"] < 0.0) | (frame["r"] > 1.0)).any():
        raise ValueError("recall target is outside [0, 1]")

    model = lgb.LGBMRegressor(
        objective="regression",
        random_state=42,
        n_estimators=100,
        verbose=-1,
        n_jobs=1,
    )
    started = time.time()
    model.fit(frame[FEATURES], frame["r"])
    elapsed = time.time() - started

    args.model.parent.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(args.model))
    metadata = {
        "status": "TRAINED_FROM_FROZEN_SOURCE_ROLE",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "model": str(args.model),
        "model_sha256": sha256(args.model),
        "features": FEATURES,
        "feature_count": len(FEATURES),
        "rows": int(len(frame)),
        "queries": len(qids),
        "qid_min": qids[0],
        "qid_max": qids[-1],
        "target_min": float(frame["r"].min()),
        "target_max": float(frame["r"].max()),
        "target_mean": float(frame["r"].mean()),
        "n_estimators": 100,
        "random_state": 42,
        "n_jobs": 1,
        "training_seconds": elapsed,
        "feature_importance_gain": {
            feature: float(gain)
            for feature, gain in zip(
                FEATURES,
                model.booster_.feature_importance(importance_type="gain"),
            )
        },
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
