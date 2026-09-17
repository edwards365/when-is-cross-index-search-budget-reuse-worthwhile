#!/usr/bin/env python3
"""Check claim-map closure and static manuscript consistency for S5."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ACTIVE_SECTIONS = (
    "introduction.tex", "02_related_work.tex", "problem_theory.tex",
    "auditor_tcp.tex", "protocol.tex", "portability.tex", "recovery.tex",
    "extensions.tex", "economics.tex", "discussion.tex",
)


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def pct(value: str) -> float:
    return 100.0 * float(value)


def main() -> None:
    checks: list[str] = []
    documents = [ROOT / "main.tex", ROOT / "appendix.tex"] + [
        ROOT / "sections" / name for name in ACTIVE_SECTIONS
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in documents)

    title_match = re.search(r"\\title(?:\[[^]]*\])?\{([^}]*)\}", (ROOT / "main.tex").read_text())
    require(title_match is not None, "main title exists", checks)
    require("[Experiments \\& Analysis]" in title_match.group(1), "required E&A title suffix", checks)

    labels = re.findall(r"\\label\{([^}]+)\}", text)
    refs = re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text)
    require(len(labels) == len(set(labels)), "labels are unique", checks)
    require(set(refs) <= set(labels), "all references resolve", checks)

    bib = (ROOT / "references.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@[A-Za-z]+\{([^,]+),", bib))
    cited: set[str] = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", text):
        cited.update(item.strip() for item in group.split(","))
    require(cited <= bib_keys, "all citations resolve", checks)

    claim_rows = list(csv.DictReader((ROOT / "evidence" / "s5_claim_map.csv").open(encoding="utf-8")))
    require(len(claim_rows) == 10, "ten claim-map rows", checks)
    for row in claim_rows:
        require((ROOT / row["source"]).exists(), f"claim source exists: {row['claim_id']}", checks)

    rows = list(csv.DictReader((ROOT / "evidence" / "s4_fresh" / "s4_summary.csv").open(encoding="utf-8")))
    selected = {
        (row["operator"], row["dataset"]): row
        for row in rows if row["lane"] == "source_selected_plus_1"
    }
    expected = {
        ("hnswlib", "sift_100k"): (1.40, 0.00, 552),
        ("hnswlib", "arxiv_nomic_100k"): (1.32, 0.00, 552),
        ("faiss_hnsw", "sift_100k"): (0.18, 8.27, 552),
        ("faiss_hnsw", "arxiv_nomic_100k"): (0.67, 29.09, 552),
    }
    for key, (risk, gain, qualified) in expected.items():
        row = selected[key]
        require(round(pct(row["target_risk"]), 2) == risk, f"S4 risk matches: {key}", checks)
        require(round(pct(row["relative_mean_ndc_saving"]), 2) == gain, f"S4 gain matches: {key}", checks)
        require(int(row["target_qualified_pairs"]) == qualified, f"S4 qualification matches: {key}", checks)

    public_replay = json.loads((ROOT / "qa" / "S5_CLEAN_REPLAY_PUBLIC.json").read_text())
    require(public_replay["status"] == "PASS", "clean replay status", checks)
    require(public_replay["w6_evidence_checks"] == {"passed": 244, "total": 244}, "W6 replay count", checks)
    require(public_replay["s4_fresh_checks"] == {"passed": 210, "total": 210}, "S4 replay count", checks)
    require(public_replay["anonymous_identity_leaks"] == 0, "anonymous scan has no leak", checks)
    require(public_replay["pdf_build"]["status"] == "PASS", "clean PDF build status", checks)

    report = {"status": "PASS", "checks": len(checks), "details": checks}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
