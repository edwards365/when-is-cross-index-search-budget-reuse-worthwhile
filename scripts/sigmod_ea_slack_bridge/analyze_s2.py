#!/usr/bin/env python3
"""S2: finite-grid stable-tail implication and certification semantics."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta

from analyze_s1 import (
    DATASETS,
    GRIDS,
    LANES,
    action_indices,
    cube,
    label_indices,
    load_faiss,
    load_hnsw,
    write_csv,
)


DELTA = 0.05


def cp_bounds(k: int, n: int, alpha: float) -> tuple[float, float]:
    if not (0 <= k <= n and n > 0 and 0 < alpha < 1):
        raise ValueError("invalid binomial inputs")
    lower = 0.0 if k == 0 else float(beta.ppf(alpha, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(1.0 - alpha, k + 1, n - k))
    return lower, upper


def three_state(k: int, n: int, alpha: float, delta: float = DELTA) -> tuple[str, float, float]:
    lower, upper = cp_bounds(k, n, alpha)
    if upper <= delta:
        state = "QUALIFIED"
    elif lower > delta:
        state = "CONFIDENTLY_ABOVE_DELTA"
    else:
        state = "INDETERMINATE"
    return state, lower, upper


def analyze_setting(operator, dataset, records, grid):
    builds, queries, hit, cost = cube(records, grid)
    first, stable, nonmono = label_indices(hit)
    pair_rows = []
    implication_violations = 0
    implication_antecedents = 0
    for lane in LANES:
        acts_by_source = action_indices(lane, first, stable, len(grid) - 1)
        for si, source in enumerate(builds):
            acts = acts_by_source[si]
            qq = np.arange(len(queries))
            source_fail = hit[si, qq, acts] < 10
            for ti, target in enumerate(builds):
                if si == ti:
                    continue
                target_fail = hit[ti, qq, acts] < 10
                target_reference_fail = first[ti] < 0
                target_stable = stable[ti]
                finite_antecedent = (target_stable >= 0) & (acts >= target_stable)
                violations = target_fail & finite_antecedent
                implication_antecedents += int(np.sum(finite_antecedent))
                implication_violations += int(np.sum(violations))
                stable_gap = (target_stable < 0) | (acts < target_stable)
                k = int(np.sum(target_fail))
                n = len(queries)
                single_state, single_low, single_up = three_state(k, n, 0.05)
                family_state, family_low, family_up = three_state(k, n, 0.025)
                pair_rows.append(
                    {
                        "operator": operator,
                        "dataset": dataset,
                        "lane": lane,
                        "source_build": source,
                        "target_build": target,
                        "target_failures": k,
                        "n": n,
                        "source_failures": int(np.sum(source_fail)),
                        "target_reference_failures": int(np.sum(target_reference_fail)),
                        "stable_gap_events": int(np.sum(stable_gap)),
                        "implication_antecedents": int(np.sum(finite_antecedent)),
                        "implication_violations": int(np.sum(violations)),
                        "single_alpha": 0.05,
                        "single_cp_lower": single_low,
                        "single_cp_upper": single_up,
                        "single_state": single_state,
                        "family_candidate_alpha": 0.025,
                        "family_endpoint_alpha": 0.025,
                        "family_cp_lower": family_low,
                        "family_cp_upper": family_up,
                        "family_state": family_state,
                    }
                )
    summary = []
    for lane in LANES:
        subset = [r for r in pair_rows if r["lane"] == lane]
        for prefix in ("single", "family"):
            states = [r[f"{prefix}_state"] for r in subset]
            summary.append(
                {
                    "operator": operator,
                    "dataset": dataset,
                    "lane": lane,
                    "allocation": "alpha_0.05" if prefix == "single" else "alpha_candidate_0.025_endpoint_0.025",
                    "directed_pairs": len(subset),
                    "qualified_pairs": states.count("QUALIFIED"),
                    "indeterminate_pairs": states.count("INDETERMINATE"),
                    "confidently_above_delta_pairs": states.count("CONFIDENTLY_ABOVE_DELTA"),
                    "pooled_target_failures": sum(r["target_failures"] for r in subset),
                    "pooled_n": sum(r["n"] for r in subset),
                    "pooled_source_failures": sum(r["source_failures"] for r in subset),
                    "pooled_reference_failures": sum(r["target_reference_failures"] for r in subset),
                    "pooled_stable_gap_events": sum(r["stable_gap_events"] for r in subset),
                    "implication_violations": sum(r["implication_violations"] for r in subset),
                }
            )
    audit = {
        "operator": operator,
        "dataset": dataset,
        "builds": len(builds),
        "queries": len(queries),
        "raw_nonmonotone_fraction": float(np.mean(nonmono)),
        "finite_grid_implication_antecedents": implication_antecedents,
        "finite_grid_implication_violations": implication_violations,
        "status": "PASS" if implication_violations == 0 else "FAIL",
    }
    return pair_rows, summary, audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hnsw-root", type=Path, required=True)
    ap.add_argument("--faiss-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pair_rows, summary_rows, audits = [], [], []
    for operator in ("hnswlib", "faiss_hnsw"):
        for dataset in DATASETS:
            if operator == "hnswlib":
                _, records, _ = load_hnsw(args.hnsw_root, dataset)
            else:
                _, records, _ = load_faiss(args.faiss_root, dataset)
            p, s, a = analyze_setting(operator, dataset, records, GRIDS[operator])
            pair_rows.extend(p)
            summary_rows.extend(s)
            audits.append(a)
    write_csv(args.output / "s2_certificate_pairs.csv", pair_rows)
    write_csv(args.output / "s2_certificate_summary.csv", summary_rows)
    write_csv(args.output / "s2_implication_audit.csv", audits)
    theory = [
        {
            "item": "T-S2-1 finite-grid stable-tail implication",
            "status": "PROVED_UNDER_STATED_ASSUMPTIONS",
            "scope": "finite registered action grid; deterministic response cube",
        },
        {
            "item": "T-S2-2 one-sided Clopper-Pearson three-state rule",
            "status": "CLASSICAL_APPLICATION",
            "scope": "query-sampling model within each frozen directed build pair",
        },
        {
            "item": "T-S2-3 stable-gap upper-bound contact",
            "status": "EMPIRICAL_CONTACT",
            "scope": "frozen SIFT-100K and Arxiv-Nomic-100K response cubes",
        },
        {
            "item": "native ef universal guarantee",
            "status": "NOT_INSTANTIATED",
            "scope": "not implied by finite-grid response semantics",
        },
    ]
    write_csv(args.output / "s2_theory_contact.csv", theory)
    decision = {
        "phase": "S2",
        "evidence_level": "POST_HOC_FROZEN_RESPONSE_REANALYSIS",
        "delta": DELTA,
        "single_policy_alpha": 0.05,
        "family_allocation": {"candidate_alpha": 0.025, "endpoint_alpha": 0.025},
        "finite_grid_implication": "PASS" if all(a["status"] == "PASS" for a in audits) else "FAIL",
        "certification_semantics": ["QUALIFIED", "INDETERMINATE", "CONFIDENTLY_ABOVE_DELTA"],
        "theory_gate": "PASS" if all(a["status"] == "PASS" for a in audits) else "FAIL",
    }
    (args.output / "s2_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
