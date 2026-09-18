"""Fail-closed checks for the SIGMOD Final V3 manuscript and supplement."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
BUILD = ROOT / "build_final_v3"


def pdf_checks(name: str, max_pages: int) -> dict:
    pdf_path = BUILD / f"{name}.pdf"
    log_path = BUILD / f"{name}.log"
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    metadata = {str(k): str(v) for k, v in (reader.metadata or {}).items()}
    assert len(reader.pages) <= max_pages, (name, len(reader.pages))
    assert all(
        abs(float(page.mediabox.width) - 612) < 0.1
        and abs(float(page.mediabox.height) - 792) < 0.1
        for page in reader.pages
    )
    forbidden = [
        "wanglekang",
        "edwards365",
        "101.6.160.66",
        "/home/wlk",
        "c:\\users\\",
        "navigation-aware-resistance-hnsw.git",
    ]
    joined = (text + json.dumps(metadata)).lower()
    assert not any(item in joined for item in forbidden)
    assert metadata.get("/Author", "") in ("", "Anonymous Author(s)")
    assert "??" not in text
    log = log_path.read_text(encoding="utf-8", errors="replace")
    assert not re.search(
        r"Overfull|undefined references|Citation .* undefined|Reference .* undefined|"
        r"multiply defined|Missing character",
        log,
        re.IGNORECASE,
    )
    return {
        "pages": len(reader.pages),
        "bytes": pdf_path.stat().st_size,
        "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "letter": True,
        "anonymous": True,
        "references_resolved": True,
    }


main_source = (ROOT / "main_final_v3.tex").read_text(encoding="utf-8")
section_text = "\n".join(
    path.read_text(encoding="utf-8") for path in sorted((ROOT / "sections_v3").glob("*.tex"))
)
all_v3 = main_source + "\n" + section_text
appendix = (ROOT / "appendix_final_v3.tex").read_text(encoding="utf-8")
rows = (ROOT / "evidence" / "final_v3_s9_rows.tex").read_text(encoding="utf-8")
derived = json.loads((ROOT / "evidence" / "final_v3_derived_intervals.json").read_text())
decision3 = json.loads((REPO / "manifests" / "sigmod_s9_3_decision.json").read_text())
decision4 = json.loads((REPO / "manifests" / "sigmod_s9_4_decision.json").read_text())

assert "ICBA is therefore the central contribution" in main_source
assert "source-slack unique method value" not in all_v3.lower()
assert decision3["decision"] == "PRIMARY_REGISTERED_CONFIGURATION_PASS_WITH_PREREGISTERED_BOUNDARIES"
assert decision4["source_slack_unique_method_value"] == "NOT_SUPPORTED"

for forbidden in ("S9-1", "S9-2", "S9-3", "S9-4", "dominates", "source-derived slack"):
    assert forbidden.lower() not in all_v3.lower(), forbidden
assert "S9-3" in appendix and "S9-4" in appendix
assert all_v3.count("\\label{sec:recovery}") == 0
assert all_v3.count("\\label{sec:economics}") == 1

required_values = [
    "56/0/0",
    "51.35 [50.87, 51.84]",
    "30.13 [28.64, 31.88]",
    "0.400 [0.050, 0.925]",
    "51.93 [51.20, 52.79]",
    "43.64 [43.33, 43.97]",
    "66.47 [66.20, 66.74]",
]
assert all(value in rows for value in required_values)
assert derived["status"] == "DERIVED_FROM_FROZEN_RESPONSES_NO_NEW_EXPERIMENT"
assert derived["replicates"] == 5000 and derived["seed"] == 991
assert derived["results"]["sift100k"]["ci95"] == [0.921, 1.29]
assert derived["results"]["arxiv_nomic_100k"]["ci95"] == [1.012, 1.285]

with (ROOT / "evidence" / "final_v3_claim_map.csv").open(newline="", encoding="utf-8") as handle:
    claim_rows = list(csv.DictReader(handle))
assert len(claim_rows) == 9
for row in claim_rows:
    source = row["source_path"]
    path = ROOT / source if source.startswith("evidence/") else REPO / source
    assert path.is_file(), path

bib = (ROOT / "references_final_v3.bib").read_text(encoding="utf-8")
assert "kassis2026scientific" not in bib
assert "Scientific Agent Skills" not in all_v3
assert "five main-paper figures" in section_text
assert "C/F/A counts candidate/fallback/abstention" in section_text
assert "per-decision certificates" in main_source
assert "not a simultaneous campaign certificate" in main_source

report = {
    "status": "PASS",
    "main": pdf_checks("main_final_v3", 12),
    "appendix": pdf_checks("appendix_final_v3", 20),
    "structure": {
        "icba_centered": True,
        "semantic_stage_names_in_main": True,
        "policy_hierarchy_explicit": True,
        "certificate_scope_explicit": True,
        "full_risk_intervals_and_cfa_counts": True,
        "claim_map_rows": len(claim_rows),
        "derived_intervals_frozen": True,
        "anonymous_url_action": "PENDING_SUBMISSION_SYSTEM_VALUE",
    },
}
(ROOT / "qa").mkdir(exist_ok=True)
(ROOT / "qa" / "FINAL_V3_READINESS.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, indent=2))
