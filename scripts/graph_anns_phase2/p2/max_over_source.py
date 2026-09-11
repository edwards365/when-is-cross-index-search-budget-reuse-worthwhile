#!/usr/bin/env python
"""P2/B1: max-over-source robust baseline from frozen per-query records. Pure code.

For each target build t and query q, a_robust(q) = max over the 23 source builds of
B_s(q) (min safe action, h=10 event). If any source has B_s(q) = BOT (no finite safe
action), the robust policy has no jointly-safe finite action: primary variant abstains,
secondary variant deploys the maximum registered action. Risk is evaluated on the target
with the same h=10 event. DistComp (cost ratio vs per-query oracle) computed only where
per-action distance-computation counts exist (hnswlib).
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA500 = Path("/home/wlk/data500")
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p2"
OUT.mkdir(parents=True, exist_ok=True)

SEED, REPS = 991, 5000
H = 10  # hit requirement


def load_hnswlib(dataset):
    """Return dict build -> (hit pivot with integer hit counts 0..10, ndc pivot)."""
    role = pd.read_csv(REPO / "results/graph_anns_e4_reanalysis/query_role_mapping.csv")
    eval_ids = set(role.loc[(role["dataset"] == dataset) &
                            (role["role"] == "confirmatory_evaluation"), "local_query_id"])
    builds, raw_dir = {}, DATA500 / "graph_anns_e4" / "raw"
    for bdir in sorted(raw_dir.iterdir()):
        if not bdir.name.startswith(dataset):
            continue
        with gzip.open(bdir / "queries.csv.gz", "rt") as f:
            df = pd.read_csv(f)
        df = df[(df["latency_round"] == 0) & (df["query_id"].isin(eval_ids))]
        df = df.drop_duplicates(subset=["query_id", "ef_search"])
        df["hits"] = np.round(df["recall_at_10"] * 10).astype(int)
        pivot_hit = df.pivot(index="query_id", columns="ef_search", values="hits")
        pivot_ndc = df.pivot(index="query_id", columns="ef_search", values="ndc")
        builds[bdir.name] = (pivot_hit, pivot_ndc)
    return builds


def load_faiss(dataset):
    builds, raw_dir = {}, DATA500 / "graph_anns_iclr_phase1_1_repair_scratch" / "faiss_100k" / "raw"
    for f in sorted(raw_dir.glob(f"{dataset}__100k__clean*.csv.gz")):
        with gzip.open(f, "rt") as fh:
            df = pd.read_csv(fh)
        pivot_hit = df.pivot(index="query_id", columns="ef", values="hit_count")
        builds[df["build_id"].iloc[0]] = (pivot_hit, None)
    return builds


def min_safe_actions(hit_pivots, grid):
    """B(q) per build: smallest ef with hit>=H; BOT if none. Also per-ef hit and ndc frames."""
    B, tables = {}, {}
    for name, (hit, ndc) in hit_pivots.items():
        cols = [c for c in grid if c in hit.columns]
        ok = (hit[cols] >= H).values
        ef_idx = np.array(cols)
        first = np.where(ok.any(axis=1), ef_idx[np.argmax(ok, axis=1)], -1)
        B[name] = first
        tables[name] = (hit[cols], (ndc[cols] if ndc is not None else None), ef_idx)
    return B, tables


def bootstrap_risk_ci(events, seed=SEED, reps=REPS):
    rng = np.random.default_rng(seed)
    n = len(events)
    if n == 0:
        return (float("nan"),) * 3
    idx = rng.integers(0, n, size=(reps, n))
    means = events[idx].mean(axis=1)
    return float(events.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def run_cell(dataset, loader, grid, max_action, cost_available):
    builds = loader(dataset)
    B, tables = min_safe_actions(builds, grid)
    names = sorted(B)
    assert len(names) == 24, f"{dataset}: expected 24 builds, got {len(names)}"
    qids = tables[names[0]][0].index.values
    Bmat = np.stack([B[n] for n in names])  # (24, nq) with -1 = BOT
    nq = Bmat.shape[1]

    rows = []
    loo_risks = []
    # per-target evaluation
    for ti, tname in enumerate(names):
        src = np.delete(Bmat, ti, axis=0)          # (23, nq)
        tgt = Bmat[ti]
        src_bot = (src < 0).any(axis=0)
        src_fin = np.where(src < 0, np.nan, src)
        a_rob = np.nanmax(src_fin, axis=0)         # max finite B_s (nan if any source BOT)
        # primary: abstain when no jointly-safe finite action
        deployable = ~src_bot
        # secondary: max registered action when not jointly safe
        a_sec = np.where(src_bot, max_action, a_rob)
        # target events
        hit_t, ndc_t, ef_idx = tables[tname]
        hit_vals = hit_t.loc[qids].values
        ndc_vals = ndc_t.loc[qids].values if ndc_t is not None else None

        def z_of(a):
            j = np.array([np.searchsorted(ef_idx, v) for v in a])
            j = np.clip(j, 0, len(ef_idx) - 1)
            z = (hit_vals[np.arange(nq), j] < H).astype(float)
            c = ndc_vals[np.arange(nq), j] if ndc_vals is not None else None
            return z, c

        z_rob, c_rob = z_of(np.nan_to_num(a_rob, nan=max_action).astype(int))
        z_sec, c_sec = z_of(a_sec.astype(int))
        # naive single-source transport averaged over the 23 sources (policy level)
        z_naive = np.zeros(nq)
        for si in range(src.shape[0]):
            a_s = np.where(src[si] < 0, max_action, src[si])
            z_s, _ = z_of(a_s.astype(int))
            z_naive += z_s
        z_naive /= src.shape[0]
        # oracle per-query cost (min safe on target) for DistComp
        if cost_available:
            feas = tgt > 0
            j_or = np.array([np.searchsorted(ef_idx, v) if v > 0 else len(ef_idx) - 1 for v in tgt])
            c_or = ndc_vals[np.arange(nq), j_or]
            distcomp_rob = float(np.nanmean(c_rob[feas] / c_or[feas])) if feas.any() else float("nan")
            distcomp_sec = float(np.nanmean(c_sec[feas] / c_or[feas])) if feas.any() else float("nan")
        else:
            distcomp_rob = distcomp_sec = "NOT_ESTIMABLE"
        # conservative rate (deployed action strictly above target min safe, feasible queries)
        feas_t = tgt > 0
        cons = float(np.mean(a_rob[feas_t & deployable] > tgt[feas_t & deployable]))
        risk_primary = z_rob[deployable]
        abstain_rate = float((~deployable).mean())
        rows.append({
            "dataset": dataset, "target": tname, "n_queries": nq,
            "risk_abstain_variant": float(np.mean(z_rob[deployable])),
            "abstain_rate_no_jointly_safe": abstain_rate,
            "risk_maxaction_variant": float(np.mean(z_sec)),
            "naive_mean_over_sources": float(np.mean(z_naive)),
            "conservative_rate_feasible": cons,
            "mean_excess_action": float(np.mean(np.where(deployable & feas_t,
                                          np.maximum(a_rob - tgt, 0), 0))),
            "distcomp_vs_oracle_abstain_variant": distcomp_rob,
            "distcomp_vs_oracle_maxaction_variant": distcomp_sec,
        })
        # leave-one-source-out risk (maxaction variant for continuity)
        for sj in range(src.shape[0]):
            keep = np.delete(src, sj, axis=0)
            keep_bot = (keep < 0).any(axis=0)
            a_k = np.where(keep_bot, max_action, np.nan_to_num(
                np.where(keep < 0, np.nan, keep).max(axis=0), nan=max_action))
            z_k, _ = z_of(a_k.astype(int))
            loo_risks.append(float(np.mean(z_k)))
    return pd.DataFrame(rows), loo_risks


def main():
    all_rows, summary = [], []
    specs = [
        ("sift_100k", load_hnswlib, [10, 20, 40, 80, 120, 200], 200, True),
        ("arxiv_nomic_100k", load_hnswlib, [10, 20, 40, 80, 120, 200], 200, True),
        ("sift_100k", load_faiss, [16, 32, 64, 128, 256, 512], 512, False),
        ("arxiv_nomic_100k", load_faiss, [16, 32, 64, 128, 256, 512], 512, False),
    ]
    for dataset, loader, grid, max_action, cost in specs:
        impl = "hnswlib" if cost else "faiss"
        df, loo = run_cell(dataset, loader, grid, max_action, cost)
        df["implementation"] = impl
        all_rows.append(df)
        risk = df["risk_abstain_variant"].values
        m, lo, hi = bootstrap_risk_ci(risk)
        summary.append({
            "dataset": dataset, "implementation": impl,
            "mean_risk_abstain_variant": m, "risk_ci_low": lo, "risk_ci_high": hi,
            "mean_risk_maxaction_variant": float(df["risk_maxaction_variant"].mean()),
            "mean_naive_over_sources": float(df["naive_mean_over_sources"].mean()),
            "mean_abstain_rate": float(df["abstain_rate_no_jointly_safe"].mean()),
            "mean_conservative_rate": float(df["conservative_rate_feasible"].mean()),
            "mean_distcomp_abstain_variant": (float(df["distcomp_vs_oracle_abstain_variant"].mean())
                                              if cost else "NOT_ESTIMABLE"),
            "loo_risk_min": min(loo), "loo_risk_max": max(loo),
        })
        print(summary[-1])
    per_target = pd.concat(all_rows, ignore_index=True)
    per_target.to_csv(OUT / "max_over_source.csv", index=False)
    pd.DataFrame(summary).to_csv(OUT / "max_over_source_summary.csv", index=False)
    (OUT / "max_over_source_summary.json").write_text(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
    run_scaling()


def k_source_scaling(dataset, loader, grid, max_action, ks=(1, 2, 3, 5, 10, 22), draws=50):
    """Risk of max-over-k-sources as a function of k (random source subsets, seed 991)."""
    builds = loader(dataset)
    B, tables = min_safe_actions(builds, grid)
    names = sorted(B)
    qids = tables[names[0]][0].index.values
    Bmat = np.stack([B[n] for n in names]).astype(float)
    Bmat[Bmat < 0] = np.nan
    rng = np.random.default_rng(SEED)
    rows = []
    for k in ks:
        risks, cons_rates = [], []
        for ti, tname in enumerate(names):
            src_idx = [i for i in range(len(names)) if i != ti]
            hit_t, _, ef_idx = tables[tname]
            hit_vals = hit_t.loc[qids].values
            for _ in range(draws):
                pick = rng.choice(src_idx, size=min(k, len(src_idx)), replace=False)
                src = Bmat[pick]
                any_bot = np.isnan(src).any(axis=0)
                a = np.where(any_bot, max_action, np.nanmax(src, axis=0))
                j = np.clip(np.searchsorted(ef_idx, a), 0, len(ef_idx) - 1)
                z = (hit_vals[np.arange(len(qids)), j] < H).astype(float)
                risks.append(np.mean(z))
                tgt = Bmat[ti]
                feas = ~np.isnan(tgt)
                cons_rates.append(np.mean(a[feas] > tgt[feas]))
        rows.append({"dataset": dataset, "k_sources": k, "mean_risk": float(np.mean(risks)),
                     "risk_p95": float(np.percentile(risks, 95)),
                     "mean_conservative_rate": float(np.mean(cons_rates)), "draws": draws})
        print(rows[-1])
    return rows


def run_scaling():
    all_rows = []
    for dataset, loader, grid, max_action, impl in [
            ("sift_100k", load_hnswlib, [10, 20, 40, 80, 120, 200], 200, "hnswlib"),
            ("arxiv_nomic_100k", load_hnswlib, [10, 20, 40, 80, 120, 200], 200, "hnswlib"),
            ("sift_100k", load_faiss, [16, 32, 64, 128, 256, 512], 512, "faiss"),
            ("arxiv_nomic_100k", load_faiss, [16, 32, 64, 128, 256, 512], 512, "faiss")]:
        rows = k_source_scaling(dataset, loader, grid, max_action)
        for r in rows:
            r["implementation"] = impl
        all_rows += rows
    pd.DataFrame(all_rows).to_csv(OUT / "max_over_k_sources.csv", index=False)
