#!/usr/bin/env python
"""P6-C: probe-distinguishability instantiation for Theorem 1 (registered pairs).

For a build pair (s,t) and probe level k (the k cheapest registered actions), the
observable transcript of query q is its hit-count vector over those actions. Theorem 1's
premise needs build pairs whose transcript distributions are close (low TV). We estimate
TV from below with a classifier two-sample test:

  acc(s,t,k) = balanced accuracy of HistGradientBoostingClassifier attributing transcripts
               to s vs t (train 375 / test 375, seed 0);
  TV_k(s,t) >= 2*acc - 1     (optimal-classifier identity, binary case).

Near-indistinguishable pair <=> acc near 0.5 on ALL k. Reported per dataset over all
C(24,2)=276 registered pairs, k in {1,3,6}. Verdict: does any registered pair instantiate
the near-indistinguishability premise?
"""
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
OUT = REPO / "results" / "graph_anns_phase2_p6"
OUT.mkdir(parents=True, exist_ok=True)
GRID = [10, 20, 40, 80, 120, 200]
K_LEVELS = {"k1": 1, "k3": 3, "k6": 6}


def load_hits(dataset):
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
        df = df[(df["latency_round"] == 0) & (df["query_id"].isin(eval_ids))]
        df = df.drop_duplicates(subset=["query_id", "ef_search"])
        h = np.round(df.pivot(index="query_id", columns="ef_search",
                              values="recall_at_10") * 10).astype(int)
        builds[bdir.name] = h[GRID].values  # (750, 6) aligned to GRID
    return builds


def tv_plugin(Hs, Ht, k):
    """Exact plug-in TV between the empirical transcript distributions (shared support)."""
    from collections import Counter
    def enc(H):
        # encode each row's first k hits as a single int key
        keys = H[:, :k]
        mult = np.array([11 ** i for i in range(k)])
        return (keys * mult).sum(axis=1)
    cs, ct = Counter(enc(Hs).tolist()), Counter(enc(Ht).tolist())
    ns, nt = sum(cs.values()), sum(ct.values())
    support = set(cs) | set(ct)
    return 0.5 * sum(abs(cs.get(v, 0) / ns - ct.get(v, 0) / nt) for v in support)


def tv_lower_bound(Hs, Ht, k, seed=0):
    Xs, Xt = Hs[:, :k].astype(float), Ht[:, :k].astype(float)
    X = np.vstack([Xs, Xt])
    y = np.r_[np.zeros(len(Xs)), np.ones(len(Xt))]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.5, random_state=seed, stratify=y)
    clf = HistGradientBoostingClassifier(max_iter=100, random_state=seed)
    clf.fit(Xtr, ytr)
    acc = float((clf.predict(Xte) == yte).mean())
    return acc, max(0.0, 2 * acc - 1)


def main():
    all_rows = []
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        builds = load_hits(dataset)
        names = sorted(builds)
        pairs = list(combinations(names, 2))
        # cap compute: all pairs at k3, all at k1/k6 too (fast features)
        for (s, t) in pairs:
            row = {"dataset": dataset, "pair": f"{s}|{t}"}
            for kname, k in K_LEVELS.items():
                acc, tvlb = tv_lower_bound(builds[s], builds[t], k)
                row[f"acc_{kname}"] = acc
                row[f"tv_lb_{kname}"] = tvlb
                row[f"tv_plugin_{kname}"] = tv_plugin(builds[s], builds[t], k)
            all_rows.append(row)
        df = pd.DataFrame([r for r in all_rows if r["dataset"] == dataset])
        print(dataset, "pairs:", len(df))
        print(df[[f"acc_{k}" for k in K_LEVELS]].describe().loc[["min", "50%"]].to_string())
    df = pd.DataFrame(all_rows)
    df.to_csv(OUT / "distinguishability_pairs.csv", index=False)
    summary = {}
    for dataset in ("sift_100k", "arxiv_nomic_100k"):
        g = df[df.dataset == dataset]
        best = g.loc[g["acc_k6"].idxmin()]
        summary[dataset] = {
            "pairs": len(g),
            "acc_k1_min": float(g.acc_k1.min()), "acc_k1_median": float(g.acc_k1.median()),
            "acc_k3_min": float(g.acc_k3.min()), "acc_k3_median": float(g.acc_k3.median()),
            "acc_k6_min": float(g.acc_k6.min()), "acc_k6_median": float(g.acc_k6.median()),
            "tv_plugin_k1_max": float(g.tv_plugin_k1.max()),
            "tv_plugin_k3_max": float(g.tv_plugin_k3.max()),
            "tv_plugin_k6_max": float(g.tv_plugin_k6.max()),
            "tv_plugin_k6_median": float(g.tv_plugin_k6.median()),
            "closest_pair_k6": best["pair"], "closest_acc_k6": float(best["acc_k6"]),
            "near_indistinguishable_pair_exists(k6_acc<0.6)": bool((g.acc_k6 < 0.6).any()),
        }
    (OUT / "distinguishability_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
