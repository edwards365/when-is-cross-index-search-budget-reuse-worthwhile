#!/usr/bin/env python3
"""Build and scan the canonical anonymous SIGMOD source/evidence package."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


TEXT_SUFFIXES = {".tex", ".md", ".py", ".json", ".csv", ".txt", ".bib"}
FORBIDDEN = (
    "wanglekang",
    "edwards365",
    "/home/wlk",
    "101.6.160.66",
    "C:\\Users",
    "navigation-aware-resistance-hnsw.git",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    src = args.source.resolve()
    out = args.output.resolve()
    if src == out or src in out.parents:
        raise SystemExit("output must be outside the manuscript source tree")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    roots = [
        "main.tex", "appendix.tex", "writing_macros.tex", "references.bib",
        "acmart.cls", "ACM-Reference-Format.bst", "ACM-LICENSE",
        "README.md", "requirements.txt", "make_figures.py", "check_evidence.py",
        "run_clean_replay.py",
    ]
    active_sections = [
        "introduction.tex", "02_related_work.tex", "problem_theory.tex",
        "auditor_tcp.tex", "protocol.tex", "portability.tex", "recovery.tex",
        "extensions.tex", "economics.tex", "discussion.tex",
    ]
    for rel in roots:
        copy_file(src / rel, out / rel)
    for name in active_sections:
        copy_file(src / "sections" / name, out / "sections" / name)
    for name in ("overview.pdf", "workflow.pdf", "decisions.pdf", "tradeoff.pdf", "tails.pdf", "cost.pdf"):
        copy_file(src / "figures" / name, out / "figures" / name)
    for rel in (
        "evidence/generated_tables.tex", "evidence/results_macros.tex",
        "evidence/w5_macros.tex", "evidence/w55_macros.tex", "evidence/w6_macros.tex",
        "evidence/certificate_rows.tex", "evidence/cost_rows.tex",
        "evidence/graph_only_rows.tex", "evidence/recovery_rows.tex",
        "evidence/sensitivity_rows.tex", "evidence/s5_claim_map.csv",
    ):
        copy_file(src / rel, out / rel)
    for folder in ("evidence/w6_audit", "evidence/extensions", "evidence/s4_fresh"):
        for path in sorted((src / folder).glob("*")):
            if path.is_file():
                copy_file(path, out / folder / path.name)
    copy_file(src / "PROVENANCE_ANONYMOUS.md", out / "PROVENANCE.md")

    leaks = []
    manifest = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        rel = path.relative_to(out).as_posix()
        if any(token.lower() in rel.lower() for token in FORBIDDEN):
            leaks.append({"path": rel, "token": "filename"})
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in FORBIDDEN:
                if token.lower() in text.lower():
                    leaks.append({"path": rel, "token": token})
        manifest.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})
    report = {"status": "PASS" if not leaks else "FAIL", "files": len(manifest), "leaks": leaks, "manifest": manifest}
    (out / "ANONYMOUS_PACKAGE_MANIFEST.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "files": len(manifest), "leaks": len(leaks)}, indent=2))
    if leaks:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
