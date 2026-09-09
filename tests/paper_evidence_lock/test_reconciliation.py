#!/usr/bin/env python3
"""Deterministic integrity checks for the paper-evidence lock outputs."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "paper_evidence_lock"
MAN = ROOT / "manifests" / "graph_anns_paper_evidence_lock_decision.json"


def rows(name: str):
    with (RES / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    spec = importlib.util.spec_from_file_location("paper_evidence_reconcile", ROOT / "scripts" / "paper_evidence_lock" / "reconcile.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert abs(module._student_t_quantile(0.975, 17) - 2.109815578) < 1e-8
    assert abs(module._student_t_quantile(0.975, 23) - 2.068657610) < 1e-8
    numeric = rows("numeric_reconciliation.csv")
    required = {"current_gate_a_main_physical_rows", "current_gate_a_main_unique_query_budget_units", "actual_common_budget_grid", "historical_972000_cross_index", "historical_648000_tournament"}
    assert required <= {r["metric_name"] for r in numeric}
    assert {r["conflict_status"] for r in numeric} >= {"RECONCILED_BY_CONTEXT", "SUPERSEDED_BY_RAW_AUDIT"}
    assert len({r["metric_name"] + "|" + r["source_file"] for r in numeric}) == len(numeric)
    assert all(r["evidence_level"] in {"E0", "E1", "E2", "E3", "E4"} for r in rows("evidence_registry.csv"))
    power = rows("build_power_analysis.csv")
    assert len(power) == 4
    assert {r["dataset"] for r in power} == {"SIFT-100K", "Arxiv-Nomic-100K"}
    assert {int(r["planned_builds"]) for r in power} == {18, 24}
    assert all(int(r["historical_target_build_units"]) == 9 for r in power)
    assert all(float(r["estimated_power"]) >= 0.80 for r in power)
    assert all(float(r["loto_min_power"]) >= 0.80 for r in power)
    assert all(r["power_gate"] == "PASS" for r in power)
    d = json.loads(MAN.read_text(encoding="utf-8"))
    assert d["decision"] == "READY_FOR_CONFIRMATORY_HNSWLIB_REBUILD_MATRIX"
    assert d["gate_status"]["P2"] == "PASS"
    assert d["gate_status"]["P3"] == "PASS"
    assert d["p2_power_analysis"]["status"] == "PASS"
    assert d["p3_resource_analysis"]["status"] == "PASS"
    assert d["p3_resource_analysis"]["remaining_margin_gib"] > 5.0
    assert d["p3_resource_analysis"]["confirmatory_compute_envelope_hours"] <= 14.0
    resource = {r["resource"]: r for r in rows("resource_estimate.csv")}
    assert resource["p3_resource_gate"]["estimate"] == "PASS"
    assert "historical_sift_search_seconds" in resource
    assert "historical_arxiv_search_seconds" in resource
    assert "historical_truth_seconds" in resource
    p3 = {r["resource"]: r for r in rows("p3_resource_audit.csv")}
    assert p3["overall_p3"]["value"] == "PASS"
    assert d["confirmatory_query_accessed"] is False
    assert d["future_replication_accessed"] is False
    print("paper_evidence_lock checks: PASS")


if __name__ == "__main__":
    main()
