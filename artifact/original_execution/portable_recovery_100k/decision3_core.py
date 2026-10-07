import numpy as np
import pandas as pd
from scipy.stats import beta
GRID=[16,32,64,128,256,512]

def cp_upper(failures, trials, alpha):
    if failures == trials:
        return 1.0
    return float(beta.ppf(1.0 - alpha, failures + 1, trials - failures))

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
