#!/usr/bin/env python3
"""Analyze one frozen DARTH/TCP data-refresh cell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta


SEEDS = [1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267]
GRID = np.array([10, 20, 40, 80, 120, 160, 200], dtype=int)


def cp_ucb(x: int, n: int) -> float:
    return 1.0 if x == n else float(beta.ppf(0.95, x + 1, n - x))


def rcol(frame: pd.DataFrame) -> pd.Series:
    return frame["r_actual"] if "r_actual" in frame else frame["r"]


def grid(path: Path, split: str) -> dict[int, pd.DataFrame]:
    return {int(ef): pd.read_csv(path / "fixed" / f"{split}_ef{ef}.txt").sort_values("qid") for ef in GRID}


def bottoms(tables: dict[int, pd.DataFrame]) -> np.ndarray:
    hit = np.stack([(rcol(tables[int(ef)]).to_numpy() >= 0.90) for ef in GRID])
    result = np.full(hit.shape[1], 200, dtype=int)
    for row, ef in enumerate(GRID):
        result[(result == 200) & hit[row]] = ef
    return result


def choose(tables: dict[int, pd.DataFrame], actions: np.ndarray) -> pd.DataFrame:
    rows = []
    for qid, ef in enumerate(actions):
        row = tables[int(ef)].iloc[qid].copy()
        row["selected_ef"] = int(ef)
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def fixed_ef(cert: dict[int, pd.DataFrame]) -> int:
    for ef in GRID:
        r = rcol(cert[int(ef)])
        x = int((r < 0.90).sum())
        if cp_ucb(x, len(r)) <= 0.05:
            return int(ef)
    return 200


def summarize(seed: int, method: str, cert: pd.DataFrame, evaluation: pd.DataFrame, fallback: int) -> tuple[dict, pd.DataFrame]:
    cr, er = rcol(cert), rcol(evaluation)
    x = int((cr < 0.90).sum())
    accepted = cp_ucb(x, len(cr)) <= 0.05
    row = {
        "seed": seed, "method": method, "accepted": accepted, "fallback_ef": fallback,
        "cert_risk": float((cr < 0.90).mean()), "cert_cp95_ucb": cp_ucb(x, len(cr)),
        "eval_risk": float((er < 0.90).mean()), "eval_mean_recall": float(er.mean()),
        "mean_dists": float(evaluation.dists.mean()), "p95_dists": float(evaluation.dists.quantile(.95)),
        "p99_dists": float(evaluation.dists.quantile(.99)), "mean_ms": float(evaluation.elaps_ms.mean()),
    }
    q = pd.DataFrame({"seed": seed, "qid": evaluation.qid.astype(int), "method": method, "dists": evaluation.dists.astype(float), "failure": (er < .90).astype(int)})
    return row, q


def bootstrap(per_query: pd.DataFrame, left: str, right: str, value: str) -> dict:
    table = per_query.pivot(index=["seed", "qid"], columns="method", values=value)
    diffs = {seed: group[left].to_numpy() - group[right].to_numpy() for seed, group in table.groupby(level=0)}
    rng = np.random.RandomState(991); seeds = np.array(sorted(diffs)); draws = np.empty(5000)
    for rep in range(5000):
        picked = rng.choice(seeds, len(seeds), replace=True); means = []
        for seed in picked:
            values = diffs[int(seed)]; means.append(float(rng.choice(values, len(values), replace=True).mean()))
        draws[rep] = float(np.mean(means))
    observed = float(np.mean([values.mean() for values in diffs.values()]))
    return {"left": left, "right": right, "value": value, "observed": observed, "ci95": [float(np.quantile(draws,.025)), float(np.quantile(draws,.975))]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-root", required=True, type=Path)
    parser.add_argument("--refresh-root", required=True, type=Path)
    parser.add_argument("--refresh", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    old_cert = {s: grid(args.old_root / "m1" / f"seed_{s}", "cert") for s in SEEDS}
    old_eval = {s: grid(args.old_root / "m1" / f"seed_{s}", "eval") for s in SEEDS}
    new_paths = {s: args.refresh_root / "runs" / f"refresh_{args.refresh}" / f"seed_{s}" for s in SEEDS}
    new_cert = {s: grid(p, "cert") for s, p in new_paths.items()}
    new_eval = {s: grid(p, "eval") for s, p in new_paths.items()}
    old_cb, old_eb = {s: bottoms(old_cert[s]) for s in SEEDS}, {s: bottoms(old_eval[s]) for s in SEEDS}
    new_cb, new_eb = {s: bottoms(new_cert[s]) for s in SEEDS}, {s: bottoms(new_eval[s]) for s in SEEDS}
    rows, qrows = [], []
    for target in SEEDS:
        sources = [s for s in SEEDS if s != target]
        fallback = fixed_ef(new_cert[target])
        fixed_cert, fixed_eval = new_cert[target][fallback], new_eval[target][fallback]
        methods = {
            "FIXED_CERTIFIED": (fixed_cert, fixed_eval),
            "TCP_OLD_POOL_RAW": (choose(new_cert[target], np.max(np.stack([old_cb[s] for s in sources]), axis=0)), choose(new_eval[target], np.max(np.stack([old_eb[s] for s in sources]), axis=0))),
            "TCP_REFRESHED_POOL_RAW": (choose(new_cert[target], np.max(np.stack([new_cb[s] for s in sources]), axis=0)), choose(new_eval[target], np.max(np.stack([new_eb[s] for s in sources]), axis=0))),
            "DARTH_OLD_MODEL_RAW": (pd.read_csv(new_paths[target] / "darth_old_cert.txt"), pd.read_csv(new_paths[target] / "darth_old_eval.txt")),
            "DARTH_REFRESH_RETRAINED_RAW": (pd.read_csv(new_paths[target] / "darth_refreshed_cert.txt"), pd.read_csv(new_paths[target] / "darth_refreshed_eval.txt")),
        }
        for method, (cert, evaluation) in methods.items():
            row, query = summarize(target, method, cert, evaluation, fallback); rows.append(row); qrows.append(query)
            if method != "FIXED_CERTIFIED":
                deployed = evaluation if row["accepted"] else fixed_eval
                effective_cert = cert if row["accepted"] else fixed_cert
                deployed_name = method.replace("_RAW", "_AUDITED_DEPLOYED")
                drow, dquery = summarize(target, deployed_name, effective_cert, deployed, fallback)
                drow["base_policy_accepted"] = row["accepted"]
                rows.append(drow); qrows.append(dquery)
    summary = pd.DataFrame(rows); per_query = pd.concat(qrows, ignore_index=True)
    args.output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output / f"m3_refresh_{args.refresh}_summary.csv", index=False)
    per_query.to_csv(args.output / f"m3_refresh_{args.refresh}_per_query.csv.gz", index=False, compression="gzip")
    pooled = summary.groupby("method", as_index=False).agg(builds=("seed","count"), certified_builds=("accepted","sum"), mean_cert_risk=("cert_risk","mean"), max_cert_ucb=("cert_cp95_ucb","max"), mean_eval_risk=("eval_risk","mean"), mean_dists=("mean_dists","mean"), mean_p95_dists=("p95_dists","mean"), mean_ms=("mean_ms","mean"))
    raw_acceptance = summary.dropna(subset=["base_policy_accepted"]).groupby("method")["base_policy_accepted"].sum().to_dict()
    pooled["base_policy_accepted_builds"] = pooled["method"].map(raw_acceptance)
    pooled.to_csv(args.output / f"m3_refresh_{args.refresh}_pooled.csv", index=False)
    deployed = ["TCP_OLD_POOL_AUDITED_DEPLOYED", "TCP_REFRESHED_POOL_AUDITED_DEPLOYED", "DARTH_OLD_MODEL_AUDITED_DEPLOYED", "DARTH_REFRESH_RETRAINED_AUDITED_DEPLOYED"]
    comparisons = [bootstrap(per_query, method, "FIXED_CERTIFIED", "dists") for method in deployed]
    decision = {"module":"M3_DATA_REFRESH", "refresh":args.refresh, "pooled":pooled.to_dict(orient="records"), "bootstrap_vs_fixed":comparisons, "formal_tcp_95pct_certificate_available":False, "safety_source":"INDEPENDENT_TARGET_QUERY_CERTIFICATION"}
    (args.output / f"m3_refresh_{args.refresh}_decision.json").write_text(json.dumps(decision,indent=2)+"\n")
    print(json.dumps(decision,indent=2))


if __name__ == "__main__":
    main()
