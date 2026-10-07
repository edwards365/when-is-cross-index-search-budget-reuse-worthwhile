import numpy as np
import pandas as pd
from scipy.stats import beta
GRID=[16,32,64,128,256,512]

def cp_upper(failures, trials, alpha):
    if failures == trials:
        return 1.0
    return float(beta.ppf(1.0 - alpha, failures + 1, trials - failures))

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
