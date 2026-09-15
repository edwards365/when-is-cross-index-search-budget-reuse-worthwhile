#!/usr/bin/env python3
"""Bonferroni-valid TCP -> source fixed -> endpoint fallback audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from phase3_baselines import constant_policy, source_global_action
from tcp_hm9_tc import (
    LIMIT, SEEDS, TARGET, bootstrap, cp_ucb, execute, history_max, load_grid,
    recall_values, risk_stats, stable_tail_actions,
)

CONFIDENCE = 1.0 - 0.05 / 3.0


def simultaneous_pass(frame: pd.DataFrame) -> tuple[bool, int, int, float, float]:
    failures, n, risk, _ = risk_stats(frame)
    ucb = cp_ucb(failures, n, CONFIDENCE)
    return ucb <= LIMIT, failures, n, risk, ucb


def choose_policy(tcp_ok: bool, fixed_ok: bool, endpoint_ok: bool) -> str:
    if tcp_ok:
        return "TCP_HM9_TC"
    if fixed_ok:
        return "SOURCE_GLOBAL_FIXED"
    if endpoint_ok:
        return "FIXED_ENDPOINT"
    return "INVALID_NO_CERTIFIED_ACTION"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()

    cert_grids = {s: load_grid(args.fixed_root / f"seed_{s}", "cert") for s in SEEDS}
    eval_grids = {s: load_grid(args.fixed_root / f"seed_{s}", "eval") for s in SEEDS}
    cert_tail = {s: stable_tail_actions(g) for s, g in cert_grids.items()}
    eval_tail = {s: stable_tail_actions(g) for s, g in eval_grids.items()}
    summaries: list[dict] = []
    query_records: list[dict] = []

    for target in SEEDS:
        sources = [s for s in SEEDS if s != target]
        source_ef = source_global_action([cert_grids[s] for s in sources])

        tcp_cert = execute(cert_grids[target], history_max([cert_tail[s] for s in sources]))
        tcp_eval = execute(eval_grids[target], history_max([eval_tail[s] for s in sources]))
        fixed_cert = constant_policy(cert_grids[target], source_ef, 0, 500)
        fixed_eval = constant_policy(eval_grids[target], source_ef)
        endpoint_cert = constant_policy(cert_grids[target], 200, 0, 500)
        endpoint_eval = constant_policy(eval_grids[target], 200)

        tcp_check = simultaneous_pass(tcp_cert)
        fixed_check = simultaneous_pass(fixed_cert)
        endpoint_check = simultaneous_pass(endpoint_cert)
        selected = choose_policy(tcp_check[0], fixed_check[0], endpoint_check[0])
        if selected == "INVALID_NO_CERTIFIED_ACTION":
            raise RuntimeError(f"no simultaneously certified action for target {target}")
        deployed = {
            "TCP_HM9_TC": tcp_eval,
            "SOURCE_GLOBAL_FIXED": fixed_eval,
            "FIXED_ENDPOINT": endpoint_eval,
        }[selected]
        selected_check = {
            "TCP_HM9_TC": tcp_check,
            "SOURCE_GLOBAL_FIXED": fixed_check,
            "FIXED_ENDPOINT": endpoint_check,
        }[selected]
        rec = recall_values(deployed)
        summaries.append({
            "seed": target,
            "source_fixed_ef": source_ef,
            "selected_policy": selected,
            "tcp_simultaneous_ucb": tcp_check[4],
            "fixed_simultaneous_ucb": fixed_check[4],
            "endpoint_simultaneous_ucb": endpoint_check[4],
            "selected_cert_failures": selected_check[1],
            "selected_cert_n": selected_check[2],
            "selected_cert_risk": selected_check[3],
            "selected_simultaneous_ucb": selected_check[4],
            "eval_risk": float((rec < TARGET).mean()),
            "mean_recall": float(rec.mean()),
            "mean_dists": float(deployed.dists.mean()),
            "p95_dists": float(deployed.dists.quantile(.95)),
            "p99_dists": float(deployed.dists.quantile(.99)),
            "abstain_rate": float(deployed.abstain.mean()) if "abstain" in deployed else 0.0,
        })
        for qid, (distance, recall) in enumerate(zip(deployed.dists, rec)):
            query_records.append({"seed": target, "qid": qid,
                                  "method": "TCP_GRADED_FALLBACK",
                                  "dists": float(distance), "recall": float(recall)})
        for qid, (distance, recall) in enumerate(zip(fixed_eval.dists, recall_values(fixed_eval))):
            query_records.append({"seed": target, "qid": qid,
                                  "method": "SOURCE_GLOBAL_FIXED_DEPLOYED",
                                  "dists": float(distance), "recall": float(recall)})

    args.output.mkdir(parents=True, exist_ok=False)
    summary = pd.DataFrame(summaries)
    query = pd.DataFrame(query_records)
    summary.to_csv(args.output / "per_build_summary.csv", index=False)
    query.to_csv(args.output / "per_query.csv.gz", index=False, compression="gzip")
    pooled = query.groupby("method").agg(
        queries=("qid", "count"), mean_dists=("dists", "mean"),
        p95_dists=("dists", lambda x: x.quantile(.95)),
        p99_dists=("dists", lambda x: x.quantile(.99)),
        eval_risk=("recall", lambda x: (x < TARGET).mean()),
        mean_recall=("recall", "mean"),
    ).reset_index()
    pooled.to_csv(args.output / "pooled_summary.csv", index=False)

    comparison = bootstrap(query, "TCP_GRADED_FALLBACK", "SOURCE_GLOBAL_FIXED_DEPLOYED")
    pivot = query.pivot(index=["seed", "qid"], columns="method", values="dists")
    build_diff = pivot["TCP_GRADED_FALLBACK"].sub(
        pivot["SOURCE_GLOBAL_FIXED_DEPLOYED"]).groupby(level=0).mean()
    tcp = pooled[pooled.method == "TCP_GRADED_FALLBACK"].iloc[0]
    base = pooled[pooled.method == "SOURCE_GLOBAL_FIXED_DEPLOYED"].iloc[0]
    largest_gain = int(build_diff.idxmin())
    decision = {
        "dataset": args.dataset,
        "policy_order": ["TCP_HM9_TC", "SOURCE_GLOBAL_FIXED", "FIXED_ENDPOINT"],
        "simultaneous_confidence": CONFIDENCE,
        "familywise_alpha": 0.05,
        "mean_gain_fraction": float((base.mean_dists - tcp.mean_dists) / base.mean_dists),
        "p95_ratio": float(tcp.p95_dists / base.p95_dists),
        "p99_ratio_diagnostic": float(tcp.p99_dists / base.p99_dists),
        "bootstrap": comparison,
        "lobo_mean_differences": {str(int(s)): float(build_diff.drop(s).mean()) for s in build_diff.index},
        "delete_largest_gain_build": largest_gain,
        "delete_largest_gain_mean_difference": float(build_diff.drop(largest_gain).mean()),
        "mean_gate": bool(comparison["ci95"][1] < 0),
        "materiality_5pct": bool((base.mean_dists - tcp.mean_dists) / base.mean_dists >= .05),
        "p95_noninferiority_5pct": bool(tcp.p95_dists / base.p95_dists <= 1.05),
        "all_selected_policies_simultaneously_certified": bool((summary.selected_simultaneous_ucb <= LIMIT).all()),
        "selection_counts": {str(k): int(v) for k, v in summary.selected_policy.value_counts().items()},
        "formal_build_certificate": False,
    }
    (args.output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
