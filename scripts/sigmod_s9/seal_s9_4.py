#!/usr/bin/env python3
"""Seal S9-4 attribution, external evidence, and unified gates."""

import argparse
import argparse
import csv
import json
from pathlib import Path

import pandas as pd


def external_matrix(root, runtime_summary, output):
    rows = []
    darth = pd.read_csv(root / "results/graph_anns_phase3_ea85/darth95_bridge/dataset_summary.csv")
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        raw = darth[(darth.dataset.eq(dataset)) & (darth.method.eq("raw_darth"))].iloc[0]
        audited = darth[(darth.dataset.eq(dataset)) & (darth.method.eq("icba_audited"))].iloc[0]
        rows.append({"family": "DARTH", "dataset": dataset, "implementation": "official_DARTH_hnswlib", "builds": 10, "design_queries": "method_native", "certification_queries": 500, "evaluation_queries": 1000, "raw_risk": raw.mean_eval_risk, "audited_risk": audited.mean_eval_risk, "audited_efficiency_gain": 0.0, "efficiency_endpoint": "distance_computations", "comparison_status": "NATIVE_ESTIMAND_CONTEXT_NOT_HEAD_TO_HEAD"})
    ada = json.loads((root / "results/graph_anns_phase3_ea85/adaef_bridge/arxiv_10build/aggregate.json").read_text())
    rows.append({"family": "Ada-ef", "dataset": "arxiv_nomic_100k", "implementation": "official_Ada-ef_cosine", "builds": 10, "design_queries": 2000, "certification_queries": 500, "evaluation_queries": 1000, "raw_risk": ada["intervals"]["raw_eval_risk"]["mean"], "audited_risk": ada["intervals"]["fixed_eval_risk"]["mean"], "audited_efficiency_gain": 0.0, "efficiency_endpoint": "distance_computations", "comparison_status": "NATIVE_ESTIMAND_CONTEXT_NOT_HEAD_TO_HEAD"})
    tcp = pd.read_csv(root / "results/graph_anns_phase3_ea85/refresh95/summary.csv")
    for dataset, source_name in (("sift_100k", "sift100k"), ("arxiv_nomic_100k", "arxiv_nomic_100k")):
        row = tcp[(tcp.dataset.eq(source_name)) & (tcp.method.eq("TARGET_SELECTION_TCP_RECALIBRATION"))].iloc[0]
        rows.append({"family": "TCP_target_recalibration", "dataset": dataset, "implementation": "registered_hnswlib_mixed_refresh", "builds": 10, "design_queries": "registered_target_selection", "certification_queries": "registered_disjoint", "evaluation_queries": "registered_disjoint", "raw_risk": row.evaluation_risk, "audited_risk": row.evaluation_risk, "audited_efficiency_gain": row.mean_gain, "efficiency_endpoint": "distance_computations", "comparison_status": "NATIVE_ESTIMAND_CONTEXT_NOT_HEAD_TO_HEAD"})
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        for arm, family in (("B1_FIXED_256_CERTIFIED", "fixed_256_certified"), ("B2_SOURCE_ONE_RUNG_CERTIFIED", "source_slack_certified"), ("B3_TARGET_GLOBAL_EQUAL_500", "target_global_equal_500"), ("B4_TARGET_GLOBAL_1000", "target_global_1000")):
            record = runtime_summary[dataset][arm]
            rows.append({"family": family, "dataset": dataset, "implementation": "Faiss_HNSW_1.8.0_S9_4", "builds": 8, "design_queries": 250 if arm == "B3_TARGET_GLOBAL_EQUAL_500" else (500 if arm == "B4_TARGET_GLOBAL_1000" else 0), "certification_queries": 250 if arm == "B3_TARGET_GLOBAL_EQUAL_500" else 500, "evaluation_queries": 500, "raw_risk": record["risk"], "audited_risk": record["risk"], "audited_efficiency_gain": record["point"]["wall_gain"], "efficiency_endpoint": "fixed_machine_wall_time", "comparison_status": "PAIRED_S9_4"})
    for family in ("ConANN", "ANNiE"):
        rows.append({"family": family, "dataset": "NOT_RUN", "implementation": "NO_FROZEN_EXECUTABLE_WITH_MATCHED_EVENT", "builds": 0, "design_queries": "NA", "certification_queries": "NA", "evaluation_queries": "NA", "raw_risk": "NA", "audited_risk": "NA", "audited_efficiency_gain": "NA", "efficiency_endpoint": "NA", "comparison_status": "NOT_EXECUTABLE_FROM_AVAILABLE_CODE"})
    pd.DataFrame(rows).to_csv(output / "external_method_evidence_matrix.csv", index=False)


