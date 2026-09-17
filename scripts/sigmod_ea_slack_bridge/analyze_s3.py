#!/usr/bin/env python3
"""S3 post-hoc role-limited source-policy bridge on frozen response cubes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import beta

from analyze_s1 import DATASETS, GRIDS, cube, load_faiss, load_hnsw, write_csv
from analyze_s2 import three_state

SEED = 991
DELTA = 0.05
ALPHA = 0.05
LANES = ("source_selected_plus_0", "source_selected_plus_1", "source_selected_plus_2", "endpoint")


def upper_cp(k, n, alpha):
    return 1.0 if k == n else float(beta.ppf(1.0 - alpha, k + 1, n - k))


def role_manifest():
    perm = np.random.default_rng(SEED).permutation(750)
    roles = {
        "source_certification": sorted(map(int, perm[:375])),
        "bridge_holdout_unused": sorted(map(int, perm[375:469])),
        "target_evaluation": sorted(map(int, perm[469:])),
    }
    hashes = {
        role: hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
        for role, ids in roles.items()
    }
    return roles, hashes


def bootstrap(values, reps=5000, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(values)
    draws = np.empty(reps)
    for i in range(reps):
        draws[i] = np.mean(values[rng.integers(0, n, n)])
    return tuple(map(float, np.quantile(draws, (0.025, 0.975))))


def select_source_actions(hit, grid, cert_idx):
    out = []
    local_alpha = ALPHA / len(grid)
    for bi in range(hit.shape[0]):
        fails = np.sum(hit[bi, cert_idx, :] < 10, axis=0)
        ucbs = np.asarray([upper_cp(int(k), len(cert_idx), local_alpha) for k in fails])
        eligible = np.where(ucbs <= DELTA)[0]
        if len(eligible):
            chosen = int(eligible[0])
            status = "SOURCE_QUALIFIED"
        else:
            chosen = len(grid) - 1
            status = "NO_SOURCE_QUALIFIED_ACTION_ENDPOINT_FALLBACK"
        out.append((chosen, status, fails, ucbs))
    return out


def analyze_setting(operator, dataset, records, grid, roles):
    builds, queries, hit, cost = cube(records, grid)
    qmap = {q: i for i, q in enumerate(queries)}
    cert_idx = np.asarray([qmap[q] for q in roles["source_certification"]])
    eval_idx = np.asarray([qmap[q] for q in roles["target_evaluation"]])
    selections = select_source_actions(hit, grid, cert_idx)
    source_rows = []
    for bi, (chosen, status, fails, ucbs) in enumerate(selections):
        source_rows.append(
            {
                "operator": operator,
                "dataset": dataset,
                "source_build": builds[bi],
                "chosen_action": int(grid[chosen]),
                "chosen_index": chosen,
                "source_certification_failures": int(fails[chosen]),
                "source_certification_n": len(cert_idx),
                "source_certification_ucb_bonferroni": float(ucbs[chosen]),
                "decision": status,
            }
        )
    pair_rows = []
    summary_rows = []
    for lane in LANES:
        per_query = [[] for _ in eval_idx]
        per_build_pair = {}
        all_costs = []
        all_fails = []
        for si, source in enumerate(builds):
            chosen, status, source_fails, source_ucbs = selections[si]
            shift = 0 if lane.endswith("plus_0") else 1 if lane.endswith("plus_1") else 2
            executed = len(grid) - 1 if lane == "endpoint" else min(chosen + shift, len(grid) - 1)
            for ti, target in enumerate(builds):
                if si == ti:
                    continue
                failures = hit[ti, eval_idx, executed] < 10
                k, n = int(np.sum(failures)), len(eval_idx)
                state, low, up = three_state(k, n, 0.05)
                costs = cost[ti, eval_idx, executed]
                finite_cost = costs[np.isfinite(costs)]
                for qi, failure in enumerate(failures):
                    per_query[qi].append(int(failure))
                per_build_pair[(si, ti)] = failures.astype(float)
                all_fails.extend(failures.astype(int))
                if finite_cost.size:
                    all_costs.extend(finite_cost)
                pair_rows.append(
                    {
                        "operator": operator,
                        "dataset": dataset,
                        "lane": lane,
                        "source_build": source,
                        "target_build": target,
                        "source_decision": status,
                        "selected_action": int(grid[chosen]),
                        "executed_action": int(grid[executed]),
                        "source_certification_failures": int(source_fails[chosen]),
                        "source_certification_n": len(cert_idx),
                        "source_certification_ucb_bonferroni": float(source_ucbs[chosen]),
                        "target_evaluation_failures": k,
                        "target_evaluation_n": n,
                        "target_evaluation_risk": k / n,
                        "target_evaluation_cp_lower": low,
                        "target_evaluation_cp_upper": up,
                        "target_evaluation_state": state,
                        "ndc_status": "ESTIMABLE" if finite_cost.size else "NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE",
                        "target_ndc_mean": float(np.mean(finite_cost)) if finite_cost.size else "NOT_ESTIMABLE",
                        "target_ndc_p95": float(np.quantile(finite_cost, 0.95)) if finite_cost.size else "NOT_ESTIMABLE",
                    }
                )
        qvalues = np.asarray([np.mean(v) for v in per_query])
        ci_low, ci_high = bootstrap(qvalues)
        drop = max(1, math.ceil(0.01 * len(qvalues)))
        trimmed = np.delete(qvalues, np.argsort(qvalues)[-drop:])
        lobo = []
        for dropped in range(len(builds)):
            vals = [v for (si, ti), v in per_build_pair.items() if si != dropped and ti != dropped]
            lobo.append(float(np.mean(np.concatenate(vals))))
        lane_pairs = [r for r in pair_rows if r["lane"] == lane]
        states = [r["target_evaluation_state"] for r in lane_pairs]
        summary_rows.append(
            {
                "operator": operator,
                "dataset": dataset,
                "lane": lane,
                "directed_pairs": len(lane_pairs),
                "source_qualified_builds": sum(r["decision"] == "SOURCE_QUALIFIED" for r in source_rows),
                "source_endpoint_fallback_builds": sum(r["decision"] != "SOURCE_QUALIFIED" for r in source_rows),
                "target_risk": float(np.mean(all_fails)),
                "target_risk_ci_low": ci_low,
                "target_risk_ci_high": ci_high,
                "target_qualified_pairs": states.count("QUALIFIED"),
                "target_indeterminate_pairs": states.count("INDETERMINATE"),
                "target_confidently_above_delta_pairs": states.count("CONFIDENTLY_ABOVE_DELTA"),
                "delete_max_1pct_query_risk": float(np.mean(trimmed)),
                "lobo_min_risk": min(lobo),
                "lobo_max_risk": max(lobo),
                "ndc_status": "ESTIMABLE" if all_costs else "NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE",
                "target_ndc_mean": float(np.mean(all_costs)) if all_costs else "NOT_ESTIMABLE",
                "target_ndc_p95": float(np.quantile(all_costs, 0.95)) if all_costs else "NOT_ESTIMABLE",
            }
        )
    return source_rows, pair_rows, summary_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hnsw-root", type=Path, required=True)
    ap.add_argument("--faiss-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    roles, hashes = role_manifest()
    role_doc = {
        "seed": SEED,
        "evidence_level": "POST_HOC_ROLE_LIMITED",
        "roles": roles,
        "role_sha256": hashes,
        "pairwise_overlap": {
            "source_certification_bridge_holdout": 0,
            "source_certification_target_evaluation": 0,
            "bridge_holdout_target_evaluation": 0,
        },
        "historical_truth_status": "ALL_750_OUTCOMES_PREVIOUSLY_INSPECTED_IN_PRIOR_PROJECT_STAGES",
    }
    (args.output / "s3_query_role_manifest.json").write_text(json.dumps(role_doc, indent=2) + "\n")
    source_rows, pair_rows, summary_rows = [], [], []
    for operator in ("hnswlib", "faiss_hnsw"):
        for dataset in DATASETS:
            if operator == "hnswlib":
                _, records, _ = load_hnsw(args.hnsw_root, dataset)
            else:
                _, records, _ = load_faiss(args.faiss_root, dataset)
            s, p, a = analyze_setting(operator, dataset, records, GRIDS[operator], roles)
            source_rows.extend(s)
            pair_rows.extend(p)
            summary_rows.extend(a)
    write_csv(args.output / "s3_source_policy.csv", source_rows)
    write_csv(args.output / "s3_pair_replay.csv", pair_rows)
    write_csv(args.output / "s3_summary.csv", summary_rows)
    decision = {
        "phase": "S3",
        "evidence_level": "POST_HOC_ROLE_LIMITED",
        "role_firewall_within_analysis": "PASS",
        "prospective_independence": "FAIL_PREVIOUSLY_INSPECTED_QUERY_OUTCOMES",
        "target_driven_selection": False,
        "bridge_gate": "PASS_AS_MECHANISM_BRIDGE_ONLY",
    }
    (args.output / "s3_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
