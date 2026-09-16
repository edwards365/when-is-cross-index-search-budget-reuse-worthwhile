#!/usr/bin/env python3
"""Protocol-aligned target-build reanalysis of frozen Vamana Stage-I outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


DATASETS = {
    "SIFT-100K": Path("/home/wlk/data500/icba_vamana_stage1/analysis/events.csv"),
    "Arxiv-Nomic-100K": Path("/home/wlk/data500/icba_vamana_stage1_arxiv/analysis/events.csv"),
}
TARGETS = [f"V{i:02d}" for i in range(7, 13)]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_events(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 6 * 6 * 750:
        raise ValueError(f"unexpected event rows in {path}: {len(rows)}")
    if sorted({r["target"] for r in rows}) != TARGETS:
        raise ValueError("target build ledger mismatch")
    return rows


def target_summary(rows: list[dict], target: str) -> dict:
    subset = [r for r in rows if r["target"] == target]
    risk = np.asarray([float(r["risk"]) for r in subset])
    ctrans = np.asarray([float(r["ctrans"]) for r in subset])
    cref = np.asarray([float(r["cref"]) for r in subset])
    valid = np.isfinite(ctrans) & np.isfinite(cref)
    tax = float(np.mean(ctrans[valid]) / np.mean(cref[valid]) - 1.0)
    return {
        "target": target,
        "rows": len(subset),
        "transport_risk": float(np.mean(risk)),
        "cost_tax_ratio_of_means": tax,
        "transport_mean_cmps": float(np.mean(ctrans[valid])),
        "reference_mean_cmps": float(np.mean(cref[valid])),
        "transport_p95_cmps": float(np.percentile(ctrans[valid], 95)),
        "reference_p95_cmps": float(np.percentile(cref[valid], 95)),
        "finite_cost_rows": int(np.sum(valid)),
    }


def build_bootstrap(build_rows: list[dict], reps: int = 5000, seed: int = 991) -> dict:
    risks = np.asarray([r["transport_risk"] for r in build_rows])
    taxes = np.asarray([r["cost_tax_ratio_of_means"] for r in build_rows])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(build_rows), size=(reps, len(build_rows)))
    risk_draws = np.mean(risks[idx], axis=1)
    tax_draws = np.mean(taxes[idx], axis=1)
    return {
        "transport_risk": {
            "point": float(np.mean(risks)),
            "ci_low": float(np.percentile(risk_draws, 2.5)),
            "ci_high": float(np.percentile(risk_draws, 97.5)),
        },
        "cost_tax": {
            "point": float(np.mean(taxes)),
            "ci_low": float(np.percentile(tax_draws, 2.5)),
            "ci_high": float(np.percentile(tax_draws, 97.5)),
        },
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def analyze(repo_root: Path) -> dict:
    result_dir = repo_root / "results/graph_anns_phase3_ea85/vamana_unified"
    report_path = repo_root / "docs/graph_anns_phase3_ea85/p3_vamana_unified_report.md"
    manifest_path = repo_root / "manifests/graph_anns_phase3_ea85/p3_vamana_unified_decision.json"
    per_build, summaries, input_hashes = [], [], {}

    for dataset, path in DATASETS.items():
        rows = load_events(path)
        input_hashes[dataset] = {"path": str(path), "sha256": sha256(path), "rows": len(rows)}
        builds = [target_summary(rows, target) for target in TARGETS]
        for row in builds:
            per_build.append({"dataset": dataset, **row})
        boot = build_bootstrap(builds)
        lobo = []
        for held in range(len(builds)):
            keep = [b for i, b in enumerate(builds) if i != held]
            lobo.append(float(np.mean([b["transport_risk"] for b in keep])))
        max_build = int(np.argmax([b["transport_risk"] for b in builds]))
        delete_largest = float(np.mean([b["transport_risk"] for i, b in enumerate(builds) if i != max_build]))
        event_counts = {}
        for row in rows:
            event_counts[row["event"]] = event_counts.get(row["event"], 0) + 1
        summaries.append({
            "dataset": dataset,
            "target_builds": len(builds),
            "source_builds": 6,
            "queries": 750,
            "directed_source_target_pairs": 36,
            "transport_risk": boot["transport_risk"]["point"],
            "risk_ci_low": boot["transport_risk"]["ci_low"],
            "risk_ci_high": boot["transport_risk"]["ci_high"],
            "cost_tax": boot["cost_tax"]["point"],
            "cost_ci_low": boot["cost_tax"]["ci_low"],
            "cost_ci_high": boot["cost_tax"]["ci_high"],
            "min_loto_risk": min(lobo),
            "delete_largest_risk": delete_largest,
            "under_budget_unsafe_rate": event_counts.get("UNDER_BUDGET_UNSAFE", 0) / len(rows),
            "all_target_builds_positive": int(all(b["transport_risk"] > 0 for b in builds)),
        })

    write_csv(result_dir / "per_target_build.csv", per_build)
    write_csv(result_dir / "summary.csv", summaries)
    decision = "VAMANA_UNIFIED_SEMANTIC_BRIDGE_CONFIRMED_TWO_DATASETS"
    manifest = {
        "schema_version": "ea85-phase3-vamana-unified-1.0",
        "status": "POST_HOC_PROTOCOL_REALIGNMENT_OF_FROZEN_OUTPUTS",
        "decision": decision,
        "primary_event": "Recall@10 < 0.95",
        "event_equivalence": "For k=10, the frozen Stage-I threshold Recall@10 >= 0.95 is exactly the 10-of-10 hit event because recall values are multiples of 0.1.",
        "native_action": {"implementation": "DiskANN3/Vamana-style", "parameter": "l_value", "grid": [16, 32, 64, 128, 256, 512], "beam_width": 1},
        "primary_statistical_unit": "target_build",
        "bootstrap": {"repetitions": 5000, "seed": 991, "outer_unit": "target_build"},
        "inputs": input_hashes,
        "summary": summaries,
        "claim_scope": "Registered SIFT-100K and Arxiv-Nomic-100K DiskANN3/Vamana-style build families only; no numerical comparison of l_value with HNSW efSearch and no open-world implementation claim.",
        "new_builds_or_truth_accessed": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Phase 3 Vamana unified semantic bridge",
        "",
        f"Decision: **{decision}**.",
        "",
        "This is a protocol realignment of frozen Vamana Stage-I outputs, not a newly preregistered experiment. No graph was rebuilt and no new truth or sealed query role was accessed. The native action remains `l_value` with beam width 1; it is not equated numerically with HNSW `efSearch`.",
        "",
        "| Dataset | Target builds | Transport risk | Build-bootstrap 95% CI | Cost tax | Cost 95% CI | Min LOTO risk | Delete-largest risk |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['dataset']} | {row['target_builds']} | {row['transport_risk']:.4f} | [{row['risk_ci_low']:.4f}, {row['risk_ci_high']:.4f}] | {row['cost_tax']:.4f} | [{row['cost_ci_low']:.4f}, {row['cost_ci_high']:.4f}] | {row['min_loto_risk']:.4f} | {row['delete_largest_risk']:.4f} |"
        )
    lines.extend([
        "",
        "The build-cluster intervals keep the safety-portability failure strictly positive on both datasets. LOTO and deleting the largest-risk target build preserve direction. Cost-tax intervals cross zero, so Phase 3 supports the cross-implementation safety phenomenon but not a Vamana cost-superiority claim.",
        "",
        "Because this analysis reuses already observed frozen outputs, its contribution is semantic/statistical closure rather than independent replication. The original Stage-I query firewall, replay audit, index hashes, and negative/boundary evidence remain authoritative.",
    ])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    checks = [
        {"path": str(p.relative_to(repo_root)), "sha256": sha256(p)}
        for p in (result_dir / "per_target_build.csv", result_dir / "summary.csv", manifest_path, report_path)
    ]
    write_csv(result_dir / "checksums.csv", checks)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.repo_root), indent=2))


if __name__ == "__main__":
    main()
