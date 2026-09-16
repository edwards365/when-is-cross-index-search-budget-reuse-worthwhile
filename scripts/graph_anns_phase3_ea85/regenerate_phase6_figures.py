#!/usr/bin/env python3
"""Generate deterministic paper-facing figures from the Phase 5 evidence tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(value: str):
    try:
        return float(value)
    except ValueError:
        return None


def generate(repo: Path) -> list[Path]:
    evidence = rows(repo / "results/graph_anns_phase3_ea85/phase5_seal/evidence_inventory.csv")
    out = repo / "figures/graph_anns_phase3_ea85"
    out.mkdir(parents=True, exist_ok=True)

    risk = [r for r in evidence if "risk" in r["estimand"] and r["phase"] in {"P1", "P3", "P4"}]
    labels = [f"{r['method']}\n{r['dataset']}" for r in risk]
    values = [float(r["estimate"]) for r in risk]
    lows = [num(r["ci_low"]) for r in risk]
    highs = [num(r["ci_high"]) for r in risk]
    lower = [v - lo if lo is not None else 0 for v, lo in zip(values, lows)]
    upper = [hi - v if hi is not None else 0 for v, hi in zip(values, highs)]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(range(len(values)), values, color="#4C78A8")
    ax.errorbar(range(len(values)), values, yerr=[lower, upper], fmt="none", color="black", capsize=3)
    ax.axhline(0.05, color="#E45756", linestyle="--", label="5% safety threshold")
    ax.set_ylabel("Registered transport risk")
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.legend(frameon=False)
    ax.set_title("Rebuild portability evidence (stratified; no cross-action pooling)")
    fig.tight_layout()
    p1 = out / "p6_portability_risk"
    fig.savefig(p1.with_suffix(".png"), dpi=180)
    fig.savefig(p1.with_suffix(".pdf"))
    plt.close(fig)

    gains = [r for r in evidence if r["phase"] == "P2" and r["method"] == "TARGET_SELECTION_TCP_RECALIBRATION"]
    gain_rows = [r for r in gains if r["estimand"] == "search_distance_gain"]
    risk_rows = [r for r in gains if r["estimand"] == "evaluation_risk"]
    datasets = [r["dataset"] for r in gain_rows]
    gvals = [float(r["estimate"]) for r in gain_rows]
    rmap = {r["dataset"]: float(r["estimate"]) for r in risk_rows}
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8))
    axes[0].bar(datasets, gvals, color="#59A14F")
    axes[0].set_ylabel("Mean search-distance saving")
    axes[0].set_ylim(0, max(gvals) * 1.35)
    axes[1].bar(datasets, [rmap[d] for d in datasets], color="#F28E2B")
    axes[1].axhline(0.05, color="#E45756", linestyle="--")
    axes[1].set_ylabel("Evaluation risk")
    axes[1].set_ylim(0, 0.06)
    fig.suptitle("Target-selection TCP recalibration under 5% mixed refresh")
    fig.tight_layout()
    p2 = out / "p6_tcp_refresh_gate"
    fig.savefig(p2.with_suffix(".png"), dpi=180)
    fig.savefig(p2.with_suffix(".pdf"))
    plt.close(fig)
    return [p1.with_suffix(s) for s in (".png", ".pdf")] + [p2.with_suffix(s) for s in (".png", ".pdf")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    args = ap.parse_args()
    for path in generate(args.repo_root.resolve()):
        print(path)


if __name__ == "__main__":
    main()
