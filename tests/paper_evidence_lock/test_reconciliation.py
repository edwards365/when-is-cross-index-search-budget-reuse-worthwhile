#!/usr/bin/env python3
"""Deterministic integrity checks for the paper-evidence lock outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "paper_evidence_lock"
MAN = ROOT / "manifests" / "graph_anns_paper_evidence_lock_decision.json"


def rows(name: str):
    with (RES / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    numeric = rows("numeric_reconciliation.csv")
    required = {"current_gate_a_main_physical_rows", "current_gate_a_main_unique_query_budget_units", "actual_common_budget_grid", "historical_972000_cross_index", "historical_648000_tournament"}
    assert required <= {r["metric_name"] for r in numeric}
    assert {r["conflict_status"] for r in numeric} >= {"RECONCILED_BY_CONTEXT", "SUPERSEDED_BY_RAW_AUDIT"}
    assert len({r["metric_name"] + "|" + r["source_file"] for r in numeric}) == len(numeric)
    assert all(r["evidence_level"] in {"E0", "E1", "E2", "E3", "E4"} for r in rows("evidence_registry.csv"))
    d = json.loads(MAN.read_text(encoding="utf-8"))
    assert d["decision"] == "BLOCKED_BY_BUILD_LEVEL_POWER_OR_RESOURCES"
    assert d["confirmatory_query_accessed"] is False
    assert d["future_replication_accessed"] is False
    print("paper_evidence_lock checks: PASS")


if __name__ == "__main__":
    main()
