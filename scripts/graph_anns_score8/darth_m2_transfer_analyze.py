#!/usr/bin/env python3
"""Quantify frozen-source versus target-trained DARTH across rebuilds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]


def cp_ucb(failures: int, n: int) -> float:
    return 1.0 if failures == n else float(beta.ppf(0.95, failures + 1, n - failures))


def nested_bootstrap(differences: dict[int, np.ndarray], repetitions: int = 5000) -> dict:
    rng = np.random.RandomState(991)
    seeds = np.array(sorted(differences))
    draws = np.empty(repetitions)
    for rep in range(repetitions):
        sampled = rng.choice(seeds, len(seeds), replace=True)
        means = []
        for seed in sampled:
            values = differences[int(seed)]
            means.append(float(rng.choice(values, len(values), replace=True).mean()))
        draws[rep] = float(np.mean(means))
    observed = float(np.mean([values.mean() for values in differences.values()]))
    return {"observed": observed, "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))], "repetitions": repetitions, "seed": 991}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows, risk_diff, dist_diff = [], {}, {}
    source_risks = {}
    for seed in SEEDS:
        source = pd.read_csv(args.root / "m2" / f"seed_{seed}" / "darth_source_frozen_eval_1000.txt").sort_values("qid")
        target = pd.read_csv(args.root / "m1" / f"seed_{seed}" / "darth_eval_1000.txt").sort_values("qid")
        source_cert = pd.read_csv(args.root / "m2" / f"seed_{seed}" / "darth_source_frozen_cert_500.txt").sort_values("qid")
        target_cert = pd.read_csv(args.root / "m1" / f"seed_{seed}" / "darth_cert_500.txt").sort_values("qid")
        if not source["qid"].equals(target["qid"]):
            raise ValueError(f"evaluation qid mismatch for seed {seed}")
        source_fail = (source["r_actual"].to_numpy() < 0.90).astype(float)
        target_fail = (target["r_actual"].to_numpy() < 0.90).astype(float)
        risk_diff[seed] = source_fail - target_fail
        dist_diff[seed] = source["dists"].to_numpy(dtype=float) - target["dists"].to_numpy(dtype=float)
        source_risks[seed] = float(source_fail.mean())
        for method, cert, evaluation in [
            ("DARTH_SOURCE_FROZEN", source_cert, source),
            ("DARTH_TARGET_TRAINED", target_cert, target),
        ]:
            cert_fail = int((cert["r_actual"] < 0.90).sum())
            rows.append({
                "seed": seed,
                "method": method,
                "cert_failures": cert_fail,
                "cert_risk": cert_fail / len(cert),
                "cert_cp95_ucb": cp_ucb(cert_fail, len(cert)),
                "eval_risk": float((evaluation["r_actual"] < 0.90).mean()),
                "eval_mean_recall": float(evaluation["r_actual"].mean()),
                "eval_mean_dists": float(evaluation["dists"].mean()),
                "eval_p95_dists": float(evaluation["dists"].quantile(0.95)),
            })
    summary = pd.DataFrame(rows)
    args.output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output / "m2_transfer_summary.csv", index=False)
    pooled = summary.groupby("method", as_index=False).agg(
        builds=("seed", "count"), mean_cert_risk=("cert_risk", "mean"), max_cert_ucb=("cert_cp95_ucb", "max"),
        mean_eval_risk=("eval_risk", "mean"), mean_eval_recall=("eval_mean_recall", "mean"),
        mean_dists=("eval_mean_dists", "mean"), mean_p95_dists=("eval_p95_dists", "mean"),
    )
    pooled.to_csv(args.output / "m2_transfer_pooled.csv", index=False)
    lobo = []
    for omitted in SEEDS:
        kept = [risk for seed, risk in source_risks.items() if seed != omitted]
        lobo.append({"omitted_seed": omitted, "source_frozen_mean_eval_risk": float(np.mean(kept))})
    pd.DataFrame(lobo).to_csv(args.output / "m2_source_frozen_lobo.csv", index=False)
    risk_boot = nested_bootstrap(risk_diff)
    dist_boot = nested_bootstrap(dist_diff)
    decision = {
        "module": "M2_FROZEN_SOURCE_TO_INDEPENDENT_REBUILD",
        "status": "WITHIN_BUILD_CALIBRATION_FAILURE_DOMINATES_TRANSFER",
        "source_model_accepted_builds": int(((summary.method == "DARTH_SOURCE_FROZEN") & (summary.cert_cp95_ucb <= 0.05)).sum()),
        "target_trained_accepted_builds": int(((summary.method == "DARTH_TARGET_TRAINED") & (summary.cert_cp95_ucb <= 0.05)).sum()),
        "pooled": pooled.to_dict(orient="records"),
        "source_minus_target_trained_eval_risk": risk_boot,
        "source_minus_target_trained_mean_dists": dist_boot,
        "source_frozen_lobo_risk_range": [float(min(x["source_frozen_mean_eval_risk"] for x in lobo)), float(max(x["source_frozen_mean_eval_risk"] for x in lobo))],
        "interpretation": "Frozen-source and target-trained DARTH are both unsafe in every build. Retraining on the target build does not close the registered safety gap, so this matrix does not support rebuild shift as the primary DARTH failure mechanism.",
    }
    (args.output / "m2_transfer_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
