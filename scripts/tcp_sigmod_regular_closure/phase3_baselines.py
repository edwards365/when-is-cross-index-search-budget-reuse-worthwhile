#!/usr/bin/env python3
"""Independent target split and deployable baseline audit for TCP-HM9-TC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tcp_hm9_tc import (
    GRID, LIMIT, SEEDS, TARGET, bootstrap, cp_ucb, execute, history_max,
    load_grid, recall_values, risk_stats, stable_tail_actions,
)


def rows(frame: pd.DataFrame, start: int, stop: int) -> pd.DataFrame:
    result = frame[(frame.qid >= start) & (frame.qid < stop)].copy()
    return result.sort_values("qid").reset_index(drop=True)


def first_passing_action(grid: dict[int, pd.DataFrame], start: int, stop: int) -> int:
    for ef in GRID:
        frame = rows(grid[int(ef)], start, stop)
        if risk_stats(frame)[3] <= LIMIT:
            return int(ef)
    return int(GRID[-1])


def source_global_action(source_grids: list[dict[int, pd.DataFrame]]) -> int:
    for ef in GRID:
        if all(risk_stats(grid[int(ef)])[3] <= LIMIT for grid in source_grids):
            return int(ef)
    return int(GRID[-1])


def constant_policy(grid: dict[int, pd.DataFrame], ef: int, start: int | None = None,
                    stop: int | None = None) -> pd.DataFrame:
    frame = grid[ef].copy()
    if start is not None and stop is not None:
        frame = rows(frame, start, stop)
    frame["selected_ef"] = ef
    frame["abstain"] = False
    return frame.reset_index(drop=True)


def record(seed: int, method: str, selected_action: str, cert: pd.DataFrame,
           evaluation: pd.DataFrame, candidate_ok: bool, deployed: bool) -> dict:
    failures, n, risk, ucb = risk_stats(cert)
    recall = recall_values(evaluation)
    return {
        "seed": seed,
        "method": method,
        "selected_action": selected_action,
        "candidate_accepted": bool(candidate_ok),
        "deployed": bool(deployed),
        "cert_n": n,
        "cert_failures": failures,
        "cert_risk": risk,
        "cert_cp95_ucb": ucb,
        "eval_risk": float((recall < TARGET).mean()),
        "mean_recall": float(recall.mean()),
        "mean_dists": float(evaluation.dists.mean()),
        "p95_dists": float(evaluation.dists.quantile(0.95)),
        "p99_dists": float(evaluation.dists.quantile(0.99)),
        "abstain_rate": float(evaluation.abstain.mean()) if "abstain" in evaluation else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-root", required=True, type=Path)
    parser.add_argument("--darth-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()

    cert_grids = {seed: load_grid(args.fixed_root / f"seed_{seed}", "cert") for seed in SEEDS}
    eval_grids = {seed: load_grid(args.fixed_root / f"seed_{seed}", "eval") for seed in SEEDS}
    cert_tail = {seed: stable_tail_actions(grid) for seed, grid in cert_grids.items()}
    eval_tail = {seed: stable_tail_actions(grid) for seed, grid in eval_grids.items()}
    summaries, query_records = [], []

    for target in SEEDS:
        sources = [seed for seed in SEEDS if seed != target]
        endpoint_cert = constant_policy(cert_grids[target], 200, 0, 500)
        endpoint_eval = constant_policy(eval_grids[target], 200)
        endpoint_ok = risk_stats(endpoint_cert)[3] <= LIMIT
        if not endpoint_ok:
            raise RuntimeError(f"fixed endpoint failed on target {target}")

        source_ef = source_global_action([cert_grids[seed] for seed in sources])
        source_cert = constant_policy(cert_grids[target], source_ef, 0, 500)
        source_eval = constant_policy(eval_grids[target], source_ef)
        source_ok = risk_stats(source_cert)[3] <= LIMIT
        source_deployed = source_eval if source_ok else endpoint_eval

        target_ef = first_passing_action(cert_grids[target], 0, 250)
        target_cert = constant_policy(cert_grids[target], target_ef, 250, 500)
        target_eval = constant_policy(eval_grids[target], target_ef)
        target_ok = risk_stats(target_cert)[3] <= LIMIT
        target_deployed = target_eval if target_ok else endpoint_eval

        cert_action = history_max([cert_tail[seed] for seed in sources])
        eval_action = history_max([eval_tail[seed] for seed in sources])
        tcp_cert = execute(cert_grids[target], cert_action)
        tcp_eval = execute(eval_grids[target], eval_action)
        tcp_ok = risk_stats(tcp_cert)[3] <= LIMIT
        tcp_deployed = tcp_eval if tcp_ok else endpoint_eval

        darth_cert_all = pd.read_csv(args.darth_root / f"seed_{target}" / "darth_cert_500.txt")
        darth_cert = rows(darth_cert_all, 0, 500)
        darth_eval = pd.read_csv(args.darth_root / f"seed_{target}" / "darth_eval_1000.txt")
        darth_ok = risk_stats(darth_cert)[3] <= LIMIT
        darth_deployed = darth_eval if darth_ok else endpoint_eval

        methods = [
            ("FIXED_ENDPOINT", "200", endpoint_cert, endpoint_eval, True),
            ("SOURCE_GLOBAL_FIXED_DEPLOYED", str(source_ef), source_cert, source_deployed, source_ok),
            ("TARGET_ONLY_GLOBAL_DEPLOYED", str(target_ef), target_cert, target_deployed, target_ok),
            ("TCP_HM9_TC_DEPLOYED", "PER_QUERY", tcp_cert, tcp_deployed, tcp_ok),
            ("DARTH_AUDITED_DEPLOYED", "MODEL", darth_cert, darth_deployed, darth_ok),
        ]
        for method, action, cert, evaluation, ok in methods:
            summaries.append(record(target, method, action, cert, evaluation, ok, True))
            for qid, (distance, recall) in enumerate(zip(evaluation.dists, recall_values(evaluation))):
                query_records.append({"seed": target, "qid": qid, "method": method,
                                      "dists": float(distance), "recall": float(recall)})

    args.output.mkdir(parents=True, exist_ok=False)
    summary = pd.DataFrame(summaries)
    query = pd.DataFrame(query_records)
    summary.to_csv(args.output / "per_build_summary.csv", index=False)
    query.to_csv(args.output / "per_query.csv.gz", index=False, compression="gzip")

    pooled = query.groupby("method").agg(
        queries=("qid", "count"), mean_dists=("dists", "mean"),
        p95_dists=("dists", lambda x: x.quantile(0.95)),
        p99_dists=("dists", lambda x: x.quantile(0.99)),
        eval_risk=("recall", lambda x: (x < TARGET).mean()),
        mean_recall=("recall", "mean"),
    ).reset_index()
    pooled.to_csv(args.output / "pooled_summary.csv", index=False)

    baseline_names = ["SOURCE_GLOBAL_FIXED_DEPLOYED", "TARGET_ONLY_GLOBAL_DEPLOYED"]
    best = pooled[pooled.method.isin(baseline_names)].sort_values("mean_dists").iloc[0]
    comparison = bootstrap(query, "TCP_HM9_TC_DEPLOYED", str(best.method))
    pivot = query.pivot(index=["seed", "qid"], columns="method", values="dists")
    build_diff = pivot["TCP_HM9_TC_DEPLOYED"].sub(pivot[str(best.method)]).groupby(level=0).mean()
    largest_gain_build = int(build_diff.idxmin())
    lobo = {str(int(seed)): float(build_diff.drop(seed).mean()) for seed in build_diff.index}
    tcp = pooled[pooled.method == "TCP_HM9_TC_DEPLOYED"].iloc[0]
    decision = {
        "dataset": args.dataset,
        "target_label_allocations": {
            "TCP_HM9_TC": "selection=0, certification=qid[0:500]",
            "SOURCE_GLOBAL_FIXED": "selection=0, certification=qid[0:500]",
            "TARGET_ONLY_GLOBAL": "selection=qid[0:250], certification=qid[250:500]"
        },
        "best_deployable_baseline": str(best.method),
        "mean_gain_fraction": float((best.mean_dists - tcp.mean_dists) / best.mean_dists),
        "p95_ratio": float(tcp.p95_dists / best.p95_dists),
        "p99_ratio": float(tcp.p99_dists / best.p99_dists),
        "bootstrap": comparison,
        "lobo_mean_differences": lobo,
        "delete_largest_gain_build": largest_gain_build,
        "delete_largest_gain_mean_difference": float(build_diff.drop(largest_gain_build).mean()),
        "mean_gate": bool(comparison["ci95"][1] < 0),
        "materiality_5pct": bool((best.mean_dists - tcp.mean_dists) / best.mean_dists >= 0.05),
        "p95_noninferiority_5pct": bool(tcp.p95_dists / best.p95_dists <= 1.05),
        "p99_ratio_diagnostic": float(tcp.p99_dists / best.p99_dists),
        "formal_build_certificate": False,
    }
    (args.output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
