"""Exact original statistical functions; new receipt-bound inputs only."""
import json
from types import SimpleNamespace
import numpy as np
import pandas as pd

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


