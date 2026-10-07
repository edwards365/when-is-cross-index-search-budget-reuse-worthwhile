"""Exact original statistical functions; new receipt-bound inputs only."""
import json
from types import SimpleNamespace
import numpy as np
import pandas as pd

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