def attribution(ndc, runtime, output):
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        n, r = ndc[dataset], runtime[dataset]
        contrasts = [
            ("one_rung_shift", "A2_SOURCE_ONE_RUNG_UNCERTIFIED", "A1_SOURCE_ACTION_DIRECT", "diagnostic NDC effect"),
            ("certification_source_slack", "B2_SOURCE_ONE_RUNG_CERTIFIED", "A2_SOURCE_ONE_RUNG_UNCERTIFIED", "certificate changes authorization; outcome difference may be zero"),
            ("certification_fixed_256", "B1_FIXED_256_CERTIFIED", "A3_FIXED_256_UNCERTIFIED", "certificate changes authorization; outcome difference may be zero"),
            ("fixed_action_sufficiency", "B1_FIXED_256_CERTIFIED", "B2_SOURCE_ONE_RUNG_CERTIFIED", "positive means fixed 256 outperforms source slack"),
            ("equal_500_target_selection", "B3_TARGET_GLOBAL_EQUAL_500", "B2_SOURCE_ONE_RUNG_CERTIFIED", "matched target-label allocation"),
            ("label_rich_target_selection", "B4_TARGET_GLOBAL_1000", "B2_SOURCE_ONE_RUNG_CERTIFIED", "not equal-information"),
            ("oracle_headroom_over_best_deployable", "O1_EVALUATION_ORACLE", max(("B1_FIXED_256_CERTIFIED", "B2_SOURCE_ONE_RUNG_CERTIFIED", "B3_TARGET_GLOBAL_EQUAL_500", "B4_TARGET_GLOBAL_1000"), key=lambda arm: n[arm]["point"]["ndc_gain"]), "nondeployable NDC upper bound"),
        ]
        for contrast, left, right, note in contrasts:
            rows.append({
                "dataset": dataset, "contrast": contrast, "left": left, "right": right,
                "risk_delta_left_minus_right": n[left]["point"]["risk"] - n[right]["point"]["risk"],
                "ndc_gain_delta_left_minus_right": n[left]["point"]["ndc_gain"] - n[right]["point"]["ndc_gain"],
                "wall_gain_delta_left_minus_right": (r[left]["point"]["wall_gain"] - r[right]["point"]["wall_gain"]) if left in r and right in r else "NOT_MEASURED_FOR_DIAGNOSTIC_ARM",
                "note": note,
            })
    pd.DataFrame(rows).to_csv(output / "component_attribution.csv", index=False)


def gate_table(runtime, output):
    rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        for arm, record in runtime[dataset].items():
            rows.append({"dataset": dataset, "arm": arm, **record["gates"], "all_value_gates": record["deployment_value_gate_pass"], "wall_gain": record["point"]["wall_gain"], "wall_gain_ci_low": record["crossed_target_query_95ci"]["wall_gain"][0], "p95_wall_ratio": record["point"]["p95_wall_ratio"], "p95_wall_ratio_ci_high": record["crossed_target_query_95ci"]["p95_wall_ratio"][1], "risk": record["risk"], "risk_ci_high": record["risk_crossed_95ci"][1]})
    pd.DataFrame(rows).to_csv(output / "unified_deployable_gate.csv", index=False)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    ndc = json.loads((args.root / "results/sigmod_s9/s9_4_arm_analysis/arm_ndc_summary.json").read_text())
    runtime = json.loads((args.root / "results/sigmod_s9/s9_4_runtime_analysis/arm_runtime_summary.json").read_text())
    external_matrix(args.root, runtime, args.output); attribution(ndc, runtime, args.output); gate_table(runtime, args.output)
    decision = {
        "decision": "ICBA_VALUE_CONFIRMED_SIMPLE_BASELINE_DOMINATES_SOURCE_SLACK_TARGET_RECALIBRATION_STRONGEST",
        "icba_audit_value": "SUPPORTED",
        "source_slack_unique_method_value": "NOT_SUPPORTED",
        "fixed_256_result": "MATCHES_SOURCE_SLACK_ON_SIFT_AND_DOMINATES_ON_ARXIV",
        "equal_500_target_global": "SAFE_POSITIVE_VALUE_BOTH_DATASETS_WITH_FALLBACK_VARIANCE",
        "label_rich_target_global": "STRONGEST_DEPLOYABLE_ARM_BOTH_DATASETS",
        "external_methods": "CONTEXTUAL_NATIVE_ESTIMANDS_NOT_HEAD_TO_HEAD",
        "paper_route": "CENTER_ICBA_AND_TARGET_RECALIBRATION; DEMOTE_SOURCE_SLACK_TO_BOUNDARY_ABLATION",
    }
    (args.output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
