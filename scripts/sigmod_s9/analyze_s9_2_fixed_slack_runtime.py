#!/usr/bin/env python3
"""Analyze the frozen Faiss +1 fixed-slack policy on S9-2 native timings."""

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


GRID = [16, 32, 64, 128, 256, 512]
ENDPOINT = 512


def quantile(values, q):
    return float(np.quantile(np.asarray(values, dtype=float), q))


def load_pairs(path):
    pairs = defaultdict(lambda: defaultdict(list))
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["deployment"] != "DEPLOY_CANDIDATE":
                raise RuntimeError(f"unexpected frozen deployment: {row}")
            pairs[row["dataset"]][row["target_build"]].append(int(row["executed_action"]))
    for dataset in pairs:
        for target, actions in pairs[dataset].items():
            if len(actions) != 23:
                raise RuntimeError(f"expected 23 source directions for {target}, got {len(actions)}")
            if any(action not in GRID for action in actions):
                raise RuntimeError(f"unregistered action for {target}")
    return pairs


def load_runtime(path):
    by_cell = defaultdict(lambda: {"wall": [], "cpu": [], "exact": []})
    dataset = build = None
    with gzip.open(path, "rt", newline="") as handle:
        for row in csv.DictReader(handle):
            dataset, build = row["dataset"], row["build"]
            key = (int(row["query_id"]), int(row["ef"]))
            by_cell[key]["wall"].append(int(row["wall_ns"]))
            by_cell[key]["cpu"].append(int(row["process_cpu_ns"]))
            by_cell[key]["exact"].append(int(row["native_exact"]))
    query_ids = sorted({key[0] for key in by_cell})
    if query_ids != list(range(500, 1000)):
        raise RuntimeError(f"unexpected evaluation role in {path}")
    wall = np.empty((500, len(GRID)), dtype=float)
    cpu = np.empty_like(wall)
    for qi, query_id in enumerate(query_ids):
        for ai, action in enumerate(GRID):
            cell = by_cell[(query_id, action)]
            if len(cell["wall"]) != 7 or not all(cell["exact"]):
                raise RuntimeError(f"invalid runtime cell {path}:{query_id}:{action}")
            wall[qi, ai] = np.median(cell["wall"])
            cpu[qi, ai] = np.median(cell["cpu"])
    return dataset, build, wall, cpu


def policy_matrices(runtime_dir, pair_map):
    result = defaultdict(list)
    for path in sorted(runtime_dir.glob("*.csv.gz")):
        dataset, build, wall, cpu = load_runtime(path)
        counts = Counter(pair_map[dataset][build])
        candidate_wall = sum(wall[:, GRID.index(action)] * count for action, count in counts.items()) / 23.0
        candidate_cpu = sum(cpu[:, GRID.index(action)] * count for action, count in counts.items()) / 23.0
        result[dataset].append({
            "build": build,
            "counts": counts,
            "wall_all": wall,
            "cpu_all": cpu,
            "candidate_wall": candidate_wall,
            "endpoint_wall": wall[:, GRID.index(ENDPOINT)],
            "candidate_cpu": candidate_cpu,
            "endpoint_cpu": cpu[:, GRID.index(ENDPOINT)],
        })
    return result


def expanded_candidate(blocks, metric):
    rows = []
    all_key = "wall_all" if metric == "wall" else "cpu_all"
    for block in blocks:
        for action, count in block["counts"].items():
            rows.append(np.repeat(block[all_key][:, GRID.index(action)], count))
    return np.concatenate(rows)


def expanded_endpoint(blocks, metric):
    key = "endpoint_wall" if metric == "wall" else "endpoint_cpu"
    return np.concatenate([np.repeat(block[key], 23) for block in blocks])


def bootstrap(blocks, reps, seed):
    rng = np.random.default_rng(seed)
    cand = np.stack([b["candidate_wall"] for b in blocks])
    endpoint = np.stack([b["endpoint_wall"] for b in blocks])
    action_arrays = np.stack([b["wall_all"] for b in blocks])
    count_arrays = np.asarray([[b["counts"].get(action, 0) for action in GRID] for b in blocks])
    gains = np.empty(reps)
    p95_ratios = np.empty(reps)
    n_targets, n_queries = cand.shape
    for rep in range(reps):
        target_idx = rng.integers(0, n_targets, n_targets)
        query_idx = rng.integers(0, n_queries, n_queries)
        sampled_cand = cand[target_idx][:, query_idx]
        sampled_endpoint = endpoint[target_idx][:, query_idx]
        gains[rep] = 1.0 - sampled_cand.sum() / sampled_endpoint.sum()
        candidate_values = []
        for sampled_position, original_target in enumerate(target_idx):
            values = action_arrays[original_target][query_idx]
            for ai, count in enumerate(count_arrays[original_target]):
                if count:
                    candidate_values.append(np.repeat(values[:, ai], count))
        candidate_values = np.concatenate(candidate_values)
        endpoint_values = np.repeat(sampled_endpoint.reshape(-1), 23)
        p95_ratios[rep] = np.quantile(candidate_values, 0.95) / np.quantile(endpoint_values, 0.95)
    return gains, p95_ratios


