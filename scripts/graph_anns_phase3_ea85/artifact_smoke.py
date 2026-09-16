#!/usr/bin/env python3
"""Read-only semantic and checksum smoke for the Phase 1--5 artifact."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def smoke(repo: Path) -> dict:
    result_root = repo / "results/graph_anns_phase3_ea85/phase5_seal"
    manifest_root = repo / "manifests/graph_anns_phase3_ea85"
    errors = []
    checked = 0
    with (result_root / "input_checksums.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            path = repo / row["path"]
            if not path.is_file() or sha256(path) != row["sha256"]:
                errors.append(f"checksum mismatch: {row['path']}")
            checked += 1
    decisions = {}
    for phase in range(1, 6):
        matches = sorted(manifest_root.glob(f"p{phase}_*decision.json"))
        if not matches:
            errors.append(f"missing P{phase} decision")
            continue
        for path in matches:
            payload = json.loads(path.read_text(encoding="utf-8"))
            decisions[path.name] = payload.get("decision", payload.get("status", "MISSING"))
    claim_rows = list(csv.DictReader((result_root / "claim_evidence_matrix.csv").open(
        newline="", encoding="utf-8")))
    if not any(r["status"] == "NOT_ESTIMABLE" for r in claim_rows):
        errors.append("lifecycle non-estimability boundary missing")
    if not any("SOTA" in r["claim"] for r in claim_rows):
        errors.append("SOTA non-claim missing")
    p4 = json.loads((manifest_root / "p4_deep1m_decision.json").read_text())
    if p4.get("instrumentation_gate") != "60/60 top-k exact matches":
        errors.append("P4 instrumentation gate mismatch")
    p2 = json.loads((manifest_root / "p2_refresh95_decision.json").read_text())
    roles = p2.get("query_roles", {})
    if roles != {"certification": 500, "cold_evaluation": 1000, "selection": 500}:
        errors.append("P2 role contract mismatch")
    status = "PASS" if not errors else "FAIL"
    summary = {
        "schema_version": "ea85-phase6-artifact-smoke-1.0",
        "status": status, "checksums_checked": checked,
        "phase_decisions": decisions, "errors": errors,
        "raw_truth_accessed": False,
    }
    if errors:
        raise RuntimeError(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(smoke(args.repo_root.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
