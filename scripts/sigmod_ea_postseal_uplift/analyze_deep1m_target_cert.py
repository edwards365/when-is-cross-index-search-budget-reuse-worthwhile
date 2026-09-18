#!/usr/bin/env python3
"""Analyze the preregistered Deep1M source-slack target-certified replication."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta


GRID = np.asarray([200, 300, 400, 600, 800, 1200])


def cp_upper(k, n, alpha):
    return 1.0 if k == n else float(beta.ppf(1.0 - alpha, k + 1, n - k))


def load_cube(replay):
    paths = sorted(replay.glob("*.csv"))
    builds = [path.stem for path in paths]
    cube_shape = (len(builds), 1500, len(GRID))
    recall = np.full(cube_shape, np.nan)
    ndc = np.full(cube_shape, np.nan)
    amap = {int(action): i for i, action in enumerate(GRID)}
    for build_idx, path in enumerate(paths):
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                idx = (build_idx, int(row["query_id"]), amap[int(row["ef"])])
                recall[idx], ndc[idx] = float(row["recall"]), float(row["ndc"])
    if len(builds) != 8 or np.isnan(recall).any() or np.isnan(ndc).any():
        raise RuntimeError("incomplete Deep1M target-certification cube")
    return builds, recall, ndc


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def point_metrics(failure, executed, endpoint):
    return float(failure.mean() / 7.0), float(1.0 - executed.sum() / endpoint.sum())


def bootstrap(failure, executed, endpoint, mode, reps=5000, seed=991):
    rng = np.random.default_rng(seed)
    nt, nq = failure.shape
    risks, savings = np.empty(reps), np.empty(reps)
    for rep in range(reps):
        ti = rng.integers(0, nt, nt) if mode != "QUERY_CLUSTER_ONLY" else np.arange(nt)
        qi = rng.integers(0, nq, nq) if mode != "TARGET_BUILD_ONLY" else np.arange(nq)
        block = np.ix_(ti, qi)
        risks[rep], savings[rep] = point_metrics(failure[block], executed[block], endpoint[block])
    return [
        float(np.quantile(risks, 0.025)), float(np.quantile(risks, 0.975)),
        float(np.quantile(savings, 0.025)), float(np.quantile(savings, 0.975)),
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    builds, recall, ndc = load_cube(args.replay)
    design, cert, evaluation = np.arange(500), np.arange(500, 1000), np.arange(1000, 1500)

    source_actions = {}
    source_rows = []
    for source_idx, source in enumerate(builds):
        candidates = []
        for action_idx, action in enumerate(GRID):
            failures = int(np.sum(recall[source_idx, design, action_idx] < 0.95))
            ucb = cp_upper(failures, 500, 0.05)
            candidates.append((action_idx, failures, ucb))
        selected_idx, selected_fail, selected_ucb = next((row for row in candidates if row[2] <= 0.05), candidates[-1])
        source_actions[source] = selected_idx
        source_rows.append({
            "source_build": source,
            "source_action": int(GRID[selected_idx]),
            "design_failures": selected_fail,
            "design_n": 500,
            "design_cp_ucb": selected_ucb,
            "candidate_action": int(GRID[min(selected_idx + 1, len(GRID) - 1)]),
            "candidate_clipped": int(selected_idx == len(GRID) - 1),
        })

    pair_rows = []
    failure = np.zeros((8, 500), dtype=float)
    executed = np.zeros((8, 500), dtype=float)
    endpoint = np.zeros((8, 500), dtype=float)
    executed_samples = [[] for _ in builds]
    endpoint_samples = [[] for _ in builds]
    deployments = {"DEPLOY_CANDIDATE": 0, "FALLBACK_ENDPOINT": 0, "ABSTAIN": 0}
    for source_idx, source in enumerate(builds):
        selected_idx = source_actions[source]
        candidate_idx = min(selected_idx + 1, len(GRID) - 1)
        for target_idx, target in enumerate(builds):
            if source == target:
                continue
            candidate_fail = int(np.sum(recall[target_idx, cert, candidate_idx] < 0.95))
            endpoint_fail = int(np.sum(recall[target_idx, cert, -1] < 0.95))
            candidate_ucb = cp_upper(candidate_fail, 500, 0.025)
            endpoint_ucb = cp_upper(endpoint_fail, 500, 0.025)
            if endpoint_ucb > 0.05:
                decision, execute_idx = "ABSTAIN", len(GRID) - 1
            elif candidate_ucb <= 0.05:
                decision, execute_idx = "DEPLOY_CANDIDATE", candidate_idx
            else:
                decision, execute_idx = "FALLBACK_ENDPOINT", len(GRID) - 1
            deployments[decision] += 1
            failures = (recall[target_idx, evaluation, execute_idx] < 0.95).astype(float)
            costs = ndc[target_idx, evaluation, execute_idx]
            endpoint_costs = ndc[target_idx, evaluation, -1]
            failure[target_idx] += failures
            executed[target_idx] += costs
            endpoint[target_idx] += endpoint_costs
            executed_samples[target_idx].append(costs)
            endpoint_samples[target_idx].append(endpoint_costs)
            pair_rows.append({
                "source_build": source,
                "target_build": target,
                "source_action": int(GRID[selected_idx]),
                "candidate_action": int(GRID[candidate_idx]),
                "executed_action": int(GRID[execute_idx]),
                "candidate_clipped": int(candidate_idx == len(GRID) - 1),
                "candidate_cert_failures": candidate_fail,
                "candidate_cert_ucb": candidate_ucb,
                "endpoint_cert_failures": endpoint_fail,
                "endpoint_cert_ucb": endpoint_ucb,
                "decision": decision,
                "evaluation_failures": int(failures.sum()),
                "evaluation_risk": float(failures.mean()),
                "relative_mean_ndc_saving": float(1.0 - costs.mean() / endpoint_costs.mean()),
                "p95_ratio": float(np.quantile(costs, 0.95) / np.quantile(endpoint_costs, 0.95)),
                "p99_ratio": float(np.quantile(costs, 0.99) / np.quantile(endpoint_costs, 0.99)),
            })

    point_risk, point_saving = point_metrics(failure, executed, endpoint)
    intervals = []
    for mode in ("TARGET_BUILD_ONLY", "QUERY_CLUSTER_ONLY", "CROSSED_TARGET_QUERY"):
        lo_r, hi_r, lo_s, hi_s = bootstrap(failure, executed, endpoint, mode)
        intervals.append({
            "resampling": mode,
            "evaluation_risk": point_risk,
            "risk_ci_low": lo_r,
            "risk_ci_high": hi_r,
            "relative_mean_ndc_saving": point_saving,
            "saving_ci_low": lo_s,
            "saving_ci_high": hi_s,
            "repetitions": 5000,
            "seed": 991,
        })
    crossed = next(row for row in intervals if row["resampling"] == "CROSSED_TARGET_QUERY")
    target_savings = []
    target_p95 = []
    target_p99 = []
    for target_idx in range(8):
        target_savings.append(1.0 - executed[target_idx].sum() / endpoint[target_idx].sum())
        target_exec = np.concatenate(executed_samples[target_idx])
        target_end = np.concatenate(endpoint_samples[target_idx])
        target_p95.append(np.quantile(target_exec, .95) / np.quantile(target_end, .95))
        target_p99.append(np.quantile(target_exec, .99) / np.quantile(target_end, .99))
    lobo = []
    for removed in range(8):
        keep = [i for i in range(8) if i != removed]
        lobo.append(1.0 - executed[keep].sum() / endpoint[keep].sum())
    summary = {
        "status": "COMPLETE",
        "builds": 8,
        "directed_pairs": 56,
        "source_actions": {str(int(a)): sum(int(row["source_action"]) == a for row in source_rows) for a in GRID},
        "nonclipped_source_candidates": sum(not int(row["candidate_clipped"]) for row in source_rows),
        "deploy_candidate": deployments["DEPLOY_CANDIDATE"],
        "fallback_endpoint": deployments["FALLBACK_ENDPOINT"],
        "abstain": deployments["ABSTAIN"],
        "max_candidate_cert_ucb": max(row["candidate_cert_ucb"] for row in pair_rows),
        "max_endpoint_cert_ucb": max(row["endpoint_cert_ucb"] for row in pair_rows),
        "evaluation_risk": point_risk,
        "evaluation_risk_crossed_ci": [crossed["risk_ci_low"], crossed["risk_ci_high"]],
        "relative_mean_ndc_saving": point_saving,
        "relative_mean_ndc_saving_crossed_ci": [crossed["saving_ci_low"], crossed["saving_ci_high"]],
        "pooled_p95_ratio": float(np.quantile(np.concatenate([np.concatenate(x) for x in executed_samples]), .95) / np.quantile(np.concatenate([np.concatenate(x) for x in endpoint_samples]), .95)),
        "pooled_p99_ratio": float(np.quantile(np.concatenate([np.concatenate(x) for x in executed_samples]), .99) / np.quantile(np.concatenate([np.concatenate(x) for x in endpoint_samples]), .99)),
        "max_target_p95_ratio": max(target_p95),
        "max_target_p99_ratio": max(target_p99),
        "lobo_min_saving": min(lobo),
        "min_target_saving": min(target_savings),
    }
    summary["gate"] = "PASS" if (
        summary["nonclipped_source_candidates"] > 0
        and summary["abstain"] == 0
        and summary["max_candidate_cert_ucb"] <= .05
        and summary["max_endpoint_cert_ucb"] <= .05
        and crossed["risk_ci_high"] < .05
        and crossed["saving_ci_low"] > 0
        and summary["pooled_p95_ratio"] <= 1
        and summary["max_target_p95_ratio"] <= 1
        and summary["lobo_min_saving"] > 0
        and summary["min_target_saving"] > 0
    ) else "FAIL"
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "source_policy.csv", source_rows)
    write_csv(args.output / "pair_results.csv", pair_rows)
    write_csv(args.output / "interval_sensitivity.csv", intervals)
    serializer = lambda value: value.item() if isinstance(value, np.generic) else str(value)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, default=serializer) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=serializer))
    if summary["gate"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
