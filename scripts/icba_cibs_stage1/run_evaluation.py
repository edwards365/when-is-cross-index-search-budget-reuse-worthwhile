#!/usr/bin/env python3
"""Run the immutable Stage-I held-out evaluation diagnostic.

The selected actions are read from the committed selected-action manifest and
are never recomputed or changed here.  Future-confirm artifacts are not opened.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results/icba_cibs_stage1/evaluation"
MANIFEST = ROOT / "manifests/icba_cibs_stage1_evaluation_realization.json"
GATE = ROOT / "results/icba_cibs_stage1/evaluation_gate.json"
EVENTS = ROOT / "results/icba_cibs_stage1/evaluation_events.jsonl"
SELECTED = ROOT / "manifests/icba_cibs_stage1_selected_actions.json"
SENTINEL_GATE = ROOT / "results/icba_cibs_stage1/sentinel_gate.json"
BUILD_MANIFEST = ROOT / "manifests/icba_cibs_stage1_build_realization.json"
ROLE_MANIFEST = ROOT / "manifests/icba_cibs_stage1_query_roles.json"
RUNTIME_MANIFEST = ROOT / "results/icba_cibs_stage1/runtime/runtime_input_manifest.json"
ACCESS_LOG = ROOT / "results/icba_cibs_stage1/phase1/query_roles/truth_access_log.csv"
ACCESS_INTENT = ROOT / "manifests/icba_cibs_stage1_evaluation_access_intent.json"
RUNNER = ROOT / "results/icba_cibs_stage1/runtime/tools/icba_cibs_stage1_evaluation_runner"
RAW_EFS = [10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]
BUILD_IDS = ["G1", "G2", "G3"]
DATASETS = {
    "sift_100k": {"dimensions": 128},
    "arxiv_nomic_100k": {"dimensions": 768},
}
FLAGS = [
    "-std=c++17", "-O3", "-DNDEBUG", "-DNO_MANUAL_VECTORIZATION",
    "-Wall", "-Wextra", "-Wpedantic",
]
BOOTSTRAP_SEED = 991
BOOTSTRAP_REPLICATES = 5000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def event(name: str, **fields) -> None:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"time_unix_ns": time.time_ns(), "event": name, **fields}, sort_keys=True) + "\n")


def run(args: list[str], log_path: Path) -> None:
    started = time.time_ns()
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(args, stdout=handle, stderr=subprocess.STDOUT, text=True)
    event("command", argv=args, returncode=completed.returncode,
          elapsed_ns=time.time_ns() - started, log=str(log_path.relative_to(ROOT)))
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}")


def parse_meta(path: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        if value in {"0", "1"}:
            result[key] = value == "1"
        else:
            try:
                result[key] = int(value)
            except ValueError:
                result[key] = value
    return result


def percentile(values, probability: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), probability * 100, method="linear"))


def cp_ucb(failures: int, n: int) -> float:
    if failures >= n:
        return 1.0
    return float(beta.ppf(0.95, failures + 1, n - failures))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_access_log() -> None:
    rows = read_csv(ACCESS_LOG)
    if len(rows) != 8:
        raise RuntimeError("query firewall access log does not have eight rows")
    for row in rows:
        if row["role"] in {"cibs_design", "cibs_sentinel", "cibs_evaluation"}:
            if row["truth_accessed"] != "1" or row["action_outcome_accessed"] != "1":
                raise RuntimeError(f"access intent is not durably armed: {row['dataset']}/{row['role']}")
        elif row["role"] == "cibs_future_confirm":
            if row["truth_accessed"] != "0" or row["action_outcome_accessed"] != "0":
                raise RuntimeError("future-confirm firewall is open")


def verify_clean_tracked_state() -> None:
    subprocess.run(["git", "diff", "--quiet"], cwd=ROOT, check=True)
    subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=True)
    allowed = (
        "artifacts/icba_cibs_stage1/",
        "results/icba_cibs_stage1/runtime/base/",
        "results/icba_cibs_stage1/runtime/orders/",
        "results/icba_cibs_stage1/runtime/queries/",
        "results/icba_cibs_stage1/runtime/tools/",
    )
    status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT, text=True).splitlines()
    unexpected = [line for line in status if not line[3:].startswith(allowed)]
    if unexpected:
        raise RuntimeError(f"unexpected pre-evaluation worktree state: {unexpected}")


def resource_snapshot() -> dict[str, object]:
    stats = os.statvfs(ROOT)
    free = stats.f_bavail * stats.f_frsize
    required = 3_365_465_672 + 5 * 1024**3
    result = {
        "free_bytes": free,
        "projected_additions_bytes": 3_365_465_672,
        "reserve_bytes": 5 * 1024**3,
        "required_bytes": required,
        "status": "PASS" if free >= required else "FAIL",
    }
    if result["status"] != "PASS":
        raise RuntimeError("INSUFFICIENT_RESOURCES_FOR_CIBS_STAGE1")
    return result


def compile_runner() -> dict[str, object]:
    run([
        "g++", *FLAGS, "-Ithird_party/hnswlib", "-Icpp/include",
        "cpp/src/icba_cibs_stage1_runner.cpp", "-o", str(RUNNER),
    ], RESULTS / "compile.log")
    return {
        "binary": str(RUNNER.relative_to(ROOT)),
        "binary_sha256": sha256(RUNNER),
        "source": "cpp/src/icba_cibs_stage1_runner.cpp",
        "source_sha256": sha256(ROOT / "cpp/src/icba_cibs_stage1_runner.cpp"),
        "flags": FLAGS,
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "threads": 1,
        "simd": "NO_MANUAL_VECTORIZATION_SCALAR",
    }


def summarize(rows: list[dict[str, object]], build_manifest: dict) -> dict[str, object]:
    if len(rows) != 500:
        raise RuntimeError(f"evaluation method has {len(rows)} rows, expected 500")
    failures = sum(int(row["Z_abs"]) for row in rows)
    recall = [float(row["raw_recall_at_10"]) for row in rows]
    ndc = [int(row["native_ndc"]) for row in rows]
    expansions = [int(row["actual_expansions"]) for row in rows]
    wall = [int(row["wall_clock_ns"]) for row in rows]
    efs = [int(row["requested_ef"]) for row in rows]
    builds = [str(row["build_id"]) for row in rows]
    build_records = {(item["dataset"], item["build_id"]): item for item in build_manifest["builds"]}
    dataset = str(rows[0]["dataset"])
    index_sizes = [build_records[(dataset, build)]["index_size_bytes"] for build in builds]
    peak_rss = [build_records[(dataset, build)]["build"]["peak_rss_kib"] for build in builds]
    return {
        "n": len(rows),
        "mean_recall_at_10": statistics.fmean(recall),
        "failures": failures,
        "risk_cp_95_ucb": cp_ucb(failures, len(rows)),
        "endpoint_failures": sum(str(row["endpoint_status"]) != "PASS" for row in rows),
        "mean_ndc": statistics.fmean(ndc),
        "p50_ndc": percentile(ndc, 0.50),
        "p95_ndc": percentile(ndc, 0.95),
        "p99_ndc": percentile(ndc, 0.99),
        "mean_expansions": statistics.fmean(expansions),
        "p95_expansions": percentile(expansions, 0.95),
        "mean_wall_clock_ns": statistics.fmean(wall),
        "p95_wall_clock_ns": percentile(wall, 0.95),
        "p99_wall_clock_ns": percentile(wall, 0.99),
        "requested_ef_counts": dict(sorted(Counter(efs).items())),
        "build_id_counts": dict(sorted(Counter(builds).items())),
        "mean_index_size_bytes": statistics.fmean(index_sizes),
        "max_build_peak_rss_kib": max(peak_rss),
    }


def paired_bootstrap(method_rows, baseline_rows) -> dict[str, object]:
    method = {int(row["query_row"]): row for row in method_rows}
    baseline = {int(row["query_row"]): row for row in baseline_rows}
    if set(method) != set(range(500)) or set(baseline) != set(range(500)):
        raise RuntimeError("paired evaluation rows are incomplete")
    m_ndc = np.array([int(method[i]["native_ndc"]) for i in range(500)], dtype=np.float64)
    b_ndc = np.array([int(baseline[i]["native_ndc"]) for i in range(500)], dtype=np.float64)
    m_recall = np.array([float(method[i]["raw_recall_at_10"]) for i in range(500)])
    b_recall = np.array([float(baseline[i]["raw_recall_at_10"]) for i in range(500)])
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    gains = np.empty(BOOTSTRAP_REPLICATES)
    recall_delta = np.empty(BOOTSTRAP_REPLICATES)
    p95_delta = np.empty(BOOTSTRAP_REPLICATES)
    for repetition in range(BOOTSTRAP_REPLICATES):
        sample = rng.integers(0, 500, size=500)
        baseline_mean = float(np.mean(b_ndc[sample]))
        gains[repetition] = (baseline_mean - float(np.mean(m_ndc[sample]))) / baseline_mean
        recall_delta[repetition] = float(np.mean(m_recall[sample] - b_recall[sample]))
        p95_delta[repetition] = float(np.percentile(m_ndc[sample], 95) - np.percentile(b_ndc[sample], 95))
    def interval(values):
        return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]
    baseline_mean = float(np.mean(b_ndc))
    return {
        "paired_query_bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "seed": BOOTSTRAP_SEED,
        "mean_ndc_relative_gain": (baseline_mean - float(np.mean(m_ndc))) / baseline_mean,
        "mean_ndc_relative_gain_95_interval": interval(gains),
        "recall_delta": float(np.mean(m_recall - b_recall)),
        "recall_delta_95_interval": interval(recall_delta),
        "p95_ndc_delta": float(np.percentile(m_ndc, 95) - np.percentile(b_ndc, 95)),
        "p95_ndc_delta_95_interval": interval(p95_delta),
    }


def fixed_action_rows(all_rows, dataset: str, action: dict) -> list[dict[str, object]]:
    build = action["build_id"]
    ef = int(action["requested_ef"])
    rows = [row for row in all_rows if row["build_id"] == build and int(row["requested_ef"]) == ef]
    if len(rows) != 500:
        raise RuntimeError(f"frozen action {dataset}/{build}/ef={ef} is incomplete")
    return rows


def main() -> None:
    if RESULTS.exists() or MANIFEST.exists() or GATE.exists() or EVENTS.exists():
        raise RuntimeError("refusing to overwrite evaluation artifacts")
    verify_clean_tracked_state()
    verify_access_log()
    selected = json.loads(SELECTED.read_text(encoding="utf-8"))
    sentinel_gate = json.loads(SENTINEL_GATE.read_text(encoding="utf-8"))
    intent = json.loads(ACCESS_INTENT.read_text(encoding="utf-8"))
    build_manifest = json.loads(BUILD_MANIFEST.read_text(encoding="utf-8"))
    roles = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))
    runtime = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))
    if selected["status"] != "FROZEN_AFTER_SENTINEL_BEFORE_EVALUATION":
        raise RuntimeError("selected-action manifest is not frozen")
    if sha256(SELECTED) != sentinel_gate["selected_action_manifest_sha256"]:
        raise RuntimeError("selected-action manifest hash mismatch")
    if intent["selected_action_manifest_sha256"] != sha256(SELECTED):
        raise RuntimeError("evaluation access intent does not bind selected actions")
    if not sentinel_gate["evaluation_access_authorized_next"] or selected["evaluation_reselection_allowed"]:
        raise RuntimeError("evaluation is not authorized or reselection is enabled")
    RESULTS.mkdir(parents=True)
    EVENTS.touch(exist_ok=False)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    event("start", head=head, selected_action_manifest_sha256=sha256(SELECTED),
          evaluation_reselection_allowed=False, future_confirm_accessed=False)
    resource = resource_snapshot()
    event("resource_gate", stage="before_evaluation", **resource)
    compiler = compile_runner()
    build_records = {(row["dataset"], row["build_id"]): row for row in build_manifest["builds"]}
    for row in build_manifest["builds"]:
        if sha256(ROOT / row["artifact_path"]) != row["artifact_sha256"]:
            raise RuntimeError(f"artifact checksum replay failed: {row['dataset']}/{row['build_id']}")
    dataset_results = {}
    raw_files = {}
    for dataset, spec in DATASETS.items():
        role = roles["datasets"][dataset]["roles"]["cibs_evaluation"]
        query_path = ROOT / runtime["datasets"][dataset]["queries"]["cibs_evaluation"]["runtime_path"]
        base_path = ROOT / runtime["datasets"][dataset]["runtime_base_path"]
        truth_csv = RESULTS / f"{dataset}__evaluation_truth.csv"
        truth_meta = RESULTS / f"{dataset}__evaluation_truth.meta"
        event("truth_access_begin", dataset=dataset, role="cibs_evaluation", query_count=500,
              query_file_sha256=role["queries_file_sha256"],
              source_ids_file_sha256=role["source_ids_file_sha256"], future_confirm_accessed=False)
        run([str(RUNNER), "truth", str(base_path), str(query_path), str(spec["dimensions"]),
             str(truth_csv), str(truth_meta)], RESULTS / f"{dataset}__evaluation_truth.log")
        truth_cost = parse_meta(truth_meta)
        if truth_cost["status"] != "PASS" or truth_cost["queries"] != 500:
            raise RuntimeError(f"evaluation truth acquisition failed: {dataset}")
        event("truth_access_complete", dataset=dataset, truth_sha256=sha256(truth_csv))
        all_rows = []
        action_files = []
        for build_id in BUILD_IDS:
            build = build_records[(dataset, build_id)]
            raw_csv = RESULTS / f"{dataset}__{build_id}__evaluation_all_actions.csv"
            run([str(RUNNER), "sentinel", str(ROOT / build["artifact_path"]), str(query_path),
                 str(spec["dimensions"]), ",".join(map(str, RAW_EFS)), str(truth_csv), str(raw_csv)],
                RESULTS / f"{dataset}__{build_id}__evaluation_all_actions.log")
            meta = parse_meta(raw_csv.with_suffix(".meta"))
            if meta["status"] != "PASS" or meta["rows"] != 500 * 12:
                raise RuntimeError("INVALID_CIBS_NDC_INSTRUMENTATION")
            rows = read_csv(raw_csv)
            if len(rows) != 500 * 12:
                raise RuntimeError("evaluation all-action matrix is incomplete")
            for row in rows:
                row["dataset"] = dataset
                row["build_id"] = build_id
            all_rows.extend(rows)
            action_files.append({"build_id": build_id, "path": str(raw_csv.relative_to(ROOT)),
                                 "sha256": sha256(raw_csv), "rows": len(rows)})
        b0_csv = RESULTS / f"{dataset}__B0_fixed_safe.csv"
        g1 = build_records[(dataset, "G1")]
        run([str(RUNNER), "sentinel", str(ROOT / g1["artifact_path"]), str(query_path),
             str(spec["dimensions"]), "100000", str(truth_csv), str(b0_csv)],
            RESULTS / f"{dataset}__B0_fixed_safe.log")
        if parse_meta(b0_csv.with_suffix(".meta"))["status"] != "PASS":
            raise RuntimeError("fixed-safe evaluation fallback failed")
        b0_rows = read_csv(b0_csv)
        if len(b0_rows) != 500:
            raise RuntimeError("B0 evaluation rows incomplete")
        for row in b0_rows:
            row["dataset"] = dataset
            row["build_id"] = "G1"
        frozen = selected["datasets"][dataset]
        methods = {
            "B0": b0_rows,
            "B1": fixed_action_rows(all_rows, dataset, frozen["B1"]),
            "B2": fixed_action_rows(all_rows, dataset, frozen["B2"]),
            "B3": fixed_action_rows(all_rows, dataset, frozen["B3"]),
            "B4_CIBS_FIXED": fixed_action_rows(all_rows, dataset, frozen["B4_CIBS_FIXED"]),
        }
        by_query = defaultdict(list)
        for row in all_rows:
            by_query[int(row["query_row"])].append(row)
        oracle_rows = []
        for query_row in range(500):
            feasible = [row for row in by_query[query_row]
                        if row["endpoint_status"] == "PASS" and float(row["raw_recall_at_10"]) >= 0.90]
            if feasible:
                oracle_rows.append(min(feasible, key=lambda row: (
                    int(row["native_ndc"]), int(row["requested_ef"]), BUILD_IDS.index(row["build_id"])
                )))
            else:
                oracle_rows.append(b0_rows[query_row])
        methods["B5_ORACLE"] = oracle_rows
        summaries = {name: summarize(rows, build_manifest) for name, rows in methods.items()}
        comparisons = {
            "B4_vs_B0": paired_bootstrap(methods["B4_CIBS_FIXED"], methods["B0"]),
            "B4_vs_B1": paired_bootstrap(methods["B4_CIBS_FIXED"], methods["B1"]),
        }
        gains = np.array([int(methods["B1"][i]["native_ndc"]) - int(methods["B4_CIBS_FIXED"][i]["native_ndc"])
                          for i in range(500)], dtype=np.float64)
        delete_count = max(1, int(np.ceil(0.01 * len(gains))))
        retained = np.sort(gains)[:-delete_count]
        top1 = {
            "deleted_queries": delete_count,
            "mean_absolute_ndc_gain_after_deleting_largest_1_percent": float(np.mean(retained)),
            "positive_after_deletion": bool(np.mean(retained) > 0),
        }
        dataset_results[dataset] = {
            "truth": {"path": str(truth_csv.relative_to(ROOT)), "sha256": sha256(truth_csv),
                      "meta_path": str(truth_meta.relative_to(ROOT)), "meta_sha256": sha256(truth_meta),
                      "cost": truth_cost},
            "methods": summaries,
            "comparisons": comparisons,
            "delete_top_1_percent_gain": top1,
            "B5_oracle_rule": "per query minimum NDC among the 36 target-feasible actions; tie raw ef then build; B0 if none",
            "B5_deployable": False,
            "selected_actions_reused_without_reselection": {
                "B1": frozen["B1"]["action_id"],
                "B4_CIBS_FIXED": frozen["B4_CIBS_FIXED"]["action_id"],
            },
        }
        raw_files[dataset] = {
            "all_actions": action_files,
            "B0": {"path": str(b0_csv.relative_to(ROOT)), "sha256": sha256(b0_csv), "rows": 500},
        }
    manifest = {
        "schema_version": 1,
        "status": "PASS_EVALUATION_HELD_OUT_RISK_DIAGNOSTIC",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "evaluation_execution_commit": head,
        "selected_action_commit": "44e206674612f6630373aa49375c27059d0f3040",
        "selected_action_manifest_sha256": sha256(SELECTED),
        "evaluation_reselection_performed": False,
        "compiler": compiler,
        "resource_gate": resource,
        "datasets": dataset_results,
        "raw_files": raw_files,
        "statistics": {"bootstrap_replicates": BOOTSTRAP_REPLICATES, "bootstrap_seed": BOOTSTRAP_SEED,
                       "interval": "paired percentile 95%"},
        "evaluation_accessed": True,
        "future_confirm_accessed": False,
        "positive_cibs_evidence": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = {
        "schema_version": 1,
        "status": "PASS_EVALUATION_COMPLETE_NO_RESELECTION",
        "evaluation_manifest_sha256": sha256(MANIFEST),
        "selected_action_manifest_sha256": sha256(SELECTED),
        "evaluation_reselection_performed": False,
        "future_confirm_accessed": False,
        "positive_cibs_evidence": False,
        "next": "MAIN_STAGE1_ANALYSIS_AND_PREREGISTERED_K2_ABLATION",
    }
    GATE.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event("complete", evaluation_manifest_sha256=sha256(MANIFEST), gate_sha256=sha256(GATE),
          evaluation_reselection_performed=False, future_confirm_accessed=False)
    print(json.dumps({
        "status": gate["status"],
        "B4_vs_B1": {dataset: result["comparisons"]["B4_vs_B1"] for dataset, result in dataset_results.items()},
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        GATE.parent.mkdir(parents=True, exist_ok=True)
        if not GATE.exists():
            GATE.write_text(json.dumps({
                "schema_version": 1,
                "status": "STOPPED_EVALUATION",
                "error": str(error),
                "evaluation_reselection_performed": False,
                "future_confirm_accessed": False,
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        event("failure", error=str(error), future_confirm_accessed=False)
        raise
