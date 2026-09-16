#!/usr/bin/env python3
"""Harmonize Phase 2 TCP lifecycle costs in native distance-evaluation units."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


N_GRID = (1_000, 10_000, 100_000, 1_000_000, 10_000_000)
REPS = 5000
SEED = 991
TARGET_BASE_ROWS = 100_000
SELECTION_LABELS = 500
CERTIFICATION_LABELS = 500


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_phase2(repo: Path):
    path = repo / "scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py"
    spec = importlib.util.spec_from_file_location("phase2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sum_grid_dists(module, replay: Path, dataset: str, seed: int, role: str) -> float:
    total = 0.0
    for ef in module.EFS:
        _, dists, _ = module.load_csv(
            replay / dataset / "target_refresh05" / f"seed_{seed}" / role / f"ef_{ef}.csv"
        )
        total += float(np.sum(dists))
    return total


def bootstrap(values: np.ndarray) -> tuple[float, float, float]:
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(values), size=(REPS, len(values)))
    draws = np.mean(values[idx], axis=1)
    return float(np.mean(values)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def bootstrap_ratio(numerators: np.ndarray, denominators: np.ndarray) -> tuple[float, float, float]:
    """Paired target-build bootstrap of ratio of means."""
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(numerators), size=(REPS, len(numerators)))
    draws = np.mean(numerators[idx], axis=1) / np.mean(denominators[idx], axis=1)
    point = float(np.mean(numerators) / np.mean(denominators))
    return point, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def analyze(repo: Path, replay: Path) -> dict:
    module = load_phase2(repo)
    per_build_path = repo / "results/graph_anns_phase3_ea85/refresh95/per_build.csv"
    with per_build_path.open(newline="", encoding="utf-8") as f:
        deployed = {
            (r["dataset"], int(r["seed"])): r for r in csv.DictReader(f)
            if r["method"] == "TARGET_SELECTION_TCP_RECALIBRATION"
        }
    if len(deployed) != 20:
        raise RuntimeError(f"expected 20 deployed build rows, found {len(deployed)}")

    rows = []
    for dataset in module.DATASETS:
        old_cert_minima = {}
        for seed in module.SEEDS:
            _, old_r, _ = module.load_tensor(replay, dataset, "old", seed, "certification")
            old_cert_minima[seed] = module.minimal_action_indices(old_r)
        for seed in module.SEEDS:
            sealed = deployed[(dataset, seed)]
            shift = int(sealed["selection_shift"])
            source_cert = module.source_pool_indices(old_cert_minima, seed)
            cert_indices = module.shift_indices(source_cert, shift)
            _, cert_r, cert_d = module.load_tensor(
                replay, dataset, "target_refresh05", seed, "certification"
            )
            _, selected_cert_d = module.outcomes(cert_r, cert_d, cert_indices)
            selection_search = sum_grid_dists(module, replay, dataset, seed, "selection")
            certification_search = float(np.sum(selected_cert_d))
            truth = float(TARGET_BASE_ROWS * (SELECTION_LABELS + CERTIFICATION_LABELS))
            source_profile = float(sealed["cold_source_profile_dists"])
            control = 0.0  # no additional distance calls beyond registered selection replay
            overhead = truth + selection_search + certification_search + source_profile + control
            saving_per_query = float(sealed["cold_serving_saving_dists"]) / float(sealed["evaluation_n"])
            break_even = overhead / saving_per_query if saving_per_query > 0 else float("inf")
            rows.append({
                "dataset": dataset, "seed": seed,
                "certified_deployment": sealed["certified_deployment"],
                "evaluation_risk": sealed["evaluation_risk"],
                "truth_distance_evals": truth,
                "selection_search_distance_evals": selection_search,
                "certification_search_distance_evals": certification_search,
                "source_profile_distance_evals": source_profile,
                "control_extra_distance_evals": control,
                "rebuild_incremental_distance_evals": 0.0,
                "rebuild_accounting": "COMMON_CANCELS_SAME_TARGET_GRAPH",
                "total_incremental_distance_evals": overhead,
                "serving_saving_per_query": saving_per_query,
                "break_even_queries": break_even,
                "fallback": sealed["fallback"],
            })

    horizon_rows = []
    for dataset in module.DATASETS:
        builds = [r for r in rows if r["dataset"] == dataset]
        for n in N_GRID:
            net = np.asarray([
                n * r["serving_saving_per_query"] - r["total_incremental_distance_evals"]
                for r in builds
            ])
            point, low, high = bootstrap(net)
            lobo = [float(np.mean(np.delete(net, i))) for i in range(len(net))]
            delete = float(np.mean(np.delete(net, int(np.argmax(net)))))
            horizon_rows.append({
                "dataset": dataset, "N": n, "net_distance_saving": point,
                "ci_low": low, "ci_high": high, "min_loto": min(lobo),
                "delete_largest": delete,
                "all_builds_certified": int(all(int(r["certified_deployment"]) == 1 for r in builds)),
                "max_evaluation_risk": max(float(r["evaluation_risk"]) for r in builds),
                "gate_pass": int(low > 0 and min(lobo) > 0 and delete > 0),
            })

    dataset_rows = []
    for dataset in module.DATASETS:
        builds = [r for r in rows if r["dataset"] == dataset]
        break_even = np.asarray([r["break_even_queries"] for r in builds])
        overheads = np.asarray([r["total_incremental_distance_evals"] for r in builds])
        savings = np.asarray([r["serving_saving_per_query"] for r in builds])
        ratio = bootstrap_ratio(overheads, savings)
        finite_break_even = break_even[np.isfinite(break_even)]
        passing = [r["N"] for r in horizon_rows if r["dataset"] == dataset and r["gate_pass"] == 1]
        dataset_rows.append({
            "dataset": dataset,
            "target_builds": len(builds),
            "ratio_of_means_break_even_queries": ratio[0],
            "bootstrap_break_even_ci_low": ratio[1],
            "bootstrap_break_even_ci_high": ratio[2],
            "max_finite_build_break_even_queries": float(np.max(finite_break_even)),
            "nonamortizing_builds": int(np.sum(~np.isfinite(break_even))),
            "first_registered_positive_N": min(passing) if passing else "NONE",
            "all_cost_components_accounted": 1,
            "wall_clock_status": "EXPLORATORY_NOT_PROMOTED",
        })
    passed = all(r["first_registered_positive_N"] != "NONE" for r in dataset_rows)
    decision_label = (
        "LIFECYCLE_DISTANCE_COST_GATE_PASSED" if passed
        else "LIFECYCLE_COST_CONDITIONAL_OR_NOT_ESTIMABLE"
    )
    out = repo / "results/graph_anns_phase3_ea85/lifecycle_cost"
    write_csv(out / "per_target_build.csv", rows)
    write_csv(out / "horizon_summary.csv", horizon_rows)
    write_csv(out / "dataset_summary.csv", dataset_rows)
    input_rows = [
        {"path": str(per_build_path.relative_to(repo)), "sha256": sha256(per_build_path)},
        {"path": "EXTERNAL:refresh95_replay/output_sha256.txt",
         "sha256": sha256(replay / "output_sha256.txt")},
    ]
    write_csv(out / "input_checksums.csv", input_rows)
    decision = {
        "schema_version": "ea85-supplement-loop2-lifecycle-cost-1.0",
        "decision": decision_label,
        "cost_currency": "implementation_native_distance_evaluations",
        "primary_unit": "target_build",
        "bootstrap": {"repetitions": REPS, "seed": SEED},
        "datasets": dataset_rows,
        "rebuild_cost": "COMMON_CANCELS_SAME_TARGET_GRAPH",
        "wall_clock": "EXPLORATORY_NOT_PROMOTED",
        "safety_results_changed": False,
        "raw_truth_accessed": False,
    }
    manifest = repo / "manifests/graph_anns_phase3_ea85/loop2_lifecycle_cost_decision.json"
    manifest.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = repo / "docs/graph_anns_phase3_ea85/loop2_lifecycle_cost_report.md"
    lines = [
        "# Supplement Loop 2: harmonized lifecycle distance cost", "",
        f"Decision: **{decision_label}**.", "",
        "Costs use native distance evaluations. Exact target labels, the full registered selection grid, independent certification search, source profiling, and serving are all counted. Rebuild cost cancels because TCP and fixed-safe serve the same rebuilt target graph. Control adds no distance calls beyond selection replay; wall-clock remains exploratory.", "",
        "| Dataset | Ratio-of-means break-even | 95% build CI | Max finite build | Non-amortizing builds | First registered positive N |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in dataset_rows:
        lines.append(
            f"| {r['dataset']} | {r['ratio_of_means_break_even_queries']:.0f} | "
            f"[{r['bootstrap_break_even_ci_low']:.0f}, {r['bootstrap_break_even_ci_high']:.0f}] | "
            f"{r['max_finite_build_break_even_queries']:.0f} | {r['nonamortizing_builds']} | "
            f"{r['first_registered_positive_N']} |"
        )
    lines.extend(["", "The result is an amortized lifecycle-distance claim, not a controlled wall-clock or monetary claim. Phase 2 safety and tail decisions are imported unchanged."])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    generated = [out / "per_target_build.csv", out / "horizon_summary.csv", out / "dataset_summary.csv", manifest, report]
    write_csv(out / "output_checksums.csv", [
        {"path": str(p.relative_to(repo)), "sha256": sha256(p)} for p in generated
    ])
    return decision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--replay-root", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(analyze(args.repo_root.resolve(), args.replay_root.resolve()), indent=2))


if __name__ == "__main__":
    main()
