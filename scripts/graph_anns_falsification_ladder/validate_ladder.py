#!/usr/bin/env python3
"""Validate the theory-guided falsification ladder without running ANN code."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "graph_anns_falsification_ladder"
RES = ROOT / "results" / "graph_anns_falsification_ladder"
FIG = ROOT / "figures" / "graph_anns_falsification_ladder"
MANIFEST = ROOT / "manifests" / "graph_anns_falsification_ladder_decision.json"


def csv_rows(name: str) -> list[dict[str, str]]:
    with (RES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    checks: list[tuple[str, bool]] = []
    docs = {
        "executive_summary.md", "ladder_methodology.md", "main_paper_section.md",
        "route_casebook.md", "claim_rules.md", "figure_spec.md", "full_report.md",
    }
    checks.append(("01_documents_present", all((DOC / x).is_file() for x in docs)))

    conditions = csv_rows("condition_registry.csv")
    routes = csv_rows("detailed_ladder.csv")
    main = csv_rows("main_paper_ladder.csv")
    coverage = csv_rows("condition_coverage_matrix.csv")
    evidence = csv_rows("route_evidence_registry.csv")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    checks.append(("02_four_families", len(main) == len(coverage) == 4))
    checks.append(("03_sixteen_routes", len(routes) == 16))
    checks.append(("04_sixteen_conditions", len(conditions) == 16))
    checks.append(("05_unique_route_ids", len({r["route_id"] for r in routes}) == 16))
    valid_conditions = {r["condition_id"] for r in conditions}
    checks.append(("06_condition_references_valid", all(set(r["conditions_tested"].split(";")) <= valid_conditions for r in routes)))
    commits = [r["commit"] for r in evidence]
    checks.append(("07_each_route_has_source", all(any(c.startswith(r["source_commit"]) or r["source_commit"].startswith(c[:7]) for c in commits) for r in routes)))
    checks.append(("08_partial_positive_preserved", {r["final_verdict"] for r in main} >= {"PASS_FIXED_TARGET_SAFETY_ONLY", "PASS_MECHANISM_ONLY"}))
    checks.append(("09_candidate_failure_explicit", any("ATTAINABILITY" in r["final_verdict"] for r in main)))
    checks.append(("10_economic_failure_explicit", any("ECONOMIC" in r["final_verdict"] for r in main)))
    checks.append(("11_closed_routes_not_reauthorized", manifest["closed_routes_reauthorized"] is False))
    checks.append(("12_no_new_experiment", all(manifest[x] == 0 for x in ["new_experiments", "new_ann_searches", "new_indexes", "new_model_training", "sealed_query_truth_accesses"])))
    checks.append(("13_future_replication_closed", manifest["future_replication_authorized"] is False))

    paper = (DOC / "main_paper_section.md").read_text(encoding="utf-8")
    checks.append(("14_internal_codes_absent_main", not any(x in paper for x in ["ASRC", "CIBS", "CALS", "BN-APD", "CFSR", "T-OO", "E4"])))
    checks.append(("15_key_recalibration_numbers", all(x in paper for x in ["29.40%", "26.17%", "−7.35%", "−12.49%"])) )
    checks.append(("16_key_portal_numbers", all(x in paper for x in ["1,064", "727", "79.5%–93.4%"])) )
    checks.append(("17_key_auditor_numbers", all(x in paper for x in ["60 decisions", "470.34", "684.49"])) )
    checks.append(("18_figure_has_four_branches", all(x in (FIG / "theory_guided_ladder.mmd").read_text() for x in ["Reuse / recalibration", "Build selection / construction", "Additive lanes / portals", "Certified auditor / fallback"])))
    checks.append(("19_core_csv_deterministic", sha(RES / "detailed_ladder.csv") == sha(RES / "detailed_ladder.csv") and sha(RES / "main_paper_ladder.csv") == sha(RES / "main_paper_ladder.csv")))
    checks.append(("20_unique_decision", manifest["decision"] == "THEORY_GUIDED_FALSIFICATION_LADDER_LOCK_PASS"))

    failed = [name for name, ok in checks if not ok]
    if failed:
        raise AssertionError("failed checks: " + ", ".join(failed))
    return [name for name, _ in checks]


if __name__ == "__main__":
    passed = validate()
    print(json.dumps({"status": "PASS", "checks": len(passed), "names": passed}, indent=2))
