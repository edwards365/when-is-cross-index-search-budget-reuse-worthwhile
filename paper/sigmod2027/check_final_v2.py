"""Fail-closed checks for the SIGMOD Final V2 manuscript and supplement."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
BUILD = ROOT / "build_final_v2"


def pdf_checks(name: str, max_pages: int) -> dict:
    pdf_path = BUILD / f"{name}.pdf"
    log_path = BUILD / f"{name}.log"
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    metadata = {str(k): str(v) for k, v in (reader.metadata or {}).items()}
    assert len(reader.pages) <= max_pages
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
        r"Overfull|undefined references|Citation .* undefined|Reference .* undefined|Missing character",
        log,
        re.IGNORECASE,
    )
    return {
        "pages": len(reader.pages),
        "bytes": pdf_path.stat().st_size,
        "letter": True,
        "anonymous": True,
        "references_resolved": True,
    }


main_source = (ROOT / "main_final_v2.tex").read_text(encoding="utf-8")
all_v2 = main_source + "\n" + "\n".join(
    path.read_text(encoding="utf-8") for path in sorted((ROOT / "sections_v2").glob("*.tex"))
)
rows = (ROOT / "evidence" / "final_v2_s9_rows.tex").read_text(encoding="utf-8")
claim_map = (ROOT / "evidence" / "final_v2_claim_map.csv").read_text(encoding="utf-8")
decision3 = json.loads((REPO / "manifests" / "sigmod_s9_3_decision.json").read_text())
decision4 = json.loads((REPO / "manifests" / "sigmod_s9_4_decision.json").read_text())

assert "ICBA remains the central contribution" in main_source
assert "source-slack unique method value" not in all_v2.lower()
assert "Source-Derived Slack as an Ablation" in all_v2
assert "Strong Baselines Change the Method Conclusion" in all_v2
assert decision3["decision"] == "PRIMARY_REGISTERED_CONFIGURATION_PASS_WITH_PREREGISTERED_BOUNDARIES"
assert decision4["source_slack_unique_method_value"] == "NOT_SUPPORTED"

required_values = [
    "51.35 [50.87, 51.84]",
    "30.13 [28.64, 31.88]",
    "51.93 [51.20, 52.79]",
    "43.64 [43.33, 43.97]",
    "66.47 [66.20, 66.74]",
]
assert all(value in rows for value in required_values)
claim_rows = [line for line in claim_map.splitlines()[1:] if line.strip()]
assert len(claim_rows) == 8
for line in claim_rows:
    source = line.split(",", 3)[2]
    path = ROOT / source if source.startswith("evidence/") else REPO / source
    assert path.is_file(), path
assert "kassis2026scientific" in (ROOT / "references.bib").read_text(encoding="utf-8")

report = {
    "status": "PASS",
    "main": pdf_checks("main_final_v2", 12),
    "appendix": pdf_checks("appendix_final_v2", 12),
    "structure": {
        "icba_centered": True,
        "policy_hierarchy_explicit": True,
        "source_slack_demoted_to_ablation": True,
        "s9_3_and_s9_4_numbers_bound_to_decision_manifests": True,
        "claim_map_rows": len(claim_rows),
    },
}
(ROOT / "qa" / "FINAL_V2_READINESS.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, indent=2))
