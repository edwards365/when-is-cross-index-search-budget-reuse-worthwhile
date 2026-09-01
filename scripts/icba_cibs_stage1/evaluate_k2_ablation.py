#!/usr/bin/env python3
"""Link the committed K=2 selection to evaluation rows without reselection."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manifests/icba_cibs_stage1_k2_selected_actions.json"
SELECTION_GATE = ROOT / "results/icba_cibs_stage1/k2_ablation/selection_gate.json"
EVALUATION = ROOT / "manifests/icba_cibs_stage1_evaluation_realization.json"
BUILD = ROOT / "manifests/icba_cibs_stage1_build_realization.json"
FROZEN_RUNNER = ROOT / "scripts/icba_cibs_stage1/run_evaluation.py"
OUT = ROOT / "results/icba_cibs_stage1/k2_ablation/evaluation.json"
GATE = ROOT / "results/icba_cibs_stage1/k2_ablation/complete_gate.json"
DATASETS = ("sift_100k", "arxiv_nomic_100k")


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


def load_frozen_runner():
    spec = importlib.util.spec_from_file_location("frozen_evaluation", FROZEN_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen evaluation runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows_for_action(dataset: str, action: dict) -> list[dict[str, str]]:
    build = action["build_id"]
    ef = int(action["requested_ef"])
    path = ROOT / f"results/icba_cibs_stage1/evaluation/{dataset}__{build}__evaluation_all_actions.csv"
    rows = [row for row in read_csv(path) if int(row["requested_ef"]) == ef]
    if len(rows) != 500:
        raise AssertionError("K2 evaluation action incomplete")
    for row in rows:
        row["dataset"] = dataset
        row["build_id"] = build
    return rows


def main() -> None:
    if OUT.exists() or GATE.exists():
        raise RuntimeError("refusing to overwrite K2 evaluation")
    frozen = load_json(MANIFEST)
    selection_gate = load_json(SELECTION_GATE)
    evaluation = load_json(EVALUATION)
    build_manifest = load_json(BUILD)
    runner = load_frozen_runner()
    if selection_gate["manifest_sha256"] != sha256(MANIFEST):
        raise AssertionError("K2 selection hash chain")
    if frozen["status"] != "FROZEN_K2_ABLATION_SELECTION_AFTER_MAIN":
        raise AssertionError("K2 selection is not frozen")
    if frozen["evaluation_access_used_for_selection"]:
        raise AssertionError("K2 selection contamination")
    if frozen["main_analysis_commit"] != "a2fbd5002865af3fb088a2498725dcb861ccf245":
        raise AssertionError("main completion binding")
    datasets = {}
    for dataset in DATASETS:
        selection = frozen["datasets"][dataset]
        b4_action = selection["selected_action"]
        b1_action = selection["B1_G1_alpha_over_12"]
        b4_rows = rows_for_action(dataset, b4_action)
        b1_rows = rows_for_action(dataset, b1_action)
        b4_summary = runner.summarize(b4_rows, build_manifest)
        b1_summary = runner.summarize(b1_rows, build_manifest)
        comparison = runner.paired_bootstrap(b4_rows, b1_rows)
        datasets[dataset] = {
            "K2_selected_action": b4_action["action_id"],
            "K2_B1_action": b1_action["action_id"],
            "B4_CIBS_K2": b4_summary,
            "B1_G1_K2": b1_summary,
            "B4_vs_B1": comparison,
            "selection_recomputed_from_evaluation": False,
        }
    result = {
        "schema_version": 1,
        "status": "PASS_K2_ABLATION_COMPLETE",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "selection_commit": "89a1ca6d77d370cbaff3738c7b41ff728649d19b",
        "selection_manifest_sha256": sha256(MANIFEST),
        "main_K3_replaced": False,
        "evaluation_reselection_performed": False,
        "future_confirm_accessed": False,
        "datasets": datasets,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = {
        "schema_version": 1,
        "status": "PASS_K2_ABLATION_SEALED_DOES_NOT_REPLACE_MAIN",
        "result_sha256": sha256(OUT),
        "selection_manifest_sha256": sha256(MANIFEST),
        "main_K3_replaced": False,
        "evaluation_reselection_performed": False,
        "future_confirm_accessed": False,
        "next": "FINAL_REPORTS_FIGURES_CHECKSUMS_AND_DECISION",
    }
    GATE.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({dataset: data["B4_vs_B1"] for dataset, data in datasets.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
