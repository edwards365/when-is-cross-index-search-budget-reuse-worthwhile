#!/usr/bin/env python3
"""Analyze the preregistered Deep1M eight-build native-count replay."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


EFS = np.asarray([10, 20, 40, 80, 120, 200], dtype=int)
ROOT = Path("/home/wlk/data500/graph_anns_phase3_ea85/deep1m")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_build(path: Path) -> tuple[str, np.ndarray, np.ndarray]:
    recalls = np.empty((len(EFS), 1000), dtype=float)
    ndc = np.empty_like(recalls)
    build = None
    seen = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            build = row["build"]
            q = int(row["query_id"])
            ef = int(row["ef"])
            i = int(np.where(EFS == ef)[0][0])
            key = (i, q)
            if key in seen:
                raise ValueError(f"duplicate row {path}: {key}")
            seen.add(key)
            recalls[i, q] = float(row["recall"])
            ndc[i, q] = float(row["ndc"])
    if len(seen) != len(EFS) * 1000 or build is None:
        raise ValueError(f"incomplete replay {path}: {len(seen)}")
    return build, recalls, ndc


def minimum_indices(recalls: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    good = recalls >= 0.95
    finite = np.any(good, axis=0)
    first = np.argmax(good, axis=0)
    return np.where(finite, first, len(EFS) - 1).astype(int), finite


def build_bootstrap(rows: list[dict], field: str, reps: int = 5000, seed: int = 991) -> tuple[float, float, float]:
    values = np.asarray([r[field] for r in rows], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(reps, len(values)))
    draws = np.mean(values[idx], axis=1)
    return float(np.mean(values)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def analyze(repo: Path) -> dict:
    if (ROOT / "STATUS").read_text().strip() != "COMPLETE":
        raise RuntimeError("Deep1M replay is not complete")
    gate = (ROOT / "INSTRUMENTATION_GATE_PASS").read_text().strip()
    if gate != "60/60 top-k exact matches":
        raise RuntimeError(f"instrumentation gate mismatch: {gate}")
    paths = sorted((ROOT / "replay").glob("*.csv"))
    if len(paths) != 8:
        raise RuntimeError(f"expected eight replay files, found {len(paths)}")
    tensors = {}
    input_rows = []
    for path in paths:
        build, recall, ndc = load_build(path)
        tensors[build] = (recall, ndc)
        input_rows.append({"build": build, "replay_sha256": sha256(path), "rows": len(EFS) * 1000})

    events, per_target = [], []
    for target, (tr, td) in tensors.items():
        t_idx, t_finite = minimum_indices(tr)
        target_events = []
        for source, (sr, _) in tensors.items():
            if source == target:
                continue
            s_idx, s_finite = minimum_indices(sr)
            q = np.arange(1000)
            transported_recall = tr[s_idx, q]
            reference_recall = tr[t_idx, q]
            transport_ndc = td[s_idx, q]
            reference_ndc = td[t_idx, q]
            for qi in range(1000):
                transport_risk = int(transported_recall[qi] < 0.95)
                reference_risk = int(reference_recall[qi] < 0.95)
                row = {
                    "source": source, "target": target, "query_id": qi,
                    "source_action": "BOT" if not s_finite[qi] else int(EFS[s_idx[qi]]),
                    "target_action": "BOT" if not t_finite[qi] else int(EFS[t_idx[qi]]),
                    "transport_risk": transport_risk,
                    "reference_risk": reference_risk,
                    "incremental_risk": transport_risk - reference_risk,
                    "transport_ndc": float(transport_ndc[qi]),
                    "reference_ndc": float(reference_ndc[qi]),
                    "source_censored": int(not s_finite[qi]),
                    "target_censored": int(not t_finite[qi]),
                }
                events.append(row)
                target_events.append(row)
        per_target.append({
            "target": target,
            "source_builds": 7,
            "queries": 1000,
            "transport_risk": float(np.mean([r["transport_risk"] for r in target_events])),
            "reference_risk": float(np.mean([r["reference_risk"] for r in target_events])),
            "incremental_risk": float(np.mean([r["incremental_risk"] for r in target_events])),
            "mean_transport_ndc": float(np.mean([r["transport_ndc"] for r in target_events])),
            "mean_reference_ndc": float(np.mean([r["reference_ndc"] for r in target_events])),
            "source_censoring": float(np.mean([r["source_censored"] for r in target_events])),
            "target_censoring": float(np.mean([r["target_censored"] for r in target_events])),
        })

    risk = build_bootstrap(per_target, "transport_risk")
    ref = build_bootstrap(per_target, "reference_risk")
    delta = build_bootstrap(per_target, "incremental_risk")
    transport_ndc = np.asarray([r["transport_ndc"] for r in events])
    reference_ndc = np.asarray([r["reference_ndc"] for r in events])
    lobo = []
    for held in range(len(per_target)):
        keep = [r for i, r in enumerate(per_target) if i != held]
        lobo.append(float(np.mean([r["incremental_risk"] for r in keep])))
    largest = int(np.argmax([r["incremental_risk"] for r in per_target]))
    delete_largest = float(np.mean([r["incremental_risk"] for i, r in enumerate(per_target) if i != largest]))
    progress = json.loads((ROOT / "progress.json").read_text())
    inputs = json.loads((ROOT / "inputs/manifest.json").read_text())
    summary = {
        "builds": 8,
        "directed_pairs": 56,
        "queries": 1000,
        "transport_risk": risk[0], "transport_risk_ci": [risk[1], risk[2]],
        "reference_risk": ref[0], "reference_risk_ci": [ref[1], ref[2]],
        "incremental_risk": delta[0], "incremental_risk_ci": [delta[1], delta[2]],
        "mean_transport_ndc": float(np.mean(transport_ndc)),
        "p95_transport_ndc": float(np.percentile(transport_ndc, 95)),
        "p99_transport_ndc": float(np.percentile(transport_ndc, 99)),
        "mean_reference_ndc": float(np.mean(reference_ndc)),
        "p95_reference_ndc": float(np.percentile(reference_ndc, 95)),
        "p99_reference_ndc": float(np.percentile(reference_ndc, 99)),
        "source_censoring": float(np.mean([r["source_censored"] for r in events])),
        "target_censoring": float(np.mean([r["target_censored"] for r in events])),
        "min_loto_incremental_risk": min(lobo),
        "delete_largest_incremental_risk": delete_largest,
        "total_build_seconds": float(sum(r["build_seconds_this_run"] for r in progress)),
        "truth_seconds": float(inputs["truth_seconds"]),
        "total_index_bytes": int(sum(r["index_bytes"] for r in progress)),
        "peak_rss_kib": int(max(r["peak_rss_kib"] for r in progress)),
    }
    passed = delta[1] > 0 and min(lobo) > 0 and delete_largest > 0
    decision = "DEEP1M_PORTABILITY_FAILURE_CONFIRMED_WITH_NATIVE_TAILS" if passed else "DEEP1M_SCALE_GATE_NOT_CLOSED"
    out = repo / "results/graph_anns_phase3_ea85/deep1m"
    write_csv(out / "input_ledger.csv", input_rows)
    write_csv(out / "per_target_build.csv", per_target)
    write_csv(out / "events.csv", events)
    write_csv(out / "summary.csv", [{"decision": decision, **summary}])
    report = repo / "docs/graph_anns_phase3_ea85/p4_deep1m_report.md"
    report.write_text(
        "# Phase 4 Deep1M native-count scale report\n\n"
        f"Decision: **{decision}**.\n\n"
        f"Eight independent registered hnswlib builds and 1,000 fresh queries produced 56 directed source→target build pairs. The native/counter equivalence Gate passed 60/60 cases. Transport risk was {risk[0]:.4f} (target-build bootstrap 95% CI [{risk[1]:.4f}, {risk[2]:.4f}]); target-own endpoint-aware reference risk was {ref[0]:.4f}; incremental risk was {delta[0]:.4f} ([{delta[1]:.4f}, {delta[2]:.4f}]).\n\n"
        f"Transport NDC mean/p95/p99 were {summary['mean_transport_ndc']:.1f}/{summary['p95_transport_ndc']:.1f}/{summary['p99_transport_ndc']:.1f}; target-own reference values were {summary['mean_reference_ndc']:.1f}/{summary['p95_reference_ndc']:.1f}/{summary['p99_reference_ndc']:.1f}. Source/target right-censoring rates were {summary['source_censoring']:.4f}/{summary['target_censoring']:.4f}. Minimum LOTO incremental risk was {min(lobo):.4f}; deleting the largest-risk target build left {delete_largest:.4f}.\n\n"
        f"Exact truth required {summary['truth_seconds']:.1f}s; registered builds required {summary['total_build_seconds']:.1f}s in total and {summary['total_index_bytes']/2**30:.2f} GiB. This phase establishes scale portability and native tail evidence only; it does not establish TCP deployment value or universal Graph-ANNS behavior.\n",
        encoding="utf-8")
    manifest_path = repo / "manifests/graph_anns_phase3_ea85/p4_deep1m_decision.json"
    manifest = {
        "schema_version": "ea85-phase4-deep1m-decision-1.0",
        "decision": decision,
        "evidence_level": "PREREGISTERED_FIXED_TARGET_DEEP1M_SCALE_CHECK",
        "instrumentation_gate": gate,
        "input_manifest_sha256": sha256(ROOT / "inputs/manifest.json"),
        "summary": summary,
        "claim_scope": "deep-image first-1M, registered hnswlib build family, Recall@10<.95; no universal or deployment-method claim",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checks = []
    for path in (out / "input_ledger.csv", out / "per_target_build.csv", out / "events.csv", out / "summary.csv", report, manifest_path):
        checks.append({"sha256": sha256(path), "path": str(path.relative_to(repo))})
    write_csv(out / "checksums.csv", checks)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.repo_root), indent=2))


if __name__ == "__main__":
    main()
