#!/usr/bin/env python3
"""Analyze independent target certification for the frozen Faiss policy."""

import argparse
import csv
import gzip
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta


GRID = np.asarray([16, 32, 64, 128, 256, 512])


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cp_upper(k, n, alpha):
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
    wall = np.full(shape, np.nan)
    for row in records:
        idx = (bmap[row["build"]], int(row["query_id"]), amap[int(row["ef"])])
        recall[idx], ndc[idx], wall[idx] = float(row["recall"]), float(row["ndc"]), float(row["wall_ns"])
    if len(builds) != 24 or np.isnan(recall).any() or np.isnan(ndc).any() or np.isnan(wall).any():
        raise RuntimeError(f"incomplete raw cube for {dataset}")
    return builds, recall, ndc, wall


def cluster_bootstrap(target_rows, reps=5000, seed=991):
    rng = np.random.default_rng(seed)
    n = len(target_rows)
    risk, saving, wall_saving = np.empty(reps), np.empty(reps), np.empty(reps)
    for rep in range(reps):
        chosen = rng.integers(0, n, n)
        risk[rep] = np.mean([target_rows[i]["risk"] for i in chosen])
        saving[rep] = 1.0 - np.mean([target_rows[i]["mean_ndc"] for i in chosen]) / np.mean(
            [target_rows[i]["mean_endpoint_ndc"] for i in chosen]
        )
        wall_saving[rep] = 1.0 - np.mean([target_rows[i]["mean_wall"] for i in chosen]) / np.mean(
            [target_rows[i]["mean_endpoint_wall"] for i in chosen]
        )
    return {
        "risk_ci_low": float(np.quantile(risk, 0.025)),
        "risk_ci_high": float(np.quantile(risk, 0.975)),
        "ndc_saving_ci_low": float(np.quantile(saving, 0.025)),
        "ndc_saving_ci_high": float(np.quantile(saving, 0.975)),
        "wall_saving_ci_low": float(np.quantile(wall_saving, 0.025)),
        "wall_saving_ci_high": float(np.quantile(wall_saving, 0.975)),
    }


