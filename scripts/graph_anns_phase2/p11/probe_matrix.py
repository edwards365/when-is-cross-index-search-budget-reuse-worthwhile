#!/usr/bin/env python
"""P11-A1+A2: probe-feature exhaustion matrix + conditional distinguishability.

Feature families (all deployment-time observable):
  F1 hits@{10,20,40}                      (registered transcript class)
  F2 runtime@ef10 (visited/queues/latency) (P8-C family)
  F3 curve-shape of hit-count vs ef grid   (NEW: saturation point, slope, AUC,
                                            argmax-gap, curve entropy)
  F4 F1+F2+F3                              (exhaustive stack)
Classifier two-sample accuracy per build pair (60 pairs/dataset, seed 0) +
PER-QUERY F-statistic: across-build variance / within-build variance per feature,
which tests conditional (query-stratified) distinguishability without a classifier.

Also: predictor matrix (A1 extension) — HistGB predict log2 B(q) per feature family,
source-train -> target-transfer R^2 (the layer-3 claim, per family).
"""
import gzip
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.model_selection import KFold, train_test_split

DATA500 = Path("/home/wlk/data500")
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p11"
OUT.mkdir(parents=True, exist_ok=True)
GRID = np.array([10, 20, 40, 80, 120, 200])
H = 10


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
            subset=["query_id", "ef_search"]).sort_values(["query_id", "ef_search"])
        hits = np.round(df.pivot(index="query_id", columns="ef_search",
                                 values="recall_at_10") * 10).astype(int)[list(GRID)]
        f10 = df[df.ef_search == 10].set_index("query_id").sort_index()
        lat10 = df[df.ef_search == 10].groupby("query_id")["latency_ns"].median().sort_index()
        hv = hits.values.astype(float)
        # F3 curve-shape features per query
        with np.errstate(divide="ignore", invalid="ignore"):
            s5, s10 = np.log2(GRID[4] / GRID[0]), None
            slope = (hv[:, 5] - hv[:, 0]) / np.log2(GRID[5] / GRID[0])
            gain_last = hv[:, 5] - hv[:, 4]
            gain_mid = hv[:, 3] - hv[:, 1]
            ratio_gain = (hv[:, 5] - hv[:, 3]) / np.maximum(hv[:, 3] - hv[:, 0], 1e-9)
        sat = (hv >= H - 1).argmax(axis=1)  # first grid index where hits nearly max
        auc = hv.sum(axis=1)
        entropy = np.apply_along_axis(
            lambda r: -np.sum((r / max(r.sum(), 1)) * np.log2((r / max(r.sum(), 1)) + 1e-12)), 1, hv)
        F3 = np.column_stack([slope, gain_last, gain_mid, ratio_gain, sat, auc, entropy])
        F2 = np.column_stack([
            f10["visited_nodes"].values, f10["candidate_queue_pushes"].values,
            f10["candidate_queue_pops"].values, f10["result_queue_pushes"].values,
            f10["result_queue_pops"].values, lat10.values])
        ok = (hits.values >= H)
        B = pd.Series(np.where(ok.any(axis=1), GRID[np.argmax(ok, axis=1)], -1), index=hits.index)
        builds[bdir.name] = {"F1": hits[[10, 20, 40]].values.astype(float),
                             "F2": F2, "F3": F3, "B": B, "ndc": df.pivot(
                                 index="query_id", columns="ef_search", values="ndc")}
    return builds


FAMS = {"F1": ["F1"], "F2": ["F2"], "F3": ["F3"], "F4": ["F1", "F2", "F3"]}


def stack(b, fams):
    return np.column_stack([b[f] for f in fams])


def main():
    rng = np.random.RandomState(0)
    pair_rows, fam_rows = [], []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load(dataset)
        names = sorted(builds)
        qids = builds[names[0]]["B"].index.values
        pairs = list(combinations(names, 2))
        sel = [pairs[i] for i in rng.choice(len(pairs), 60, replace=False)]

        # ---- A1: classifier matrix
        for (s, t) in sel:
            r = {"dataset": dataset, "pair": f"{s}|{t}"}
            for fam, parts in FAMS.items():
                Xs, Xt = stack(builds[s], parts), stack(builds[t], parts)
                X = np.vstack([Xs, Xt])
                y = np.r_[np.zeros(len(Xs)), np.ones(len(Xt))]
                Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.5,
                                                      random_state=0, stratify=y)
                clf = HistGradientBoostingClassifier(max_iter=80, random_state=0)
                clf.fit(Xtr, ytr)
                r[f"acc_{fam}"] = float((clf.predict(Xte) == yte).mean())
            pair_rows.append(r)
        g = pd.DataFrame([x for x in pair_rows if x["dataset"] == dataset])
        print(dataset, {f: (round(g['acc_' + f].min(), 3), round(g['acc_' + f].median(), 3),
                            round(g['acc_' + f].max(), 3)) for f in FAMS}, flush=True)

        # ---- A2: per-query conditional F-statistic (across-build / within-build) ----
        # For each feature column and query, across-build variance vs mean within-build
        # variance (features constant per (query,build)); aggregate over queries.
        fstats = {}
        for fam, parts in FAMS.items():
            X = np.stack([stack(builds[n], parts) for n in names])  # (24, nq, d)
            across = X.var(axis=0).mean(axis=0)                     # var over builds per q
            fstats[fam] = float(np.nanmean(across))
        # within-build variance is 0 by construction (one value per (q,build));
        # so the informative scale is across-query variance: report normalized
        # across-build / across-query variance per family
        cond = {}
        for fam, parts in FAMS.items():
            X = np.stack([stack(builds[n], parts) for n in names])
            across_build = X.var(axis=0).mean(axis=0).mean()
            across_query = X.var(axis=1).mean(axis=0).mean()
            cond[fam] = float(across_build / max(across_query, 1e-12))
        fam_rows.append({"dataset": dataset, **{f"acrossbuild_over_query_{f}": round(v, 4)
                                                for f, v in cond.items()}})
        print("conditional variance ratio:", fam_rows[-1])

        # ---- predictor matrix (per family) ----
        t = names[0]
        Bt = builds[t]["B"].loc[qids]
        m = (Bt > 0).values
        for fam, parts in FAMS.items():
            Xs, ys = [], []
            for s in names:
                if s == t:
                    continue
                Bs = builds[s]["B"].loc[qids]
                mm = (Bs > 0).values
                Xs.append(stack(builds[s], parts)[mm])
                ys.append(np.log2(Bs.values[mm]))
            gbr = HistGradientBoostingRegressor(max_iter=150, random_state=0)
            gbr.fit(np.vstack(Xs), np.concatenate(ys))
            r2 = gbr.score(stack(builds[t], parts)[m], np.log2(Bt.values[m]))
            fam_rows.append({"dataset": dataset, "family": fam, "transfer_r2_target0": round(r2, 4)})
            print(f"  predictor {fam}: transfer R2 = {r2:.4f}")

    pd.DataFrame(pair_rows).to_csv(OUT / "probe_matrix_pairs.csv", index=False)
    pd.DataFrame(fam_rows).to_csv(OUT / "probe_matrix_families.csv", index=False)


if __name__ == "__main__":
    main()
