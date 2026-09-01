#!/usr/bin/env python3
"""Independently replay the frozen Stage-I evaluation bookkeeping."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/icba_cibs_stage1/evaluation_independent_validation.json"
MANIFEST = ROOT / "manifests/icba_cibs_stage1_evaluation_realization.json"
GATE = ROOT / "results/icba_cibs_stage1/evaluation_gate.json"
SELECTED = ROOT / "manifests/icba_cibs_stage1_selected_actions.json"
BUILD_MANIFEST = ROOT / "manifests/icba_cibs_stage1_build_realization.json"
EVENTS = ROOT / "results/icba_cibs_stage1/evaluation_events.jsonl"
ACCESS = ROOT / "results/icba_cibs_stage1/phase1/query_roles/truth_access_log.csv"
RUNNER_SCRIPT = ROOT / "scripts/icba_cibs_stage1/run_evaluation.py"
DATASETS = ("sift_100k", "arxiv_nomic_100k")
RAW_EFS = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_runner_module():
    spec = importlib.util.spec_from_file_location("frozen_evaluation", RUNNER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen evaluation runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_equal(left, right, context: str) -> None:
    if left != right:
        raise AssertionError(f"{context}: independently recomputed value differs")


def validate_action_matrix(rows: list[dict[str, str]], dataset: str, build_id: str) -> None:
    if len(rows) != 500 * len(RAW_EFS):
        raise AssertionError(f"{dataset}/{build_id}: action row count")
    cells: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        query_row = int(row["query_row"])
        cells[query_row].append(int(row["requested_ef"]))
        if row["endpoint_status"] != "PASS":
            raise AssertionError(f"{dataset}/{build_id}: endpoint failure")
        if row["native_tracer_topk_equal"] != "1":
            raise AssertionError(f"{dataset}/{build_id}: native/tracer top-k mismatch")
        if row["native_tracer_ndc_equal"] != "1":
            raise AssertionError(f"{dataset}/{build_id}: native/tracer NDC mismatch")
        if row["native_ndc"] != row["tracer_ndc"]:
            raise AssertionError(f"{dataset}/{build_id}: NDC fields differ")
        expected_z = int(float(row["raw_recall_at_10"]) < 0.90)
        if int(row["Z_abs"]) != expected_z:
            raise AssertionError(f"{dataset}/{build_id}: Z_abs mismatch")
    if set(cells) != set(range(500)):
        raise AssertionError(f"{dataset}/{build_id}: query coverage")
    for query_row, efs in cells.items():
        if tuple(sorted(efs)) != RAW_EFS:
            raise AssertionError(f"{dataset}/{build_id}/q={query_row}: ef grid")


def main() -> None:
    if OUT.exists():
        raise RuntimeError("refusing to overwrite evaluation validation")
    frozen = load_runner_module()
    manifest = load_json(MANIFEST)
    gate = load_json(GATE)
    selected = load_json(SELECTED)
    build_manifest = load_json(BUILD_MANIFEST)

    if gate["evaluation_manifest_sha256"] != sha256(MANIFEST):
        raise AssertionError("evaluation manifest hash chain")
    if gate["selected_action_manifest_sha256"] != sha256(SELECTED):
        raise AssertionError("selected-action hash chain")
    if manifest["selected_action_manifest_sha256"] != sha256(SELECTED):
        raise AssertionError("manifest selected-action hash chain")
    if manifest["selected_action_commit"] != "44e206674612f6630373aa49375c27059d0f3040":
        raise AssertionError("selected action commit")
    if manifest["evaluation_execution_commit"] != "0eac6a5e7203fd69f51ca59bb630c9b9238530a9":
        raise AssertionError("evaluation execution commit")
    if manifest["evaluation_reselection_performed"] or manifest["future_confirm_accessed"]:
        raise AssertionError("evaluation isolation flags")

    events = [json.loads(line) for line in EVENTS.read_text(encoding="utf-8").splitlines() if line]
    if not events or events[0]["event"] != "start" or events[-1]["event"] != "complete":
        raise AssertionError("event boundary")
    if any(event.get("returncode", 0) != 0 for event in events):
        raise AssertionError("command failure in event log")
    serialized_events = json.dumps(events, sort_keys=True)
    if "future_confirm" in serialized_events and '"future_confirm_accessed": false' not in serialized_events:
        raise AssertionError("future-confirm event contamination")
    if any(event.get("evaluation_reselection_allowed") for event in events):
        raise AssertionError("evaluation reselection enabled")

    access_rows = read_csv(ACCESS)
    if len(access_rows) != 8:
        raise AssertionError("access-log row count")
    for row in access_rows:
        if row["role"] == "cibs_future_confirm":
            exact_equal((row["truth_accessed"], row["action_outcome_accessed"]), ("0", "0"), "future firewall")
        elif row["role"] == "cibs_evaluation":
            exact_equal((row["truth_accessed"], row["action_outcome_accessed"]), ("1", "1"), "evaluation access")

    dataset_checks = {}
    for dataset in DATASETS:
        all_rows: list[dict[str, str]] = []
        for item in manifest["raw_files"][dataset]["all_actions"]:
            path = ROOT / item["path"]
            exact_equal(sha256(path), item["sha256"], f"{dataset}/{item['build_id']} sha")
            rows = read_csv(path)
            exact_equal(len(rows), item["rows"], f"{dataset}/{item['build_id']} rows")
            validate_action_matrix(rows, dataset, item["build_id"])
            for row in rows:
                row["dataset"] = dataset
                row["build_id"] = item["build_id"]
            all_rows.extend(rows)

        b0_item = manifest["raw_files"][dataset]["B0"]
        b0_path = ROOT / b0_item["path"]
        exact_equal(sha256(b0_path), b0_item["sha256"], f"{dataset}/B0 sha")
        b0_rows = read_csv(b0_path)
        exact_equal(len(b0_rows), 500, f"{dataset}/B0 rows")
        for row in b0_rows:
            if row["endpoint_status"] != "PASS" or row["native_tracer_topk_equal"] != "1" or row["native_tracer_ndc_equal"] != "1":
                raise AssertionError(f"{dataset}/B0 equivalence")
            if int(row["actual_expansions"]) != 100000 or int(row["visited_count"]) != 100000:
                raise AssertionError(f"{dataset}/B0 full enumeration")
            if float(row["raw_recall_at_10"]) != 1.0 or int(row["Z_abs"]) != 0:
                raise AssertionError(f"{dataset}/B0 exactness")
            row["dataset"] = dataset
            row["build_id"] = "G1"

        frozen_actions = selected["datasets"][dataset]
        method_rows = {
            "B0": b0_rows,
            "B1": frozen.fixed_action_rows(all_rows, dataset, frozen_actions["B1"]),
            "B2": frozen.fixed_action_rows(all_rows, dataset, frozen_actions["B2"]),
            "B3": frozen.fixed_action_rows(all_rows, dataset, frozen_actions["B3"]),
            "B4_CIBS_FIXED": frozen.fixed_action_rows(all_rows, dataset, frozen_actions["B4_CIBS_FIXED"]),
        }
        for method, rows in method_rows.items():
            recomputed = frozen.summarize(rows, build_manifest)
            json_normalized = json.loads(json.dumps(recomputed, sort_keys=True))
            exact_equal(json_normalized, manifest["datasets"][dataset]["methods"][method], f"{dataset}/{method} summary")
        for baseline in ("B0", "B1"):
            recomputed = frozen.paired_bootstrap(method_rows["B4_CIBS_FIXED"], method_rows[baseline])
            exact_equal(recomputed, manifest["datasets"][dataset]["comparisons"][f"B4_vs_{baseline}"], f"{dataset}/B4_vs_{baseline}")
        dataset_checks[dataset] = {
            "action_cells": len(all_rows),
            "B0_full_enumeration_queries": len(b0_rows),
            "selected_B1": frozen_actions["B1"]["action_id"],
            "selected_B4": frozen_actions["B4_CIBS_FIXED"]["action_id"],
            "recomputed_summaries": "PASS",
            "recomputed_bootstrap": "PASS",
        }

    result = {
        "schema_version": 1,
        "status": "PASS_EVALUATION_INDEPENDENT_REPLAY",
        "evaluation_manifest_sha256": sha256(MANIFEST),
        "selected_action_manifest_sha256": sha256(SELECTED),
        "event_log_sha256": sha256(EVENTS),
        "evaluation_reselection_performed": False,
        "future_confirm_accessed": False,
        "native_tracer_equivalence": "PASS_ALL_EVALUATION_ROWS",
        "fixed_safe_fallback": "PASS_1000_OF_1000_FULL_ENUMERATION_EXACT_ROWS",
        "datasets": dataset_checks,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
