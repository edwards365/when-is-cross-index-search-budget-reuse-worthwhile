#!/usr/bin/env python3
"""S4 target-stage lifecycle NDC and bounded wall-clock analysis."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


GRID = (16, 32, 64, 128, 256, 512)
N_GRID = (1_000, 10_000, 100_000, 1_000_000, 10_000_000)
REPS = 5000
SEED = 991
TRUTH_NDC = 100_000 * 500


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_raw(raw: Path, dataset: str):
    result = {}
    for path in sorted(raw.glob(f"{dataset}*.csv.gz")):
        with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        build = rows[0]["build"]
        cube = defaultdict(lambda: {"ndc": 0.0, "wall_ns": 0.0, "count": 0})
        for row in rows:
            key = (row["role"], int(row["ef"]))
            cube[key]["ndc"] += float(row["ndc"])
            cube[key]["wall_ns"] += float(row["wall_ns"])
            cube[key]["count"] += 1
        result[build] = cube
    if len(result) != 24:
        raise RuntimeError(f"expected 24 raw target builds for {dataset}, got {len(result)}")
    return result


def bootstrap_target(rows, value_fn):
    rng = np.random.default_rng(SEED)
    n = len(rows)
    draws = np.empty(REPS)
    for rep in range(REPS):
        chosen = rng.integers(0, n, n)
        draws[rep] = value_fn([rows[i] for i in chosen])
    point = value_fn(rows)
    return point, float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def analyze_dataset(dataset, raw, pairs):
    pair_rows = []
    for row in pairs:
        target = row["target_build"]
        candidate = int(row["candidate_action"])
        endpoint = GRID[-1]
        executed = int(row["executed_action"])
        required = sorted({candidate, endpoint})
        cert_ndc = sum(raw[target][("target_certification", action)]["ndc"] for action in required)
        cert_wall = sum(raw[target][("target_certification", action)]["wall_ns"] for action in required)
        eval_exec = raw[target][("target_evaluation", executed)]
        eval_endpoint = raw[target][("target_evaluation", endpoint)]
        saving = (eval_endpoint["ndc"] - eval_exec["ndc"]) / eval_exec["count"]
        wall_saving = (eval_endpoint["wall_ns"] - eval_exec["wall_ns"]) / eval_exec["count"]
        overhead = TRUTH_NDC + cert_ndc
        pair_rows.append({
            "dataset": dataset,
            "source_build": row["source_build"],
            "target_build": target,
            "candidate_action": candidate,
            "executed_action": executed,
            "required_cert_actions": ";".join(map(str, required)),
            "truth_ndc": TRUTH_NDC,
            "certification_search_ndc": cert_ndc,
            "target_stage_overhead_ndc": overhead,
            "serving_saving_ndc_per_query": saving,
            "pairwise_break_even_queries": overhead / saving if saving > 0 else "INF",
            "certification_search_wall_ns": cert_wall,
            "serving_wall_saving_ns_per_query": wall_saving,
            "search_only_wall_break_even_queries": cert_wall / wall_saving if wall_saving > 0 else "INF",
            "full_wall_lifecycle_status": "NOT_ESTIMABLE_EXACT_TRUTH_WALL_TIME_MISSING",
        })

    target_rows = []
    targets = sorted(raw)
    for target in targets:
        local = [r for r in pair_rows if r["target_build"] == target]
        actions = sorted({int(a) for r in local for a in r["required_cert_actions"].split(";")})
        cert_ndc = sum(raw[target][("target_certification", action)]["ndc"] for action in actions)
        cert_wall = sum(raw[target][("target_certification", action)]["wall_ns"] for action in actions)
        saving = sum(float(r["serving_saving_ndc_per_query"]) for r in local)
        wall_saving = sum(float(r["serving_wall_saving_ns_per_query"]) for r in local)
        overhead = TRUTH_NDC + cert_ndc
        target_rows.append({
            "dataset": dataset,
            "target_build": target,
            "source_directions": len(local),
            "unique_cert_actions": ";".join(map(str, actions)),
            "truth_ndc": TRUTH_NDC,
            "certification_search_ndc": cert_ndc,
            "shared_target_overhead_ndc": overhead,
            "aggregate_serving_saving_ndc_per_query_per_direction": saving,
            "shared_break_even_queries_per_direction": overhead / saving if saving > 0 else "INF",
            "certification_search_wall_ns": cert_wall,
            "aggregate_wall_saving_ns_per_query_per_direction": wall_saving,
            "search_only_wall_break_even_queries_per_direction": cert_wall / wall_saving if wall_saving > 0 else "INF",
        })

    horizon_rows = []
    for scenario in ("PAIRWISE_TARGET_CERTIFICATION", "SHARED_TARGET_CERTIFICATION_23_SOURCES"):
        for n_query in N_GRID:
            if scenario.startswith("PAIRWISE"):
                per_target = []
                for target in targets:
                    local = [r for r in pair_rows if r["target_build"] == target]
                    per_target.append({
                        "target_build": target,
                        "net": float(np.mean([n_query * float(r["serving_saving_ndc_per_query"]) - float(r["target_stage_overhead_ndc"]) for r in local])),
                    })
            else:
                per_target = [{
                    "target_build": r["target_build"],
                    "net": n_query * float(r["aggregate_serving_saving_ndc_per_query_per_direction"]) - float(r["shared_target_overhead_ndc"]),
                } for r in target_rows]
            point, low, high = bootstrap_target(per_target, lambda xs: float(np.mean([x["net"] for x in xs])))
            lobo = [float(np.mean([x["net"] for j, x in enumerate(per_target) if j != i])) for i in range(len(per_target))]
            delete_largest = float(np.mean([x["net"] for i, x in enumerate(per_target) if i != int(np.argmax([z["net"] for z in per_target]))]))
            horizon_rows.append({
                "dataset": dataset,
                "scenario": scenario,
                "N_queries_per_direction": n_query,
                "mean_net_ndc": point,
                "bootstrap_ci_low": low,
                "bootstrap_ci_high": high,
                "lobo_min": min(lobo),
                "delete_largest": delete_largest,
                "gate_positive": int(low > 0 and min(lobo) > 0 and delete_largest > 0),
            })

    summaries = []
    for scenario, rows, overhead_key, saving_key, be_key in [
        ("PAIRWISE_TARGET_CERTIFICATION", pair_rows, "target_stage_overhead_ndc", "serving_saving_ndc_per_query", "pairwise_break_even_queries"),
        ("SHARED_TARGET_CERTIFICATION_23_SOURCES", target_rows, "shared_target_overhead_ndc", "aggregate_serving_saving_ndc_per_query_per_direction", "shared_break_even_queries_per_direction"),
    ]:
        overhead = np.asarray([float(r[overhead_key]) for r in rows])
        saving = np.asarray([float(r[saving_key]) for r in rows])
        ratio = float(np.sum(overhead) / np.sum(saving))
        finite = [float(r[be_key]) for r in rows if r[be_key] != "INF"]
        passed = [r for r in horizon_rows if r["scenario"] == scenario and r["gate_positive"] == 1]
        summaries.append({
            "dataset": dataset,
            "scenario": scenario,
            "units": len(rows),
            "ratio_of_sums_break_even_queries": ratio,
            "max_finite_unit_break_even": max(finite),
            "nonamortizing_units": len(rows) - len(finite),
            "first_registered_positive_N": min(int(r["N_queries_per_direction"]) for r in passed) if passed else "NONE",
            "target_stage_ndc_status": "ESTIMABLE",
            "full_end_to_end_lifecycle_status": "NOT_ESTIMABLE_SOURCE_POLICY_ACQUISITION_NDC_MISSING",
            "wall_clock_status": "SEARCH_ONLY_EXPLORATORY_FULL_LIFECYCLE_NOT_ESTIMABLE",
        })
    return pair_rows, target_rows, horizon_rows, summaries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    prereg = root / "manifests/sigmod_ea_postseal_uplift_s4_preregistration.json"
    doc = json.loads(prereg.read_text(encoding="utf-8"))
    if doc["status"] != "PREREGISTERED_BEFORE_S4_COST_DERIVATION":
        raise RuntimeError("S4 is not preregistered")
    raw_root = root / "results/sigmod_ea_postseal_uplift/s3_raw_faiss"
    pairs = read_csv(root / "results/sigmod_ea_postseal_uplift/s3_analysis/s3_pair_results.csv")
    all_pair, all_target, all_horizon, all_summary = [], [], [], []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        raw = load_raw(raw_root, dataset)
        local_pairs = [r for r in pairs if r["dataset"] == dataset]
        p, t, h, s = analyze_dataset(dataset, raw, local_pairs)
        all_pair.extend(p); all_target.extend(t); all_horizon.extend(h); all_summary.extend(s)
    out = root / "results/sigmod_ea_postseal_uplift/s4_lifecycle"
    write_csv(out / "pairwise_cost_ledger.csv", all_pair)
    write_csv(out / "shared_target_cost_ledger.csv", all_target)
    write_csv(out / "horizon_summary.csv", all_horizon)
    write_csv(out / "dataset_summary.csv", all_summary)
    target_pass = all(r["first_registered_positive_N"] != "NONE" for r in all_summary)
    decision = {
        "schema_version": 1,
        "phase": "S4",
        "final_label": "S4_TARGET_STAGE_NDC_LIFECYCLE_GATE_PASSED_FULL_LIFECYCLE_NOT_ESTIMABLE" if target_pass else "S4_TARGET_STAGE_NDC_GATE_FAILED",
        "target_stage_ndc_gate": "PASS" if target_pass else "FAIL",
        "full_end_to_end_lifecycle": "NOT_ESTIMABLE_SOURCE_POLICY_ACQUISITION_NDC_MISSING",
        "wall_clock": "SEARCH_ONLY_EXPLORATORY_FULL_LIFECYCLE_NOT_ESTIMABLE_EXACT_TRUTH_WALL_TIME_MISSING",
        "datasets": all_summary,
        "new_query_or_truth_access": False,
        "new_index_builds": 0,
        "input_preregistration_sha256": sha256(prereg),
        "next_phase": "S5_NOT_STARTED_REQUIRES_USER_AUTHORIZATION",
    }
    manifest = root / "manifests/sigmod_ea_postseal_uplift_s4_decision.json"
    manifest.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    generated = [out / "pairwise_cost_ledger.csv", out / "shared_target_cost_ledger.csv", out / "horizon_summary.csv", out / "dataset_summary.csv", manifest]
    write_csv(out / "output_inventory.csv", [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in generated])
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
