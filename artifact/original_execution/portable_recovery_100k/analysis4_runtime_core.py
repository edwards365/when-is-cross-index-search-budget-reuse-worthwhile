"""Exact original statistical functions; new receipt-bound inputs only."""
import json
from types import SimpleNamespace
import numpy as np
import pandas as pd

def technical_cells(runtime):
    return runtime.groupby(["dataset", "target_build", "query_position", "ef_search"], as_index=False).agg(
        wall_ns=("wall_ns", "mean"), cpu_ns=("cpu_ns", "mean"), ndc=("ndc", "mean")
    )


def attach(decisions, technical):
    rows = []
    deployable = decisions[decisions.deployable.astype(str).str.lower().eq("true")]
    for decision in deployable.itertuples(index=False):
        if pd.isna(decision.executed_action):
            continue
        block = technical[(technical.dataset.eq(decision.dataset)) & (technical.target_build.eq(decision.target_build))]
        selected = block[block.ef_search.eq(int(decision.executed_action))].sort_values("query_position")
        endpoint = block[block.ef_search.eq(512)].sort_values("query_position")
        if len(selected) != 500 or len(endpoint) != 500:
            raise RuntimeError(f"missing runtime action for {decision.arm}")
        for left, right in zip(selected.itertuples(index=False), endpoint.itertuples(index=False)):
            rows.append({
                "dataset": decision.dataset, "arm": decision.arm, "source_build": decision.source_build,
                "target_build": decision.target_build, "query_position": int(left.query_position),
                "executed_action": int(decision.executed_action), "wall_ns": float(left.wall_ns),
                "endpoint_wall_ns": float(right.wall_ns), "cpu_ns": float(left.cpu_ns),
                "endpoint_cpu_ns": float(right.cpu_ns), "ndc": float(left.ndc), "endpoint_ndc": float(right.ndc),
            })
    return pd.DataFrame(rows)


def metrics(values):
    return {
        "wall_gain": float(1.0 - values.wall_ns.sum() / values.endpoint_wall_ns.sum()),
        "cpu_gain": float(1.0 - values.cpu_ns.sum() / values.endpoint_cpu_ns.sum()),
        "ndc_gain": float(1.0 - values.ndc.sum() / values.endpoint_ndc.sum()),
        "p95_wall_ratio": float(values.wall_ns.quantile(0.95) / values.endpoint_wall_ns.quantile(0.95)),
        "p99_wall_ratio": float(values.wall_ns.quantile(0.99) / values.endpoint_wall_ns.quantile(0.99)),
    }


def bootstrap(values, repeats=5000, seed=991):
    targets = sorted(values.target_build.unique()); queries = sorted(values.query_position.unique()); sources = len(targets) - 1
    names = ["wall_ns", "endpoint_wall_ns", "cpu_ns", "endpoint_cpu_ns", "ndc", "endpoint_ndc"]
    arrays = {name: np.empty((len(targets), len(queries), sources), dtype=float) for name in names}
    for ti, target in enumerate(targets):
        block = values[values.target_build.eq(target)].sort_values(["query_position", "source_build"])
        for name in names:
            arrays[name][ti] = block[name].to_numpy().reshape(len(queries), sources)
    rng = np.random.default_rng(seed)
    draws = {name: np.empty(repeats) for name in ("wall_gain", "cpu_gain", "ndc_gain", "p95_wall_ratio", "p99_wall_ratio")}
    for repeat in range(repeats):
        ti = rng.integers(0, len(targets), len(targets)); qi = rng.integers(0, len(queries), len(queries)); selector = np.ix_(ti, qi, np.arange(sources))
        wall, endpoint = arrays["wall_ns"][selector], arrays["endpoint_wall_ns"][selector]
        draws["wall_gain"][repeat] = 1.0 - wall.sum() / endpoint.sum()
        draws["cpu_gain"][repeat] = 1.0 - arrays["cpu_ns"][selector].sum() / arrays["endpoint_cpu_ns"][selector].sum()
        draws["ndc_gain"][repeat] = 1.0 - arrays["ndc"][selector].sum() / arrays["endpoint_ndc"][selector].sum()
        draws["p95_wall_ratio"][repeat] = np.quantile(wall, .95) / np.quantile(endpoint, .95)
        draws["p99_wall_ratio"][repeat] = np.quantile(wall, .99) / np.quantile(endpoint, .99)
    return {name: [float(np.quantile(value, .025)), float(np.quantile(value, .975))] for name, value in draws.items()}


def cv_summary(runtime):
    blocks = runtime.groupby(["dataset", "target_build", "ef_search", "repetition"], as_index=False).wall_ns.mean()
    cells = blocks.groupby(["dataset", "target_build", "ef_search"]).wall_ns.agg(lambda x: x.std(ddof=1) / x.mean()).reset_index(name="block_cv")
    return cells, {dataset: {"median": float(group.block_cv.median()), "max": float(group.block_cv.max())} for dataset, group in cells.groupby("dataset")}


def analyze(runtime, decisions, safety, output, checked):
    args=SimpleNamespace(output=output)
    ndc_summary=safety
    mismatch_count=mismatches=0
    technical = technical_cells(runtime)
    cells = attach(decisions, technical)
    cv_cells, cvs = cv_summary(runtime)
    summary = {}
    for (dataset, arm), group in cells.groupby(["dataset", "arm"]):
            point = metrics(group); confidence = bootstrap(group)
            loto = [metrics(group[~group.target_build.eq(target)]) for target in sorted(group.target_build.unique())]
            benefit = group.assign(benefit=group.endpoint_wall_ns - group.wall_ns).groupby("query_position").benefit.sum().sort_values(ascending=False)
            remove = set(benefit.head(5).index); trimmed = metrics(group[~group.query_position.isin(remove)])
            risk = ndc_summary[dataset][arm]["point"]["risk"]
            risk_ci = ndc_summary[dataset][arm]["crossed_target_query_95ci"]["risk"]
            gates = {
                "safety": risk <= .05 and risk_ci[1] <= .05,
                "mean_wall": confidence["wall_gain"][0] > 0,
                "p95": confidence["p95_wall_ratio"][1] <= 1.05,
                "loto": min(item["wall_gain"] for item in loto) > 0,
                "timing": cvs[dataset]["median"] <= .05 and cvs[dataset]["max"] <= .10,
            }
            summary.setdefault(dataset, {})[arm] = {
                "risk": risk, "risk_crossed_95ci": risk_ci, "point": point,
                "crossed_target_query_95ci": confidence,
                "loto_min_wall_gain": min(item["wall_gain"] for item in loto),
                "loto_max_p95_wall_ratio": max(item["p95_wall_ratio"] for item in loto),
                "delete_top_1pct_query_benefit": trimmed, "gates": gates,
                "deployment_value_gate_pass": bool(all(gates.values())),
            }
    summary["timing_stability"] = cvs
    summary["integrity"] = {"top10_checked_cells": checked, "top10_mismatches": mismatches}
    technical.to_csv(args.output / "technical_runtime_cells.csv.gz", index=False, compression="gzip")
    cells.to_csv(args.output / "arm_runtime_cells.csv.gz", index=False, compression="gzip")
    cv_cells.to_csv(args.output / "action_block_cv.csv", index=False)
    (args.output / "arm_runtime_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
