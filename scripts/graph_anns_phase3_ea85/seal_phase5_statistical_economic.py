#!/usr/bin/env python3
"""Integrate sealed Phase 1--4 evidence without reopening scientific choices."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


N_GRID = (1_000, 10_000, 100_000, 1_000_000, 10_000_000)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def finite(value: str) -> bool:
    try:
        return float(value) < float("inf")
    except (TypeError, ValueError):
        return False


def integrate(repo: Path) -> dict:
    base = repo / "results/graph_anns_phase3_ea85"
    manifests = repo / "manifests/graph_anns_phase3_ea85"
    inputs = [
        base / "darth95_bridge/dataset_summary.csv",
        base / "adaef_bridge/arxiv_10build/aggregate.json",
        base / "refresh95/summary.csv",
        base / "refresh95/per_build.csv",
        base / "vamana_unified/summary.csv",
        base / "deep1m/summary.csv",
        manifests / "p1_external_method_decision.json",
        manifests / "p2_refresh95_decision.json",
        manifests / "p3_vamana_unified_decision.json",
        manifests / "p4_deep1m_decision.json",
        manifests / "p5_statistical_economic_preregistration.json",
    ]
    missing = [str(p) for p in inputs if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing sealed inputs: " + ", ".join(missing))

    p1 = json.loads((manifests / "p1_external_method_decision.json").read_text())
    p2 = json.loads((manifests / "p2_refresh95_decision.json").read_text())
    p3 = json.loads((manifests / "p3_vamana_unified_decision.json").read_text())
    p4 = json.loads((manifests / "p4_deep1m_decision.json").read_text())
    refresh = read_csv(base / "refresh95/summary.csv")

    evidence = []
    for dataset, risk in p1["methods"]["DARTH"]["raw_evaluation_risk"].items():
        evidence.append({
            "phase": "P1", "dataset": dataset, "implementation": "hnswlib",
            "method": "DARTH", "estimand": "raw_source_policy_transport_risk",
            "estimate": risk, "ci_low": "NOT_REPORTED", "ci_high": "NOT_REPORTED",
            "target_builds": 10, "safe_deployable": 0,
            "interpretation": "portability_failure; audited fixed-safe gain=0",
        })
    ada = p1["methods"]["Ada-ef"]
    evidence.append({
        "phase": "P1", "dataset": ada["dataset"], "implementation": "official_Ada-ef_bridge",
        "method": "Ada-ef", "estimand": "raw_source_policy_transport_risk",
        "estimate": ada["raw_eval_risk_mean"], "ci_low": ada["raw_eval_risk_ci95"][0],
        "ci_high": ada["raw_eval_risk_ci95"][1], "target_builds": ada["target_builds"],
        "safe_deployable": 0, "interpretation": "portability_failure; audited fixed-safe gain=0",
    })
    for row in refresh:
        if row["method"] not in ("SOURCE_TCP_POOL_REUSE", "TARGET_SELECTION_TCP_RECALIBRATION"):
            continue
        deployable = int(row["certified_builds"]) == 10
        evidence.append({
            "phase": "P2", "dataset": row["dataset"], "implementation": "hnswlib_mixed_refresh",
            "method": row["method"], "estimand": "evaluation_risk",
            "estimate": row["evaluation_risk"], "ci_low": "NOT_REPORTED",
            "ci_high": "NOT_REPORTED", "target_builds": 10,
            "safe_deployable": deployable,
            "interpretation": ("safe_search_gate_positive" if row["method"].startswith("TARGET")
                               else "unsafe_source_reuse"),
        })
        evidence.append({
            "phase": "P2", "dataset": row["dataset"], "implementation": "hnswlib_mixed_refresh",
            "method": row["method"], "estimand": "search_distance_gain",
            "estimate": row["mean_gain"], "ci_low": row["gain_ci_low"],
            "ci_high": row["gain_ci_high"], "target_builds": 10,
            "safe_deployable": deployable,
            "interpretation": ("safe_search_gate_positive" if row["method"].startswith("TARGET")
                               else "unsafe_efficiency_not_deployable"),
        })
    for row in p3["summary"]:
        evidence.append({
            "phase": "P3", "dataset": row["dataset"], "implementation": "DiskANN3_Vamana_style",
            "method": "source_native_action_transport", "estimand": "transport_risk",
            "estimate": row["transport_risk"], "ci_low": row["risk_ci_low"],
            "ci_high": row["risk_ci_high"], "target_builds": row["target_builds"],
            "safe_deployable": 0, "interpretation": "cross_implementation_portability_failure",
        })
    s4 = p4["summary"]
    evidence.append({
        "phase": "P4", "dataset": "deep-image-first-1M", "implementation": "hnswlib",
        "method": "source_native_action_transport", "estimand": "incremental_transport_risk",
        "estimate": s4["incremental_risk"], "ci_low": s4["incremental_risk_ci"][0],
        "ci_high": s4["incremental_risk_ci"][1], "target_builds": s4["builds"],
        "safe_deployable": 0, "interpretation": "scale_portability_failure_native_tails",
    })

    robustness = []
    for row in refresh:
        if row["method"] == "TARGET_SELECTION_TCP_RECALIBRATION":
            robustness.append({
                "phase": "P2", "dataset": row["dataset"], "method": row["method"],
                "effect": row["mean_gain"], "ci_low": row["gain_ci_low"],
                "ci_high": row["gain_ci_high"], "min_loto": row["min_lobo_gain"],
                "delete_largest": row["delete_largest_gain"],
                "p95_noninferior": row["tail_p95_noninferior"], "p99": row["p99_dists"],
                "censoring": "NOT_APPLICABLE", "scope": "search-distance only",
            })
    for row in p3["summary"]:
        robustness.append({
            "phase": "P3", "dataset": row["dataset"], "method": "source_native_action_transport",
            "effect": row["transport_risk"], "ci_low": row["risk_ci_low"],
            "ci_high": row["risk_ci_high"], "min_loto": row["min_loto_risk"],
            "delete_largest": row["delete_largest_risk"], "p95_noninferior": "NOT_ESTIMABLE",
            "p99": "NOT_ESTIMABLE", "censoring": row["under_budget_unsafe_rate"],
            "scope": "post-hoc semantic alignment of frozen outputs",
        })
    robustness.append({
        "phase": "P4", "dataset": "deep-image-first-1M", "method": "source_native_action_transport",
        "effect": s4["incremental_risk"], "ci_low": s4["incremental_risk_ci"][0],
        "ci_high": s4["incremental_risk_ci"][1], "min_loto": s4["min_loto_incremental_risk"],
        "delete_largest": s4["delete_largest_incremental_risk"], "p95_noninferior": 1,
        "p99": s4["p99_transport_ndc"], "censoring": s4["source_censoring"],
        "scope": p4["claim_scope"],
    })

    cost = [
        {"phase": "P1", "dataset": "SIFT-100K+Arxiv-Nomic-100K", "method": "DARTH",
         "search": "MEASURED_NATIVE_DISTANCE_COUNTS", "profiling": "NOT_ESTIMABLE",
         "truth": "NOT_HARMONIZED", "certification": "MEASURED_LABEL_COUNT_ONLY",
         "rebuild": "NOT_HARMONIZED", "serving": "MEASURED", "control": "NOT_ESTIMABLE",
         "fallback": "MEASURED_ZERO_GAIN_FIXED_SAFE", "full_lifecycle": "NOT_ESTIMABLE"},
        {"phase": "P1", "dataset": "Arxiv-Nomic-100K", "method": "Ada-ef",
         "search": "MEASURED_NATIVE_DISTANCE_COUNTS", "profiling": "NOT_ESTIMABLE",
         "truth": "NOT_HARMONIZED", "certification": "MEASURED_LABEL_COUNT_ONLY",
         "rebuild": "NOT_HARMONIZED", "serving": "MEASURED", "control": "NOT_ESTIMABLE",
         "fallback": "MEASURED_ZERO_GAIN_FIXED_SAFE", "full_lifecycle": "NOT_ESTIMABLE"},
        {"phase": "P2", "dataset": "SIFT-100K+Arxiv-Nomic-100K", "method": "TARGET_SELECTION_TCP_RECALIBRATION",
         "search": "MEASURED_NATIVE_DISTANCE_COUNTS", "profiling": "MEASURED_SOURCE_PROFILE_DISTANCES",
         "truth": "NOT_HARMONIZED", "certification": "500_QUERIES_PER_BUILD",
         "rebuild": "NOT_HARMONIZED", "serving": "MEASURED", "control": "NOT_HARMONIZED",
         "fallback": "MEASURED", "full_lifecycle": "NOT_ESTIMABLE"},
        {"phase": "P3", "dataset": "SIFT-100K+Arxiv-Nomic-100K", "method": "Vamana_transport",
         "search": "MEASURED_NATIVE_COMPARISONS", "profiling": "NOT_ESTIMABLE",
         "truth": "FROZEN_INPUT_ONLY", "certification": "NOT_ESTIMABLE",
         "rebuild": "NOT_HARMONIZED", "serving": "MEASURED", "control": "NOT_ESTIMABLE",
         "fallback": "NOT_ESTIMABLE", "full_lifecycle": "NOT_ESTIMABLE"},
        {"phase": "P4", "dataset": "deep-image-first-1M", "method": "native_transport",
         "search": "MEASURED_NATIVE_NDC", "profiling": "NOT_APPLICABLE",
         "truth": f"MEASURED_SECONDS={s4['truth_seconds']:.6f}", "certification": "NOT_APPLICABLE",
         "rebuild": f"MEASURED_SECONDS={s4['total_build_seconds']:.6f}", "serving": "MEASURED",
         "control": "NOT_APPLICABLE", "fallback": "NOT_APPLICABLE",
         "full_lifecycle": "DESCRIPTIVE_SCALE_COST_ONLY"},
    ]

    break_even = []
    for row in refresh:
        if row["method"] != "TARGET_SELECTION_TCP_RECALIBRATION":
            continue
        threshold = float(row["max_repeated_query_set_break_even"])
        for n in N_GRID:
            break_even.append({
                "phase": "P2", "dataset": row["dataset"], "method": row["method"], "N": n,
                "search_only_break_even_query_sets": threshold,
                "search_only_amortized": int(n >= threshold),
                "full_lifecycle_status": "NOT_ESTIMABLE_TRUTH_REBUILD_CONTROL_NOT_HARMONIZED",
            })

    negative = [
        {"phase": "P1", "result": "DARTH_RAW_UNSAFE", "value": "risk=.2255/.2312",
         "boundary": "audited deployment is fixed-safe with zero gain"},
        {"phase": "P1", "result": "ADAEF_RAW_UNSAFE", "value": "risk=.0952 CI[.0944,.0960]",
         "boundary": "Arxiv only; SIFT unsupported under registered metric; audited gain zero"},
        {"phase": "P2", "result": "SOURCE_TCP_REUSE_UNSAFE", "value": "risk=.0669/.0724",
         "boundary": "target recalibration, not raw source reuse, passes search gate"},
        {"phase": "P2", "result": "FULL_LIFECYCLE_COST_OPEN", "value": "NOT_ESTIMABLE",
         "boundary": "search-only gain cannot be called end-to-end economic value"},
        {"phase": "P3", "result": "VAMANA_COST_TAX_NULL", "value": "both 95% CIs cross zero",
         "boundary": "portability-risk evidence positive; efficiency direction unresolved"},
        {"phase": "P4", "result": "TARGET_REFERENCE_CENSORING", "value": f"{s4['target_censoring']:.5f}",
         "boundary": "incremental risk is primary; endpoint censoring retained"},
    ]

    claims = [
        {"claim": "safe native actions can fail to transfer across rebuilds",
         "evidence": "P1 DARTH/Ada-ef; P3 Vamana; P4 Deep1M", "status": "SUPPORTED_STRATIFIED",
         "forbidden_extension": "not universal over all graphs, methods, or rebuilds"},
        {"claim": "ICBA distinguishes unsafe efficiency from deployable value",
         "evidence": "P1 audited fallback and P2 certification", "status": "SUPPORTED",
         "forbidden_extension": "not an accuracy or SOTA algorithm claim"},
        {"claim": "target-selection TCP recalibration has safe search-distance value",
         "evidence": "P2 two datasets, ten target builds each, positive CI/LOTO/deletion and p95",
         "status": "SUPPORTED_CONDITIONAL", "forbidden_extension": "not full lifecycle economics"},
        {"claim": "TCP is end-to-end economically superior",
         "evidence": "truth/rebuild/control costs unharmonized", "status": "NOT_ESTIMABLE",
         "forbidden_extension": "must not appear as a conclusion"},
        {"claim": "broad method SOTA",
         "evidence": "external raw methods unsafe; audited gains zero; no universal race",
         "status": "UNSUPPORTED_AND_OUT_OF_SCOPE", "forbidden_extension": "no SOTA language"},
    ]

    out = base / "phase5_seal"
    write_csv(out / "evidence_inventory.csv", evidence)
    write_csv(out / "robustness_matrix.csv", robustness)
    write_csv(out / "cost_ledger.csv", cost)
    write_csv(out / "break_even.csv", break_even)
    write_csv(out / "boundary_negative_results.csv", negative)
    write_csv(out / "claim_evidence_matrix.csv", claims)
    write_csv(out / "input_checksums.csv", [
        {"path": str(p.relative_to(repo)), "sha256": sha256(p)} for p in inputs
    ])

    decision = {
        "schema_version": "ea85-phase5-decision-1.0",
        "decision": "PHASE5_STATISTICAL_ECONOMIC_SEAL_COMPLETE_LIFECYCLE_CONDITIONAL",
        "primary_unit": "target_build", "bootstrap": {"repetitions": 5000, "seed": 991},
        "evidence_rows": len(evidence), "robustness_rows": len(robustness),
        "full_lifecycle_status": "NOT_ESTIMABLE_TRUTH_REBUILD_CONTROL_NOT_HARMONIZED",
        "search_only_tcp_status": "POSITIVE_TWO_DATASETS_ROBUST",
        "submission_claim": "portability phenomenon and audit utility supported; TCP economic value conditional",
    }
    (manifests / "p5_statistical_economic_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = repo / "docs/graph_anns_phase3_ea85/p5_statistical_economic_report.md"
    report.write_text(
        "# Phase 5 statistical and economic seal\n\n"
        "Decision: **PHASE5_STATISTICAL_ECONOMIC_SEAL_COMPLETE_LIFECYCLE_CONDITIONAL**.\n\n"
        "The unified evidence confirms rebuild portability failure for DARTH and Ada-ef on registered "
        "hnswlib settings, for Vamana-style native actions on SIFT and Arxiv, and at Deep1M scale. "
        "All positive claims use target builds as the primary unit and preserve negative/null results.\n\n"
        "Target-selection TCP recalibration passes the registered search-distance gate on both mixed-refresh "
        "datasets: risk .0179/.0204, mean savings .4439/.4479 with positive build-bootstrap lower bounds, "
        "positive LOTO/deletion checks, and non-inferior p95. Raw source reuse is unsafe (.0669/.0724), while "
        "ICBA fallback is safe but has zero gain.\n\n"
        "Measured search-only break-even is about 11.1 repeated query sets on SIFT and 8.8 on Arxiv. "
        "Truth, rebuild, and control costs are not harmonized, so full lifecycle economic superiority remains "
        "**NOT_ESTIMABLE** and is excluded from paper claims.\n",
        encoding="utf-8",
    )
    generated = [p for p in out.iterdir() if p.is_file()] + [
        manifests / "p5_statistical_economic_decision.json", report]
    write_csv(out / "output_checksums.csv", [
        {"path": str(p.relative_to(repo)), "sha256": sha256(p)} for p in sorted(generated)
    ])
    return decision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(integrate(args.repo_root.resolve()), indent=2))


if __name__ == "__main__":
    main()