def analyze_dataset(dataset, blocks, reps, seed):
    blocks = sorted(blocks, key=lambda row: row["build"])
    candidate = np.stack([b["candidate_wall"] for b in blocks])
    endpoint = np.stack([b["endpoint_wall"] for b in blocks])
    cpu_candidate = np.stack([b["candidate_cpu"] for b in blocks])
    cpu_endpoint = np.stack([b["endpoint_cpu"] for b in blocks])
    gain = 1.0 - candidate.sum() / endpoint.sum()
    cpu_gain = 1.0 - cpu_candidate.sum() / cpu_endpoint.sum()
    candidate_expanded = expanded_candidate(blocks, "wall")
    endpoint_expanded = expanded_endpoint(blocks, "wall")
    p95_ratio = quantile(candidate_expanded, 0.95) / quantile(endpoint_expanded, 0.95)
    p99_ratio = quantile(candidate_expanded, 0.99) / quantile(endpoint_expanded, 0.99)
    gains, p95_ratios = bootstrap(blocks, reps, seed)
    per_build = []
    for i, block in enumerate(blocks):
        per_build.append({
            "dataset": dataset,
            "target_build": block["build"],
            "candidate_action_counts": ";".join(f"{a}:{block['counts'].get(a, 0)}" for a in GRID),
            "wall_gain": 1.0 - candidate[i].sum() / endpoint[i].sum(),
            "cpu_gain": 1.0 - cpu_candidate[i].sum() / cpu_endpoint[i].sum(),
        })
    loto = []
    for held_out in range(len(blocks)):
        keep = np.arange(len(blocks)) != held_out
        loto.append(1.0 - candidate[keep].sum() / endpoint[keep].sum())
    per_query_benefit = (endpoint - candidate).sum(axis=0)
    delete_n = max(1, int(np.ceil(0.01 * candidate.shape[1])))
    delete_ids = np.argsort(per_query_benefit)[-delete_n:]
    keep_queries = np.ones(candidate.shape[1], dtype=bool)
    keep_queries[delete_ids] = False
    delete_gain = 1.0 - candidate[:, keep_queries].sum() / endpoint[:, keep_queries].sum()
    summary = {
        "dataset": dataset,
        "target_builds": len(blocks),
        "evaluation_queries": candidate.shape[1],
        "source_directions_per_target": 23,
        "wall_gain": gain,
        "wall_gain_ci95": [quantile(gains, 0.025), quantile(gains, 0.975)],
        "process_cpu_gain": cpu_gain,
        "p95_ratio": p95_ratio,
        "p95_ratio_ci95": [quantile(p95_ratios, 0.025), quantile(p95_ratios, 0.975)],
        "p99_ratio": p99_ratio,
        "min_loto_wall_gain": min(loto),
        "delete_largest_gain_1pct_wall_gain": delete_gain,
        "mean_gate_pass": bool(quantile(gains, 0.025) > 0.0),
        "p95_noninferiority_gate_pass": bool(quantile(p95_ratios, 0.975) <= 1.05),
        "loto_gate_pass": bool(min(loto) > 0.0),
    }
    return summary, per_build


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--pairs", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--bootstrap-reps", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=991)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    pairs = load_pairs(args.pairs)
    matrices = policy_matrices(args.runtime, pairs)
    expected = set(pairs)
    if set(matrices) != expected or any(len(matrices[d]) != 24 for d in expected):
        raise RuntimeError("runtime matrix does not contain 24 target builds for each dataset")
    summaries, per_build = [], []
    for dataset in sorted(matrices):
        summary, rows = analyze_dataset(dataset, matrices[dataset], args.bootstrap_reps, args.seed)
        summaries.append(summary)
        per_build.extend(rows)
    with (args.output / "summary.json").open("w") as handle:
        json.dump({
            "status": "PASS" if all(row["mean_gate_pass"] and row["p95_noninferiority_gate_pass"] and row["loto_gate_pass"] for row in summaries) else "MIXED_OR_FAIL",
            "estimand": "frozen target-certified Faiss +1 fixed-slack versus efSearch=512 endpoint",
            "statistics": {"crossed_target_query_bootstrap_reps": args.bootstrap_reps, "seed": args.seed},
            "datasets": summaries,
            "claim_boundary": "This block does not time TCP or target-global calibration, whose recurring-query roles and native grid are different."
        }, handle, indent=2)
        handle.write("\n")
    with (args.output / "per_build.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_build[0]))
        writer.writeheader()
        writer.writerows(per_build)


if __name__ == "__main__":
    main()
