#!/usr/bin/env python3
"""Analyze frozen S9-3 source selection, target certification, and evaluation."""

import argparse
import csv
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


GRID = [16, 32, 64, 128, 256, 512]


def cp_upper(failures, trials, alpha):
    if failures == trials:
        return 1.0
    return float(beta.ppf(1.0 - alpha, failures + 1, trials - failures))


def load_responses(root):
    frames = []
    for path in sorted(root.glob("responses/*/*.csv.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            frames.append(pd.read_csv(handle))
    result = pd.concat(frames, ignore_index=True)
    expected = 2 * 8 * 3 * 6 * 500
    if len(result) != expected or result.duplicated(["dataset", "build_id", "query_role", "query_position", "ef_search"]).any():
        raise RuntimeError("response cube incomplete or duplicated")
    return result


def select_source(group, grid, risk_limit):
    alpha = 0.05 / len(grid)
    for action in grid:
        rows = group[group.ef_search.eq(action)]
        if cp_upper(int(rows.failure.sum()), len(rows), alpha) <= risk_limit:
            return action
    return grid[-1]


def next_rung(action, grid):
    return grid[min(grid.index(action) + 1, len(grid) - 1)]


def make_decisions(response, grid, risk_limit):
    records = []
    for dataset, dataset_rows in response.groupby("dataset"):
        builds = sorted(dataset_rows.build_id.unique())
        source_actions = {}
        for source in builds:
            design = dataset_rows[(dataset_rows.build_id.eq(source)) & (dataset_rows.query_role.eq("source_design"))]
            selected = select_source(design, grid, risk_limit)
            source_actions[source] = (selected, next_rung(selected, grid))
        for source in builds:
            selected, candidate = source_actions[source]
            for target in builds:
                if source == target:
                    continue
                cert = dataset_rows[(dataset_rows.build_id.eq(target)) & (dataset_rows.query_role.eq("target_certification"))]
                candidate_rows = cert[cert.ef_search.eq(candidate)]
                endpoint_rows = cert[cert.ef_search.eq(grid[-1])]
                candidate_ucb = cp_upper(int(candidate_rows.failure.sum()), len(candidate_rows), 0.025)
                endpoint_ucb = cp_upper(int(endpoint_rows.failure.sum()), len(endpoint_rows), 0.025)
                if endpoint_ucb > risk_limit:
                    action, status = None, "ABSTAIN_ENDPOINT_UNQUALIFIED"
                elif candidate_ucb <= risk_limit:
                    action, status = candidate, "CANDIDATE_ACCEPTED"
                else:
                    action, status = grid[-1], "FIXED_SAFE_FALLBACK"
                records.append({
                    "dataset": dataset,
                    "source_build": source,
                    "target_build": target,
                    "source_action": selected,
                    "candidate_action": candidate,
                    "candidate_cert_failures": int(candidate_rows.failure.sum()),
                    "candidate_cert_ucb": candidate_ucb,
                    "endpoint_cert_failures": int(endpoint_rows.failure.sum()),
                    "endpoint_cert_ucb": endpoint_ucb,
                    "deployed_action": action,
                    "decision": status,
                    "grid": "|".join(map(str, grid)),
                    "risk_limit": risk_limit,
                })
    return pd.DataFrame(records)


def attach_evaluation(decisions, response):
    rows = []
    for decision in decisions.itertuples(index=False):
        if pd.isna(decision.deployed_action):
            continue
        target = response[(response.dataset.eq(decision.dataset)) & (response.build_id.eq(decision.target_build)) & (response.query_role.eq("target_evaluation"))]
        action = target[target.ef_search.eq(int(decision.deployed_action))].sort_values("query_position")
        endpoint = target[target.ef_search.eq(512)].sort_values("query_position")
        if not np.array_equal(action.query_position.to_numpy(), endpoint.query_position.to_numpy()):
            raise RuntimeError("evaluation query alignment failed")
        for left, right in zip(action.itertuples(index=False), endpoint.itertuples(index=False)):
            rows.append({
                "dataset": decision.dataset,
                "source_build": decision.source_build,
                "target_build": decision.target_build,
                "query_position": int(left.query_position),
                "deployed_action": int(decision.deployed_action),
                "failure": int(left.failure),
                "recall_at_10": float(left.recall_at_10),
                "ndc": int(left.ndc),
                "endpoint_failure": int(right.failure),
                "endpoint_ndc": int(right.ndc),
            })
    return pd.DataFrame(rows)


def aggregate(values):
    endpoint = values.endpoint_ndc.to_numpy(float)
    deployed = values.ndc.to_numpy(float)
    return {
        "risk": float(values.failure.mean()),
        "endpoint_risk": float(values.endpoint_failure.mean()),
        "ndc_gain": float(1.0 - deployed.sum() / endpoint.sum()),
        "p95_ratio": float(np.quantile(deployed, 0.95) / np.quantile(endpoint, 0.95)),
        "p99_ratio": float(np.quantile(deployed, 0.99) / np.quantile(endpoint, 0.99)),
    }


def crossed_bootstrap(values, repeats=5000, seed=991):
    rng = np.random.default_rng(seed)
    targets = sorted(values.target_build.unique())
    query_ids = np.sort(values.query_position.unique())
    source_count = len(targets) - 1
    shape = (len(targets), len(query_ids), source_count)
    failure = np.empty(shape, dtype=np.uint8)
    endpoint_failure = np.empty(shape, dtype=np.uint8)
    ndc = np.empty(shape, dtype=np.float64)
    endpoint_ndc = np.empty(shape, dtype=np.float64)
    for target_position, target in enumerate(targets):
        block = values[values.target_build.eq(target)].sort_values(["query_position", "source_build"])
        if len(block) != len(query_ids) * source_count:
            raise RuntimeError("crossed bootstrap target block incomplete")
        failure[target_position] = block.failure.to_numpy().reshape(len(query_ids), source_count)
        endpoint_failure[target_position] = block.endpoint_failure.to_numpy().reshape(len(query_ids), source_count)
        ndc[target_position] = block.ndc.to_numpy().reshape(len(query_ids), source_count)
        endpoint_ndc[target_position] = block.endpoint_ndc.to_numpy().reshape(len(query_ids), source_count)
    draws = {key: np.empty(repeats, dtype=np.float64) for key in ("risk", "endpoint_risk", "ndc_gain", "p95_ratio", "p99_ratio")}
    for _ in range(repeats):
        sampled_targets = rng.integers(0, len(targets), len(targets))
        sampled_queries = rng.integers(0, len(query_ids), len(query_ids))
        selector = np.ix_(sampled_targets, sampled_queries, np.arange(source_count))
        sampled_ndc = ndc[selector]
        sampled_endpoint = endpoint_ndc[selector]
        position = _
        draws["risk"][position] = failure[selector].mean()
        draws["endpoint_risk"][position] = endpoint_failure[selector].mean()
        draws["ndc_gain"][position] = 1.0 - sampled_ndc.sum() / sampled_endpoint.sum()
        draws["p95_ratio"][position] = np.quantile(sampled_ndc, 0.95) / np.quantile(sampled_endpoint, 0.95)
        draws["p99_ratio"][position] = np.quantile(sampled_ndc, 0.99) / np.quantile(sampled_endpoint, 0.99)
    intervals = {}
    for key, vector in draws.items():
        intervals[key] = [float(np.quantile(vector, 0.025)), float(np.quantile(vector, 0.975))]
    return intervals


def summarize(decisions, evaluation):
    output = {}
    for dataset, values in evaluation.groupby("dataset"):
        point = aggregate(values)
        ci = crossed_bootstrap(values)
        decision_rows = decisions[decisions.dataset.eq(dataset)]
        loto = []
        for target in sorted(values.target_build.unique()):
            reduced = values[~values.target_build.eq(target)]
            loto.append({"deleted_target": target, **aggregate(reduced)})
        output[dataset] = {
            "directed_decisions": len(decision_rows),
            "decision_counts": {str(k): int(v) for k, v in decision_rows.decision.value_counts().items()},
            "deployed_actions": {str(int(k)): int(v) for k, v in decision_rows.deployed_action.dropna().value_counts().sort_index().items()},
            "point": point,
            "crossed_target_query_95ci": ci,
            "loto_min_ndc_gain": min(row["ndc_gain"] for row in loto),
            "loto_max_p95_ratio": max(row["p95_ratio"] for row in loto),
            "loto": loto,
        }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    response = load_responses(args.input)
    primary = make_decisions(response, GRID, 0.05)
    evaluation = attach_evaluation(primary, response)
    primary.to_csv(args.output / "primary_decisions.csv", index=False)
    evaluation.to_csv(args.output / "primary_evaluation_cells.csv.gz", index=False, compression="gzip")
    summary = summarize(primary, evaluation)
    (args.output / "primary_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    sensitivity_rows = []
    for grid in ([16, 64, 256, 512], [32, 64, 128, 256, 512]):
        for risk_limit in (0.025, 0.05):
            decisions = make_decisions(response, list(grid), risk_limit)
            evaluation_cells = attach_evaluation(decisions, response)
            for dataset, block in evaluation_cells.groupby("dataset"):
                sensitivity_rows.append({
                    "dataset": dataset,
                    "grid": "|".join(map(str, grid)),
                    "risk_limit": risk_limit,
                    "accepted": int((decisions[decisions.dataset.eq(dataset)].decision == "CANDIDATE_ACCEPTED").sum()),
                    "fallback": int((decisions[decisions.dataset.eq(dataset)].decision == "FIXED_SAFE_FALLBACK").sum()),
                    "abstain": int((decisions[decisions.dataset.eq(dataset)].decision == "ABSTAIN_ENDPOINT_UNQUALIFIED").sum()),
                    **aggregate(block),
                })
    pd.DataFrame(sensitivity_rows).to_csv(args.output / "preregistered_sensitivities.csv", index=False)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
