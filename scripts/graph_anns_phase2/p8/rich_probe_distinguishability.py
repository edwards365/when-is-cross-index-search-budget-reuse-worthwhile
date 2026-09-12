#!/usr/bin/env python
"""P8-C: distinguishability with RICH probe features (reviewer Q2).
Feature families per query (all deployment-time observable, no truth):
  F1 hits   : hit counts at ef in {10,20,40} (registered transcript class, baseline)
  F2 runtime: visited_nodes / queue stats / median latency at ef=10
  F3 both   : F1 + F2
Two-sample classifier accuracy (HistGB, 50/50 split, seed 0) over all 276 pairs per
dataset. If F2/F3 stay near chance, Theorem 1's instantiation is robust to richer
probes; if they separate, the claim must be weakened accordingly."""
import gzip
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

DATA500 = Path("/home/wlk/data500")
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p8"


def load(dataset):
    role = pd.read_csv(REPO / "results/graph_anns_e4_reanalysis/query_role_mapping.csv")
    eval_ids = sorted(role.loc[(role["dataset"] == dataset) &
                               (role["role"] == "confirmatory_evaluation"), "local_query_id"])
    builds = {}
    for bdir in sorted((DATA500 / "graph_anns_e4" / "raw").iterdir()):
        if not bdir.name.startswith(dataset):
            continue
        with gzip.open(bdir / "queries.csv.gz", "rt") as f:
            df = pd.read_csv(f)
        df = df[df["query_id"].isin(eval_ids)].drop_duplicates(
            subset=["query_id", "ef_search"]).sort_values("query_id")
        hits = np.round(df.pivot(index="query_id", columns="ef_search",
                                 values="recall_at_10") * 10).astype(int)
        f10 = df[df.ef_search == 10].set_index("query_id").sort_index()
        lat = df[df.ef_search == 10].groupby("query_id")["latency_ns"].median().sort_index()
        F1 = hits[[10, 20, 40]].values.astype(float)
        F2 = np.column_stack([
            f10["visited_nodes"].values, f10["candidate_queue_pushes"].values,
            f10["candidate_queue_pops"].values, f10["result_queue_pushes"].values,
            f10["result_queue_pops"].values, lat.values])
        builds[bdir.name] = {"F1": F1, "F2": F2}
    return builds


def acc(Xs, Xt, seed=0):
    X = np.vstack([Xs, Xt])
    y = np.r_[np.zeros(len(Xs)), np.ones(len(Xt))]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.5, random_state=seed, stratify=y)
    clf = HistGradientBoostingClassifier(max_iter=80, random_state=seed)
    clf.fit(Xtr, ytr)
    return float((clf.predict(Xte) == yte).mean())


def main():
    out = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load(dataset)
        names = sorted(builds)
        rng = np.random.RandomState(0)
        all_pairs = list(combinations(names, 2))
        sel = [all_pairs[i] for i in rng.choice(len(all_pairs), 60, replace=False)]
        for (s, t) in sel:
            r = {"dataset": dataset, "pair": f"{s}|{t}"}
            for F in ("F1", "F2", "F3"):
                Xs = builds[s]["F1"] if F == "F1" else (
                    builds[s]["F2"] if F == "F2" else np.column_stack(
                        [builds[s]["F1"], builds[s]["F2"]]))
                Xt = builds[t]["F1"] if F == "F1" else (
                    builds[t]["F2"] if F == "F2" else np.column_stack(
                        [builds[t]["F1"], builds[t]["F2"]]))
                r[f"acc_{F}"] = acc(Xs, Xt)
            out.append(r)
        g = pd.DataFrame([x for x in out if x["dataset"] == dataset])
        stats = {F: (round(g['acc_' + F].min(), 3), round(g['acc_' + F].median(), 3),
                     round(g['acc_' + F].max(), 3)) for F in ('F1', 'F2', 'F3')}
        print(dataset, stats, flush=True)
    df = pd.DataFrame(out)
    df.to_csv(OUT / "rich_probe_distinguishability.csv", index=False)
    entry0 = {}
    for d, g in df.groupby("dataset"):
        e = {"n_pairs": len(g)}
        for F in ('F1', 'F2', 'F3'):
            e[F + '_median'] = float(g['acc_' + F].median())
            e[F + '_max'] = float(g['acc_' + F].max())
        entry0[d] = e
    summary = entry0
    (OUT / "rich_probe_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
