#!/usr/bin/env python3
"""Analyze preregistered DARTH/TCP same-index efficacy over ten rebuilds."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
GRID = np.array([10, 20, 40, 80, 120, 160, 200], dtype=int)
RISK_LIMIT = 0.05
RECALL_TARGET = 0.90


def cp_ucb(failures: int, n: int) -> float:
    return 1.0 if failures == n else float(beta.ppf(0.95, failures + 1, n - failures))


def recall_column(frame: pd.DataFrame) -> pd.Series:
    return frame["r_actual"] if "r_actual" in frame else frame["r"]


def load_grid(build: Path, split: str) -> dict[int, pd.DataFrame]:
    result = {}
    for ef in GRID:
        frame = pd.read_csv(build / "fixed" / f"{split}_ef{ef}.txt").sort_values("qid")
        if frame["qid"].tolist() != list(range(len(frame))):
            raise ValueError(f"non-contiguous qids: {build}, {split}, ef={ef}")
        result[int(ef)] = frame
    return result


def min_safe_actions(grid: dict[int, pd.DataFrame]) -> np.ndarray:
    recalls = np.stack([recall_column(grid[int(ef)]).to_numpy() for ef in GRID])
    safe = recalls >= RECALL_TARGET
    action = np.full(recalls.shape[1], GRID[-1], dtype=int)
    for index, ef in enumerate(GRID):
        action[(action == GRID[-1]) & safe[index]] = ef
    return action


def select_rows(grid: dict[int, pd.DataFrame], actions: np.ndarray) -> pd.DataFrame:
    rows = []
    for qid, ef in enumerate(actions):
        row = grid[int(ef)].iloc[qid].copy()
        row["selected_ef"] = int(ef)
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def fixed_safe_ef(cert_grid: dict[int, pd.DataFrame]) -> int:
    for ef in GRID:
        recalls = recall_column(cert_grid[int(ef)])
        failures = int((recalls < RECALL_TARGET).sum())
        if cp_ucb(failures, len(recalls)) <= RISK_LIMIT:
            return int(ef)
    return int(GRID[-1])


def policy_summary(seed: int, method: str, cert: pd.DataFrame, evaluation: pd.DataFrame, accepted: bool, fallback_ef: int) -> dict:
    cert_recall = recall_column(cert)
    eval_recall = recall_column(evaluation)
    failures = int((cert_recall < RECALL_TARGET).sum())
    return {
        "seed": seed,
        "method": method,
        "accepted": bool(accepted),
        "fallback_ef": fallback_ef,
        "cert_n": len(cert),
        "cert_failures": failures,
        "cert_risk": failures / len(cert),
        "cert_cp95_ucb": cp_ucb(failures, len(cert)),
        "eval_n": len(evaluation),
        "eval_mean_recall": float(eval_recall.mean()),
        "eval_failures": int((eval_recall < RECALL_TARGET).sum()),
        "eval_risk": float((eval_recall < RECALL_TARGET).mean()),
        "mean_dists": float(evaluation["dists"].mean()),
        "p50_dists": float(evaluation["dists"].quantile(0.50)),
        "p95_dists": float(evaluation["dists"].quantile(0.95)),
        "p99_dists": float(evaluation["dists"].quantile(0.99)),
        "mean_ms": float(evaluation["elaps_ms"].mean()),
        "p95_ms": float(evaluation["elaps_ms"].quantile(0.95)),
    }


def bootstrap_difference(per_query: pd.DataFrame, left: str, right: str, repetitions: int = 5000) -> dict:
    pivot = per_query.pivot(index=["seed", "qid"], columns="method", values="dists")
    by_seed = {seed: group[left].to_numpy() - group[right].to_numpy() for seed, group in pivot.groupby(level=0)}
    seeds = np.array(sorted(by_seed))
    rng = np.random.RandomState(991)
    values = np.empty(repetitions)
    for rep in range(repetitions):
        sampled_seeds = rng.choice(seeds, len(seeds), replace=True)
        inner = []
        for seed in sampled_seeds:
            values_for_seed = by_seed[int(seed)]
            inner.append(float(rng.choice(values_for_seed, len(values_for_seed), replace=True).mean()))
        values[rep] = float(np.mean(inner))
    observed = float(np.mean([v.mean() for v in by_seed.values()]))
    return {
        "left": left,
        "right": right,
        "estimand": "mean_distance_computations_left_minus_right",
        "observed": observed,
        "ci95": [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))],
        "repetitions": repetitions,
        "seed": 991,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    builds = {seed: args.root / "m1" / f"seed_{seed}" for seed in SEEDS}
    cert_grids = {seed: load_grid(path, "cert") for seed, path in builds.items()}
    eval_grids = {seed: load_grid(path, "eval") for seed, path in builds.items()}
    cert_actions = {seed: min_safe_actions(grid) for seed, grid in cert_grids.items()}
    eval_actions = {seed: min_safe_actions(grid) for seed, grid in eval_grids.items()}

    summaries, query_rows = [], []
    formal_alpha_floor = 1.0 / len(SEEDS)
    for target in SEEDS:
        source = [seed for seed in SEEDS if seed != target]
        # With nine source builds and alpha=.05, the registered conformal rank is
        # beyond the observed pool. The conservative executable action is the
        # source maximum; it is independently certified on the target build.
        tcp_cert_action = np.max(np.stack([cert_actions[seed] for seed in source]), axis=0)
        tcp_eval_action = np.max(np.stack([eval_actions[seed] for seed in source]), axis=0)
        tcp_cert_raw = select_rows(cert_grids[target], tcp_cert_action)
        tcp_eval_raw = select_rows(eval_grids[target], tcp_eval_action)
        tcp_fail = int((recall_column(tcp_cert_raw) < RECALL_TARGET).sum())
        tcp_accepted = cp_ucb(tcp_fail, len(tcp_cert_raw)) <= RISK_LIMIT

        fallback = fixed_safe_ef(cert_grids[target])
        fixed_cert = cert_grids[target][fallback].assign(selected_ef=fallback)
        fixed_eval = eval_grids[target][fallback].assign(selected_ef=fallback)
        summaries.append(policy_summary(target, "FIXED_CERTIFIED", fixed_cert, fixed_eval, True, fallback))
        summaries.append(policy_summary(target, "TCP_RAW_MAX9", tcp_cert_raw, tcp_eval_raw, tcp_accepted, fallback))
        tcp_deployed = tcp_eval_raw if tcp_accepted else fixed_eval
        summaries.append(policy_summary(target, "TCP_AUDITED_DEPLOYED", tcp_cert_raw, tcp_deployed, tcp_accepted, fallback))

        darth_cert = pd.read_csv(builds[target] / "darth_cert_500.txt").sort_values("qid")
        darth_eval = pd.read_csv(builds[target] / "darth_eval_1000.txt").sort_values("qid")
        darth_fail = int((recall_column(darth_cert) < RECALL_TARGET).sum())
        darth_accepted = cp_ucb(darth_fail, len(darth_cert)) <= RISK_LIMIT
        summaries.append(policy_summary(target, "DARTH_TARGET_TRAINED_RAW", darth_cert, darth_eval, darth_accepted, fallback))
        darth_deployed = darth_eval if darth_accepted else fixed_eval
        summaries.append(policy_summary(target, "DARTH_AUDITED_DEPLOYED", darth_cert, darth_deployed, darth_accepted, fallback))

        for method, frame in [
            ("FIXED_CERTIFIED", fixed_eval),
            ("TCP_RAW_MAX9", tcp_eval_raw),
            ("TCP_AUDITED_DEPLOYED", tcp_deployed),
            ("DARTH_TARGET_TRAINED_RAW", darth_eval),
            ("DARTH_AUDITED_DEPLOYED", darth_deployed),
        ]:
            recalls = recall_column(frame).to_numpy()
            for qid, (dist, recall) in enumerate(zip(frame["dists"].to_numpy(), recalls)):
                query_rows.append({"seed": target, "qid": qid, "method": method, "dists": float(dist), "recall": float(recall)})

    args.output.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summaries)
    per_query = pd.DataFrame(query_rows)
    summary.to_csv(args.output / "m1_multibuild_summary.csv", index=False)
    per_query.to_csv(args.output / "m1_multibuild_per_query.csv.gz", index=False, compression="gzip")
    pooled = summary.groupby("method", as_index=False).agg(
        builds=("seed", "count"), accepted_builds=("accepted", "sum"), mean_cert_risk=("cert_risk", "mean"),
        max_cert_ucb=("cert_cp95_ucb", "max"), mean_eval_risk=("eval_risk", "mean"),
        mean_dists=("mean_dists", "mean"), mean_p95_dists=("p95_dists", "mean"), mean_ms=("mean_ms", "mean"),
    )
    pooled.to_csv(args.output / "m1_multibuild_pooled.csv", index=False)
    comparisons = [
        bootstrap_difference(per_query, "TCP_RAW_MAX9", "FIXED_CERTIFIED"),
        bootstrap_difference(per_query, "DARTH_TARGET_TRAINED_RAW", "FIXED_CERTIFIED"),
        bootstrap_difference(per_query, "TCP_AUDITED_DEPLOYED", "FIXED_CERTIFIED"),
        bootstrap_difference(per_query, "DARTH_AUDITED_DEPLOYED", "FIXED_CERTIFIED"),
    ]
    decision = {
        "module": "M1_MULTIBUILD_INTERIM",
        "builds": len(SEEDS),
        "source_builds_per_target": len(SEEDS) - 1,
        "formal_tcp_alpha_floor": formal_alpha_floor,
        "formal_tcp_95pct_certificate_available": formal_alpha_floor <= RISK_LIMIT,
        "tcp_action": "MAX_OF_NINE_SOURCE_MIN_SAFE_ACTIONS_PLUS_INDEPENDENT_TARGET_CERTIFICATION",
        "warning": "Nine source builds cannot alone provide a 5% exchangeable-build conformal certificate; do not claim Theorem 3 at alpha=.05 for this matrix.",
        "pooled": pooled.to_dict(orient="records"),
        "bootstrap": comparisons,
    }
    (args.output / "m1_multibuild_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
