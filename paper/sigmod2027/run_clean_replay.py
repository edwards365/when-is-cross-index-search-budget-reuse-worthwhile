#!/usr/bin/env python3
"""Replay the anonymous SIGMOD package without importing the main repository."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalized_text_digest(path: Path) -> str:
    """Hash generated TeX semantically, ignoring platform line endings."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip() + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def compile_pdf(root: Path, stem: str) -> dict[str, object]:
    latexmk = shutil.which("latexmk")
    tectonic = shutil.which("tectonic")
    xelatex = shutil.which("xelatex")
    if latexmk:
        result = run([latexmk, "-pdfxe", "-interaction=nonstopmode", f"{stem}.tex"], root)
        engine = "latexmk-pdfxe"
    elif tectonic:
        result = run([tectonic, "--keep-logs", f"{stem}.tex"], root)
        engine = "tectonic"
    elif xelatex:
        first = run([xelatex, "-interaction=nonstopmode", f"{stem}.tex"], root)
        bibtex = shutil.which("bibtex")
        middle = run([bibtex, stem], root) if bibtex and first["returncode"] == 0 else None
        second = run([xelatex, "-interaction=nonstopmode", f"{stem}.tex"], root)
        third = run([xelatex, "-interaction=nonstopmode", f"{stem}.tex"], root)
        result = {
            "returncode": max(
                int(first["returncode"]),
                int(middle["returncode"]) if middle else 0,
                int(second["returncode"]),
                int(third["returncode"]),
            ),
            "passes": [first, middle, second, third],
        }
        engine = "xelatex-bibtex"
    else:
        return {"status": "BLOCKED_NO_LATEX_ENGINE", "engine": None}
    pdf = root / f"{stem}.pdf"
    status = "PASS" if result["returncode"] == 0 and pdf.exists() else "FAIL"
    record: dict[str, object] = {"status": status, "engine": engine, "run": result}
    if pdf.exists():
        record.update({"pdf_bytes": pdf.stat().st_size, "pdf_sha256": digest(pdf)})
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path, default=Path("S5_CLEAN_REPLAY.json"))
    args = parser.parse_args()
    root = args.package.resolve()
    report_path = args.report if args.report.is_absolute() else root / args.report

    forbidden_parent = "navigation-aware-resistance-hnsw-main"
    if forbidden_parent in str(root):
        raise SystemExit("clean replay must run from the exported anonymous package")
    if not (root / "ANONYMOUS_PACKAGE_MANIFEST.json").exists():
        raise SystemExit("anonymous package manifest missing")

    manifest = json.loads((root / "ANONYMOUS_PACKAGE_MANIFEST.json").read_text())
    before_tables = {
        path.name: normalized_text_digest(path)
        for path in sorted((root / "evidence").glob("*.tex"))
    }
    evidence = run([sys.executable, "check_evidence.py"], root)
    figures = run([sys.executable, "make_figures.py"], root)
    after_tables = {
        path.name: normalized_text_digest(path)
        for path in sorted((root / "evidence").glob("*.tex"))
    }
    table_mismatches = {
        name: {"before": value, "after": after_tables.get(name)}
        for name, value in before_tables.items()
        if after_tables.get(name) != value
    }

    s4_validation_path = root / "evidence" / "s4_fresh" / "s4_validation.json"
    s4_validation = json.loads(s4_validation_path.read_text())
    s4_pass = bool(s4_validation.get("all_pass")) and (
        s4_validation.get("passed") == s4_validation.get("total")
    )

    compiled = {stem: compile_pdf(root, stem) for stem in ("main", "appendix")}
    hard_fail = (
        manifest.get("status") != "PASS"
        or evidence["returncode"] != 0
        or figures["returncode"] != 0
        or bool(table_mismatches)
        or not s4_pass
        or any(item["status"] == "FAIL" for item in compiled.values())
    )
    blocked_compile = any(
        item["status"] == "BLOCKED_NO_LATEX_ENGINE" for item in compiled.values()
    )
    status = "FAIL" if hard_fail else ("PASS_WITH_PDF_BUILD_BLOCKED" if blocked_compile else "PASS")

    report = {
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "package_root": str(root),
        "main_repository_imported": False,
        "python": sys.version,
        "executable": sys.executable,
        "cwd": os.getcwd(),
        "packages": {
            name: package_version(name)
            for name in ("numpy", "matplotlib", "pypdf", "pandas", "scipy")
        },
        "anonymous_manifest": {
            "status": manifest.get("status"),
            "files": manifest.get("files"),
            "leaks": manifest.get("leaks"),
        },
        "w6_evidence_replay": evidence,
        "figure_table_regeneration": figures,
        "generated_table_hash_mismatches": table_mismatches,
        "s4_validation": {
            "status": "PASS" if s4_pass else "FAIL",
            "passed": s4_validation.get("passed"),
            "total": s4_validation.get("total"),
            "sha256": digest(s4_validation_path),
        },
        "pdf_builds": compiled,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "w6_evidence_returncode": evidence["returncode"],
        "s4_checks": f"{s4_validation.get('passed')}/{s4_validation.get('total')}",
        "table_hash_mismatches": len(table_mismatches),
        "pdf": {name: item["status"] for name, item in compiled.items()},
    }, indent=2))
    if hard_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
