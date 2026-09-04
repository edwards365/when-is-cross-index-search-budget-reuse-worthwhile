from __future__ import annotations

import csv
from pathlib import Path

from operator_registry_check import validate


REGISTRY = Path(__file__).parents[2] / "results" / "icba_gsc" / "operator_proposal_plan.csv"


def test_registry_passes_pre_certification_constraints() -> None:
    result = validate(REGISTRY)
    assert result["status"] == "PASS"
    assert result["rows"] == 8
    assert result["max_configs_ok"] is True


def test_primary_operators_have_conservative_profiles() -> None:
    rows = list(csv.DictReader(REGISTRY.open(newline="", encoding="utf-8")))
    conservative = {row["operator"] for row in rows if row["profile"] == "conservative"}
    assert {"O4", "O6"} <= conservative


def test_all_rows_are_pre_certification_only() -> None:
    rows = list(csv.DictReader(REGISTRY.open(newline="", encoding="utf-8")))
    assert all(row["certification_eligible"] == "no" for row in rows)
    assert all("evaluation" not in row["allowed_inputs"] for row in rows)
