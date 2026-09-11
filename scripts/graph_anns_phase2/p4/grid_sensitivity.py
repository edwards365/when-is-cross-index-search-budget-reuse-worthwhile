#!/usr/bin/env python
"""P4: budget-grid sensitivity of the incremental transport risk, computed from frozen
per-query records. Grid variants are SUBGRIDS of the registered grid only (no
interpolation; non-registered action values are NOT_ESTIMABLE by design):

  FULL      all registered actions
  DROP_MIN  registered grid without the smallest action
  DROP_MAX  registered grid without the largest action
  COARSE    every other registered action (10/40/120 or 16/64/256)

Metric: mean incremental transport risk over the 552 directed pairs of the 24-build family
(single-source transport of the per-query min safe action, evaluated on the target; mean
over all 24 targets as the registered family summary), h=10 event, hnswlib and clean Faiss.
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA500 = Path("/home/wlk/data500")
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "results" / "graph_anns_phase2_p4"
OUT.mkdir(parents=True, exist_ok=True)
H = 10


def load_hnswlib(dataset):
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
        builds[bdir.name] = df.pivot(index="query_id", columns="ef_search", values="hits")
    return builds


def load_faiss(dataset):
    builds, raw_dir = {}, DATA500 / "graph_anns_iclr_phase1_1_repair_scratch" / "faiss_100k" / "raw"
    for f in sorted(raw_dir.glob(f"{dataset}__100k__clean*.csv.gz")):
        with gzip.open(f, "rt") as fh:
            df = pd.read_csv(fh)
        builds[df["build_id"].iloc[0]] = df.pivot(index="query_id", columns="ef", values="hit_count")
    return builds


def family_risk(builds, grid, H=10):
    """Mean single-source transport risk over all 24 targets on the given grid."""
    B, hit_tables, ef_maps = {}, {}, {}
    for name, hit in builds.items():
        cols = [c for c in grid if c in hit.columns]
        h = hit[cols].values
        ok = h >= H
        first = np.where(ok.any(axis=1), np.array(cols)[np.argmax(ok, axis=1)], -1)
        B[name] = first
        hit_tables[name] = h
        ef_maps[name] = np.array(cols)
    names = sorted(B)
    n = len(names)
    total = 0.0
    for ti, t in enumerate(names):
        tgt_hits, tgt_ef = hit_tables[t], ef_maps[t]
        for si in range(n):
            if si == ti:
                continue
            a = B[names[si]]
            deploy = np.where(a < 0, tgt_ef[-1], a)
            j = np.clip(np.searchsorted(tgt_ef, deploy), 0, len(tgt_ef) - 1)
            z = tgt_hits[np.arange(len(a)), j] < H
            total += z.mean()
    return total / (n * (n - 1))


def main():
    specs = [
        ("hnswlib", "sift_100k", load_hnswlib, [10, 20, 40, 80, 120, 200]),
        ("hnswlib", "arxiv_nomic_100k", load_hnswlib, [10, 20, 40, 80, 120, 200]),
        ("faiss", "sift_100k", load_faiss, [16, 32, 64, 128, 256, 512]),
        ("faiss", "arxiv_nomic_100k", load_faiss, [16, 32, 64, 128, 256, 512]),
    ]
    rows = []
    for impl, ds, loader, grid in specs:
        builds = loader(ds)
        variants = {
            "FULL": grid,
            "DROP_MIN": grid[1:],
            "DROP_MAX": grid[:-1],
            "COARSE": grid[::2],
        }
        for vname, g in variants.items():
            r = family_risk(builds, g)
            rows.append({"implementation": impl, "dataset": ds, "grid_variant": vname,
                         "grid": "|".join(map(str, g)), "mean_family_transport_risk": r,
                         "n_actions": len(g)})
            print(rows[-1])
    pd.DataFrame(rows).to_csv(OUT / "grid_sensitivity.csv", index=False)
    piv = rows and pd.DataFrame(rows).pivot_table(index=["implementation", "dataset"],
                                                  columns="grid_variant",
                                                  values="mean_family_transport_risk")
    piv["max_rel_shift_vs_full"] = (piv.drop(columns=["FULL"]).sub(piv["FULL"], axis=0)
                                    .abs().div(piv["FULL"], axis=0)).max(axis=1)
    piv.reset_index().to_csv(OUT / "grid_sensitivity_summary.csv", index=False)
    (OUT / "grid_sensitivity_summary.json").write_text(piv.to_json(indent=1))
    print(piv)


if __name__ == "__main__":
    main()
