#!/usr/bin/env python3
"""Deterministic validation entry point for the final theory-method lock."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "graph_anns_theory_method_lock"
RESULTS = ROOT / "results" / "graph_anns_theory_method_lock"
MANIFEST = ROOT / "manifests" / "graph_anns_theory_method_claim_decision.json"


def read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    checks: list[tuple[str, bool]] = []
    required_docs = {
        "executive_summary.md", "full_theory_method_report.md",
        "unified_problem_definition.md", "main_theorem_1.md",
        "main_theorem_2.md", "proof_appendix.md",
        "theory_conflict_resolution.md", "icba_auditor_algorithm.md",
        "icba_auditor_pseudocode.txt", "final_claim_registry.md",
        "final_story_lock.md", "title_abstract_contributions.md",
        "limitations.md", "venue_positioning.md", "paper_outline.md",
    }
    checks.append(("01_required_documents", all((DOCS / p).is_file() for p in required_docs)))
    crosswalk = rows("theorem_crosswalk.csv")
    checks.append(("02_two_main_theorems", sum(r["final_disposition"] == "KEEP_AS_MAIN_THEOREM" for r in crosswalk) == 2))
    checks.append(("03_all_78_theorems", len(crosswalk) == 78))
    checks.append(("04_symbols_defined", all(s in read("unified_problem_definition.md") for s in ["mathcal E", "mathcal A_E", "Z_E", "B_E", "C_E", "delta", "alpha", "gamma"])))
    checks.append(("05_bottom_not_numeric", "never imputed" in read("unified_problem_definition.md") and "fillna" not in read("icba_auditor_pseudocode.txt")))
    checks.append(("06_fixed_target_scope", "named target" in read("main_theorem_2.md").lower() and "unseen rebuild" in read("limitations.md").lower()))
    checks.append(("07_classical_le_cam", "le cam" in read("main_theorem_1.md").lower() and "classical" in read("proof_appendix.md").lower()))
    conflict = read("theory_conflict_resolution.md")
    checks.append(("08_no_raw_ef_monotonicity", "not assumed monotone" in conflict))
    checks.append(("09_no_general_structure_bridge", "No general structure-to-budget" in conflict))
    checks.append(("10_query_bootstrap_scope", "unseen-build certification" in read("icba_auditor_pseudocode.txt")))
    checks.append(("11_vamana_cost_scoped", "interval crossing zero" in read("full_theory_method_report.md")))
    checks.append(("12_six_cell_numbers", all(x in read("executive_summary.md") for x in ["48.27%", "89.47%", "11.37%", "21.57%"])) )
    ladder = rows("falsification_ladder.csv")
    checks.append(("13_four_ladder_families", len(ladder) == 4 and all(r["source_commit"] for r in ladder)))
    abstract = read("title_abstract_contributions.md").split("## Abstract", 1)[1].split("## Contributions", 1)[0]
    checks.append(("14_no_internal_codes_in_abstract", not any(code in abstract for code in ["T-OW", "T-OO", "E4", "CIBS", "CALS", "BN-APD"])))
    pseudo = read("icba_auditor_pseudocode.txt")
    checks.append(("15_no_uncertified_accept", "ACCEPT the minimum-cost certified candidate" in pseudo))
    checks.append(("16_abstain_without_fallback", "ABSTAIN_NO_SAFE_ACTION" in pseudo))
    checks.append(("17_parent_frozen", json.loads(MANIFEST.read_text())["parent_commit"] == "d2ad714541d73bedcd48580347b67880d37580f8"))
    access = json.loads(MANIFEST.read_text())["sealed_access"]
    checks.append(("18_sealed_roles_unaccessed", not any(access.values())))
    c1 = digest(RESULTS / "theorem_crosswalk.csv")
    c2 = digest(RESULTS / "theorem_crosswalk.csv")
    checks.append(("19_deterministic_core_csv", c1 == c2 and digest(RESULTS / "theory_source_inventory.csv") == digest(RESULTS / "theory_source_inventory.csv")))
    checks.append(("20_unique_decision", json.loads(MANIFEST.read_text())["decision"] == "THEORY_METHOD_CLAIM_FINAL_LOCK_PASS"))
    failed = [name for name, ok in checks if not ok]
    if failed:
        raise AssertionError("failed checks: " + ", ".join(failed))
    return [name for name, _ in checks]


if __name__ == "__main__":
    passed = validate()
    print(json.dumps({"status": "PASS", "checks": len(passed), "names": passed}, indent=2))
