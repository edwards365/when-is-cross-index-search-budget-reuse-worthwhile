#!/usr/bin/env python3
"""Frozen Phase-F analysis for the 100K hardness-portability core matrix."""
import csv
import gzip
import glob
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, spearmanr

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k")
RAW = ROOT / "results/hardness_portability_100k/core_raw"
DER = ROOT / "results/hardness_portability_100k/derived"
DER.mkdir(parents=True, exist_ok=False)
EFS = np.array([10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512])
SPLIT = json.loads((ROOT / "manifests/hardness_portability_100k/query_split.json").read_text())["splits"]
CAL = np.asarray(SPLIT["train_design"], dtype=int)
AUD = np.asarray(SPLIT["internal_test"], dtype=int)
BOOTSTRAPS = 5000
RNG = np.random.default_rng(991)


def ci(values):
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def ceil_grid(value):
    available = EFS[EFS >= value]
    return int(available[0]) if len(available) else 512


def stable_budget(curve, target=0.90):
    for ef in EFS:
        if all(curve[int(later)]["recall"] >= target for later in EFS[EFS >= ef]):
            return int(ef), False
    return 1024, True


def read_graphs():
    graphs = {}
    expected_fields = {"dataset", "query_id", "query_split", "graph_seed", "insertion_order", "ef_search", "returned_top10_ids", "recall_at_10", "exact_ndc", "graph_hash", "native_or_instrumented", "success"}
    for name in sorted(glob.glob(str(RAW / "*.csv.gz"))):
        with gzip.open(name, "rt", newline="") as handle:
            reader = csv.DictReader(handle)
            if not expected_fields.issubset(reader.fieldnames or []):
                raise RuntimeError(f"schema failure: {name}")
            rows = list(reader)
        if len(rows) != 12000:
            raise RuntimeError(f"row count failure: {name}")
        key = (rows[0]["dataset"], int(rows[0]["graph_seed"]), rows[0]["insertion_order"])
        curves = {query: {} for query in range(1000)}
        for row in rows:
            query = int(row["query_id"])
            ef = int(row["ef_search"])
            if ef in curves[query]:
                raise RuntimeError(f"duplicate cell: {name}:{query}:{ef}")
            if row["native_or_instrumented"] != "instrumented_verified_against_native_per_row" or row["success"] != "True":
                raise RuntimeError(f"native/schema failure: {name}:{query}:{ef}")
            curves[query][ef] = {"recall": float(row["recall_at_10"]), "ndc": float(row["exact_ndc"]), "ids": tuple(map(int, row["returned_top10_ids"].split(";")))}
        if any(set(curves[q]) != set(EFS) for q in curves):
            raise RuntimeError(f"coverage failure: {name}")
        graphs[key] = curves
    if len(graphs) != 27:
        raise RuntimeError(f"expected 27 graphs, got {len(graphs)}")
    return graphs


def omega(matrix):
    mean = matrix.mean()
    query = matrix.mean(axis=1, keepdims=True) - mean
    graph = matrix.mean(axis=0, keepdims=True) - mean
    interaction = matrix - mean - query - graph
    vq, vg, vi = np.var(query), np.var(graph), np.var(interaction)
    return (float(vi / (vq + vi)) if vq + vi else 0.0, float(vq), float(vg), float(vi))


