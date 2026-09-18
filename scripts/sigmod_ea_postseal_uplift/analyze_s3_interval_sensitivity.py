#!/usr/bin/env python3
"""Frozen S3 target/query resampling sensitivity.

The deployment decision is reconstructed exactly as in
``analyze_s3_target_cert.py``.  Only the held-out evaluation role is
resampled.  Source directions remain grouped inside each target/query cell.
"""

import argparse
import csv
import gzip
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta


GRID = np.asarray([16, 32, 64, 128, 256, 512])


def cp_upper(k, n, alpha=0.025):
    return 1.0 if k == n else float(beta.ppf(1.0 - alpha, k + 1, n - k))


def load_cube(raw, dataset):
    records = []
    for path in sorted(raw.glob(f"{dataset}*.csv.gz")):
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            records.extend(csv.DictReader(handle))
    builds = sorted({row["build"] for row in records})
    bmap = {build: i for i, build in enumerate(builds)}
    amap = {int(action): i for i, action in enumerate(GRID)}
    shape = (len(builds), 1000, len(GRID))
    recall = np.full(shape, np.nan)
    ndc = np.full(shape, np.nan)
    for row in records:
        idx = (bmap[row["build"]], int(row["query_id"]), amap[int(row["ef"])])
        recall[idx], ndc[idx] = float(row["recall"]), float(row["ndc"])
    if len(builds) != 24 or np.isnan(recall).any() or np.isnan(ndc).any():
        raise RuntimeError(f"incomplete raw cube for {dataset}")
    return builds, recall, ndc


def frozen_vectors(dataset, raw, policy_rows):
    builds, recall, ndc = load_cube(raw, dataset)
    pmap = {
        row["source_build"]: int(row["chosen_action"])
        for row in policy_rows
        if row["dataset"] == dataset
    }
    if set(builds) != set(pmap):
        raise RuntimeError(f"policy/build mismatch for {dataset}")
    cert = np.arange(500)
    evaluation = np.arange(500, 1000)
    # target x evaluation-query, with the 23 source directions retained
    # inside each cell rather than treated as independent clusters.
    failures = np.zeros((24, 500), dtype=np.float64)
    executed = np.zeros((24, 500), dtype=np.float64)
    endpoint = np.zeros((24, 500), dtype=np.float64)
    deployments = {"DEPLOY_CANDIDATE": 0, "FALLBACK_ENDPOINT": 0, "NO_CERTIFIED_ACTION": 0}
    for source_idx, source in enumerate(builds):
        selected_idx = int(np.where(GRID == pmap[source])[0][0])
        candidate_idx = min(selected_idx + 1, len(GRID) - 1)
        for target_idx, target in enumerate(builds):
            if source == target:
                continue
            candidate_fail = int(np.sum(recall[target_idx, cert, candidate_idx] < 0.95))
            endpoint_fail = int(np.sum(recall[target_idx, cert, -1] < 0.95))
            if cp_upper(endpoint_fail, 500) > 0.05:
                deployment, executed_idx = "NO_CERTIFIED_ACTION", len(GRID) - 1
            elif cp_upper(candidate_fail, 500) <= 0.05:
                deployment, executed_idx = "DEPLOY_CANDIDATE", candidate_idx
            else:
                deployment, executed_idx = "FALLBACK_ENDPOINT", len(GRID) - 1
            deployments[deployment] += 1
            failures[target_idx] += (recall[target_idx, evaluation, executed_idx] < 0.95)
            executed[target_idx] += ndc[target_idx, evaluation, executed_idx]
            endpoint[target_idx] += ndc[target_idx, evaluation, -1]
    return builds, failures, executed, endpoint, deployments


def metrics(failures, executed, endpoint):
    directions = 23.0
    return (
        float(failures.sum() / (failures.size * directions)),
        float(1.0 - executed.sum() / endpoint.sum()),
    )


def bootstrap(failures, executed, endpoint, mode, reps, seed):
    rng = np.random.default_rng(seed)
    n_target, n_query = failures.shape
    risk = np.empty(reps)
    saving = np.empty(reps)
    for rep in range(reps):
        target_idx = rng.integers(0, n_target, n_target) if mode != "QUERY_CLUSTER_ONLY" else np.arange(n_target)
        query_idx = rng.integers(0, n_query, n_query) if mode != "TARGET_BUILD_ONLY" else np.arange(n_query)
        block = np.ix_(target_idx, query_idx)
        risk[rep], saving[rep] = metrics(failures[block], executed[block], endpoint[block])
    return {
        "risk_ci_low": float(np.quantile(risk, 0.025)),
        "risk_ci_high": float(np.quantile(risk, 0.975)),
        "saving_ci_low": float(np.quantile(saving, 0.025)),
        "saving_ci_high": float(np.quantile(saving, 0.975)),
    }


def write_rows(path, rows, compressed=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if compressed else open
    kwargs = {"mode": "wt", "encoding": "utf-8", "newline": ""} if compressed else {"mode": "w", "encoding": "utf-8", "newline": ""}
    with opener(path, **kwargs) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=991)
    args = parser.parse_args()
    with args.policy.open(encoding="utf-8", newline="") as handle:
        policy = [row for row in csv.DictReader(handle) if row["operator"] == "faiss_hnsw"]

    summaries, vectors = [], []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds, failure, executed, endpoint, deployments = frozen_vectors(dataset, args.raw, policy)
        point_risk, point_saving = metrics(failure, executed, endpoint)
        for mode in ("TARGET_BUILD_ONLY", "QUERY_CLUSTER_ONLY", "CROSSED_TARGET_QUERY"):
            interval = bootstrap(failure, executed, endpoint, mode, args.reps, args.seed)
            summaries.append({
                "dataset": dataset,
                "resampling": mode,
                "bootstrap_reps": args.reps,
                "seed": args.seed,
                "evaluation_risk": point_risk,
                "evaluation_risk_ci_low": interval["risk_ci_low"],
                "evaluation_risk_ci_high": interval["risk_ci_high"],
                "relative_mean_ndc_saving": point_saving,
                "relative_mean_ndc_saving_ci_low": interval["saving_ci_low"],
                "relative_mean_ndc_saving_ci_high": interval["saving_ci_high"],
                "target_builds": len(builds),
                "shared_evaluation_queries": failure.shape[1],
                "source_directions_per_target": 23,
                **{key.lower(): value for key, value in deployments.items()},
            })
        for target_idx, target in enumerate(builds):
            for query_offset in range(failure.shape[1]):
                vectors.append({
                    "dataset": dataset,
                    "target_build": target,
                    "query_id": query_offset + 500,
                    "failure_sum": int(failure[target_idx, query_offset]),
                    "source_count": 23,
                    "executed_ndc_sum": float(executed[target_idx, query_offset]),
                    "endpoint_ndc_sum": float(endpoint[target_idx, query_offset]),
                })

    write_rows(args.output / "s3_interval_sensitivity.csv", summaries)
    write_rows(args.output / "s3_target_query_vectors.csv.gz", vectors, compressed=True)
    decision = {
        "status": "COMPLETE",
        "estimand": "frozen post-seal target-certified policy",
        "decision_refit": False,
        "query_role": "evaluation query IDs 500--999",
        "resampling": ["target build", "shared query ID", "crossed target build and shared query ID"],
        "reps": args.reps,
        "seed": args.seed,
    }
    (args.output / "s3_interval_sensitivity.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
