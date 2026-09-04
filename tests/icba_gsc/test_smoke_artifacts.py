from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).parents[2]
OUT = REPO / "results" / "icba_gsc" / "operator_smoke"


def test_smoke_metadata_is_validation_only() -> None:
    data = json.loads((OUT / "smoke_metadata.json").read_text())
    assert data["status"] == "OPERATOR_VALIDATION_SMOKE_COMPLETE"
    assert data["operator_trials"] == 8
    assert data["certification_accessed"] is False
    assert data["evaluation_accessed"] is False
    assert data["future_confirm_accessed"] is False


def test_query_roles_are_disjoint_and_future_sealed() -> None:
    rows = list(csv.DictReader((OUT / "query_role_manifest.csv").open()))
    assert len(rows) == 6
    assert len({row["role"] for row in rows}) == 6
    assert next(row for row in rows if row["role"] == "gsc_future_confirm")["count"] == "0"
    assert next(row for row in rows if row["role"] == "gsc_operator_proposal")["last_id_exclusive"] == "200"
    assert next(row for row in rows if row["role"] == "gsc_operator_validation")["first_id"] == "200"


def test_o4_structural_rows_pass_invariants() -> None:
    rows = list(csv.DictReader((OUT / "operator_trials.csv").open()))
    o4 = [row for row in rows if row.get("operator") == "O4"]
    assert len(o4) == 4
    assert all(row["degree_equal"] == "True" for row in o4)
    assert all(row["self_loops"] == "0" for row in o4)


def test_o6_smoke_has_no_half_track_row() -> None:
    rows = list(csv.DictReader((REPO / "results" / "icba_gsc" / "pareto_archive.csv").open()))
    o6 = [row for row in rows if row["run_id"].startswith("O6-")]
    assert o6
    assert not any(float(row["recall_delta"]) >= -0.001 and float(row["p95_ndc_delta_pct"]) <= -2.5 for row in o6)


def test_checksum_manifest_exists() -> None:
    assert (REPO / "results" / "icba_gsc" / "checksums.sha256").stat().st_size > 0
