#!/usr/bin/env python3
"""Resolve S9-4 deployable baselines, ablations, and NDC attribution."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


GRID = [16, 32, 64, 128, 256, 512]
DEPLOYABLE = {"B0_ENDPOINT_512", "B1_FIXED_256_CERTIFIED", "B2_SOURCE_ONE_RUNG_CERTIFIED", "B3_TARGET_GLOBAL_EQUAL_500", "B4_TARGET_GLOBAL_1000"}


def cp_upper(failures, trials, alpha):
    if failures == trials:
        return 1.0
    return float(beta.ppf(1.0 - alpha, failures + 1, trials - failures))


def load_responses(root):
    frames = [pd.read_csv(path) for path in sorted(root.glob("responses/*/*.csv.gz"))]
    result = pd.concat(frames, ignore_index=True)
    expected = 2 * 8 * 3 * 6 * 500
    keys = ["dataset", "build_id", "query_role", "query_position", "ef_search"]
    if len(result) != expected or result.duplicated(keys).any():
        raise RuntimeError("S9-4 response cube incomplete or duplicated")
    return result


def choose_action(rows, count):
    subset = rows[rows.query_position.lt(count)]
    for action in GRID:
        action_rows = subset[subset.ef_search.eq(action)]
        if cp_upper(int(action_rows.failure.sum()), len(action_rows), 0.05 / len(GRID)) <= 0.05:
            return action
    return 512


def certify(rows, action, count):
    subset = rows[rows.query_position.lt(count)]
    candidate = subset[subset.ef_search.eq(action)]
    endpoint = subset[subset.ef_search.eq(512)]
    candidate_ucb = cp_upper(int(candidate.failure.sum()), len(candidate), 0.025)
    endpoint_ucb = cp_upper(int(endpoint.failure.sum()), len(endpoint), 0.025)
    if endpoint_ucb > 0.05:
        return None, "ABSTAIN_ENDPOINT_UNQUALIFIED", candidate_ucb, endpoint_ucb
    if candidate_ucb <= 0.05:
        return action, "CANDIDATE_ACCEPTED", candidate_ucb, endpoint_ucb
    return 512, "FIXED_SAFE_FALLBACK", candidate_ucb, endpoint_ucb


def source_policy_map(path):
    prior = pd.read_csv(path)
    result = {}
    for (dataset, source), group in prior.groupby(["dataset", "source_build"]):
        if group.source_action.nunique() != 1 or group.candidate_action.nunique() != 1:
            raise RuntimeError("S9-3 source policy drift")
        result[(dataset, source)] = (int(group.source_action.iloc[0]), int(group.candidate_action.iloc[0]))
    return result


def make_decisions(response, source_map):
    records = []
    for dataset, dataset_rows in response.groupby("dataset"):
        builds = sorted(dataset_rows.build_id.unique())
        target_actions = {}
        for target in builds:
            select_rows = dataset_rows[(dataset_rows.build_id.eq(target)) & (dataset_rows.query_role.eq("baseline_selection"))]
            cert_rows = dataset_rows[(dataset_rows.build_id.eq(target)) & (dataset_rows.query_role.eq("baseline_certification"))]
            target_actions[(target, 250)] = choose_action(select_rows, 250)
            target_actions[(target, 500)] = choose_action(select_rows, 500)
            for source in builds:
                if source == target:
                    continue
                source_action, source_candidate = source_map[(dataset, source)]
                arms = [
                    ("B0_ENDPOINT_512", 512, 500, True),
                    ("B1_FIXED_256_CERTIFIED", 256, 500, True),
                    ("B2_SOURCE_ONE_RUNG_CERTIFIED", source_candidate, 500, True),
                    ("B3_TARGET_GLOBAL_EQUAL_500", target_actions[(target, 250)], 250, True),
                    ("B4_TARGET_GLOBAL_1000", target_actions[(target, 500)], 500, True),
                    ("A1_SOURCE_ACTION_DIRECT", source_action, 0, False),
                    ("A2_SOURCE_ONE_RUNG_UNCERTIFIED", source_candidate, 0, False),
                    ("A3_FIXED_256_UNCERTIFIED", 256, 0, False),
                ]
                evaluation = dataset_rows[(dataset_rows.build_id.eq(target)) & (dataset_rows.query_role.eq("baseline_evaluation"))]
                oracle_action = next((action for action in GRID if evaluation[evaluation.ef_search.eq(action)].failure.mean() <= 0.05), 512)
                arms.append(("O1_EVALUATION_ORACLE", oracle_action, 0, False))
                for arm, proposed, cert_count, deployable in arms:
                    if deployable:
                        executed, status, candidate_ucb, endpoint_ucb = certify(cert_rows, proposed, cert_count)
                    else:
                        executed, status, candidate_ucb, endpoint_ucb = proposed, "DIAGNOSTIC_NO_CERTIFICATE", np.nan, np.nan
                    records.append({
                        "dataset": dataset,
                        "arm": arm,
                        "deployable": deployable,
                        "source_build": source,
                        "target_build": target,
                        "source_action": source_action,
                        "proposed_action": proposed,
                        "executed_action": executed,
                        "decision": status,
                        "certification_queries": cert_count,
                        "candidate_cert_ucb": candidate_ucb,
                        "endpoint_cert_ucb": endpoint_ucb,
                    })
    return pd.DataFrame(records)


def evaluation_cells(decisions, response):
    rows = []
    for decision in decisions.itertuples(index=False):
        if pd.isna(decision.executed_action):
            continue
        block = response[(response.dataset.eq(decision.dataset)) & (response.build_id.eq(decision.target_build)) & (response.query_role.eq("baseline_evaluation"))]
        executed = block[block.ef_search.eq(int(decision.executed_action))].sort_values("query_position")
        endpoint = block[block.ef_search.eq(512)].sort_values("query_position")
        for left, right in zip(executed.itertuples(index=False), endpoint.itertuples(index=False)):
            rows.append({
                "dataset": decision.dataset,
                "arm": decision.arm,
                "deployable": decision.deployable,
                "source_build": decision.source_build,
                "target_build": decision.target_build,
                "query_position": int(left.query_position),
                "executed_action": int(decision.executed_action),
                "failure": int(left.failure),
                "ndc": int(left.ndc),
                "endpoint_failure": int(right.failure),
                "endpoint_ndc": int(right.ndc),
            })
    return pd.DataFrame(rows)


def metrics(values):
    return {
        "risk": float(values.failure.mean()),
        "ndc_gain": float(1.0 - values.ndc.sum() / values.endpoint_ndc.sum()),
        "p95_ndc_ratio": float(values.ndc.quantile(0.95) / values.endpoint_ndc.quantile(0.95)),
        "p99_ndc_ratio": float(values.ndc.quantile(0.99) / values.endpoint_ndc.quantile(0.99)),
    }


def crossed_bootstrap(values, repeats=5000, seed=991):
    targets = sorted(values.target_build.unique())
    queries = sorted(values.query_position.unique())
    sources = len(targets) - 1
    names = ["failure", "ndc", "endpoint_ndc"]
    arrays = {name: np.empty((len(targets), len(queries), sources), dtype=float) for name in names}
    for ti, target in enumerate(targets):
        block = values[values.target_build.eq(target)].sort_values(["query_position", "source_build"])
        for name in names:
            arrays[name][ti] = block[name].to_numpy().reshape(len(queries), sources)
    rng = np.random.default_rng(seed)
    draws = {name: np.empty(repeats) for name in ("risk", "ndc_gain", "p95_ndc_ratio", "p99_ndc_ratio")}
    for repeat in range(repeats):
        ti = rng.integers(0, len(targets), len(targets)); qi = rng.integers(0, len(queries), len(queries))
        selector = np.ix_(ti, qi, np.arange(sources))
        ndc, endpoint = arrays["ndc"][selector], arrays["endpoint_ndc"][selector]
        draws["risk"][repeat] = arrays["failure"][selector].mean()
        draws["ndc_gain"][repeat] = 1.0 - ndc.sum() / endpoint.sum()
        draws["p95_ndc_ratio"][repeat] = np.quantile(ndc, 0.95) / np.quantile(endpoint, 0.95)
        draws["p99_ndc_ratio"][repeat] = np.quantile(ndc, 0.99) / np.quantile(endpoint, 0.99)
    return {name: [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))] for name, values in draws.items()}


def summarize(decisions, cells):
    output = {}
    for (dataset, arm), values in cells.groupby(["dataset", "arm"]):
        decision_rows = decisions[(decisions.dataset.eq(dataset)) & (decisions.arm.eq(arm))]
        point = metrics(values)
        confidence = crossed_bootstrap(values)
        loto = [metrics(values[~values.target_build.eq(target)]) for target in sorted(values.target_build.unique())]
        output.setdefault(dataset, {})[arm] = {
            "deployable": bool(decision_rows.deployable.iloc[0]),
            "decision_counts": {str(k): int(v) for k, v in decision_rows.decision.value_counts().items()},
            "executed_actions": {str(int(k)): int(v) for k, v in decision_rows.executed_action.dropna().value_counts().sort_index().items()},
            "point": point,
            "crossed_target_query_95ci": confidence,
            "loto_min_ndc_gain": min(item["ndc_gain"] for item in loto),
            "loto_max_p95_ndc_ratio": max(item["p95_ndc_ratio"] for item in loto),
        }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--source-decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    response = load_responses(args.responses)
    decisions = make_decisions(response, source_policy_map(args.source_decisions))
    cells = evaluation_cells(decisions, response)
    summary = summarize(decisions, cells)
    decisions.to_csv(args.output / "arm_decisions.csv", index=False)
    cells.to_csv(args.output / "arm_evaluation_cells.csv.gz", index=False, compression="gzip")
    (args.output / "arm_ndc_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
