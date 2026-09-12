#!/usr/bin/env python
"""P6-B: learned-predictor transfer probe (policy layer, retrospective replay).

Question: does a query-level budget predictor trained on SOURCE builds transfer to a
TARGET build, compared with (i) naive single-source transport and (ii) per-build
recalibration (in-target training)?

Predictor: HistGradientBoostingRegressor on deployment-time features observable without
truth: the per-query transcript of the CHEAPEST registered action (ef=10) on the index
being served (visited nodes, queue pushes/pops, result pushes/pops, log latency median).
Label: log2 of the minimum safe action B(q) (BOT excluded from training/eval).
Deploy rule: a = smallest registered grid action >= 2^pred (conservative rounding).

Protocol per target build t (24 hnswlib builds per dataset):
  train on 23 source builds' (features@ef10 on that same build, B_s(q))
  predict on t's features@ef10 -> deploy on t -> risk/cost
  in-target upper bound: 5-fold CV of the same model trained on t itself.
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

DATA500 = Path("/home/wlk/data500")
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p6"
OUT.mkdir(parents=True, exist_ok=True)
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10
FEATS = ["visited_nodes", "candidate_queue_pushes", "candidate_queue_pops",
         "result_queue_pushes", "result_queue_pops", "latency_ns"]


def load(dataset):
    role = pd.read_csv(REPO / "results/graph_anns_e4_reanalysis/query_role_mapping.csv")
    eval_ids = set(role.loc[(role["dataset"] == dataset) &
                            (role["role"] == "confirmatory_evaluation"), "local_query_id"])
    builds = {}
    raw = DATA500 / "graph_anns_e4" / "raw"
    for bdir in sorted(raw.iterdir()):
        if not bdir.name.startswith(dataset):
            continue
        with gzip.open(bdir / "queries.csv.gz", "rt") as f:
            df = pd.read_csv(f)
        df = df[df["query_id"].isin(eval_ids)].drop_duplicates(subset=["query_id", "ef_search"])
        hits = df.pivot(index="query_id", columns="ef_search", values="recall_at_10")
        hits = np.round(hits * 10).astype(int)
        f10 = df[df.ef_search == 10].set_index("query_id").sort_index()
        lat = df[df.ef_search == 10].groupby("query_id")["latency_ns"].median()
        feat = pd.DataFrame({
            "visited_nodes": f10["visited_nodes"],
            "candidate_queue_pushes": f10["candidate_queue_pushes"],
            "candidate_queue_pops": f10["candidate_queue_pops"],
            "result_queue_pushes": f10["result_queue_pushes"],
            "result_queue_pops": f10["result_queue_pops"],
            "latency_ns": lat,
        })
        # B(q)
        ok = (hits >= H).values
        B = pd.Series(np.where(ok.any(axis=1), GRID[np.argmax(ok, axis=1)], -1),
                      index=hits.index)
        ndc = df.pivot(index="query_id", columns="ef_search", values="ndc")
        builds[bdir.name] = {"B": B, "feat": feat, "hits": hits, "ndc": ndc}
    return builds


def snap(pred_log2):
    return GRID[np.searchsorted(GRID, np.power(2.0, np.clip(pred_log2, np.log2(10), np.log2(200))))].clip(max=200)


def run(dataset):
    builds = load(dataset)
    names = sorted(builds)
    qids = builds[names[0]]["B"].index.values
    rows = []
    for t in names:
        Bt = builds[t]["B"].loc[qids]
        feas = Bt > 0
        hits_t = builds[t]["hits"].loc[qids]
        ndc_t = builds[t]["ndc"].loc[qids]
        # oracle cost
        j_or = np.array([np.searchsorted(GRID, v) if v > 0 else len(GRID) - 1 for v in Bt.values])
        c_or = ndc_t.values[np.arange(len(qids)), j_or]

        def risk_cost(a):
            j = np.clip(np.searchsorted(GRID, a), 0, len(GRID) - 1)
            z = (hits_t.values[np.arange(len(qids)), j] < H).astype(float)
            c = ndc_t.values[np.arange(len(qids)), j]
            ok = feas.values & ~np.isnan(c_or)
            return z.mean(), float(np.mean(c[ok] / c_or[ok]))

        # (i) naive: single random source (mean over 8 draws)
        rng = np.random.RandomState(991)
        naive = [risk_cost(builds[s]["B"].loc[qids].fillna(200).values.astype(float))
                 for s in rng.choice([n for n in names if n != t], 8)]
        naive_risk = float(np.mean([n[0] for n in naive]))
        # (ii) predictor transfer: train on 23 sources, apply to t
        Xs, ys = [], []
        for s in names:
            if s == t:
                continue
            Bs = builds[s]["B"].loc[qids]
            m = Bs > 0
            Xs.append(builds[s]["feat"].loc[qids].values[m.values])
            ys.append(np.log2(Bs.values[m.values]))
        Xs, ys = np.vstack(Xs), np.concatenate(ys)
        gbr = HistGradientBoostingRegressor(max_iter=200, random_state=0)
        gbr.fit(Xs, ys)
        Xt = builds[t]["feat"].loc[qids].values
        a_pred = snap(gbr.predict(Xt))
        tr_risk, tr_cost = risk_cost(a_pred)
        # (iii) in-target 5-fold CV
        from sklearn.model_selection import KFold
        m = feas.values
        cv_a = np.full(len(qids), np.nan)
        idx_m = np.where(m)[0]
        for tr, te in KFold(5, shuffle=True, random_state=0).split(qids[m]):
            g2 = HistGradientBoostingRegressor(max_iter=200, random_state=0)
            g2.fit(Xt[m][tr], np.log2(Bt.values[m][tr]))
            cv_a[idx_m[te]] = snap(g2.predict(Xt[m][te]))
        cv_risk, cv_cost = risk_cost(np.nan_to_num(cv_a, nan=200))
        rows.append({"dataset": dataset, "target": t,
                     "naive_risk": naive_risk,
                     "transfer_risk": tr_risk, "transfer_distcomp": tr_cost,
                     "intarget_cv_risk": cv_risk, "intarget_cv_distcomp": cv_cost,
                     "transfer_excess_action": float(np.mean(a_pred[feas.values] - Bt.values[feas.values]))})
        print(f"{t}: naive={naive_risk:.3f} transfer={tr_risk:.3f}@{tr_cost:.2f}x intarget={cv_risk:.3f}@{cv_cost:.2f}x")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"predictor_probe_{dataset}.csv", index=False)
    return df


if __name__ == "__main__":
    all_df = pd.concat([run("sift_100k"), run("arxiv_nomic_100k")], ignore_index=True)
    summary = all_df.groupby("dataset")[["naive_risk", "transfer_risk", "transfer_distcomp",
                                         "intarget_cv_risk", "intarget_cv_distcomp"]].mean()
    summary.to_csv(OUT / "predictor_probe_summary.csv")
    print(summary)