def write_csv(name, rows):
    with (DER / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


G = read_graphs()
DATASETS = sorted({key[0] for key in G})
stable = {}
fixed = {}
effort_rows = []
headroom_rows = []
oracle_summary = {}
for dataset in DATASETS:
    keys = sorted(key for key in G if key[0] == dataset)
    per_query = np.zeros((len(AUD), len(keys)))
    seed_means = {seed: [] for seed in (43, 59, 71)}
    order_means = {order: [] for order in ("random", "lid_ascending", "lid_descending")}
    for column, key in enumerate(keys):
        graph = G[key]
        fixed_target = 0.95 if any(np.mean([graph[q][int(ef)]["recall"] for q in CAL]) >= 0.95 for ef in EFS) else 0.90
        fixed_ef = next((int(ef) for ef in EFS if np.mean([graph[q][int(ef)]["recall"] for q in CAL]) >= fixed_target), 512)
        fixed[key] = fixed_ef
        stable[key] = {}
        local = []
        for query in range(1000):
            budget, censored = stable_budget(graph[query])
            stable[key][query] = budget
            effort_rows.append({"dataset": dataset, "seed": key[1], "order": key[2], "query_id": query, "split": "train_design" if query in set(CAL) else "confirmatory_audit", "stable_ef": budget, "right_censored": censored, "fixed_ef": fixed_ef})
        for row, query in enumerate(AUD):
            oracle_ef = min(stable[key][int(query)], 512)
            fixed_cost = graph[int(query)][fixed_ef]["ndc"]
            saving = (fixed_cost - graph[int(query)][oracle_ef]["ndc"]) / fixed_cost
            per_query[row, column] = saving
            local.append(saving)
        local = np.asarray(local)
        seed_means[key[1]].append(float(local.mean()))
        order_means[key[2]].append(float(local.mean()))
        headroom_rows.append({"dataset": dataset, "seed": key[1], "order": key[2], "fixed_ef": fixed_ef, "fixed_recall_target": fixed_target, "mean_headroom": float(local.mean()), "p50_headroom": float(np.quantile(local, .50)), "p95_headroom": float(np.quantile(local, .95)), "p99_headroom": float(np.quantile(local, .99)), "trimmed_top1pct_headroom": float(np.mean(np.sort(local)[:-max(1, int(.01 * len(local)))])), "right_censored_rate": float(np.mean([stable[key][int(q)] > 512 for q in AUD]))})
    per_query_mean = per_query.mean(axis=1)
    boot = [float(per_query_mean[RNG.integers(0, len(AUD), len(AUD))].mean()) for _ in range(BOOTSTRAPS)]
    oracle_summary[dataset] = {"mean": float(per_query_mean.mean()), "ci95": ci(boot), "trimmed_top1pct": float(np.mean(np.sort(per_query_mean)[:-max(1, int(.01 * len(per_query_mean)))])), "seed_means": {str(k): float(np.mean(v)) for k, v in seed_means.items()}, "order_means": {k: float(np.mean(v)) for k, v in order_means.items()}}

variance_rows = []
rank_rows = []
omega_summary = {}
for dataset in DATASETS:
    keys = sorted(key for key in G if key[0] == dataset)
    Y = np.asarray([[math.log2(stable[key][int(query)]) for key in keys] for query in AUD])
    estimate, vq, vg, vi = omega(Y)
    boot = [omega(Y[RNG.integers(0, len(Y), len(Y))])[0] for _ in range(BOOTSTRAPS)]
    leave_seed = {str(seed): omega(Y[:, [i for i, key in enumerate(keys) if key[1] != seed]])[0] for seed in (43, 59, 71)}
    leave_order = {order: omega(Y[:, [i for i, key in enumerate(keys) if key[2] != order]])[0] for order in ("random", "lid_ascending", "lid_descending")}
    query_interaction = np.var(Y - Y.mean(axis=1, keepdims=True) - Y.mean(axis=0, keepdims=True) + Y.mean(), axis=1)
    keep = np.argsort(query_interaction)[: int(.99 * len(Y))]
    trimmed = omega(Y[keep])[0]
    omega_summary[dataset] = {"omega": estimate, "ci95": ci(boot), "leave_one_seed": leave_seed, "leave_one_order": leave_order, "trimmed_top1pct": trimmed}
    variance_rows.append({"dataset": dataset, "omega": estimate, "omega_ci_low": ci(boot)[0], "omega_ci_high": ci(boot)[1], "query_variance": vq, "graph_variance": vg, "interaction_variance": vi, "trimmed_top1pct_omega": trimmed})
    for i, source in enumerate(keys):
        for j in range(i + 1, len(keys)):
            target = keys[j]
            rho = float(spearmanr(Y[:, i], Y[:, j]).statistic)
            tau = float(kendalltau(Y[:, i], Y[:, j]).statistic)
            rank_rows.append({"dataset": dataset, "source": f"{source[1]}_{source[2]}", "target": f"{target[1]}_{target[2]}", "same_order": source[2] == target[2], "same_seed": source[1] == target[1], "spearman": rho, "kendall": tau, "rank_reversal_rate": float((1.0 - tau) / 2.0)})

transfer_rows = []
portability = {}
for dataset in DATASETS:
    keys = sorted(key for key in G if key[0] == dataset)
    query_regret = {"same_order": [], "cross_order": []}
    pair_vectors = {"same_order": [], "cross_order": []}
    for source in keys:
        for target in keys:
            if source == target:
                continue
            target_graph = G[target]
            fixed_ef = fixed[target]
            baseline_recall = np.mean([target_graph[int(q)][fixed_ef]["recall"] for q in CAL])
            candidates = sorted({float(ef / stable[source][int(q)]) for q in CAL for ef in EFS})
            multiplier = candidates[-1]
            for candidate in candidates:
                recall = np.mean([target_graph[int(q)][ceil_grid(candidate * stable[source][int(q)])]["recall"] for q in CAL])
                if recall >= baseline_recall - .001:
                    multiplier = candidate
                    break
            regrets, recall_diffs, under, over = [], [], [], []
            for query in AUD:
                query = int(query)
                predicted = ceil_grid(multiplier * stable[source][query])
                target_oracle = min(stable[target][query], 512)
                denominator = target_graph[query][fixed_ef]["ndc"]
                regrets.append((target_graph[query][predicted]["ndc"] - target_graph[query][target_oracle]["ndc"]) / denominator)
                recall_diffs.append(target_graph[query][predicted]["recall"] - target_graph[query][fixed_ef]["recall"])
                under.append(predicted < target_oracle)
                over.append(predicted > target_oracle)
            category = "same_order" if source[2] == target[2] else "cross_order"
            vector = np.asarray(regrets)
            pair_vectors[category].append(vector)
            transfer_rows.append({"dataset": dataset, "source": f"{source[1]}_{source[2]}", "target": f"{target[1]}_{target[2]}", "category": category, "same_seed": source[1] == target[1], "multiplier": multiplier, "recall_diff": float(np.mean(recall_diffs)), "normalized_regret": float(vector.mean()), "under_budget_rate": float(np.mean(under)), "over_budget_rate": float(np.mean(over))})
    same = np.mean(pair_vectors["same_order"], axis=0)
    cross = np.mean(pair_vectors["cross_order"], axis=0)
    delta = cross - same
    boot = [float(delta[RNG.integers(0, len(delta), len(delta))].mean()) for _ in range(BOOTSTRAPS)]
    same_rho = np.mean([row["spearman"] for row in rank_rows if row["dataset"] == dataset and row["same_order"]])
    cross_rho = np.mean([row["spearman"] for row in rank_rows if row["dataset"] == dataset and not row["same_order"]])
    pair_excess = np.asarray([v.mean() - same.mean() for v in pair_vectors["cross_order"]])
    positive = np.maximum(pair_excess, 0)
    max_pair_share = float(positive.max() / positive.sum()) if positive.sum() else 1.0
    portability[dataset] = {"delta_history": float(delta.mean()), "ci95": ci(boot), "same_order_spearman": float(same_rho), "cross_order_spearman": float(cross_rho), "rank_correlation_drop": float(same_rho - cross_rho), "max_positive_pair_share": max_pair_share}

oracle_gate = {dataset: (value["mean"] > .10 and value["trimmed_top1pct"] > .03 and value["ci95"][0] > 0 and min(value["seed_means"].values()) > 0 and min(value["order_means"].values()) > 0) for dataset, value in oracle_summary.items()}
conditionality_gate = {dataset: (value["omega"] > .10 and value["ci95"][0] > .05 and min(value["leave_one_seed"].values()) > .10 and min(value["leave_one_order"].values()) > .10 and value["trimmed_top1pct"] > .10) for dataset, value in omega_summary.items()}
portability_gate = {dataset: (value["delta_history"] >= .05 and value["ci95"][0] > 0 and value["rank_correlation_drop"] >= .10 and value["max_positive_pair_share"] < .50) for dataset, value in portability.items()}
gate_o = sum(oracle_gate.values()) >= 2
gate_c = sum(conditionality_gate.values()) >= 2
gate_p = sum(portability_gate.values()) >= 2
if not gate_o:
    status = "STOP_AT_10K_MECHANISM_ONLY"
elif not (gate_c and gate_p):
    status = "SHRINK_TO_ORACLE_REALIZABILITY_GAP"
else:
    status = "PASS_TO_REALISTIC_HISTORY_GATE"

summary = {"status": status, "gate_oracle_pass": gate_o, "gate_conditionality_pass": gate_c, "gate_portability_pass": gate_p, "oracle_gate_by_dataset": oracle_gate, "conditionality_gate_by_dataset": conditionality_gate, "portability_gate_by_dataset": portability_gate, "oracle": oracle_summary, "omega": omega_summary, "portability": portability, "graphs": 27, "rows": 324000, "bootstrap_replicates": BOOTSTRAPS, "bootstrap_seed": 991, "formal_test_accessed": False}
write_csv("per_query_effort.csv", effort_rows)
write_csv("oracle_headroom.csv", headroom_rows)
write_csv("variance_components.csv", variance_rows)
write_csv("rank_reversal.csv", rank_rows)
write_csv("transfer_matrix.csv", transfer_rows)
(DER / "core_gate_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
