import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "graph_anns_phase3_ea85" / "paper_compliance"
DOC = ROOT / "docs" / "graph_anns_phase3_ea85" / "loop3_recommended_ea_language.md"
MANIFEST = ROOT / "manifests" / "graph_anns_phase3_ea85" / "loop3_paper_compliance_decision.json"


def test_title_marker_and_page_budget():
    text = DOC.read_text(encoding="utf-8")
    title = next(line for line in text.splitlines() if line.startswith("**When Safe"))
    assert title.endswith(": [Experiments & Analysis]**")
    with (OUT / "paper_section_budget.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert float(rows[-1]["cumulative_pages"]) <= 12.0
    assert float(rows[-2]["cumulative_pages"]) == 11.3


def test_all_claims_and_reviewer_risks_are_disposed():
    with (OUT / "claim_to_paper.csv").open(newline="", encoding="utf-8") as handle:
        claims = list(csv.DictReader(handle))
    assert claims and all(row["status"] == "PASS" for row in claims)
    with (OUT / "reviewer_risk_checklist.csv").open(newline="", encoding="utf-8") as handle:
        risks = list(csv.DictReader(handle))
    assert risks and all(row["status"] in {"CLOSED", "CLOSED_IN_RECOMMENDED_LANGUAGE", "ACCEPTED_LIMITATION"} for row in risks)


def test_manifest_preserves_scientific_boundaries():
    decision = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert decision["decision"] == "SIGMOD_EA_PAPER_COMPLIANCE_PASS"
    assert decision["unsupported_headline_claims"] == 0
    assert decision["known_format_blockers"] == 0
    text = DOC.read_text(encoding="utf-8").lower()
    for boundary in ("target-selection", "post-hoc", "first one million", "one arxiv", "wall-clock"):
        assert boundary in text
