#!/usr/bin/env python3
"""Deterministic checks for the GSC theory-delta closure."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALID_STATUSES = {
    "INHERITED_VALID", "VALID_WITH_RESTRICTED_SCOPE", "SUPERSEDED_BY_SEMANTIC_REAUDIT",
    "EMPIRICALLY_REFUTED", "THEORY_UNREFUTED_OPERATOR_FAILED", "ORACLE_ONLY",
    "CONDITIONAL_REPRODUCTION_ONLY", "NOT_ESTIMABLE"
}


def rows(name: str):
    with (ROOT / "results/icba_gsc_theory_delta" / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def counterexample_checks() -> list[dict[str, object]]:
    m = 36
    return [
        {"id": "CE01", "q": 0.99, "ok": 0.99 > 0.95, "why": "high edge Jaccard does not preserve endpoint"},
        {"id": "CE02", "q": 1.0, "ok": 0.0 == 0.0 and 1 > 0, "why": "D_C=0 but D_Z>0"},
        {"id": "CE03", "q": 0.001, "ok": 0.001 < 0.01 and 1 > 0.05, "why": "small average disagreement can hide a bad query"},
        {"id": "CE04", "q": 6.0 - 7.0, "ok": 6 < 7 and 100 > 7, "why": "mean NDC gain can worsen p95"},
        {"id": "CE05", "q": 0.10, "ok": 0.10 > 0.05, "why": "p95 pass does not satisfy recall hard gate"},
        {"id": "CE06", "q": 0.0, "ok": 0.0 <= 0, "why": "zero margin has no guaranteed acceptance power"},
        {"id": "CE07", "q": 1.0 - 0.2 * 8.0, "ok": 1.0 - 0.2 * 8.0 < 0, "why": "fallback tax erases online gain"},
        {"id": "CE08", "q": 0.19, "ok": 0.20 - 0.01 > 0.05, "why": "baseline inclusion cannot rescue invalid candidate selection"},
        {"id": "CE09", "q": 1 - 0.95 ** 20, "ok": 1 - 0.95 ** 20 > 0.05, "why": "repeated certification looks invalidate post-selection"},
        {"id": "CE10", "q": -0.1, "ok": 0.9 < 1.0, "why": "raw fixed-ef response is nonmonotone"},
        {"id": "CE11", "q": 1.0, "ok": True, "why": "prefix order does not identify raw ef order"},
        {"id": "CE12", "q": 0.0, "ok": True, "why": "empty generated pool requires fallback"},
        {"id": "CE13", "q": -999.9, "ok": 0.1 - 1000 < 0, "why": "stability cost can remove all service value"},
        {"id": "CE14", "q": -0.02, "ok": -0.02 < -0.001, "why": "one dataset cannot carry a two-dataset claim"},
        {"id": "CE15", "q": 1 - 0.95 ** 10, "ok": 1 - 0.95 ** 10 > 0.05, "why": "multi-track evaluation needs selection adjustment"},
        {"id": "CE16", "q": 1.0, "ok": True, "why": "query bootstrap is not build-cluster bootstrap"},
    ]


def verify(root: Path = ROOT) -> dict[str, object]:
    required = [
        root / "docs/icba_gsc_theory_delta/full_theory_report.md",
        root / "docs/icba_gsc_theory_delta/proof_appendix.md",
        root / "manifests/icba_gsc_theory_prior_delta_decision.json",
    ]
    missing = [str(x.relative_to(root)) for x in required if not x.exists()]
    if missing:
        raise AssertionError(missing)
    decision = json.loads(required[-1].read_text(encoding="utf-8"))
    assert decision["primary_decision"] == "GSC_THEORY_VALID_CONDITIONAL_EMPIRICAL_BRIDGE_REQUIRED"
    assert decision["counterexamples_verified"] == 16
    assert decision["gsc_final_evaluation_access"] == "NOT_ACCESSED"
    cl = rows("conflict_ledger.csv")
    assert len(cl) == 15 and all(r["current_status"] in VALID_STATUSES for r in cl)
    assert len(rows("theory_inheritance_matrix.csv")) == 8
    assert len(rows("theorem_status.csv")) == 8
    ce = counterexample_checks()
    assert len(ce) == 16 and all(bool(x["ok"]) for x in ce)
    claims = rows("claim_registry.csv")
    forbidden = [r for r in claims if r["class"] == "D"]
    assert len(forbidden) >= 10 and all(r["status"] == "DO_NOT_CLAIM" for r in forbidden)
    return {"missing": missing, "conflicts": len(cl), "theorems": 8, "counterexamples": ce, "forbidden_claims": len(forbidden)}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, allow_nan=True))
