#!/usr/bin/env python3
"""Run the frozen sentinel certificate and freeze the selected actions.

This program is committed before it may access any sentinel truth or action
outcome.  It never opens evaluation or future-confirm queries or truth.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import statistics
import subprocess
import time
from pathlib import Path

from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results/icba_cibs_stage1/sentinel"
SELECTED = ROOT / "manifests/icba_cibs_stage1_selected_actions.json"
GATE = ROOT / "results/icba_cibs_stage1/sentinel_gate.json"
EVENTS = ROOT / "results/icba_cibs_stage1/sentinel_events.jsonl"
BUILD_MANIFEST = ROOT / "manifests/icba_cibs_stage1_build_realization.json"
BUILD_GATE = ROOT / "results/icba_cibs_stage1/build_and_fallback_gate.json"
ROLE_MANIFEST = ROOT / "manifests/icba_cibs_stage1_query_roles.json"
RUNTIME_MANIFEST = ROOT / "results/icba_cibs_stage1/runtime/runtime_input_manifest.json"
RUNNER = ROOT / "results/icba_cibs_stage1/runtime/tools/icba_cibs_stage1_sentinel_runner"
RAW_EFS = [10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]
BUILD_IDS = ["G1", "G2", "G3"]
DATASETS = {
    "sift_100k": {"dimensions": 128},
    "arxiv_nomic_100k": {"dimensions": 768},
}
FLAGS = [
    "-std=c++17",
    "-O3",
    "-DNDEBUG",
    "-DNO_MANUAL_VECTORIZATION",
    "-Wall",
    "-Wextra",
    "-Wpedantic",
]
ALPHA = 0.05


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def event(name: str, **fields) -> None:
    record = {"time_unix_ns": time.time_ns(), "event": name, **fields}
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def run(args: list[str], log_path: Path) -> None:
    started = time.time_ns()
    with log_path.open("w", encoding="utf-8") as handle:
        completed = subprocess.run(args, stdout=handle, stderr=subprocess.STDOUT, text=True)
    event(
        "command",
        argv=args,
        elapsed_ns=time.time_ns() - started,
        log=str(log_path.relative_to(ROOT)),
        returncode=completed.returncode,
    )
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


def percentile(values: list[int], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def cp_ucb(failures: int, n: int, family_size: int) -> float:
    if failures >= n:
        return 1.0
    return float(beta.ppf(1 - ALPHA / family_size, failures + 1, n - failures))


def summarize_action(rows: list[dict[str, str]], family_size: int) -> dict[str, object]:
    if len(rows) != 256:
        raise RuntimeError(f"sentinel action has {len(rows)} rows, expected 256")
    failures = sum(int(row["Z_abs"]) for row in rows)
    endpoint_failures = sum(row["endpoint_status"] != "PASS" for row in rows)
    for row in rows:
        if row["endpoint_status"] == "PASS" and (
            row["native_tracer_topk_equal"] != "1"
            or row["native_tracer_ndc_equal"] != "1"
        ):
            raise RuntimeError("INVALID_CIBS_NDC_INSTRUMENTATION")
    ndc = [int(row["native_ndc"]) for row in rows]
    expansions = [int(row["actual_expansions"]) for row in rows]
    wall = [int(row["wall_clock_ns"]) for row in rows]
    recall = [float(row["raw_recall_at_10"]) for row in rows]
    ucb = cp_ucb(failures, len(rows), family_size)
    return {
        "n": len(rows),
        "failures": failures,
        "endpoint_failures": endpoint_failures,
        "mean_recall_at_10": statistics.fmean(recall),
        "risk_cp_ucb": ucb,
        "risk_cp_family_size": family_size,
        "certified": ucb <= 0.05,
        "mean_ndc": statistics.fmean(ndc),
        "p50_ndc": percentile(ndc, 0.50),
        "p95_ndc": percentile(ndc, 0.95),
        "p99_ndc": percentile(ndc, 0.99),
        "mean_expansions": statistics.fmean(expansions),
        "p95_expansions": percentile(expansions, 0.95),
        "mean_wall_clock_ns": statistics.fmean(wall),
        "p95_wall_clock_ns": percentile(wall, 0.95),
        "p99_wall_clock_ns": percentile(wall, 0.99),
    }


def select_action(actions: list[dict[str, object]]) -> dict[str, object] | None:
    certified = [action for action in actions if action["statistics"]["certified"]]
    if not certified:
        return None
    return min(
        certified,
        key=lambda action: (
            action["statistics"]["mean_ndc"],
            action["statistics"]["p95_ndc"],
            action["requested_ef"],
            BUILD_IDS.index(action["build_id"]),
        ),
    )


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
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, text=True
    ).splitlines()
    unexpected = [line for line in status if not line[3:].startswith(allowed)]
    if unexpected:
        raise RuntimeError(f"unexpected pre-sentinel worktree state: {unexpected}")


def resource_snapshot() -> dict[str, int | str]:
    stats = os.statvfs(ROOT)
    free = stats.f_bavail * stats.f_frsize
    required = 3_365_465_672 + 5 * 1024**3
    result: dict[str, int | str] = {
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
    command = [
        "g++",
        *FLAGS,
        "-Ithird_party/hnswlib",
        "-Icpp/include",
        "cpp/src/icba_cibs_stage1_runner.cpp",
        "-o",
        str(RUNNER),
    ]
    run(command, RESULTS / "compile.log")
    return {
        "binary": str(RUNNER.relative_to(ROOT)),
        "binary_sha256": sha256(RUNNER),
        "source": "cpp/src/icba_cibs_stage1_runner.cpp",
        "source_sha256": sha256(ROOT / "cpp/src/icba_cibs_stage1_runner.cpp"),
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "flags": FLAGS,
        "threads": 1,
        "simd": "NO_MANUAL_VECTORIZATION_SCALAR",
    }


def main() -> None:
    if RESULTS.exists() or SELECTED.exists() or GATE.exists() or EVENTS.exists():
        raise RuntimeError("refusing to overwrite sentinel or selected-action artifacts")
    verify_clean_tracked_state()
    RESULTS.mkdir(parents=True)
    EVENTS.touch(exist_ok=False)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    event("start", head=head, evidence_level="EXPLORATORY_FIXED_TARGET_STAGE_I")
    build_manifest = json.loads(BUILD_MANIFEST.read_text(encoding="utf-8"))
    build_gate = json.loads(BUILD_GATE.read_text(encoding="utf-8"))
    roles = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))
    runtime = json.loads(RUNTIME_MANIFEST.read_text(encoding="utf-8"))
    if build_manifest["status"] != "PASS_BUILD_REALIZATION_BEFORE_SENTINEL":
        raise RuntimeError("build realization is not frozen")
    if not build_gate["sentinel_access_authorized_next"]:
        raise RuntimeError("build/fallback gate does not authorize sentinel")
    build_records = {
        (row["dataset"], row["build_id"]): row for row in build_manifest["builds"]
    }
    for row in build_manifest["builds"]:
        if sha256(ROOT / row["artifact_path"]) != row["artifact_sha256"]:
            raise RuntimeError(f"artifact checksum replay failed: {row['dataset']}/{row['build_id']}")
    resource = resource_snapshot()
    event("resource_gate", stage="before_sentinel", **resource)
    compiler = compile_runner()
    all_actions: dict[str, list[dict[str, object]]] = {}
    selected_by_dataset: dict[str, dict[str, object]] = {}
    truth_records: dict[str, dict[str, object]] = {}
    raw_records: dict[str, list[dict[str, object]]] = {}
    sentinel_started = time.time_ns()
    selection_cost_wall_clock_ns = 0
    for dataset, spec in DATASETS.items():
        role = roles["datasets"][dataset]["roles"]["cibs_sentinel"]
        query_path = ROOT / runtime["datasets"][dataset]["queries"]["cibs_sentinel"]["runtime_path"]
        base_path = ROOT / runtime["datasets"][dataset]["runtime_base_path"]
        truth_csv = RESULTS / f"{dataset}__sentinel_truth.csv"
        truth_meta = RESULTS / f"{dataset}__sentinel_truth.meta"
        event(
            "truth_access_begin",
            dataset=dataset,
            role="cibs_sentinel",
            query_count=256,
            query_file_sha256=role["queries_file_sha256"],
            source_ids_file_sha256=role["source_ids_file_sha256"],
            evaluation_accessed=False,
            future_confirm_accessed=False,
        )
        run(
            [
                str(RUNNER),
                "truth",
                str(base_path),
                str(query_path),
                str(spec["dimensions"]),
                str(truth_csv),
                str(truth_meta),
            ],
            RESULTS / f"{dataset}__sentinel_truth.log",
        )
        truth_meta_values = parse_meta(truth_meta)
        if truth_meta_values["status"] != "PASS" or truth_meta_values["queries"] != 256:
            raise RuntimeError(f"sentinel truth acquisition failed: {dataset}")
        truth_records[dataset] = {
            "role": "cibs_sentinel",
            "query_count": 256,
            "query_file_sha256": role["queries_file_sha256"],
            "source_ids_file_sha256": role["source_ids_file_sha256"],
            "truth_path": str(truth_csv.relative_to(ROOT)),
            "truth_sha256": sha256(truth_csv),
            "truth_meta_path": str(truth_meta.relative_to(ROOT)),
            "truth_meta_sha256": sha256(truth_meta),
            "truth_cost": truth_meta_values,
            "truth_source": "independent full scan of frozen 100K runtime base",
            "tie_rule": "distance_then_label",
        }
        event("truth_access_complete", dataset=dataset, truth_sha256=sha256(truth_csv))
        dataset_actions: list[dict[str, object]] = []
        raw_records[dataset] = []
        for build_id in BUILD_IDS:
            record = build_records[(dataset, build_id)]
            if sha256(ROOT / record["artifact_path"]) != record["artifact_sha256"]:
                raise RuntimeError(f"artifact changed before sentinel: {dataset}/{build_id}")
            raw_csv = RESULTS / f"{dataset}__{build_id}__sentinel_actions.csv"
            raw_meta = raw_csv.with_suffix(".meta")
            run(
                [
                    str(RUNNER),
                    "sentinel",
                    str(ROOT / record["artifact_path"]),
                    str(query_path),
                    str(spec["dimensions"]),
                    ",".join(map(str, RAW_EFS)),
                    str(truth_csv),
                    str(raw_csv),
                ],
                RESULTS / f"{dataset}__{build_id}__sentinel_actions.log",
            )
            meta = parse_meta(raw_meta)
            if meta["status"] != "PASS" or meta["rows"] != 256 * len(RAW_EFS):
                raise RuntimeError("INVALID_CIBS_NDC_INSTRUMENTATION")
            with raw_csv.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            if len(rows) != 256 * len(RAW_EFS):
                raise RuntimeError("action matrix is not 256x12")
            raw_records[dataset].append(
                {
                    "build_id": build_id,
                    "path": str(raw_csv.relative_to(ROOT)),
                    "sha256": sha256(raw_csv),
                    "meta_path": str(raw_meta.relative_to(ROOT)),
                    "meta_sha256": sha256(raw_meta),
                    "rows": len(rows),
                }
            )
            for ef in RAW_EFS:
                action_rows = [row for row in rows if int(row["requested_ef"]) == ef]
                dataset_actions.append(
                    {
                        "action_id": f"{build_id}:ef={ef}",
                        "build_id": build_id,
                        "requested_ef": ef,
                        "artifact_sha256": record["artifact_sha256"],
                        "statistics": summarize_action(action_rows, 36),
                    }
                )
        if len(dataset_actions) != 36:
            raise RuntimeError("action matrix does not contain 36 actions")
        all_actions[dataset] = dataset_actions
        selection_started = time.time_ns()
        b4 = select_action(dataset_actions)
        b1_candidates = []
        for action in dataset_actions:
            if action["build_id"] != "G1":
                continue
            b1_action = dict(action)
            raw_file = next(row for row in raw_records[dataset] if row["build_id"] == "G1")
            with (ROOT / raw_file["path"]).open(newline="", encoding="utf-8") as handle:
                rows = [
                    row
                    for row in csv.DictReader(handle)
                    if int(row["requested_ef"]) == action["requested_ef"]
                ]
            b1_action["statistics"] = summarize_action(rows, 12)
            b1_candidates.append(b1_action)
        b1 = select_action(b1_candidates)
        fallback = {
            "kind": "fixed_safe_fallback",
            "build_id": "G1",
            "requested_ef": 100000,
            "artifact_sha256": build_gate["fallback"][dataset]["artifact_sha256"],
            "design_cost_and_exactness": build_gate["fallback"][dataset]["cost_and_exactness"],
            "trigger": "EMPTY_CERTIFIED_SET",
        }
        selected_by_dataset[dataset] = {
            "B0": fallback,
            "B1": b1 if b1 is not None else fallback,
            "B2": next(action for action in dataset_actions if action["action_id"] == "G1:ef=512"),
            "B3": next(action for action in dataset_actions if action["action_id"] == "G2:ef=512"),
            "B4_CIBS_FIXED": b4 if b4 is not None else fallback,
            "B5": {
                "kind": "post_hoc_per_query_oracle_over_all_36_actions",
                "deployable": False,
                "selection_use": "NONE",
            },
            "simultaneously_certified_action_ids": [
                action["action_id"] for action in dataset_actions if action["statistics"]["certified"]
            ],
            "G1_alpha_over_12_certified_action_ids": [
                action["action_id"] for action in b1_candidates if action["statistics"]["certified"]
            ],
        }
        selection_cost_wall_clock_ns += time.time_ns() - selection_started
    sentinel_elapsed = time.time_ns() - sentinel_started
    summary = {
        "schema_version": 1,
        "status": "PASS_SENTINEL_PROCEDURE_CERTIFICATE",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "sentinel_semantics": "FROZEN_FINITE_POOL_WITHOUT_REPLACEMENT",
        "head_before_sentinel": head,
        "build_realization_commit": "404b504d0f063ed66101d08e5c4ae62964c14ea6",
        "build_manifest_sha256": sha256(BUILD_MANIFEST),
        "build_gate_sha256": sha256(BUILD_GATE),
        "role_manifest_sha256": sha256(ROLE_MANIFEST),
        "compiler": compiler,
        "resource_gate": resource,
        "risk": {
            "alpha": ALPHA,
            "family_size": 36,
            "one_sided_exact_clopper_pearson": True,
            "certification_threshold": 0.05,
        },
        "truth": truth_records,
        "raw_action_files": raw_records,
        "actions": all_actions,
        "sentinel_truth_search_and_selection_wall_clock_ns": sentinel_elapsed,
        "selection_cost_wall_clock_ns": selection_cost_wall_clock_ns,
        "sentinel_truth_accessed": True,
        "sentinel_action_outcomes_accessed": True,
        "evaluation_accessed": False,
        "future_confirm_accessed": False,
    }
    summary_path = RESULTS / "sentinel_procedure_certificate.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    selected_manifest = {
        "schema_version": 1,
        "status": "FROZEN_AFTER_SENTINEL_BEFORE_EVALUATION",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "selection_rule": {
            "B4_primary": "minimum sentinel mean exact NDC among alpha/36 CP-certified actions",
            "B1_primary": "minimum sentinel mean exact NDC among G1 alpha/12 CP-certified actions",
            "tie_break": ["lower_p95_NDC", "lower_raw_ef", "lower_build_id"],
            "raw_recall_monotonicity_assumed": False,
            "right_censoring_counted_as_success": False,
            "fallback": "G1 raw ef=100000 only when the applicable certified set is empty",
        },
        "datasets": selected_by_dataset,
        "sentinel_certificate_path": str(summary_path.relative_to(ROOT)),
        "sentinel_certificate_sha256": sha256(summary_path),
        "build_realization_commit": "404b504d0f063ed66101d08e5c4ae62964c14ea6",
        "sentinel_execution_commit": head,
        "evaluation_access_authorized_next": True,
        "evaluation_reselection_allowed": False,
        "evaluation_accessed": False,
        "future_confirm_accessed": False,
        "positive_cibs_evidence": False,
    }
    SELECTED.write_text(json.dumps(selected_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    selected_sha = sha256(SELECTED)
    (RESULTS / "selected_actions.sha256").write_text(
        f"{selected_sha}  manifests/icba_cibs_stage1_selected_actions.json\n",
        encoding="utf-8",
    )
    gate = {
        "schema_version": 1,
        "status": "PASS_SENTINEL_SELECTION_FROZEN",
        "selected_action_manifest_sha256": selected_sha,
        "sentinel_certificate_sha256": sha256(summary_path),
        "evaluation_access_authorized_next": True,
        "evaluation_reselection_allowed": False,
        "future_confirm_accessed": False,
        "positive_cibs_evidence": False,
    }
    GATE.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event(
        "complete",
        selected_action_manifest_sha256=selected_sha,
        sentinel_certificate_sha256=sha256(summary_path),
        gate_sha256=sha256(GATE),
    )
    print(json.dumps({
        "status": gate["status"],
        "selected": {
            dataset: values["B4_CIBS_FIXED"]["action_id"]
            if "action_id" in values["B4_CIBS_FIXED"]
            else "G1:ef=100000:fallback"
            for dataset, values in selected_by_dataset.items()
        },
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        GATE.parent.mkdir(parents=True, exist_ok=True)
        if not GATE.exists():
            GATE.write_text(json.dumps({
                "schema_version": 1,
                "status": "STOPPED_SENTINEL_OR_SELECTION",
                "error": str(error),
                "evaluation_access_authorized_next": False,
                "evaluation_accessed": False,
                "future_confirm_accessed": False,
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        event("failure", error=str(error))
        raise
