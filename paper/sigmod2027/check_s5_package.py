#!/usr/bin/env python3
"""Check claim-map closure and static manuscript consistency for S5."""
from __future__ import annotations

import csv
import hashlib
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    checks: list[str] = []
    documents = [ROOT / "main.tex", ROOT / "appendix.tex"] + [
        ROOT / "sections" / name for name in ACTIVE_SECTIONS
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in documents)

    title_match = re.search(r"\\title(?:\[[^]]*\])?\{([^}]*)\}", (ROOT / "main.tex").read_text())
    require(title_match is not None, "main title exists", checks)
    require("[Experiments \\& Analysis]" in title_match.group(1), "required E&A title suffix", checks)
    require("Conference'17" not in text and "Conference’17" not in text, "no default ACM conference placeholder", checks)
    require("552/552" not in text, "source certificates are not described as 552 pair certificates", checks)
    require("0.05/6" in text and "375 queries per build" in text, "source-action rule is self-contained", checks)
    require("previously analyzed S3 role" in text and "only the 500/500 S4 roles are prospective" in text,
            "fresh-stage provenance distinguishes prior design from prospective roles", checks)
    require("B when $U_{.05}\\leq0.05$" in text and "A when $L_{.05}>0.05$" in text,
            "target B/U/A labels define both CP tails", checks)
    require("No multiplicity correction is applied across the 552 directions" in text,
            "target audit disclaims simultaneous 552-direction validity", checks)
    require("independently certified source decisions" not in text and
            "source decisions per dataset are independently certified" not in text,
            "shared-query source certificates are not called independent", checks)
    require("transfers economically" not in text and "no economic gain on either hnswlib" not in text,
            "fresh bridge claims serving work rather than net economics", checks)
    require(text.count("source_selected_plus_") == 0, "internal lane identifiers stay out of manuscript prose", checks)
    require(all((ROOT / "evidence" / "s4_fresh" / name).exists() for name in (
        "s4_preregistration_public.json", "s4_source_policy.csv", "S4_PROTOCOL_PUBLIC.md"
    )), "public S4 preregistration and source-policy records are packaged", checks)
    reanalysis = ROOT / "evidence" / "reanalyze_review.py"
    require(reanalysis.exists(), "post-hoc native-response reanalysis script is packaged", checks)
    require(
        sha256(reanalysis) == "ab012e376fa73686fe07bad7498aa6ec928d89d06fef28842ccebd8732dab471",
        "post-hoc reanalysis script hash matches the published anchor", checks,
    )

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
    require(len(rows) == 16, "S4 summary contains three lanes plus endpoint for four blocks", checks)
    require(
        {row["lane"] for row in rows} == {
            "source_selected_plus_0", "source_selected_plus_1",
            "source_selected_plus_2", "endpoint",
        },
        "all preregistered S4 lanes are present", checks,
    )
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

    source_rows = list(csv.DictReader(
        (ROOT / "evidence" / "s4_fresh" / "s4_source_policy.csv").open(encoding="utf-8")
    ))
    require(len(source_rows) == 96, "96 frozen source actions are packaged", checks)
    require(
        len({(r["operator"], r["dataset"], r["source_build"]) for r in source_rows}) == 96,
        "one frozen source action per implementation-dataset-build", checks,
    )
    require(
        all(r["decision"] == "SOURCE_QUALIFIED" for r in source_rows),
        "all packaged source actions satisfy the frozen source rule", checks,
    )
    prereg = json.loads(
        (ROOT / "evidence" / "s4_fresh" / "s4_preregistration_public.json").read_text()
    )
    require(
        prereg["status"] == "FROZEN_BEFORE_FUTURE_VECTOR_OR_TRUTH_ACCESS",
        "public S4 registration preserves the freeze order", checks,
    )
    require(
        prereg["source_policy_sha256"] == "327f57beda1109a1eaf700f16fab158efc7409779e11911cc54eb0a4c7163319",
        "public S4 registration identifies the frozen source policy", checks,
    )

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
