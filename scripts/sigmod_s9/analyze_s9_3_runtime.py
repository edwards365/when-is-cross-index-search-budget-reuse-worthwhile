#!/usr/bin/env python3
"""Analyze paired, interleaved real-runtime evidence for S9-3."""

import argparse
import glob
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_runtime(root):
    frames = [pd.read_csv(path) for path in sorted(root.glob("runtime/*/*.csv.gz"))]
    result = pd.concat(frames, ignore_index=True)
    expected = 2 * 8 * 500 * 2 * 7
    keys = ["dataset", "target_build", "query_position", "repetition", "ef_search"]
    if len(result) != expected or result.duplicated(keys).any():
        raise RuntimeError("runtime cube incomplete or duplicated")
    hash_counts = result.groupby(["dataset", "target_build", "query_position", "ef_search"]).top10_sha256.nunique()
    if int(hash_counts.max()) != 1:
        raise RuntimeError("runtime top-10 is not deterministic across repetitions")
    return result


def response_hash_mismatches(runtime, response_root):
    frames = []
    for path in sorted(response_root.glob("responses/*/*.csv.gz")):
        frame = pd.read_csv(path)
        frames.append(frame[frame.query_role.eq("target_evaluation")])
    response = pd.concat(frames, ignore_index=True).rename(columns={"build_id": "target_build"})
    expected = response[["dataset", "target_build", "query_position", "ef_search", "top10_sha256"]].drop_duplicates()
    observed = runtime[["dataset", "target_build", "query_position", "ef_search", "top10_sha256"]].drop_duplicates()
    merged = observed.merge(expected, on=["dataset", "target_build", "query_position", "ef_search"], suffixes=("_runtime", "_response"), validate="one_to_one")
    return int((merged.top10_sha256_runtime != merged.top10_sha256_response).sum()), len(merged)


def technical_cells(runtime):
    return runtime.groupby(["dataset", "target_build", "query_position", "ef_search"], as_index=False).agg(
        wall_ns=("wall_ns", "mean"), cpu_ns=("cpu_ns", "mean"), ndc=("ndc", "mean")
    )