def analyze(dataset, raw, policy_rows):
    builds, recall, ndc, wall = load_cube(raw, dataset)
    pmap = {row["source_build"]: int(row["chosen_action"]) for row in policy_rows if row["dataset"] == dataset}
    if set(builds) != set(pmap):
        raise RuntimeError(f"policy/build mismatch for {dataset}")
    cert, evaluation = np.arange(500), np.arange(500, 1000)
    pair_rows = []
    target_vectors = {target: {"failure": [], "cost": [], "endpoint": [], "wall": [], "endpoint_wall": []} for target in builds}
    deployments = {"DEPLOY_CANDIDATE": 0, "FALLBACK_ENDPOINT": 0, "NO_CERTIFIED_ACTION": 0}
    for source in builds:
        source_idx = builds.index(source)
        selected = pmap[source]
        candidate_idx = min(int(np.where(GRID == selected)[0][0]) + 1, len(GRID) - 1)
        for target in builds:
            if source == target:
                continue
            target_idx = builds.index(target)
            candidate_fail = int(np.sum(recall[target_idx, cert, candidate_idx] < 0.95))
            endpoint_fail = int(np.sum(recall[target_idx, cert, -1] < 0.95))
            candidate_ucb = cp_upper(candidate_fail, 500, 0.025)
            endpoint_ucb = cp_upper(endpoint_fail, 500, 0.025)
            if endpoint_ucb > 0.05:
                deployment, executed_idx = "NO_CERTIFIED_ACTION", len(GRID) - 1
            elif candidate_ucb <= 0.05:
                deployment, executed_idx = "DEPLOY_CANDIDATE", candidate_idx
            else:
                deployment, executed_idx = "FALLBACK_ENDPOINT", len(GRID) - 1
            deployments[deployment] += 1
            failures = recall[target_idx, evaluation, executed_idx] < 0.95
            costs = ndc[target_idx, evaluation, executed_idx]
            endpoint_costs = ndc[target_idx, evaluation, -1]
            walls = wall[target_idx, evaluation, executed_idx]
            endpoint_walls = wall[target_idx, evaluation, -1]
            target_vectors[target]["failure"].append(failures.astype(float))
            target_vectors[target]["cost"].append(costs)
            target_vectors[target]["endpoint"].append(endpoint_costs)
            target_vectors[target]["wall"].append(walls)
            target_vectors[target]["endpoint_wall"].append(endpoint_walls)
            pair_rows.append({
                "dataset": dataset,
                "source_build": source,
                "target_build": target,
                "source_action": selected,
                "candidate_action": int(GRID[candidate_idx]),
                "executed_action": int(GRID[executed_idx]),
                "candidate_cert_failures": candidate_fail,
                "candidate_cert_n": 500,
                "candidate_cert_ucb": candidate_ucb,
                "endpoint_cert_failures": endpoint_fail,
                "endpoint_cert_ucb": endpoint_ucb,
                "deployment": deployment,
                "evaluation_failures": int(np.sum(failures)),
                "evaluation_n": 500,
                "evaluation_risk": float(np.mean(failures)),
                "relative_mean_ndc_saving": float(1.0 - np.mean(costs) / np.mean(endpoint_costs)),
                "ndc_p95_ratio": float(np.quantile(costs, 0.95) / np.quantile(endpoint_costs, 0.95)),
                "relative_mean_wall_saving": float(1.0 - np.mean(walls) / np.mean(endpoint_walls)),
            })
    target_rows = []
    for target, vectors in target_vectors.items():
        failure = np.concatenate(vectors["failure"])
        cost = np.concatenate(vectors["cost"])
        endpoint = np.concatenate(vectors["endpoint"])
        timing = np.concatenate(vectors["wall"])
        endpoint_timing = np.concatenate(vectors["endpoint_wall"])
        target_rows.append({
            "target_build": target,
            "risk": float(np.mean(failure)),
            "mean_ndc": float(np.mean(cost)),
            "mean_endpoint_ndc": float(np.mean(endpoint)),
            "ndc_saving": float(1.0 - np.mean(cost) / np.mean(endpoint)),
            "mean_wall": float(np.mean(timing)),
            "mean_endpoint_wall": float(np.mean(endpoint_timing)),
            "wall_saving": float(1.0 - np.mean(timing) / np.mean(endpoint_timing)),
            "ndc_p95_ratio": float(np.quantile(cost, 0.95) / np.quantile(endpoint, 0.95)),
        })
    ci = cluster_bootstrap(target_rows)
    all_failure = np.concatenate([np.concatenate(v["failure"]) for v in target_vectors.values()])
    all_cost = np.concatenate([np.concatenate(v["cost"]) for v in target_vectors.values()])
    all_endpoint = np.concatenate([np.concatenate(v["endpoint"]) for v in target_vectors.values()])
    all_wall = np.concatenate([np.concatenate(v["wall"]) for v in target_vectors.values()])
    all_endpoint_wall = np.concatenate([np.concatenate(v["endpoint_wall"]) for v in target_vectors.values()])
    delete_candidates = []
    for removed in builds:
        kept = [row for row in target_rows if row["target_build"] != removed]
        delete_candidates.append(
            1.0
            - np.mean([row["mean_ndc"] for row in kept])
            / np.mean([row["mean_endpoint_ndc"] for row in kept])
        )
    summary = {
        "dataset": dataset,
        "pairs": len(pair_rows),
        "target_builds": len(builds),
        "target_certification_n": 500,
        "target_evaluation_n": 500,
        "deploy_candidate_pairs": deployments["DEPLOY_CANDIDATE"],
        "fallback_endpoint_pairs": deployments["FALLBACK_ENDPOINT"],
        "no_certified_action_pairs": deployments["NO_CERTIFIED_ACTION"],
        "max_candidate_cert_ucb": max(float(row["candidate_cert_ucb"]) for row in pair_rows),
        "max_endpoint_cert_ucb": max(float(row["endpoint_cert_ucb"]) for row in pair_rows),
        "evaluation_risk": float(np.mean(all_failure)),
        "evaluation_risk_ci_low": ci["risk_ci_low"],
        "evaluation_risk_ci_high": ci["risk_ci_high"],
        "relative_mean_ndc_saving": float(1.0 - np.mean(all_cost) / np.mean(all_endpoint)),
        "relative_mean_ndc_saving_ci_low": ci["ndc_saving_ci_low"],
        "relative_mean_ndc_saving_ci_high": ci["ndc_saving_ci_high"],
        "query_pooled_ndc_p95_ratio": float(np.quantile(all_cost, 0.95) / np.quantile(all_endpoint, 0.95)),
        "max_target_ndc_p95_ratio": max(row["ndc_p95_ratio"] for row in target_rows),
        "lobo_min_ndc_saving": min(delete_candidates),
        "relative_mean_wall_saving": float(1.0 - np.mean(all_wall) / np.mean(all_endpoint_wall)),
        "relative_mean_wall_saving_ci_low": ci["wall_saving_ci_low"],
        "relative_mean_wall_saving_ci_high": ci["wall_saving_ci_high"],
        "wall_clock_status": "EXPLORATORY_FIXED_MACHINE_INTERLEAVED",
    }
    summary["gate_certification"] = "PASS" if deployments["NO_CERTIFIED_ACTION"] == 0 else "FAIL"
    summary["gate_evaluation_risk"] = "PASS" if summary["evaluation_risk"] <= 0.05 else "FAIL"
    summary["gate_mean_ndc"] = "PASS" if summary["relative_mean_ndc_saving_ci_low"] > 0 else "FAIL"
    summary["gate_p95"] = "PASS" if summary["query_pooled_ndc_p95_ratio"] <= 1 else "FAIL"
    summary["gate_robustness"] = "PASS" if summary["lobo_min_ndc_saving"] > 0 else "FAIL"
    return pair_rows, target_rows, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.policy.open(encoding="utf-8", newline="") as handle:
        policy = [row for row in csv.DictReader(handle) if row["operator"] == "faiss_hnsw"]
    all_pairs, all_targets, summaries = [], [], []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        pairs, targets, summary = analyze(dataset, args.raw, policy)
        all_pairs.extend(pairs)
        all_targets.extend({"dataset": dataset, **row} for row in targets)
        summaries.append(summary)
    write_csv(args.output / "s3_pair_results.csv", all_pairs)
    write_csv(args.output / "s3_target_build_results.csv", all_targets)
    write_csv(args.output / "s3_summary.csv", summaries)
    gates = [key for key in summaries[0] if key.startswith("gate_")]
    decision = {
        "phase": "S3",
        "status": "COMPLETE",
        "decision": "S3_GATE_PASS" if all(row[key] == "PASS" for row in summaries for key in gates) else "S3_GATE_FAIL",
        "datasets": {row["dataset"]: {key: row[key] for key in gates} for row in summaries},
    }
    (args.output / "s3_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
