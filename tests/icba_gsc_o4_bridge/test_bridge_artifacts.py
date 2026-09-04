from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "icba_gsc_o4_bridge"


def read_rows(name: str):
    with (OUT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_bridge_metadata_reports_reload_and_upper_invariants():
    for config in ("O4-CONSERVATIVE", "O4-BALANCED", "O4-ROBUST", "O4-TIEONLY"):
        metadata = json.loads((OUT / config / "bridge_metadata.json").read_text())
        assert metadata["status"] == "O4_BRIDGE_REPLAY_COMPLETE"
        assert metadata["upper_unchanged"] is True
        assert metadata["reload_equal"] is True
        assert metadata["changed_positions"] > 0


def test_bridge_plan_covers_all_nodes_and_preserves_edge_count():
    rows = read_rows("o4_plan_summary.csv")
    assert len(rows) == 4
    for row in rows:
        assert int(row["nodes"]) == 10000
        assert int(row["planned_directed_edges"]) == int(row["baseline_directed_edges"])
        assert int(row["changed_positions"]) > 0


def test_noop_trace_native_equality():
    metadata = json.loads((OUT / "bridge" / "noop" / "meta.json").read_text())
    assert metadata["trace_matches_native_search"] is True
    assert metadata["harmed_query_ef_pairs"] == 0


def test_o4_trace_native_equality():
    for config in ("O4-CONSERVATIVE", "O4-BALANCED", "O4-ROBUST", "O4-TIEONLY"):
        metadata = json.loads((OUT / config / "compare_meta.json").read_text())
        assert metadata["trace_matches_native_search"] is True
        assert metadata["formal_test_members_accessed"] is False


def test_role_audit_has_disjoint_proposal_validation():
    rows = read_rows("query_role_audit.csv")
    proposal = next(row for row in rows if row["role"] == "gsc_operator_proposal")
    validation = next(row for row in rows if row["role"] == "gsc_operator_validation")
    assert proposal["id_sha256"] != validation["id_sha256"]
    assert int(proposal["count"]) == 200
    assert int(validation["count"]) == 500


def test_safety_gate_is_explicit_failure():
    rows = read_rows("gate_assessment.csv")
    status = {row["gate"]: row["status"] for row in rows}
    assert status["recall_noninferiority"] == "FAIL"
    assert status["p95_noninferiority"] == "FAIL"


def test_certification_and_evaluation_never_opened():
    metadata = json.loads((OUT / "smoke_metadata.json").read_text())
    assert metadata["certification_accessed"] is False
    assert metadata["evaluation_accessed"] is False
    assert metadata["future_confirm_accessed"] is False


def test_previous_decision_scope_patch_present():
    text = (ROOT / "docs" / "icba_gsc_o4_bridge" / "gsc_previous_decision_scope_patch.md").read_text()
    assert "GSC_NO_OPERATOR_SIGNAL_AT_SMOKE" in text
    assert "preserved" in text.lower()
