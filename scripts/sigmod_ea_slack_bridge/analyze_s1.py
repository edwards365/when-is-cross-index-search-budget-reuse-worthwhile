#!/usr/bin/env python3
"""S1 frozen-response slack and stable-tail analysis.

This script only reads stored query response cubes.  It does not build an
index or invoke ANN search.  Shared-query resampling keeps every directed
source/target pair for a query together.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np


DATASETS = ("sift_100k", "arxiv_nomic_100k")
GRIDS = {
    "hnswlib": np.asarray((10, 20, 40, 80, 120, 200), dtype=int),
    "faiss_hnsw": np.asarray((16, 32, 64, 128, 256, 512), dtype=int),
}
LANES = ("first_plus_0", "first_plus_1", "first_plus_2", "stable_tail", "endpoint")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load_hnsw(root: Path, dataset: str):
    records = []
    paths = sorted(root.glob(dataset + "__seed*__*/queries.csv.gz"))
    for path in paths:
        with gzip.open(path, "rt", newline="") as f:
            for row in csv.DictReader(f):
                if int(row.get("latency_round", 0)) != 0 or int(row["query_id"]) >= 750:
                    continue
                records.append((
                    path.parent.name,
                    int(row["query_id"]),
                    int(row["ef_search"]),
                    int(round(float(row["recall_at_10"]) * 10)),
                    float(row["ndc"]),
                ))
    return paths, records, True


def load_faiss(root: Path, dataset: str):
    records = []
    paths = sorted(root.glob(dataset + "__100k__clean*.csv.gz"))
    for path in paths:
        with gzip.open(path, "rt", newline="") as f:
            for row in csv.DictReader(f):
                if int(row["query_id"]) >= 750:
                    continue
                records.append((
                    row["build_id"],
                    int(row["query_id"]),
                    int(row["ef"]),
                    int(row["hit_count"]),
                    math.nan,
                ))
    return paths, records, False


def cube(records, grid):
    builds = sorted({r[0] for r in records})
    queries = sorted({r[1] for r in records})
    bmap = {v: i for i, v in enumerate(builds)}
    qmap = {v: i for i, v in enumerate(queries)}
    amap = {int(v): i for i, v in enumerate(grid)}
    hit = np.full((len(builds), len(queries), len(grid)), -1, dtype=np.int16)
    cost = np.full(hit.shape, np.nan, dtype=float)
    for b, q, a, h, c in records:
        hit[bmap[b], qmap[q], amap[a]] = h
        cost[bmap[b], qmap[q], amap[a]] = c
    if np.any(hit < 0):
        raise ValueError("incomplete build/query/action response cube")
    return builds, queries, hit, cost


def label_indices(hit):
    safe = hit >= 10
    first = np.full(safe.shape[:2], -1, dtype=int)
    stable = np.full(safe.shape[:2], -1, dtype=int)
    raw_nonmonotone = np.zeros(safe.shape[:2], dtype=bool)
    for j in range(safe.shape[2]):
        first[(first < 0) & safe[:, :, j]] = j
        tail_ok = np.all(safe[:, :, j:], axis=2)
        stable[(stable < 0) & tail_ok] = j
    for j in range(safe.shape[2] - 1):
        raw_nonmonotone |= safe[:, :, j] & np.any(~safe[:, :, j + 1 :], axis=2)
    return first, stable, raw_nonmonotone


def action_indices(lane, first, stable, jmax):
    if lane == "endpoint":
        return np.full(first.shape, jmax, dtype=int)
    if lane == "stable_tail":
        return np.where(stable < 0, jmax, stable)
    shift = int(lane.rsplit("_", 1)[1])
    return np.where(first < 0, jmax, np.minimum(first + shift, jmax))


def bootstrap_ci(qvalues, seed=991, reps=5000):
    rng = np.random.default_rng(seed)
    n = len(qvalues)
    draws = np.empty(reps, dtype=float)
    for i in range(reps):
        draws[i] = np.mean(qvalues[rng.integers(0, n, n)])
    return np.quantile(draws, (0.025, 0.975))


def metrics(builds, grid, hit, cost, first, stable, lane):
    b, q, _ = hit.shape
    aidx = action_indices(lane, first, stable, len(grid) - 1)
    abs_values = []
    ref_values = []
    inc_values = []
    src_values = []
    target_cost = []
    requested = []
    per_q = [[] for _ in range(q)]
    per_target = {name: {"abs": [], "ref": [], "inc": [], "cost": []} for name in builds}
    for si in range(b):
        for ti in range(b):
            if si == ti:
                continue
            acts = aidx[si]
            qq = np.arange(q)
            target_fail = hit[ti, qq, acts] < 10
            reference_fail = first[ti] < 0
            source_fail = hit[si, qq, acts] < 10
            increment = target_fail.astype(int) - reference_fail.astype(int)
            abs_values.extend(target_fail.astype(int))
            ref_values.extend(reference_fail.astype(int))
            inc_values.extend(increment)
            src_values.extend(source_fail.astype(int))
            requested.extend(grid[acts])
            for qi, value in enumerate(increment):
                per_q[qi].append(int(value))
            row = per_target[builds[ti]]
            row["abs"].extend(target_fail.astype(int))
            row["ref"].extend(reference_fail.astype(int))
            row["inc"].extend(increment)
            if np.isfinite(cost).any():
                cc = cost[ti, qq, acts]
                target_cost.extend(cc)
                row["cost"].extend(cc)
    qvalues = np.asarray([np.mean(v) for v in per_q])
    ci_low, ci_high = bootstrap_ci(qvalues)
    drop_n = max(1, int(math.ceil(0.01 * len(qvalues))))
    keep = np.argsort(qvalues)[:-drop_n]
    lobo = []
    for dropped in range(b):
        values = []
        for si in range(b):
            if si == dropped:
                continue
            for ti in range(b):
                if ti == dropped or si == ti:
                    continue
                acts = aidx[si]
                qq = np.arange(q)
                target_fail = hit[ti, qq, acts] < 10
                reference_fail = first[ti] < 0
                values.extend(target_fail.astype(int) - reference_fail.astype(int))
        lobo.append(float(np.mean(values)))
    costs = np.asarray(target_cost, dtype=float)
    return {
        "absolute_risk": float(np.mean(abs_values)),
        "reference_risk": float(np.mean(ref_values)),
        "incremental_risk": float(np.mean(inc_values)),
        "increment_ci_low": float(ci_low),
        "increment_ci_high": float(ci_high),
        "source_execution_risk": float(np.mean(src_values)),
        "endpoint_saturation": float(np.mean(aidx == len(grid) - 1)),
        "requested_action_mean": float(np.mean(requested)),
        "requested_action_p95": float(np.quantile(requested, 0.95)),
        "ndc_status": "ESTIMABLE" if costs.size else "NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE",
        "target_ndc_mean": float(np.mean(costs)) if costs.size else "NOT_ESTIMABLE",
        "target_ndc_p95": float(np.quantile(costs, 0.95)) if costs.size else "NOT_ESTIMABLE",
        "delete_max_1pct_increment": float(np.mean(qvalues[keep])),
        "lobo_min_increment": float(np.min(lobo)),
        "lobo_max_increment": float(np.max(lobo)),
    }, per_target


def setting_label(rows):
    by = {r["lane"]: r for r in rows}
    base = by["first_plus_0"]["incremental_risk"]
    plus1 = by["first_plus_1"]["incremental_risk"]
    plus2 = by["first_plus_2"]["incremental_risk"]
    if plus2 >= 0.05 and by["first_plus_2"]["increment_ci_low"] > 0:
        return "BROAD_PORTABILITY_GAP_PERSISTS"
    if base > 0 and (plus1 <= 0.25 * base or plus1 < 0.01):
        return "SLACK_ABSORBS_MOST_FAILURE_RISK_ONLY"
    if plus2 < base:
        return "SLACK_REDUCES_RISK_WITH_UNRESOLVED_OR_MATERIAL_COST"
    return "MIXED_OR_NO_MONOTONE_SLACK_RESPONSE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hnsw-root", type=Path, required=True)
    ap.add_argument("--faiss-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = []
    target_rows = []
    diagnostic_rows = []
    inventory = []
    decisions = []
    for operator in ("hnswlib", "faiss_hnsw"):
        for dataset in DATASETS:
            if operator == "hnswlib":
                paths, records, has_ndc = load_hnsw(args.hnsw_root, dataset)
            else:
                paths, records, has_ndc = load_faiss(args.faiss_root, dataset)
            for path in paths:
                inventory.append({
                    "operator": operator,
                    "dataset": dataset,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
            grid = GRIDS[operator]
            builds, queries, hit, cost = cube(records, grid)
            first, stable, nonmono = label_indices(hit)
            diagnostic_rows.append({
                "operator": operator,
                "dataset": dataset,
                "builds": len(builds),
                "queries": len(queries),
                "grid": ";".join(map(str, grid)),
                "raw_nonmonotone_fraction": float(np.mean(nonmono)),
                "first_unresolved_fraction": float(np.mean(first < 0)),
                "stable_unresolved_fraction": float(np.mean(stable < 0)),
                "stable_ge_first_when_both_finite": bool(np.all(stable[(first >= 0) & (stable >= 0)] >= first[(first >= 0) & (stable >= 0)])),
                "ndc_available": has_ndc,
            })
            local = []
            for lane in LANES:
                values, targets = metrics(builds, grid, hit, cost, first, stable, lane)
                row = {"operator": operator, "dataset": dataset, "lane": lane, **values}
                summary.append(row)
                local.append(row)
                for target, vals in targets.items():
                    cc = np.asarray(vals["cost"], dtype=float)
                    target_rows.append({
                        "operator": operator,
                        "dataset": dataset,
                        "lane": lane,
                        "target_build": target,
                        "absolute_risk": float(np.mean(vals["abs"])),
                        "reference_risk": float(np.mean(vals["ref"])),
                        "incremental_risk": float(np.mean(vals["inc"])),
                        "target_ndc_mean": float(np.mean(cc)) if cc.size else "NOT_ESTIMABLE",
                        "target_ndc_p95": float(np.quantile(cc, 0.95)) if cc.size else "NOT_ESTIMABLE",
                    })
            decisions.append({"operator": operator, "dataset": dataset, "decision": setting_label(local)})
    overall = "MIXED_BY_IMPLEMENTATION_DATASET"
    labels = {d["decision"] for d in decisions}
    if labels == {"BROAD_PORTABILITY_GAP_PERSISTS"}:
        overall = "BROAD_PORTABILITY_GAP_PERSISTS"
    elif all(x in {"SLACK_ABSORBS_MOST_FAILURE_RISK_ONLY", "SLACK_REDUCES_RISK_WITH_UNRESOLVED_OR_MATERIAL_COST"} for x in labels):
        overall = "SLACK_REDUCES_RISK_ACROSS_SETTINGS"
    write_csv(args.output / "s1_slack_summary.csv", summary)
    write_csv(args.output / "s1_per_target.csv", target_rows)
    write_csv(args.output / "s1_semantic_diagnostics.csv", diagnostic_rows)
    write_csv(args.output / "s1_input_inventory.csv", inventory)
    payload = {
        "phase": "S1",
        "evidence_level": "POST_HOC_FROZEN_RESPONSE_REANALYSIS",
        "bootstrap": {"unit": "shared query with complete directed-pair vector", "replicates": 5000, "seed": 991},
        "per_setting": decisions,
        "overall_decision": overall,
        "prohibitions": ["no new ANN search", "no index build", "ef is not NDC", "Faiss NDC remains not estimable"],
    }
    (args.output / "s1_decision.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
