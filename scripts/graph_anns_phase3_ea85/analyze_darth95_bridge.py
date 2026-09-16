#!/usr/bin/env python3
"""Seal the preregistered DARTH Recall@10=.95 bridge at target-build level."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


ROOT = Path("/home/wlk/data500/graph_anns_phase3_ea85/darth95_bridge")
REPO = Path("/home/wlk/data500/navigation-aware-resistance-hnsw-main")
OUT = REPO / "results/graph_anns_phase3_ea85/darth95_bridge"
DOC = REPO / "docs/graph_anns_phase3_ea85/darth95_bridge_report.md"
SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
DATASETS = ["sift_100k", "arxiv_nomic_100k"]
ALPHA = 0.05
REPS = 5000
RNG_SEED = 991


def cp_upper(failures: int, n: int, confidence: float = 0.95) -> float:
    if failures >= n:
        return 1.0
    return float(beta.ppf(confidence, failures + 1, n - failures))


def metrics(path: Path) -> dict[str, float | int]:
    frame = pd.read_csv(path)
    recall_column = "r_actual" if "r_actual" in frame.columns else "r"
    required = {recall_column, "dists", "elaps_ms", "qid"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    failure = frame[recall_column].to_numpy(float) < 0.95
    dists = frame["dists"].to_numpy(float)
    return {
        "n": int(len(frame)),
        "failures": int(failure.sum()),
        "risk": float(failure.mean()),
        "mean_recall": float(frame[recall_column].mean()),
        "mean_dists": float(dists.mean()),
        "p95_dists": float(np.quantile(dists, 0.95)),
        "p99_dists": float(np.quantile(dists, 0.99)),
        "mean_latency_ms": float(frame["elaps_ms"].mean()),
        "p95_latency_ms": float(frame["elaps_ms"].quantile(0.95)),
    }


def fixed_path(dataset: str, seed: int, split: str) -> Path:
    base = Path("/home/wlk/data500/graph_anns_score8/darth_comparison")
    if dataset == "sift_100k":
        return base / f"multibuild/m1/seed_{seed}/fixed/{split}_ef200.txt"
    return base / f"arxiv/runs/m1/seed_{seed}/fixed/{split}_ef200.txt"


def bootstrap_gain(rows: pd.DataFrame) -> dict[str, float]:
    rng = np.random.default_rng(RNG_SEED)
    pivot = rows.pivot(index="seed", columns="method", values="mean_dists")
    delta = pivot["fixed_safe"].to_numpy() - pivot["icba_audited"].to_numpy()
    draws = np.empty(REPS, dtype=float)
    for index in range(REPS):
        draws[index] = rng.choice(delta, size=len(delta), replace=True).mean()
    baseline = float(pivot["fixed_safe"].mean())
    return {
        "absolute_gain": float(delta.mean()),
        "absolute_ci_low": float(np.quantile(draws, 0.025)),
        "absolute_ci_high": float(np.quantile(draws, 0.975)),
        "relative_gain": float(delta.mean() / baseline),
        "relative_ci_low": float(np.quantile(draws / baseline, 0.025)),
        "relative_ci_high": float(np.quantile(draws / baseline, 0.975)),
    }


def main() -> None:
    if (ROOT / "STATUS").read_text(encoding="utf-8").strip() != "COMPLETE":
        raise RuntimeError("bridge run is not complete")
    build_rows: list[dict[str, object]] = []
    for dataset in DATASETS:
        for seed in SEEDS:
            run = ROOT / dataset / f"seed_{seed}"
            darth_cert = metrics(run / "cert_500.csv")
            darth_eval = metrics(run / "eval_1000.csv")
            fixed_cert = metrics(fixed_path(dataset, seed, "cert"))
            fixed_eval = metrics(fixed_path(dataset, seed, "eval"))
            darth_ucb = cp_upper(int(darth_cert["failures"]), int(darth_cert["n"]))
            fixed_ucb = cp_upper(int(fixed_cert["failures"]), int(fixed_cert["n"]))
            if fixed_ucb > ALPHA:
                raise RuntimeError(f"fixed-safe failed certification: {dataset} seed={seed}")
            accepted = darth_ucb <= ALPHA
            for method, selected, cert, evaluation in [
                ("raw_darth", "DARTH", darth_cert, darth_eval),
                ("fixed_safe", "EF200", fixed_cert, fixed_eval),
                (
                    "icba_audited",
                    "DARTH" if accepted else "EF200",
                    darth_cert if accepted else fixed_cert,
                    darth_eval if accepted else fixed_eval,
                ),
            ]:
                build_rows.append(
                    {
                        "dataset": dataset,
                        "seed": seed,
                        "method": method,
                        "selected": selected,
                        "certified": accepted if method == "raw_darth" else True,
                        "raw_darth_cert_ucb": darth_ucb,
                        "cert_risk": cert["risk"],
                        "eval_risk": evaluation["risk"],
                        "mean_recall": evaluation["mean_recall"],
                        "mean_dists": evaluation["mean_dists"],
                        "p95_dists": evaluation["p95_dists"],
                        "p99_dists": evaluation["p99_dists"],
                        "mean_latency_ms": evaluation["mean_latency_ms"],
                        "p95_latency_ms": evaluation["p95_latency_ms"],
                    }
                )
    builds = pd.DataFrame(build_rows)
    summary = (
        builds.groupby(["dataset", "method"], as_index=False)
        .agg(
            builds=("seed", "nunique"),
            selected_darth_builds=("selected", lambda values: int((values == "DARTH").sum())),
            certified_builds=("certified", "sum"),
            mean_eval_risk=("eval_risk", "mean"),
            max_eval_risk=("eval_risk", "max"),
            mean_recall=("mean_recall", "mean"),
            mean_dists=("mean_dists", "mean"),
            mean_p95_dists=("p95_dists", "mean"),
            mean_p99_dists=("p99_dists", "mean"),
        )
    )
    gains = {
        dataset: bootstrap_gain(builds[builds["dataset"] == dataset])
        for dataset in DATASETS
    }
    OUT.mkdir(parents=True, exist_ok=True)
    DOC.parent.mkdir(parents=True, exist_ok=True)
    builds.to_csv(OUT / "build_metrics.csv", index=False)
    summary.to_csv(OUT / "dataset_summary.csv", index=False)
    decision = {
        "status": "DARTH95_BRIDGE_COMPLETE",
        "primary_event": "Recall@10 < 0.95",
        "primary_unit": "target_build",
        "builds_per_dataset": len(SEEDS),
        "bootstrap_reps": REPS,
        "bootstrap_seed": RNG_SEED,
        "gains_vs_fixed_safe": gains,
    }
    (OUT / "decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    columns = list(summary.columns)
    table_lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for record in summary.to_dict(orient="records"):
        values = []
        for column in columns:
            value = record[column]
            values.append(f"{value:.6f}" if isinstance(value, float) else str(value))
        table_lines.append("| " + " | ".join(values) + " |")
    table = "\n".join(table_lines)
    lines = [
        "# DARTH Recall@10=.95 semantic bridge",
        "",
        "The official DARTH checkout was evaluated at target recall .95 on ten frozen target builds per dataset. Independent 500-query certification selected either raw DARTH or the pre-registered EF200 fixed-safe endpoint before the 1,000-query evaluation role was read.",
        "",
        table,
        "",
        "## Build-cluster efficiency gain of ICBA-audited deployment versus fixed-safe",
        "",
    ]
    for dataset, gain in gains.items():
        lines.append(
            f"- {dataset}: relative mean-distance gain {gain['relative_gain']:.2%} "
            f"(95% build-bootstrap CI {gain['relative_ci_low']:.2%}, {gain['relative_ci_high']:.2%})."
        )
    lines.extend(
        [
            "",
            "Wall-clock values are descriptive; distance computations are the primary efficiency currency.",
            "Negative, fallback-only, and zero-gain outcomes are retained.",
            "",
        ]
    )
    DOC.write_text("\n".join(lines), encoding="utf-8")
    hashes = []
    for path in sorted(OUT.glob("*")):
        if path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append(f"{digest}  {path.name}")
    (OUT / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
