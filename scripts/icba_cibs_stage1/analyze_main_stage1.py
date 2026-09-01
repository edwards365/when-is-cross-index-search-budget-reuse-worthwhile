#!/usr/bin/env python3
"""Produce the preregistered main K=3 Stage-I analyses without reselection."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/icba_cibs_stage1/analysis"
EVALUATION = ROOT / "manifests/icba_cibs_stage1_evaluation_realization.json"
SELECTED = ROOT / "manifests/icba_cibs_stage1_selected_actions.json"
BUILD = ROOT / "manifests/icba_cibs_stage1_build_realization.json"
PREREG = ROOT / "manifests/icba_cibs_stage1_phase1_preregistration.json"
SENTINEL_CERT = ROOT / "results/icba_cibs_stage1/sentinel/sentinel_procedure_certificate.json"
SENTINEL_EVENTS = ROOT / "results/icba_cibs_stage1/sentinel_events.jsonl"
DATASETS = ("sift_100k", "arxiv_nomic_100k")
BUILDS = ("G1", "G2", "G3")
EFS = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
WORKLOADS = (1_000, 10_000, 100_000, 1_000_000, 10_000_000)
BOOTSTRAP_SEED = 991
BOOTSTRAP_REPLICATES = 5000


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_meta(path: Path) -> dict[str, object]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        try:
            result[key] = int(value)
        except ValueError:
            result[key] = value
    return result


def write_json(name: str, payload: dict) -> None:
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def action_rows(dataset: str) -> list[dict[str, object]]:
    rows = []
    for build in BUILDS:
        path = ROOT / f"results/icba_cibs_stage1/sentinel/{dataset}__{build}__sentinel_actions.csv"
        for raw in read_csv(path):
            rows.append({
                **raw,
                "query_row": int(raw["query_row"]),
                "requested_ef": int(raw["requested_ef"]),
                "Z_abs": int(raw["Z_abs"]),
                "native_ndc": int(raw["native_ndc"]),
                "actual_expansions": int(raw["actual_expansions"]),
                "wall_clock_ns": int(raw["wall_clock_ns"]),
                "raw_recall_at_10": float(raw["raw_recall_at_10"]),
                "build_id": build,
                "action_id": f"{build}:ef={raw['requested_ef']}",
            })
    return rows


def group_actions(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["action_id"])].append(row)
    if len(grouped) != 36 or any(len(values) != 256 for values in grouped.values()):
        raise AssertionError("main action matrix is not 36 x 256")
    return dict(grouped)


def action_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "n": len(rows),
        "failures": sum(int(row["Z_abs"]) for row in rows),
        "mean_recall_at_10": statistics.fmean(float(row["raw_recall_at_10"]) for row in rows),
        "mean_ndc": statistics.fmean(int(row["native_ndc"]) for row in rows),
        "p95_ndc": float(np.percentile([int(row["native_ndc"]) for row in rows], 95)),
        "mean_expansions": statistics.fmean(int(row["actual_expansions"]) for row in rows),
        "mean_wall_clock_ns": statistics.fmean(int(row["wall_clock_ns"]) for row in rows),
    }


def action_key(action_id: str, summaries: dict[str, dict]) -> tuple:
    build, ef_text = action_id.split(":ef=")
    stats = summaries[action_id]
    return (stats["mean_ndc"], stats["p95_ndc"], int(ef_text), build)


def evaluation_rows(dataset: str) -> dict[str, list[dict[str, str]]]:
    result = {}
    for build in BUILDS:
        path = ROOT / f"results/icba_cibs_stage1/evaluation/{dataset}__{build}__evaluation_all_actions.csv"
        rows = read_csv(path)
        for row in rows:
            row["build_id"] = build
        result[build] = rows
    return result


def evaluate_action(rows_by_build: dict[str, list[dict[str, str]]], action_id: str) -> dict[str, object]:
    build, ef_text = action_id.split(":ef=")
    ef = int(ef_text)
    rows = [row for row in rows_by_build[build] if int(row["requested_ef"]) == ef]
    return {
        "action_id": action_id,
        "n": len(rows),
        "mean_recall_at_10": statistics.fmean(float(row["raw_recall_at_10"]) for row in rows),
        "failures": sum(int(row["Z_abs"]) for row in rows),
        "mean_ndc": statistics.fmean(int(row["native_ndc"]) for row in rows),
        "p95_ndc": float(np.percentile([int(row["native_ndc"]) for row in rows], 95)),
        "mean_wall_clock_ns": statistics.fmean(int(row["wall_clock_ns"]) for row in rows),
    }


def cp_lcb(failures: int, n: int, alpha: float = 0.05) -> float:
    if failures == 0:
        return 0.0
    return float(beta.ppf(alpha, failures, n - failures + 1))


def robustness(dataset: str, selected: dict) -> dict:
    rows = action_rows(dataset)
    grouped = group_actions(rows)
    summaries = {action: action_summary(values) for action, values in grouped.items()}
    certified = list(selected["datasets"][dataset]["simultaneously_certified_action_ids"])
    frozen = selected["datasets"][dataset]["B4_CIBS_FIXED"]["action_id"]
    if min(certified, key=lambda action: action_key(action, summaries)) != frozen:
        raise AssertionError("frozen main selection does not replay")

    build_effects = []
    for ef in EFS:
        per_build = {build: summaries[f"{build}:ef={ef}"] for build in BUILDS}
        build_effects.append({
            "requested_ef": ef,
            "per_build": per_build,
            "mean_ndc_range": max(x["mean_ndc"] for x in per_build.values()) - min(x["mean_ndc"] for x in per_build.values()),
            "mean_recall_range": max(x["mean_recall_at_10"] for x in per_build.values()) - min(x["mean_recall_at_10"] for x in per_build.values()),
        })

    eval_rows = evaluation_rows(dataset)
    lobo = {}
    for omitted in BUILDS:
        candidates = [action for action in certified if not action.startswith(f"{omitted}:")]
        chosen = min(candidates, key=lambda action: action_key(action, summaries)) if candidates else "G1:ef=100000"
        lobo[omitted] = {"selected": chosen, "evaluation": None if chosen.endswith("100000") else evaluate_action(eval_rows, chosen)}
    without_action = [action for action in certified if action != frozen]
    next_action = min(without_action, key=lambda action: action_key(action, summaries))
    selected_build = frozen.split(":", 1)[0]
    without_build = [action for action in certified if not action.startswith(f"{selected_build}:")]
    next_build_action = min(without_build, key=lambda action: action_key(action, summaries))

    action_order = sorted(certified)
    matrices = {action: np.asarray([int(row["native_ndc"]) for row in grouped[action]], dtype=np.int64) for action in action_order}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    counts = Counter()
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = rng.integers(0, 256, size=256)
        def sampled_key(action: str) -> tuple:
            values = matrices[action][sample]
            build, ef_text = action.split(":ef=")
            return (float(np.mean(values)), float(np.percentile(values, 95)), int(ef_text), build)
        counts[min(action_order, key=sampled_key)] += 1

    return {
        "dataset": dataset,
        "frozen_selected_action": frozen,
        "selection_replay": "PASS",
        "build_effects": build_effects,
        "leave_one_build_out": lobo,
        "selected_action_removed": {"selected": next_action, "evaluation": evaluate_action(eval_rows, next_action)},
        "selected_build_removed": {"selected": next_build_action, "evaluation": evaluate_action(eval_rows, next_build_action)},
        "selection_stability": {
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": BOOTSTRAP_SEED,
            "conditioning": "bootstrap over sentinel queries within the originally simultaneous-certified set",
            "frequencies": dict(sorted(counts.items())),
            "frozen_action_frequency": counts[frozen] / BOOTSTRAP_REPLICATES,
        },
    }


def cost_ledger(dataset: str, evaluation: dict, build_manifest: dict) -> dict:
    builds = [row for row in build_manifest["builds"] if row["dataset"] == dataset]
    build_by_id = {row["build_id"]: row for row in builds}
    sentinel_rows = group_actions(action_rows(dataset))
    sentinel_wall_by_build = {
        build: sum(int(row["wall_clock_ns"]) for action, rows in sentinel_rows.items() if action.startswith(f"{build}:") for row in rows)
        for build in BUILDS
    }
    sentinel_ndc_by_build = {
        build: sum(int(row["native_ndc"]) for action, rows in sentinel_rows.items() if action.startswith(f"{build}:") for row in rows)
        for build in BUILDS
    }
    sentinel_truth = parse_meta(ROOT / f"results/icba_cibs_stage1/sentinel/{dataset}__sentinel_truth.meta")
    evaluation_truth = evaluation["datasets"][dataset]["truth"]["cost"]
    b1 = evaluation["datasets"][dataset]["methods"]["B1"]
    b4 = evaluation["datasets"][dataset]["methods"]["B4_CIBS_FIXED"]
    extra_fixed_wall = (
        build_by_id["G2"]["build"]["build_time_ns"]
        + build_by_id["G3"]["build"]["build_time_ns"]
        + sentinel_wall_by_build["G2"]
        + sentinel_wall_by_build["G3"]
    )
    online_wall_saving = b1["mean_wall_clock_ns"] - b4["mean_wall_clock_ns"]
    break_even = math.ceil(extra_fixed_wall / online_wall_saving) if online_wall_saving > 0 else None
    workloads = []
    b1_offline = build_by_id["G1"]["build"]["build_time_ns"] + sentinel_wall_by_build["G1"]
    b4_offline = sum(row["build"]["build_time_ns"] for row in builds) + sum(sentinel_wall_by_build.values())
    truth_wall = int(sentinel_truth["truth_acquisition_total_wall_clock_ns"])
    for n in WORKLOADS:
        workloads.append({
            "N": n,
            "truth_available": {
                "B1_total_wall_clock_ns": b1_offline + n * b1["mean_wall_clock_ns"],
                "B4_total_wall_clock_ns": b4_offline + n * b4["mean_wall_clock_ns"],
            },
            "truth_acquisition_included": {
                "B1_total_wall_clock_ns": truth_wall + b1_offline + n * b1["mean_wall_clock_ns"],
                "B4_total_wall_clock_ns": truth_wall + b4_offline + n * b4["mean_wall_clock_ns"],
            },
        })
    result_files = list((ROOT / "results/icba_cibs_stage1").rglob("*"))
    result_storage = sum(path.stat().st_size for path in result_files if path.is_file())
    return {
        "dataset": dataset,
        "construction": {row["build_id"]: {"build_time_ns": row["build"]["build_time_ns"], "peak_rss_kib": row["build"]["peak_rss_kib"]} for row in builds},
        "index_storage_bytes": {row["build_id"]: row["index_size_bytes"] for row in builds},
        "truth": {"sentinel": sentinel_truth, "evaluation_diagnostic": evaluation_truth},
        "action_search_36": {"wall_clock_ns_by_build": sentinel_wall_by_build, "ndc_by_build": sentinel_ndc_by_build},
        "selection_and_certification": "included in measured sentinel supervisor residual; not separately identifiable",
        "serialization_and_replay": "included in build/inspection commands; not separately identifiable from input IO",
        "storage_snapshot_all_stage1_results_bytes": result_storage,
        "fallback_evaluation": evaluation["datasets"][dataset]["methods"]["B0"],
        "incremental_B4_vs_B1": {
            "extra_fixed_wall_clock_ns": extra_fixed_wall,
            "per_query_wall_clock_saving_ns": online_wall_saving,
            "finite_wall_clock_break_even": break_even is not None,
            "break_even_queries": break_even if break_even is not None else "NO_FINITE_BREAK_EVEN",
            "extra_index_storage_bytes": build_by_id["G2"]["index_size_bytes"] + build_by_id["G3"]["index_size_bytes"],
        },
        "workloads": workloads,
    }


def main() -> None:
    if OUT.exists():
        raise RuntimeError("refusing to overwrite main analysis")
    OUT.mkdir(parents=True)
    started = time.time_ns()
    evaluation = load_json(EVALUATION)
    selected = load_json(SELECTED)
    build_manifest = load_json(BUILD)
    prereg = load_json(PREREG)
    sentinel_cert = load_json(SENTINEL_CERT)
    if evaluation["status"] != "PASS_EVALUATION_HELD_OUT_RISK_DIAGNOSTIC":
        raise AssertionError("evaluation not complete")
    if selected["status"] != "FROZEN_AFTER_SENTINEL_BEFORE_EVALUATION":
        raise AssertionError("selected action manifest state")
    if evaluation["selected_action_manifest_sha256"] != sha256(SELECTED):
        raise AssertionError("selected action hash")

    robust = {dataset: robustness(dataset, selected) for dataset in DATASETS}
    costs = {dataset: cost_ledger(dataset, evaluation, build_manifest) for dataset in DATASETS}
    gates = {}
    promotion_per_dataset = {}
    for dataset in DATASETS:
        data = evaluation["datasets"][dataset]
        comparison = data["comparisons"]["B4_vs_B1"]
        b1 = data["methods"]["B1"]
        b4 = data["methods"]["B4_CIBS_FIXED"]
        evaluation_no_clear_conflict = cp_lcb(b4["failures"], b4["n"]) <= 0.05 and b4["endpoint_failures"] <= b1["endpoint_failures"]
        checks = {
            "recall_delta_ge_minus_0_001": comparison["recall_delta"] >= -0.001,
            "relative_B1_mean_ndc_gain_ge_0_01": comparison["mean_ndc_relative_gain"] >= 0.01,
            "p95_ndc_delta_le_0": comparison["p95_ndc_delta"] <= 0,
            "procedure_certificate_valid": bool(selected["datasets"][dataset]["B4_CIBS_FIXED"]["statistics"]["certified"]),
            "evaluation_no_clear_conflict": evaluation_no_clear_conflict,
            "endpoint_not_worse": b4["endpoint_failures"] <= b1["endpoint_failures"],
            "delete_top_1_percent_gain_positive": data["delete_top_1_percent_gain"]["positive_after_deletion"],
            "finite_break_even": costs[dataset]["incremental_B4_vs_B1"]["finite_wall_clock_break_even"],
        }
        gates[dataset] = {"checks": checks, "pass": all(checks.values())}
        ci = comparison
        promotion_checks = {
            "recall_noninferiority_interval_support": ci["recall_delta_95_interval"][0] >= -0.001,
            "mean_gain_CI_lower_bound_gt_0": ci["mean_ndc_relative_gain_95_interval"][0] > 0,
            "p95_no_clear_worsening": ci["p95_ndc_delta_95_interval"][0] <= 0,
            "no_contamination_or_replay_failure": evaluation["future_confirm_accessed"] is False,
            "complete_cost_break_even_reasonable": costs[dataset]["incremental_B4_vs_B1"]["finite_wall_clock_break_even"],
        }
        promotion_per_dataset[dataset] = {"checks": promotion_checks, "pass": all(promotion_checks.values())}

    same_direction = all(evaluation["datasets"][dataset]["comparisons"]["B4_vs_B1"]["mean_ndc_relative_gain"] > 0 for dataset in DATASETS)
    decision = {
        "schema_version": 1,
        "status": "MAIN_K3_ANALYSIS_COMPLETE_MINIMUM_GATE_FAILED",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "minimum_gate": {"datasets": gates, "both_datasets_pass": all(item["pass"] for item in gates.values())},
        "promotion_gate": {
            "datasets": promotion_per_dataset,
            "same_direction_both_datasets": same_direction,
            "pass": same_direction and all(item["pass"] for item in promotion_per_dataset.values()),
        },
        "evaluation_manifest_sha256": sha256(EVALUATION),
        "selected_action_manifest_sha256": sha256(SELECTED),
        "sentinel_certificate_sha256": sha256(SENTINEL_CERT),
        "future_confirm_accessed": False,
        "evaluation_reselection_performed": False,
        "positive_cibs_evidence": False,
        "next": "PREREGISTERED_K2_L12_N128_M24_ZERO_FAILURE_ABLATION",
    }
    write_json("robustness.json", {"schema_version": 1, "status": "PASS_ROBUSTNESS_ANALYSIS", "datasets": robust})
    write_json("cost_ledger.json", {"schema_version": 1, "status": "PASS_COST_ACCOUNTING", "truth_channels": ["truth_available", "truth_acquisition_included"], "datasets": costs})
    write_json("main_gate_decision.json", decision)
    write_json("main_analysis_execution.json", {
        "schema_version": 1,
        "status": "PASS_MAIN_ANALYSIS_EXECUTION",
        "preregistration_sha256": sha256(PREREG),
        "evaluation_sha256": sha256(EVALUATION),
        "sentinel_certificate_status": sentinel_cert["status"],
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "elapsed_ns": time.time_ns() - started,
    })
    print(json.dumps(decision, sort_keys=True))


if __name__ == "__main__":
    main()