def attach_decisions(decisions, technical):
    rows = []
    for decision in decisions.itertuples(index=False):
        selected = technical[(technical.dataset.eq(decision.dataset)) & (technical.target_build.eq(decision.target_build)) & (technical.ef_search.eq(int(decision.deployed_action)))].sort_values("query_position")
        endpoint = technical[(technical.dataset.eq(decision.dataset)) & (technical.target_build.eq(decision.target_build)) & (technical.ef_search.eq(512))].sort_values("query_position")
        if len(selected) != 500 or len(endpoint) != 500 or not np.array_equal(selected.query_position.to_numpy(), endpoint.query_position.to_numpy()):
            raise RuntimeError("runtime decision alignment failed")
        for left, right in zip(selected.itertuples(index=False), endpoint.itertuples(index=False)):
            rows.append({
                "dataset": decision.dataset,
                "source_build": decision.source_build,
                "target_build": decision.target_build,
                "query_position": int(left.query_position),
                "deployed_action": int(decision.deployed_action),
                "wall_ns": float(left.wall_ns),
                "endpoint_wall_ns": float(right.wall_ns),
                "cpu_ns": float(left.cpu_ns),
                "endpoint_cpu_ns": float(right.cpu_ns),
                "ndc": float(left.ndc),
                "endpoint_ndc": float(right.ndc),
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


def crossed_bootstrap(values, repeats=5000, seed=991):
    targets = sorted(values.target_build.unique())
    queries = sorted(values.query_position.unique())
    sources = len(targets) - 1
    names = ["wall_ns", "endpoint_wall_ns", "cpu_ns", "endpoint_cpu_ns", "ndc", "endpoint_ndc"]
    arrays = {name: np.empty((len(targets), len(queries), sources), dtype=np.float64) for name in names}
    for ti, target in enumerate(targets):
        block = values[values.target_build.eq(target)].sort_values(["query_position", "source_build"])
        for name in names:
            arrays[name][ti] = block[name].to_numpy().reshape(len(queries), sources)
    rng = np.random.default_rng(seed)
    draws = {key: np.empty(repeats) for key in ("wall_gain", "cpu_gain", "ndc_gain", "p95_wall_ratio", "p99_wall_ratio")}
    for repeat in range(repeats):
        ti = rng.integers(0, len(targets), len(targets))
        qi = rng.integers(0, len(queries), len(queries))
        selector = np.ix_(ti, qi, np.arange(sources))
        selected_wall = arrays["wall_ns"][selector]
        endpoint_wall = arrays["endpoint_wall_ns"][selector]
        draws["wall_gain"][repeat] = 1.0 - selected_wall.sum() / endpoint_wall.sum()
        draws["cpu_gain"][repeat] = 1.0 - arrays["cpu_ns"][selector].sum() / arrays["endpoint_cpu_ns"][selector].sum()
        draws["ndc_gain"][repeat] = 1.0 - arrays["ndc"][selector].sum() / arrays["endpoint_ndc"][selector].sum()
        draws["p95_wall_ratio"][repeat] = np.quantile(selected_wall, 0.95) / np.quantile(endpoint_wall, 0.95)
        draws["p99_wall_ratio"][repeat] = np.quantile(selected_wall, 0.99) / np.quantile(endpoint_wall, 0.99)
    return {key: [float(np.quantile(value, 0.025)), float(np.quantile(value, 0.975))] for key, value in draws.items()}


def cv_diagnostics(runtime):
    blocks = runtime.groupby(["dataset", "target_build", "ef_search", "repetition"], as_index=False).wall_ns.mean()
    cells = blocks.groupby(["dataset", "target_build", "ef_search"]).wall_ns.agg(lambda x: x.std(ddof=1) / x.mean()).reset_index(name="block_cv")
    summary = {}
    for dataset, group in cells.groupby("dataset"):
        summary[dataset] = {
            "median_action_block_cv": float(group.block_cv.median()),
            "max_action_block_cv": float(group.block_cv.max()),
            "gate_pass": bool(group.block_cv.median() <= 0.05 and group.block_cv.max() <= 0.10),
        }
    return cells, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--safety-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    runtime = load_runtime(args.input)
    mismatch_count, checked = response_hash_mismatches(runtime, args.input)
    if mismatch_count:
        raise RuntimeError("runtime/native response top-10 mismatch")
    decisions = pd.read_csv(args.decisions)
    technical = technical_cells(runtime)
    cells = attach_decisions(decisions, technical)
    cv_cells, cv_summary = cv_diagnostics(runtime)
    safety = json.loads(args.safety_summary.read_text(encoding="utf-8"))
    summary = {}
    for dataset, group in cells.groupby("dataset"):
        point = metrics(group)
        confidence = crossed_bootstrap(group)
        loto = [metrics(group[~group.target_build.eq(target)]) for target in sorted(group.target_build.unique())]
        query_benefit = group.assign(benefit=group.endpoint_wall_ns - group.wall_ns).groupby("query_position").benefit.sum().sort_values(ascending=False)
        delete_ids = set(query_benefit.head(max(1, int(np.ceil(0.01 * len(query_benefit))))).index)
        trimmed = metrics(group[~group.query_position.isin(delete_ids)])
        gate = {
            "safety": bool(safety[dataset]["crossed_target_query_95ci"]["risk"][1] <= 0.05),
            "mean_wall": bool(confidence["wall_gain"][0] > 0),
            "p95": bool(confidence["p95_wall_ratio"][1] <= 1.05),
            "loto": bool(min(item["wall_gain"] for item in loto) > 0),
            "timing_stability": bool(cv_summary[dataset]["gate_pass"]),
        }
        summary[dataset] = {
            "runtime_cells": int(len(group)),
            "point": point,
            "crossed_target_query_95ci": confidence,
            "loto_min_wall_gain": min(item["wall_gain"] for item in loto),
            "loto_max_p95_wall_ratio": max(item["p95_wall_ratio"] for item in loto),
            "delete_top_1pct_query_benefit": trimmed,
            "timing_stability": cv_summary[dataset],
            "gate": gate,
            "primary_gate_pass": bool(all(gate.values())),
        }
    summary["integrity"] = {"runtime_top10_checked_cells": checked, "runtime_top10_mismatches": mismatch_count}
    technical.to_csv(args.output / "technical_runtime_cells.csv.gz", index=False, compression="gzip")
    cells.to_csv(args.output / "decision_runtime_cells.csv.gz", index=False, compression="gzip")
    cv_cells.to_csv(args.output / "action_block_cv.csv", index=False)
    (args.output / "runtime_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
