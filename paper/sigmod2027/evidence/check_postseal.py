#!/usr/bin/env python3
"""Validate and typeset the post-seal target-certification evidence."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
D = ROOT / "target_certified"
CHECKS: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    CHECKS.append(message)


def rows(name: str) -> list[dict[str, str]]:
    with (D / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def close(a: float | str, b: float | str, tol: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def pct(value: str) -> float:
    return 100.0 * float(value)


def fmt_int(value: float | str) -> str:
    return f"{float(value):,.0f}"


def main() -> None:
    summary = rows("s3_summary.csv")
    pairs = rows("s3_pair_results.csv")
    targets = rows("s3_target_build_results.csv")
    cost = rows("s4_dataset_summary.csv")
    horizons = rows("s4_horizon_summary.csv")
    pair_cost = rows("s4_pairwise_cost_ledger.csv")
    shared_cost = rows("s4_shared_target_cost_ledger.csv")
    interval_rows = rows("s3_interval_sensitivity.csv")

    require(len(summary) == 2, "two target-certified dataset summaries")
    require(len(pairs) == 1104, "1,104 directed target-certified decisions")
    require(len(targets) == 48, "48 target-build summaries")
    require(len(cost) == 4, "four target-stage cost summaries")
    require(len(horizons) == 20, "twenty registered horizon rows")
    require(len(pair_cost) == 1104, "1,104 pairwise cost rows")
    require(len(shared_cost) == 48, "48 shared-target cost rows")
    require(len(interval_rows) == 6, "six target/query interval sensitivity rows")
    require(json.loads((D / "s3_integrity_checks.json").read_text())["checks_passed"] == 15,
            "15/15 native-stage integrity checks")
    require(json.loads((D / "s4_validation.json").read_text())["passed"] == 14,
            "14/14 cost-ledger checks")

    expected = {
        "sift_100k": (0.0012608695652173913, 0.08283110083571854, 0.9963617002395954),
        "arxiv_nomic_100k": (0.005304347826086957, 0.29082672983398916, 0.9796615432386275),
    }
    for row in summary:
        ds = row["dataset"]
        risk, saving, p95 = expected[ds]
        require(int(row["pairs"]) == 552, f"{ds}: 552 directed decisions")
        require(int(row["target_builds"]) == 24, f"{ds}: 24 targets")
        require(int(row["target_certification_n"]) == 500 and int(row["target_evaluation_n"]) == 500,
                f"{ds}: disjoint 500/500 target roles")
        require(int(row["deploy_candidate_pairs"]) == 552, f"{ds}: every candidate certified")
        require(int(row["fallback_endpoint_pairs"]) == 0 and int(row["no_certified_action_pairs"]) == 0,
                f"{ds}: no fallback or abstention")
        require(close(row["evaluation_risk"], risk), f"{ds}: pooled evaluation risk")
        require(close(row["relative_mean_ndc_saving"], saving), f"{ds}: mean-NDC saving")
        require(close(row["query_pooled_ndc_p95_ratio"], p95), f"{ds}: pooled p95 ratio")
        require(float(row["max_candidate_cert_ucb"]) <= 0.05 and float(row["max_endpoint_cert_ucb"]) <= 0.05,
                f"{ds}: candidate and endpoint certificates pass")
        require(float(row["relative_mean_ndc_saving_ci_low"]) > 0 and
                float(row["max_target_ndc_p95_ratio"]) <= 1 and
                float(row["lobo_min_ndc_saving"]) > 0,
                f"{ds}: efficiency, tail, and LOBO gates pass")

    require(all(r["deployment"] == "DEPLOY_CANDIDATE" for r in pairs),
            "all pair decisions deploy the frozen candidate")
    require(all(int(r["candidate_cert_n"]) == 500 and int(r["evaluation_n"]) == 500 for r in pairs),
            "all pair decisions retain 500/500 target roles")
    require(all(float(r["candidate_cert_ucb"]) <= 0.05 for r in pairs),
            "every deployed candidate has target CP-UCB at most 5%")

    interval_map = {(r["dataset"], r["resampling"]): r for r in interval_rows}
    for row in summary:
        ds = row["dataset"]
        crossed = interval_map[(ds, "CROSSED_TARGET_QUERY")]
        require(close(crossed["evaluation_risk"], row["evaluation_risk"]),
                f"{ds}: crossed risk preserves the frozen point estimate")
        require(close(crossed["relative_mean_ndc_saving"], row["relative_mean_ndc_saving"]),
                f"{ds}: crossed saving preserves the frozen point estimate")
        require(float(crossed["evaluation_risk_ci_high"]) < 0.05,
                f"{ds}: crossed risk interval remains below 5%")
        require(float(crossed["relative_mean_ndc_saving_ci_low"]) > 0,
                f"{ds}: crossed saving interval remains positive")

    for row in pair_cost:
        require(close(float(row["truth_ndc"]) + float(row["certification_search_ndc"]),
                      row["target_stage_overhead_ndc"]),
                "pairwise target-stage overhead identity")
    for row in shared_cost:
        require(close(float(row["truth_ndc"]) + float(row["certification_search_ndc"]),
                      row["shared_target_overhead_ndc"]),
                "shared-target overhead identity")

    expected_be = {
        ("sift_100k", "PAIRWISE_TARGET_CERTIFICATION"): (66914.4449875517, 460),
        ("sift_100k", "SHARED_TARGET_CERTIFICATION_23_SOURCES"): (3019.259554633382, 0),
        ("arxiv_nomic_100k", "PAIRWISE_TARGET_CERTIFICATION"): (17018.23486213788, 230),
        ("arxiv_nomic_100k", "SHARED_TARGET_CERTIFICATION_23_SOURCES"): (755.4615900974743, 0),
    }
    for row in cost:
        key = (row["dataset"], row["scenario"])
        be, non = expected_be[key]
        require(close(row["ratio_of_sums_break_even_queries"], be), f"{key}: break-even")
        require(int(row["nonamortizing_units"]) == non, f"{key}: nonamortizing count")
        require(row["full_end_to_end_lifecycle_status"] ==
                "NOT_ESTIMABLE_SOURCE_POLICY_ACQUISITION_NDC_MISSING",
                f"{key}: full lifecycle remains not estimable")

    labels = {"sift_100k": "SIFT", "arxiv_nomic_100k": "Arxiv"}
    certified_lines = []
    for row in summary:
        crossed = interval_map[(row["dataset"], "CROSSED_TARGET_QUERY")]
        certified_lines.append(
            f"{labels[row['dataset']]} & 552/0/0 & "
            f"{pct(row['evaluation_risk']):.3f} [{pct(crossed['evaluation_risk_ci_low']):.3f}, "
            f"{pct(crossed['evaluation_risk_ci_high']):.3f}] & "
            f"{pct(row['relative_mean_ndc_saving']):.3f} "
            f"[{pct(crossed['relative_mean_ndc_saving_ci_low']):.3f}, "
            f"{pct(crossed['relative_mean_ndc_saving_ci_high']):.3f}] & "
            f"{float(row['query_pooled_ndc_p95_ratio']):.4f} / "
            f"{float(row['max_target_ndc_p95_ratio']):.4f} & "
            f"{pct(row['lobo_min_ndc_saving']):.3f} \\\\"
        )

    cost_lines = []
    for row in cost:
        scenario = "Pairwise" if row["scenario"].startswith("PAIRWISE") else "Shared target"
        cost_lines.append(
            f"{labels[row['dataset']]} & {scenario} & {int(row['units'])} & "
            f"{fmt_int(row['ratio_of_sums_break_even_queries'])} "
            f"[{fmt_int(row['break_even_bootstrap_ci_low'])}, "
            f"{fmt_int(row['break_even_bootstrap_ci_high'])}] & "
            f"{int(row['nonamortizing_units'])} & "
            f"{fmt_int(row['first_registered_positive_N'])} \\\\"
        )

    tex = (
        "% Generated by evidence/check_postseal.py from packaged post-seal evidence.\n"
        "\\newcommand{\\TargetCertifiedRows}{%\n" + "\n".join(certified_lines) + "\n}\n"
        "\\newcommand{\\TargetStageCostRows}{%\n" + "\n".join(cost_lines) + "\n}\n"
    )
    (ROOT / "postseal_tables.tex").write_text(tex, encoding="utf-8")
    report = {"status": "PASS", "checks": len(CHECKS), "details": CHECKS}
    (D / "postseal_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "checks": len(CHECKS)}))


if __name__ == "__main__":
    main()
