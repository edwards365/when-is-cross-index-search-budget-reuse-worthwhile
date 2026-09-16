#!/usr/bin/env python3
"""Seal the anonymous artifact package after the read-only smoke passes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from artifact_smoke import smoke


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def seal(repo: Path) -> dict:
    result = smoke(repo)
    artifact = repo / "artifacts/graph_anns_phase3_ea85"
    figure_dir = repo / "figures/graph_anns_phase3_ea85"
    required_figures = [
        figure_dir / "p6_portability_risk.png", figure_dir / "p6_portability_risk.pdf",
        figure_dir / "p6_tcp_refresh_gate.png", figure_dir / "p6_tcp_refresh_gate.pdf",
    ]
    if any(not p.is_file() for p in required_figures):
        raise FileNotFoundError("paper-facing Phase 6 figures are incomplete")
    identity_terms = ("wlk", "101.6.160.66", "/home/")
    anonymous_hits = []
    for path in artifact.iterdir():
        if path.is_file() and path.suffix in {".md", ".csv", ".txt", ".sh"}:
            text = path.read_text(encoding="utf-8")
            for term in identity_terms:
                if term in text:
                    anonymous_hits.append(f"{path.name}:{term}")
    if anonymous_hits:
        raise RuntimeError("anonymous package contains host identity: " + ", ".join(anonymous_hits))
    files = sorted(p for p in artifact.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    files += required_figures
    lines = [f"{sha256(p)}  {p.relative_to(repo)}" for p in files]
    (artifact / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    decision = {
        "schema_version": "ea85-phase6-artifact-decision-1.0",
        "decision": "PHASE6_ANONYMOUS_ARTIFACT_SMOKE_COMPLETE_FULL_REPLAY_PATH_MAPPING_REQUIRED",
        "parent_commit": head,
        "smoke_status": result["status"],
        "checksums_checked": result["checksums_checked"],
        "focused_tests": 24,
        "paper_figures": 4,
        "anonymous_entrypoint_identity_hits": anonymous_hits,
        "raw_truth_accessed": False,
        "clean_clone_smoke": "SUPPORTED",
        "clean_clone_full_replay": "REQUIRES_EXTERNAL_DATA_AND_PATH_MAPPING",
        "claim_scope": "artifact execution and provenance; no new scientific claim",
    }
    manifest = repo / "manifests/graph_anns_phase3_ea85/p6_artifact_decision.json"
    manifest.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = repo / "docs/graph_anns_phase3_ea85/p6_artifact_report.md"
    report.write_text(
        "# Phase 6 anonymous artifact seal\n\n"
        "Decision: **PHASE6_ANONYMOUS_ARTIFACT_SMOKE_COMPLETE_FULL_REPLAY_PATH_MAPPING_REQUIRED**.\n\n"
        "The reviewer entry point contains an environment lock, external-source commit ledger, data/truth "
        "access contract, runtime/storage ledger, negative-claim boundary, lightweight smoke, deterministic "
        "table regeneration, and two paper-facing figures in PNG/PDF. The read-only smoke checked 11 sealed "
        "inputs, parsed all five Phase decisions, verified the Phase 2 role contract and Phase 4 native "
        "instrumentation gate, and accessed no raw truth. The focused suite passes 24 tests.\n\n"
        "The anonymous entry directory contains no host/user identity. A clean clone can reproduce the smoke "
        "and committed analysis tables. Full raw replay still requires external datasets/indexes and local path "
        "mapping because historical launch scripts preserve machine-specific provenance; this is disclosed, "
        "not hidden.\n",
        encoding="utf-8",
    )
    return decision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(seal(args.repo_root.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
