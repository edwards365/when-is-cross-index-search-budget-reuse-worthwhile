#!/usr/bin/env python3
"""Pure-code Arxiv-10K deep conformal pool re-audit.

Consumes the frozen 100-build hit-count tensors. It does not build an index or
run ANN search. The legacy Arxiv farm summary accidentally compared boolean
success values with H=10; this script keeps the frozen result intact and emits
a corrected, independently testable derivative.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[2]
INPUT = REPO / "results/graph_anns_phase2_p11/arxiv_farm_hits.npz"
OUT = REPO / "results/graph_anns_score8/p1_arxiv_deep_pool"
DOC = REPO / "docs/graph_anns_score8/p1_arxiv_deep_pool_report.md"
MANIFEST = REPO / "manifests/graph_anns_score8_p1_arxiv_deep_pool.json"
PARENT = "6638e34101d592ed8a4d0e7cf44fc900c5ec2956"
H = 10
SEED = 991
DRAWS_PER_TARGET = 20
BOOTSTRAPS = 5000
CONFIGS = ((9, 0.10), (19, 0.05), (25, 0.05), (49, 0.05))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def minimum_safe_actions(hit_counts: np.ndarray, grid: np.ndarray) -> np.ndarray:
    ok = hit_counts >= H
    first = np.argmax(ok, axis=2)
    out = grid[first].astype(float)
    out[~ok.any(axis=2)] = np.nan
    return out


def conformal_action(source_actions: np.ndarray, alpha: float) -> tuple[np.ndarray, int]:
    """Return m-th order statistic with BOT represented by +infinity."""
    k = source_actions.shape[0]
    m = int(math.ceil((1.0 - alpha) * (k + 1)))
    if m > k:
        return np.full(source_actions.shape[1], np.nan), m
    ordered = np.sort(np.where(np.isnan(source_actions), np.inf, source_actions), axis=0)
    action = ordered[m - 1].astype(float)
    action[~np.isfinite(action)] = np.nan
    return action, m


def risk_from_raw_counts(hit_counts: np.ndarray, action: np.ndarray, grid: np.ndarray) -> np.ndarray:
    deployed = np.where(np.isnan(action), grid[-1], action)
    idx = np.clip(np.searchsorted(grid, deployed), 0, len(grid) - 1)
    return (hit_counts[np.arange(len(action)), idx] < H).astype(float)


def cluster_interval(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.RandomState(seed)
    n = len(values)
    draws = np.empty(BOOTSTRAPS, dtype=float)
    for i in range(BOOTSTRAPS):
        draws[i] = values[rng.randint(0, n, size=n)].mean()
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def evaluate_arm(name: str, hit_counts: np.ndarray, grid: np.ndarray, arm_offset: int) -> list[dict]:
    actions = minimum_safe_actions(hit_counts, grid)
    n_builds, n_queries, _ = hit_counts.shape
    rows = []
    for k, alpha in CONFIGS:
        per_target = []
        worst_draw = 0.0
        for target in range(n_builds):
            candidates = np.delete(np.arange(n_builds), target)
            t_fail = t_live = t_abst = 0.0
            chosen_sum = chosen_n = ratio_sum = ratio_n = 0.0
            target_oracle = actions[target]
            for draw in range(DRAWS_PER_TARGET):
                rng = np.random.RandomState(SEED + arm_offset + 100_000 * k + 1_000 * target + draw)
                pool = rng.choice(candidates, size=k, replace=False)
                chosen, m = conformal_action(actions[pool], alpha)
                live = ~np.isnan(chosen)
                z = risk_from_raw_counts(hit_counts[target], chosen, grid)
                live_n = int(live.sum())
                draw_risk = float(z[live].mean()) if live_n else float("nan")
                if live_n:
                    worst_draw = max(worst_draw, draw_risk)
                    t_fail += float(z[live].sum())
                    t_live += live_n
                    chosen_sum += float(chosen[live].sum())
                    chosen_n += live_n
                    comparable = live & ~np.isnan(target_oracle)
                    ratio_sum += float((chosen[comparable] / target_oracle[comparable]).sum())
                    ratio_n += int(comparable.sum())
                t_abst += int((~live).sum())
            per_target.append({
                "risk": t_fail / t_live if t_live else float("nan"),
                "live": t_live,
                "fail": t_fail,
                "abstain_rate": t_abst / (DRAWS_PER_TARGET * n_queries),
                "mean_chosen_ef": chosen_sum / chosen_n if chosen_n else float("nan"),
                "budget_ratio_to_target_oracle": ratio_sum / ratio_n if ratio_n else float("nan"),
            })
        target_risk = np.array([x["risk"] for x in per_target])
        total_fail = sum(x["fail"] for x in per_target)
        total_live = sum(x["live"] for x in per_target)
        realized = total_fail / total_live
        ci_low, ci_high = cluster_interval(target_risk, SEED + arm_offset + k)
        loto = np.array([(target_risk.sum() - target_risk[i]) / (n_builds - 1) for i in range(n_builds)])
        rows.append({
            "dataset": "arxiv_nomic_10k_farm",
            "arm": name,
            "n_builds": n_builds,
            "n_queries": n_queries,
            "k": k,
            "alpha": alpha,
            "rank_m": m,
            "nonvacuous": m <= k,
            "draws_per_target": DRAWS_PER_TARGET,
            "realized_failure_rate": realized,
            "target_cluster_ci_low": ci_low,
            "target_cluster_ci_high": ci_high,
            "mean_target_failure_rate": float(target_risk.mean()),
            "worst_target_failure_rate": float(target_risk.max()),
            "worst_target_draw_failure_rate": worst_draw,
            "mean_abstain_rate": float(np.mean([x["abstain_rate"] for x in per_target])),
            "mean_chosen_ef": float(np.mean([x["mean_chosen_ef"] for x in per_target])),
            "mean_budget_ratio_to_target_oracle": float(np.mean([x["budget_ratio_to_target_oracle"] for x in per_target])),
            "loto_min": float(loto.min()),
            "loto_max": float(loto.max()),
            "point_valid": realized <= alpha + 1e-12,
            "cluster_ci_valid": ci_high <= alpha + 1e-12,
            "legacy_boolean_bug_repaired": True,
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with np.load(INPUT) as data:
        grid = data["grid"].astype(int)
        ha = data["HA"].astype(np.int8)
        hb = data["HB"].astype(np.int8)
    assert ha.shape == (100, 500, 6) and hb.shape == (100, 500, 6)
    assert grid.tolist() == [10, 20, 40, 80, 120, 200]
    rows = evaluate_arm("A_single_thread", ha, grid, 0)
    rows += evaluate_arm("B_8thread", hb, grid, 10_000_000)
    result_csv = OUT / "arxiv_deep_pool_validity.csv"
    write_csv(result_csv, rows)
    all_point = all(r["point_valid"] for r in rows)
    all_ci = all(r["cluster_ci_valid"] for r in rows)
    verdict = {
        "label": "ARXIV_DEEP_POOL_VALIDATED" if all_point and all_ci else "ARXIV_DEEP_POOL_POINT_ONLY_OR_FAILED",
        "all_point_valid": all_point,
        "all_target_cluster_ci_valid": all_ci,
        "legacy_summary_preserved": True,
        "legacy_bug": "boolean success was compared with H=10, making every query appear failed",
        "input_sha256": sha256(INPUT),
        "result_sha256": sha256(result_csv),
        "ann_search_invoked": False,
        "index_built": False,
        "seed": SEED,
        "bootstraps": BOOTSTRAPS,
    }
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "P1_ARXIV_10K_DEEP_POOL_PURE_CODE_REAUDIT",
        "branch": "exp/graph_anns_score8_extension",
        "parent_commit": PARENT,
        "input": str(INPUT.relative_to(REPO)),
        "input_sha256": verdict["input_sha256"],
        "configs": [{"k": k, "alpha": a} for k, a in CONFIGS],
        "query_role": "frozen_arxiv_farm_queries_only",
        "ann_search_invoked": False,
        "index_built": False,
        "legacy_outputs_modified": False,
        "final_label": verdict["label"],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    lines = [
        "# Arxiv-10K deep conformal pool re-audit",
        "",
        "This is a pure-code derivative of the frozen 100-build hit tensors; no ANN search or graph build was run.",
        "The old Arxiv farm summary is preserved. Its k=9 risk used `(boolean_success < 10)`, which is always true; the corrected audit evaluates raw hit counts.",
        "",
        "| arm | k | alpha | risk | target-cluster 95% CI | abstain | budget/oracle | point | CI |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['arm']} | {r['k']} | {r['alpha']:.2f} | {r['realized_failure_rate']:.6f} | "
            f"[{r['target_cluster_ci_low']:.6f}, {r['target_cluster_ci_high']:.6f}] | "
            f"{r['mean_abstain_rate']:.6f} | {r['mean_budget_ratio_to_target_oracle']:.4f} | "
            f"{r['point_valid']} | {r['cluster_ci_valid']} |"
        )
    lines += ["", f"Final label: `{verdict['label']}`."]
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(lines) + "\n")
    print(json.dumps(verdict, sort_keys=True))


if __name__ == "__main__":
    main()
