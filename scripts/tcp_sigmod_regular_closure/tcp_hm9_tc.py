#!/usr/bin/env python3
"""Canonical TCP-HM9-TC fixed-target analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


SEEDS = (1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267)
GRID = np.array((10, 20, 40, 80, 120, 160, 200), dtype=int)
TARGET = 0.90
LIMIT = 0.05


def cp_ucb(failures: int, n: int, confidence: float = 0.95) -> float:
    if n <= 0:
        raise ValueError("n must be positive")
    if failures < 0 or failures > n:
        raise ValueError("invalid failure count")
    if failures == n:
        return 1.0
    return float(beta.ppf(confidence, failures + 1, n - failures))


def recall_values(frame: pd.DataFrame) -> np.ndarray:
    column = "r_actual" if "r_actual" in frame else "r"
    return frame[column].to_numpy(dtype=float)


def load_grid(root: Path, split: str) -> dict[int, pd.DataFrame]:
    result = {}
    for ef in GRID:
        frame = pd.read_csv(root / f"{split}_ef{ef}.txt").sort_values("qid")
        if frame["qid"].tolist() != list(range(len(frame))):
            raise ValueError(f"non-contiguous qids in {root}, {split}, ef={ef}")
        result[int(ef)] = frame.reset_index(drop=True)
    return result


def raw_first_safe(grid: dict[int, pd.DataFrame]) -> np.ndarray:
    safe = np.stack([recall_values(grid[int(ef)]) >= TARGET for ef in GRID])
    result = np.full(safe.shape[1], np.inf)
    for index, ef in enumerate(GRID):
        result[np.isinf(result) & safe[index]] = ef
    return result


def stable_tail_actions(grid: dict[int, pd.DataFrame]) -> np.ndarray:
    safe = np.stack([recall_values(grid[int(ef)]) >= TARGET for ef in GRID])
    stable = np.logical_and.accumulate(safe[::-1], axis=0)[::-1]
    result = np.full(stable.shape[1], np.inf)
    for index, ef in enumerate(GRID):
        result[np.isinf(result) & stable[index]] = ef
    return result


def history_max(action_sets: list[np.ndarray]) -> np.ndarray:
    if not action_sets:
        raise ValueError("source history is empty")
    return np.max(np.stack(action_sets), axis=0)


def execute(grid: dict[int, pd.DataFrame], actions: np.ndarray) -> pd.DataFrame:
    if len(actions) != len(next(iter(grid.values()))):
        raise ValueError("action/query length mismatch")
    rows = []
    for qid, action in enumerate(actions):
        abstain = bool(np.isinf(action))
        ef = int(GRID[-1] if abstain else action)
        if ef not in grid:
            raise ValueError(f"action outside frozen grid: {ef}")
        row = grid[ef].iloc[qid].copy()
        row["selected_ef"] = ef
        row["abstain"] = abstain
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def risk_stats(frame: pd.DataFrame) -> tuple[int, int, float, float]:
    failures = int((recall_values(frame) < TARGET).sum())
    n = len(frame)
    return failures, n, failures / n, cp_ucb(failures, n)


def summary(seed: int, method: str, cert: pd.DataFrame, evaluation: pd.DataFrame,
            accepted: bool, decision: str) -> dict:
    failures, n, risk, ucb = risk_stats(cert)
    eval_recall = recall_values(evaluation)
    return {
        "seed": seed,
        "method": method,
        "accepted": bool(accepted),
        "decision": decision,
        "cert_n": n,
        "cert_failures": failures,
        "cert_risk": risk,
        "cert_cp95_ucb": ucb,
        "eval_n": len(evaluation),
        "eval_risk": float((eval_recall < TARGET).mean()),
        "eval_mean_recall": float(eval_recall.mean()),
        "mean_dists": float(evaluation["dists"].mean()),
        "p50_dists": float(evaluation["dists"].quantile(0.50)),
        "p95_dists": float(evaluation["dists"].quantile(0.95)),
        "p99_dists": float(evaluation["dists"].quantile(0.99)),
        "abstain_rate": (
            float(evaluation["abstain"].mean()) if "abstain" in evaluation else 0.0
        ),
    }


def bootstrap(per_query: pd.DataFrame, left: str, right: str,
              repetitions: int = 5000) -> dict:
    pivot = per_query.pivot(index=["seed", "qid"], columns="method", values="dists")
    differences = {
        seed: group[left].to_numpy() - group[right].to_numpy()
        for seed, group in pivot.groupby(level=0)
    }
    seeds = np.array(sorted(differences))
    rng = np.random.RandomState(991)
    samples = np.empty(repetitions)
    for repetition in range(repetitions):
        sampled_builds = rng.choice(seeds, len(seeds), replace=True)
        build_means = []
        for seed in sampled_builds:
            values = differences[int(seed)]
            build_means.append(float(rng.choice(values, len(values), replace=True).mean()))
        samples[repetition] = float(np.mean(build_means))
    observed = float(np.mean([values.mean() for values in differences.values()]))
    return {
        "estimand": f"mean_distance_computations_{left}_minus_{right}",
        "observed": observed,
        "ci95": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "repetitions": repetitions,
        "seed": 991,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-root", required=True, type=Path)
    parser.add_argument("--darth-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    cert_grids = {seed: load_grid(args.fixed_root / f"seed_{seed}", "cert") for seed in SEEDS}
    eval_grids = {seed: load_grid(args.fixed_root / f"seed_{seed}", "eval") for seed in SEEDS}
    cert_tail = {seed: stable_tail_actions(grid) for seed, grid in cert_grids.items()}
    eval_tail = {seed: stable_tail_actions(grid) for seed, grid in eval_grids.items()}
    cert_raw = {seed: raw_first_safe(grid) for seed, grid in cert_grids.items()}
    eval_raw = {seed: raw_first_safe(grid) for seed, grid in eval_grids.items()}

    summaries = []
    query_rows = []
    diagnostics = []
    for target in SEEDS:
        sources = [seed for seed in SEEDS if seed != target]
        endpoint_cert = cert_grids[target][int(GRID[-1])].assign(
            selected_ef=int(GRID[-1]), abstain=False
        )
        endpoint_eval = eval_grids[target][int(GRID[-1])].assign(
            selected_ef=int(GRID[-1]), abstain=False
        )
        endpoint_ucb = risk_stats(endpoint_cert)[3]
        endpoint_ok = endpoint_ucb <= LIMIT

        cert_actions = history_max([cert_tail[seed] for seed in sources])
        eval_actions = history_max([eval_tail[seed] for seed in sources])
        candidate_cert = execute(cert_grids[target], cert_actions)
        candidate_eval = execute(eval_grids[target], eval_actions)
        candidate_ucb = risk_stats(candidate_cert)[3]
        candidate_ok = endpoint_ok and candidate_ucb <= LIMIT
        deployed_cert = candidate_cert if candidate_ok else endpoint_cert
        deployed_eval = candidate_eval if candidate_ok else endpoint_eval

        summaries.append(summary(target, "FIXED_ENDPOINT", endpoint_cert, endpoint_eval,
                                 endpoint_ok, "ACCEPT" if endpoint_ok else "UNDEPLOYABLE"))
        summaries.append(summary(target, "TCP_HM9_TC_CANDIDATE", candidate_cert,
                                 candidate_eval, candidate_ok,
                                 "ACCEPT_TCP" if candidate_ok else "REJECT_TO_ENDPOINT"))
        summaries.append(summary(target, "TCP_HM9_TC_DEPLOYED", deployed_cert,
                                 deployed_eval, endpoint_ok,
                                 "TCP" if candidate_ok else "FIXED_ENDPOINT"))

        darth_cert = pd.read_csv(args.darth_root / f"seed_{target}" / "darth_cert_500.txt")
        darth_eval = pd.read_csv(args.darth_root / f"seed_{target}" / "darth_eval_1000.txt")
        darth_ok = endpoint_ok and risk_stats(darth_cert)[3] <= LIMIT
        summaries.append(summary(target, "DARTH_RAW", darth_cert, darth_eval, darth_ok,
                                 "ACCEPT_DARTH" if darth_ok else "REJECT_TO_ENDPOINT"))
        summaries.append(summary(target, "DARTH_AUDITED_DEPLOYED",
                                 darth_cert if darth_ok else endpoint_cert,
                                 darth_eval if darth_ok else endpoint_eval,
                                 endpoint_ok, "DARTH" if darth_ok else "FIXED_ENDPOINT"))

        for method, frame in (("FIXED_ENDPOINT", endpoint_eval),
                              ("TCP_HM9_TC_CANDIDATE", candidate_eval),
                              ("TCP_HM9_TC_DEPLOYED", deployed_eval),
                              ("DARTH_RAW", darth_eval),
                              ("DARTH_AUDITED_DEPLOYED", darth_eval if darth_ok else endpoint_eval)):
            for qid, (dist, recall) in enumerate(zip(frame["dists"], recall_values(frame))):
                query_rows.append({"seed": target, "qid": qid, "method": method,
                                   "dists": float(dist), "recall": float(recall)})

        diagnostics.append({
            "target_seed": target,
            "cert_source_raw_vs_tail_changed": int(sum(
                np.sum(cert_raw[seed] != cert_tail[seed]) for seed in sources
            )),
            "eval_source_raw_vs_tail_changed": int(sum(
                np.sum(eval_raw[seed] != eval_tail[seed]) for seed in sources
            )),
            "cert_candidate_abstain": int(np.isinf(cert_actions).sum()),
            "eval_candidate_abstain": int(np.isinf(eval_actions).sum()),
            "endpoint_ucb": endpoint_ucb,
            "candidate_ucb": candidate_ucb,
            "candidate_accepted": bool(candidate_ok),
        })

    args.output.mkdir(parents=True, exist_ok=False)
    summary_frame = pd.DataFrame(summaries)
    query_frame = pd.DataFrame(query_rows)
    summary_frame.to_csv(args.output / "per_build_summary.csv", index=False)
    query_frame.to_csv(args.output / "per_query.csv.gz", index=False, compression="gzip")
    pd.DataFrame(diagnostics).to_csv(args.output / "stable_tail_diagnostics.csv", index=False)

    pooled_rows = []
    for method, frame in query_frame.groupby("method"):
        recalls = frame["recall"]
        pooled_rows.append({
            "method": method,
            "queries": len(frame),
            "eval_risk": float((recalls < TARGET).mean()),
            "mean_recall": float(recalls.mean()),
            "mean_dists": float(frame["dists"].mean()),
            "p50_dists": float(frame["dists"].quantile(0.50)),
            "p95_dists": float(frame["dists"].quantile(0.95)),
            "p99_dists": float(frame["dists"].quantile(0.99)),
        })
    pooled = pd.DataFrame(pooled_rows)
    pooled.to_csv(args.output / "pooled_summary.csv", index=False)
    decision = {
        "method": "TCP_HM9_TC",
        "claim": "FIXED_TARGET_QUERY_RISK_ONLY",
        "formal_5pct_build_certificate": False,
        "fixed_sequence": ["FIXED_ENDPOINT", "TCP_HM9_TC"],
        "accepted_target_builds": int(summary_frame[
            summary_frame.method == "TCP_HM9_TC_CANDIDATE"
        ].accepted.sum()),
        "endpoint_safe_target_builds": int(summary_frame[
            summary_frame.method == "FIXED_ENDPOINT"
        ].accepted.sum()),
        "pooled": pooled.to_dict(orient="records"),
        "bootstrap": bootstrap(query_frame, "TCP_HM9_TC_DEPLOYED", "FIXED_ENDPOINT"),
    }
    (args.output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
