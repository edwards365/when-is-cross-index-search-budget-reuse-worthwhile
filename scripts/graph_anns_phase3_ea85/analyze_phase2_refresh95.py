#!/usr/bin/env python3
"""Analyze the preregistered Recall@10=.95 mixed-refresh replay."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import beta


EFS = np.asarray([10, 20, 40, 80, 120, 160, 200], dtype=int)
SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
ROLES = ("selection", "certification", "cold_evaluation")
DATASETS = ("sift100k", "arxiv_nomic_100k")
METHODS = (
    "FIXED_SAFE_NATIVE_ENDPOINT",
    "SOURCE_TCP_POOL_REUSE",
    "ICBA_AUDITED_SOURCE_TCP_WITH_FIXED_SAFE_FALLBACK",
    "TARGET_SELECTION_TCP_RECALIBRATION",
)


def cp_upper(failures: int, n: int, confidence: float = 0.95) -> float:
    if n <= 0:
        return math.nan
    if failures >= n:
        return 1.0
    return float(beta.ppf(confidence, failures + 1, n - failures))


def load_csv(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.genfromtxt(path, delimiter=",", skip_header=1, usecols=(0, 2, 26))
    if arr.ndim == 1:
        arr = arr[None, :]
    return arr[:, 0].astype(int), arr[:, 1].astype(float), arr[:, 2].astype(float)


def load_tensor(root: Path, dataset: str, snapshot: str, seed: int, role: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    recalls, dists, qids = [], [], None
    for ef in EFS:
        q, d, r = load_csv(root / dataset / snapshot / f"seed_{seed}" / role / f"ef_{ef}.csv")
        if qids is None:
            qids = q
        elif not np.array_equal(qids, q):
            raise ValueError(f"qid mismatch: {dataset}/{snapshot}/{seed}/{role}/ef_{ef}")
        recalls.append(r)
        dists.append(d)
    return qids, np.stack(recalls), np.stack(dists)


def minimal_action_indices(recalls: np.ndarray) -> np.ndarray:
    good = recalls >= 0.95
    first = np.argmax(good, axis=0)
    any_good = np.any(good, axis=0)
    return np.where(any_good, first, len(EFS) - 1).astype(int)


def source_pool_indices(source_minima: dict[int, np.ndarray], target_seed: int) -> np.ndarray:
    contributors = [v for seed, v in source_minima.items() if seed != target_seed]
    if len(contributors) != len(SEEDS) - 1:
        raise ValueError("leave-one-build-out source pool is incomplete")
    return np.max(np.stack(contributors), axis=0)


def shift_indices(indices: np.ndarray, shift: int) -> np.ndarray:
    return np.minimum(indices + int(shift), len(EFS) - 1)


def outcomes(recalls: np.ndarray, dists: np.ndarray, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    cols = np.arange(indices.size)
    return recalls[indices, cols], dists[indices, cols]


def sequential_profile_cost(dists: np.ndarray, stopping_indices: np.ndarray) -> float:
    """Conservative cost of replaying grid rungs through the first successful rung."""
    mask = np.arange(dists.shape[0])[:, None] <= stopping_indices[None, :]
    return float(np.sum(dists[mask]))


def choose_shift(selection_recalls: np.ndarray, base_indices: np.ndarray) -> tuple[int, float, int]:
    for shift in range(len(EFS)):
        r, _ = outcomes(selection_recalls, np.empty_like(selection_recalls), shift_indices(base_indices, shift))
        failures = int(np.sum(r < 0.95))
        ucb = cp_upper(failures, r.size)
        if ucb <= 0.05:
            return shift, ucb, failures
    endpoint_r = selection_recalls[-1]
    failures = int(np.sum(endpoint_r < 0.95))
    return len(EFS) - 1, cp_upper(failures, endpoint_r.size), failures


def summarize(values: np.ndarray) -> dict[str, float]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"mean": math.nan, "p50": math.nan, "p95": math.nan, "p99": math.nan}
    return {
        "mean": float(np.mean(finite)),
        "p50": float(np.percentile(finite, 50)),
        "p95": float(np.percentile(finite, 95)),
        "p99": float(np.percentile(finite, 99)),
    }


def bootstrap_gain(method_by_build: list[np.ndarray], fixed_by_build: list[np.ndarray], reps: int = 5000, seed: int = 991) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    b = len(method_by_build)
    draws = np.empty(reps, dtype=float)
    for j in range(reps):
        selected = rng.integers(0, b, size=b)
        m_parts, f_parts = [], []
        for idx in selected:
            n = method_by_build[idx].size
            q = rng.integers(0, n, size=n)
            m_parts.append(method_by_build[idx][q])
            f_parts.append(fixed_by_build[idx][q])
        m = np.concatenate(m_parts)
        f = np.concatenate(f_parts)
        draws[j] = 1.0 - float(np.mean(m)) / float(np.mean(f))
    point = 1.0 - float(np.mean(np.concatenate(method_by_build))) / float(np.mean(np.concatenate(fixed_by_build)))
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def strict_json_value(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: strict_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [strict_json_value(v) for v in value]
    return value


def analyze(replay_root: Path, repo_root: Path) -> dict:
    expected = len(DATASETS) * 2 * len(SEEDS) * len(ROLES) * len(EFS)
    actual = sum(1 for _ in replay_root.rglob("ef_*.csv"))
    if actual != expected or (replay_root / "STATUS").read_text().strip() != "COMPLETE":
        raise RuntimeError(f"incomplete replay: {actual}/{expected}")

    result_dir = repo_root / "results/graph_anns_phase3_ea85/refresh95"
    doc_path = repo_root / "docs/graph_anns_phase3_ea85/p2_refresh95_report.md"
    manifest_path = repo_root / "manifests/graph_anns_phase3_ea85/p2_refresh95_decision.json"
    per_build_rows, summary_rows, action_rows = [], [], []
    all_payload: dict[str, dict] = {}

    for dataset in DATASETS:
        source_minima: dict[str, dict[int, np.ndarray]] = {role: {} for role in ROLES}
        source_dists: dict[str, dict[int, np.ndarray]] = {role: {} for role in ROLES}
        target_tensors: dict[tuple[int, str], tuple[np.ndarray, np.ndarray]] = {}
        for role in ROLES:
            for seed in SEEDS:
                _, old_r, old_d = load_tensor(replay_root, dataset, "old", seed, role)
                source_minima[role][seed] = minimal_action_indices(old_r)
                source_dists[role][seed] = old_d
                _, target_r, target_d = load_tensor(replay_root, dataset, "target_refresh05", seed, role)
                target_tensors[(seed, role)] = (target_r, target_d)

        dataset_payload: dict[str, list[dict]] = {m: [] for m in METHODS}
        for seed in SEEDS:
            source_idx = {role: source_pool_indices(source_minima[role], seed) for role in ROLES}
            source_profile_cost = {
                role: sum(
                    sequential_profile_cost(source_dists[role][s], source_minima[role][s])
                    for s in SEEDS if s != seed
                )
                for role in ROLES
            }
            sel_r, sel_d = target_tensors[(seed, "selection")]
            shift, selection_ucb, selection_failures = choose_shift(sel_r, source_idx["selection"])
            cert_r, cert_d = target_tensors[(seed, "certification")]
            eval_r, eval_d = target_tensors[(seed, "cold_evaluation")]
            endpoint_cert_fail = int(np.sum(cert_r[-1] < 0.95))
            endpoint_cert_ucb = cp_upper(endpoint_cert_fail, cert_r.shape[1])
            endpoint_certified = endpoint_cert_ucb <= 0.05

            candidate_indices = {
                "SOURCE_TCP_POOL_REUSE": source_idx["cold_evaluation"],
                "ICBA_AUDITED_SOURCE_TCP_WITH_FIXED_SAFE_FALLBACK": source_idx["cold_evaluation"],
                "TARGET_SELECTION_TCP_RECALIBRATION": shift_indices(source_idx["cold_evaluation"], shift),
            }
            cert_indices = {
                "SOURCE_TCP_POOL_REUSE": source_idx["certification"],
                "ICBA_AUDITED_SOURCE_TCP_WITH_FIXED_SAFE_FALLBACK": source_idx["certification"],
                "TARGET_SELECTION_TCP_RECALIBRATION": shift_indices(source_idx["certification"], shift),
            }

            method_eval: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, float, bool, bool]] = {}
            fixed_idx = np.full(eval_r.shape[1], len(EFS) - 1, dtype=int)
            fixed_eval_r, fixed_eval_d = outcomes(eval_r, eval_d, fixed_idx)
            method_eval["FIXED_SAFE_NATIVE_ENDPOINT"] = (
                fixed_eval_r, fixed_eval_d, fixed_idx, endpoint_cert_ucb, endpoint_certified, False
            )

            for method in METHODS[1:]:
                c_r, _ = outcomes(cert_r, cert_d, cert_indices[method])
                c_fail = int(np.sum(c_r < 0.95))
                c_ucb = cp_upper(c_fail, c_r.size)
                candidate_certified = c_ucb <= 0.05
                if method == "SOURCE_TCP_POOL_REUSE":
                    deploy_idx = candidate_indices[method]
                    fallback = False
                    deployable = candidate_certified
                elif candidate_certified:
                    deploy_idx = candidate_indices[method]
                    fallback = False
                    deployable = True
                elif endpoint_certified:
                    deploy_idx = fixed_idx
                    fallback = True
                    deployable = True
                else:
                    deploy_idx = fixed_idx
                    fallback = True
                    deployable = False
                e_r, e_d = outcomes(eval_r, eval_d, deploy_idx)
                method_eval[method] = (e_r, e_d, deploy_idx, c_ucb, deployable, fallback)

            for method, (e_r, e_d, deploy_idx, cert_ucb, deployable, fallback) in method_eval.items():
                failures = int(np.sum(e_r < 0.95))
                stats = summarize(e_d)
                fixed_total = float(np.sum(fixed_eval_d))
                serving_saving = fixed_total - float(np.sum(e_d))
                recurring_profile = 0.0 if method == "FIXED_SAFE_NATIVE_ENDPOINT" else source_profile_cost["cold_evaluation"]
                break_even_repeats = recurring_profile / serving_saving if serving_saving > 0 else math.inf
                row = {
                    "dataset": dataset,
                    "seed": seed,
                    "method": method,
                    "cert_ucb": cert_ucb,
                    "certified_deployment": int(deployable),
                    "fallback": int(fallback),
                    "selection_shift": shift if method == "TARGET_SELECTION_TCP_RECALIBRATION" else 0,
                    "selection_failures": selection_failures if method == "TARGET_SELECTION_TCP_RECALIBRATION" else "",
                    "selection_ucb": selection_ucb if method == "TARGET_SELECTION_TCP_RECALIBRATION" else "",
                    "evaluation_failures": failures,
                    "evaluation_n": int(e_r.size),
                    "evaluation_risk": failures / e_r.size,
                    "mean_dists": stats["mean"],
                    "p50_dists": stats["p50"],
                    "p95_dists": stats["p95"],
                    "p99_dists": stats["p99"],
                    "mean_ef": float(np.mean(EFS[deploy_idx])),
                    "cold_source_profile_dists": recurring_profile,
                    "cold_serving_saving_dists": serving_saving,
                    "repeated_query_set_break_even": break_even_repeats,
                }
                per_build_rows.append(row)
                dataset_payload[method].append({"risk": failures / e_r.size, "dists": e_d, "recalls": e_r, "fallback": fallback})
                counts = np.bincount(deploy_idx, minlength=len(EFS))
                for idx, count in enumerate(counts):
                    action_rows.append({"dataset": dataset, "seed": seed, "method": method, "ef": int(EFS[idx]), "queries": int(count)})

        fixed = dataset_payload["FIXED_SAFE_NATIVE_ENDPOINT"]
        for method in METHODS:
            items = dataset_payload[method]
            dists = np.concatenate([x["dists"] for x in items])
            recalls = np.concatenate([x["recalls"] for x in items])
            fixed_dists = np.concatenate([x["dists"] for x in fixed])
            point, lo, hi = bootstrap_gain([x["dists"] for x in items], [x["dists"] for x in fixed])
            stats = summarize(dists)
            fixed_stats = summarize(fixed_dists)
            build_gains = [1.0 - float(np.mean(x["dists"])) / float(np.mean(fixed[i]["dists"])) for i, x in enumerate(items)]
            lobo = []
            for held in range(len(items)):
                keep = [i for i in range(len(items)) if i != held]
                md = np.concatenate([items[i]["dists"] for i in keep])
                fd = np.concatenate([fixed[i]["dists"] for i in keep])
                lobo.append(1.0 - float(np.mean(md)) / float(np.mean(fd)))
            delete_idx = int(np.argmax(build_gains))
            keep = [i for i in range(len(items)) if i != delete_idx]
            delete_gain = 1.0 - float(np.mean(np.concatenate([items[i]["dists"] for i in keep]))) / float(np.mean(np.concatenate([fixed[i]["dists"] for i in keep])))
            certified_builds = sum(int(r["certified_deployment"]) for r in per_build_rows if r["dataset"] == dataset and r["method"] == method)
            fallback_builds = sum(int(x["fallback"]) for x in items)
            method_build_rows = [r for r in per_build_rows if r["dataset"] == dataset and r["method"] == method]
            finite_break_even = [float(r["repeated_query_set_break_even"]) for r in method_build_rows if math.isfinite(float(r["repeated_query_set_break_even"]))]
            summary_rows.append({
                "dataset": dataset,
                "method": method,
                "certified_builds": certified_builds,
                "fallback_builds": fallback_builds,
                "evaluation_risk": float(np.mean(recalls < 0.95)),
                "mean_dists": stats["mean"],
                "p95_dists": stats["p95"],
                "p99_dists": stats["p99"],
                "fixed_mean_dists": fixed_stats["mean"],
                "fixed_p95_dists": fixed_stats["p95"],
                "mean_gain": point,
                "gain_ci_low": lo,
                "gain_ci_high": hi,
                "min_lobo_gain": min(lobo),
                "delete_largest_gain": delete_gain,
                "tail_p95_noninferior": int(stats["p95"] <= fixed_stats["p95"]),
                "median_repeated_query_set_break_even": float(np.median(finite_break_even)) if finite_break_even else math.inf,
                "max_repeated_query_set_break_even": max(finite_break_even) if finite_break_even else math.inf,
            })
        all_payload[dataset] = dataset_payload

    write_csv(result_dir / "per_build.csv", per_build_rows)
    write_csv(result_dir / "summary.csv", summary_rows)
    write_csv(result_dir / "action_counts.csv", action_rows)

    adaptive = [r for r in summary_rows if r["method"] in METHODS[2:]]
    gate_pass = any(
        all(
            next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["certified_builds"] == 10
            and next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["evaluation_risk"] <= 0.05
            and next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["mean_gain"] >= 0.05
            and next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["gain_ci_low"] > 0
            and next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["tail_p95_noninferior"] == 1
            and next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["min_lobo_gain"] > 0
            and next(x for x in adaptive if x["dataset"] == ds and x["method"] == method)["delete_largest_gain"] > 0
            for ds in DATASETS
        )
        for method in METHODS[2:]
    )
    decision = "REFRESH95_SEARCH_GATE_PASSED_LIFECYCLE_COST_CONDITIONAL" if gate_pass else "REFRESH95_TCP_GATE_NOT_CLOSED"
    decision_manifest = {
        "schema_version": "ea85-phase2-refresh95-decision-1.0",
        "decision": decision,
        "evidence_level": "EXPLORATORY_PREREGISTERED_FIXED_TARGET_REFRESH",
        "replay_files": actual,
        "datasets": list(DATASETS),
        "target_builds_per_dataset": len(SEEDS),
        "query_roles": {"selection": 500, "certification": 500, "cold_evaluation": 1000},
        "primary_event": "Recall@10 < 0.95",
        "risk_limit": 0.05,
        "summary": strict_json_value(summary_rows),
        "claim": "TCP is promoted for mixed-refresh deployment only if one audited adaptive method closes every preregistered gate on both datasets.",
        "cost_status": "SEARCH_DISTANCE_COST_MEASURED_SOURCE_PROFILE_BREAK_EVEN_MEASURED_TRUTH_REBUILD_CONTROL_COST_NOT_HARMONIZED",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(decision_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Phase 2 Recall@10=.95 mixed-refresh report",
        "",
        f"Decision: **{decision}**.",
        "",
        "This report uses 20 fixed target builds, disjoint 500/500/1000 selection/certification/cold-evaluation roles, one-sided 95% Clopper–Pearson certification, and 5,000 paired target-build bootstrap replicates (seed 991).",
        "",
        "| Dataset | Method | Certified builds | Fallback builds | Eval risk | Mean gain | 95% CI | p95 noninferior | Min LOBO | Delete-largest | Median repeated-set break-even |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary_rows:
        lines.append(
            f"| {r['dataset']} | {r['method']} | {r['certified_builds']}/10 | {r['fallback_builds']}/10 | {r['evaluation_risk']:.4f} | {r['mean_gain']:.4f} | [{r['gain_ci_low']:.4f}, {r['gain_ci_high']:.4f}] | {r['tail_p95_noninferior']} | {r['min_lobo_gain']:.4f} | {r['delete_largest_gain']:.4f} | {r['median_repeated_query_set_break_even']:.1f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The raw source TCP row is a transfer diagnostic; certification status is reported but evaluation is not replaced by fallback. The audited and target-recalibrated rows are deployable lanes: a rejected candidate falls back to the independently checked ef=200 endpoint. Fixed-safe fallback is not counted as adaptive-method value.",
        "",
        "A one-dataset improvement is conditional evidence only. The primary promotion gate requires simultaneous safety, mean, tail, bootstrap, LOBO, and delete-largest closure on both datasets.",
        "",
        "The search-only Gate closes for target-selection recalibration, but this is not yet an unconditional end-to-end lifecycle claim. Source profiling is charged separately: the break-even column is the number of repeated passes over the same profiled query set needed for target-serving savings to repay conservative source-grid profiling. Exact-truth, rebuild, and control-plane costs are not harmonized, so the lifecycle conclusion remains conditional.",
    ])
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    checksum_rows = []
    for p in sorted([result_dir / "per_build.csv", result_dir / "summary.csv", result_dir / "action_counts.csv", manifest_path, doc_path]):
        checksum_rows.append({"sha256": sha256(p), "path": str(p.relative_to(repo_root))})
    write_csv(result_dir / "checksums.csv", checksum_rows)
    return {"decision": decision, "summary": summary_rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.replay_root, args.repo_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
