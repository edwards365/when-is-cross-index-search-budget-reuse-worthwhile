#!/usr/bin/env python3
import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[2]
DOC_DIR = ROOT / "docs/icba_cibs_joint_closure"
RES_DIR = ROOT / "results/icba_cibs_joint_closure"
MAN_DIR = ROOT / "manifests"
TARGETS = [
    ROOT / "artifacts/icba_cibs_stage1",
    ROOT / "results/icba_cibs_stage1/runtime/base",
    ROOT / "results/icba_cibs_stage1/runtime/orders",
    ROOT / "results/icba_cibs_stage1/runtime/queries",
    ROOT / "results/icba_cibs_stage1/runtime/tools",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def category(path: Path) -> Tuple[str, str]:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("artifacts/icba_cibs_stage1/") and path.suffix == ".bin":
        return "PERSISTENT_REPLAY_ARTIFACT", "PRESERVE_UNTIL_RELIABLE_COPY_VERIFIED"
    if "/runtime/base/" in rel:
        return "REGENERABLE_DATA_CONVERSION_CACHE", "PRESERVE_NO_DELETION_AUTHORIZED"
    if "/runtime/orders/" in rel:
        return "REGENERABLE_PREREGISTERED_ORDER_CACHE", "PRESERVE_NO_DELETION_AUTHORIZED"
    if "/runtime/queries/" in rel:
        return "REGENERABLE_ROLE_MATERIALIZATION_CACHE", "PRESERVE_NO_DELETION_AUTHORIZED"
    if "/runtime/tools/" in rel:
        return "REGENERABLE_COMPILED_TOOL", "PRESERVE_NO_DELETION_AUTHORIZED"
    if path.suffix in {".log", ".out"}:
        return "LOG", "PRESERVE"
    return "UNCLASSIFIED", "PRESERVE_AND_REVIEW"


def main() -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    RES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for target in TARGETS:
        if not target.exists():
            continue
        for path in sorted(p for p in target.rglob("*") if p.is_file()):
            stat = path.stat()
            kind, disposition = category(path)
            rows.append({
                "path": path.relative_to(ROOT).as_posix(),
                "absolute_path": str(path),
                "size_bytes": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": sha256(path),
                "classification": kind,
                "disposition": disposition,
                "reliable_independent_copy_verified": "NO",
                "git_tracked": "NO",
            })

    inventory = RES_DIR / "artifact_inventory.csv"
    with inventory.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["path"])
        writer.writeheader()
        writer.writerows(rows)

    old_manifest = MAN_DIR / "icba_cibs_stage1_decision.json"
    old = json.loads(old_manifest.read_text(encoding="utf-8"))
    old_hash = sha256(old_manifest)
    corrected = {
        "schema_version": 1,
        "status": "CORRECTED_LABEL_SUPERSEDES_LABEL_ONLY",
        "evidence_level": "EXPLORATORY_REPLAY_EQUIVALENT_WITH_PROTOCOL_DEVIATION",
        "frozen_stage1_commit": "10363a3a8a9abe0170af02b0b7ba29ffbf8f4621",
        "original_manifest": "manifests/icba_cibs_stage1_decision.json",
        "original_manifest_sha256": old_hash,
        "original_label": old.get("final_label"),
        "corrected_protocol_label": "CIBS_RECALL_OR_TAIL_GATE_FAILED",
        "scientific_result_changed": False,
        "secondary_reasons": [
            "RECALL_NONINFERIORITY_FAILED_BOTH_DATASETS",
            "SIFT_MEAN_NDC_GAIN_FAILED",
            "SIFT_P95_FAILED",
            "SIFT_NO_FINITE_BREAK_EVEN",
            "ARXIV_BREAK_EVEN_EXCEEDS_MAIN_HORIZON",
        ],
        "authorize_independent_portfolio_confirmation": False,
        "authorize_cibs_race": False,
        "future_confirm_accessed": False,
    }
    (MAN_DIR / "icba_cibs_stage1_corrected_decision.json").write_text(
        json.dumps(corrected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    total = sum(int(r["size_bytes"]) for r in rows)
    counts = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    status = git("status", "--short", "--branch")
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    disk = subprocess.check_output(["df", "-B1", str(ROOT)], text=True).splitlines()[-1].split()
    process_lines = subprocess.check_output(
        ["bash", "-lc", "ps -u \"$USER\" -o pid=,etime=,%cpu=,%mem=,stat=,cmd= --sort=-%cpu | head -20"],
        text=True,
    ).strip().splitlines()
    report = [
        "# CIBS joint-closure artifact and site audit",
        "",
        f"- Audit UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Branch: `{branch}`",
        f"- Frozen HEAD: `{head}`",
        f"- Stage-I decision manifest SHA256 before correction: `{old_hash}`",
        f"- Persistent free bytes: `{disk[3]}`",
        f"- Inventoried files: `{len(rows)}`; total bytes: `{total}`",
        "- Reliable independent copy of large untracked artifacts: `NOT_VERIFIED`.",
        "- Deletion performed: `NO`.",
        "- Git ignore added: `NO`; no broad pattern may hide unknown evidence.",
        "",
        "## Classification",
        "",
    ]
    report += [f"- `{key}`: {value} files" for key, value in sorted(counts.items())]
    report += [
        "",
        "The six serialized index files are replay artifacts and remain preserved outside Git. Runtime base conversions, role materializations, insertion orders, and compiled runners are reproducible caches, but they also remain preserved because this closure has no deletion authorization. Their exact paths, sizes, mtimes, and SHA256 values are in `results/icba_cibs_joint_closure/artifact_inventory.csv`.",
        "",
        "## Worktree status at audit",
        "",
        "```text",
        status,
        "```",
        "",
        "## Relevant process snapshot",
        "",
        "```text",
        *process_lines,
        "```",
        "",
        "## Label-only correction",
        "",
        "The frozen Stage-I manifest is unchanged. Its out-of-dictionary label is mapped in a new manifest to `CIBS_RECALL_OR_TAIL_GATE_FAILED`. The correction changes no metrics, action selection, bootstrap sample, gate threshold, or scientific conclusion.",
    ]
    (DOC_DIR / "artifact_audit.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
