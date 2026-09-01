#!/usr/bin/env python3
"""Freeze the preregistered K=2 ablation from sentinel rows only."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "results/icba_cibs_stage1/analysis/main_gate_decision.json"
PREREG = ROOT / "manifests/icba_cibs_stage1_phase1_preregistration.json"
OUT = ROOT / "results/icba_cibs_stage1/k2_ablation"
MANIFEST = ROOT / "manifests/icba_cibs_stage1_k2_selected_actions.json"
GATE = OUT / "selection_gate.json"
DATASETS = ("sift_100k", "arxiv_nomic_100k")
BUILDS = ("G1", "G2")
EFS = (10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
N = 128
M = 24
ALPHA = 0.05


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


def cp_ucb(failures: int, n: int, family: int) -> float:
    if failures >= n:
        return 1.0
    return float(beta.ppf(1.0 - ALPHA / family, failures + 1, n - failures))


def summarize(rows: list[dict[str, str]], family: int) -> dict[str, object]:
    if len(rows) != N:
        raise AssertionError("K2 action does not contain 128 rows")
    failures = sum(int(row["Z_abs"]) for row in rows)
    return {
        "n": N,
        "failures": failures,
        "maximum_certifiable_failures": 0,
        "risk_cp_family_size": family,
        "risk_cp_ucb": cp_ucb(failures, N, family),
        "certified": failures == 0 and cp_ucb(failures, N, family) <= 0.05,
        "mean_recall_at_10": statistics.fmean(float(row["raw_recall_at_10"]) for row in rows),
        "mean_ndc": statistics.fmean(int(row["native_ndc"]) for row in rows),
        "p95_ndc": float(np.percentile([int(row["native_ndc"]) for row in rows], 95)),
        "mean_expansions": statistics.fmean(int(row["actual_expansions"]) for row in rows),
        "mean_wall_clock_ns": statistics.fmean(int(row["wall_clock_ns"]) for row in rows),
        "endpoint_failures": sum(row["endpoint_status"] != "PASS" for row in rows),
    }


def selection_key(item: dict) -> tuple:
    return (
        item["statistics"]["mean_ndc"],
        item["statistics"]["p95_ndc"],
        item["requested_ef"],
        item["build_id"],
    )


def main() -> None:
    if OUT.exists() or MANIFEST.exists():
        raise RuntimeError("refusing to overwrite K2 selection")
    main_decision = load_json(MAIN)
    prereg = load_json(PREREG)
    if main_decision["status"] != "MAIN_K3_ANALYSIS_COMPLETE_MINIMUM_GATE_FAILED":
        raise AssertionError("main K3 analysis is not complete")
    frozen = prereg["ablation"]
    if frozen != {
        "K": 2,
        "L": 12,
        "M": 24,
        "authorized_after_main_completion_only": True,
        "maximum_failures_for_certificate": 0,
        "sentinel_n": 128,
    }:
        raise AssertionError("K2 preregistration differs")
    OUT.mkdir(parents=True)
    datasets = {}
    source_hashes = {}
    for dataset in DATASETS:
        grouped = defaultdict(list)
        source_hashes[dataset] = {}
        for build in BUILDS:
            path = ROOT / f"results/icba_cibs_stage1/sentinel/{dataset}__{build}__sentinel_actions.csv"
            source_hashes[dataset][build] = sha256(path)
            for row in read_csv(path):
                query_row = int(row["query_row"])
                if query_row >= N:
                    continue
                ef = int(row["requested_ef"])
                if ef not in EFS:
                    raise AssertionError("unexpected raw ef")
                if row["native_tracer_topk_equal"] != "1" or row["native_tracer_ndc_equal"] != "1":
                    raise AssertionError("INVALID_CIBS_NDC_INSTRUMENTATION")
                grouped[(build, ef)].append(row)
        if len(grouped) != M or any(len(rows) != N for rows in grouped.values()):
            raise AssertionError("K2 matrix is not 24 x 128")
        actions = []
        for build in BUILDS:
            for ef in EFS:
                actions.append({
                    "action_id": f"{build}:ef={ef}",
                    "build_id": build,
                    "requested_ef": ef,
                    "statistics": summarize(grouped[(build, ef)], M),
                })
        certified = [item for item in actions if item["statistics"]["certified"]]
        if not certified:
            raise AssertionError("K2 certified set empty; fallback path not implemented in ablation")
        selected = min(certified, key=selection_key)

        g1_actions = [item for item in actions if item["build_id"] == "G1"]
        g1_retested = []
        for item in g1_actions:
            copy = dict(item)
            copy["statistics"] = summarize(grouped[("G1", item["requested_ef"])], 12)
            g1_retested.append(copy)
        g1_certified = [item for item in g1_retested if item["statistics"]["certified"]]
        b1 = min(g1_certified, key=selection_key) if g1_certified else None
        datasets[dataset] = {
            "sentinel_prefix_rule": "query_row 0..127 of the frozen ordered cibs_sentinel role",
            "actions": actions,
            "simultaneously_certified_action_ids": [item["action_id"] for item in certified],
            "selected_action": selected,
            "B1_G1_alpha_over_12": b1,
        }

    manifest = {
        "schema_version": 1,
        "status": "FROZEN_K2_ABLATION_SELECTION_AFTER_MAIN",
        "evidence_level": "EXPLORATORY_FIXED_TARGET_STAGE_I",
        "conditionality": "CONDITIONAL_ON_ONE_REGISTERED_PORTFOLIO",
        "main_analysis_commit": "a2fbd5002865af3fb088a2498725dcb861ccf245",
        "K": 2,
        "L": 12,
        "M": 24,
        "sentinel_n": 128,
        "maximum_certifiable_failures": 0,
        "alpha": ALPHA,
        "selection_rule": "minimum mean sentinel NDC; tie p95 NDC, raw ef, build ID",
        "datasets": datasets,
        "sentinel_source_sha256": source_hashes,
        "evaluation_access_used_for_selection": False,
        "future_confirm_accessed": False,
        "may_not_replace_main_K3": True,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gate = {
        "schema_version": 1,
        "status": "PASS_K2_SELECTION_FROZEN_BEFORE_K2_EVALUATION_LINKAGE",
        "manifest_sha256": sha256(MANIFEST),
        "evaluation_access_used_for_selection": False,
        "future_confirm_accessed": False,
        "may_not_replace_main_K3": True,
    }
    GATE.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({dataset: data["selected_action"]["action_id"] for dataset, data in datasets.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
