#!/usr/bin/env python
"""P4: full six-cell economics matrix from frozen artifacts, with per-component status.

Status semantics (paper-facing):
  MEASURED      numeric value exists in a frozen artifact for this cell
  DERIVED       deterministic function of frozen numbers (e.g. ratios)
  SYMBOLIC_ONLY break-even formula defined but denominator/numerator not fully estimable
  NOT_ESTIMABLE the frozen evidence cannot produce this number for this cell
"""
import csv
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RES = REPO / "results"
OUT = RES / "graph_anns_phase2_p4"
OUT.mkdir(parents=True, exist_ok=True)

prof = pd.read_csv(RES / "graph_anns_iclr_phase1/paper_table_P4_profiling_cost.csv")
be = pd.read_csv(RES / "graph_anns_iclr_phase1/paper_table_P6_break_even.csv")
d3 = pd.read_csv(RES / "graph_anns_iclr_phase1_1/deterministic_semantic_reanalysis.csv")
vam = pd.read_csv(RES / "graph_anns_cross_family/main_effect_table.csv")

CELLS = [
    ("hnswlib", "sift_100k"), ("hnswlib", "arxiv_nomic_100k"),
    ("faiss", "sift_100k"), ("faiss", "arxiv_nomic_100k"),
    ("vamana", "sift_100k"), ("vamana", "arxiv_nomic_100k"),
]

rows = []
for impl, ds in CELLS:
    r = {"implementation": impl, "dataset": ds}
    # build cost (deterministic contract tier, median, from frozen D3 rows)
    if impl == "hnswlib":
        d = d3[(d3.dataset == ds) & (d3.regime == "D3")]
        r["build_time_d3_median_s"] = (float(d["build_time_median_seconds"].iloc[0]), "MEASURED")
        # profiling: hnswlib rows in P4
        p = prof[(prof.implementation == "hnswlib") & (prof.dataset == ds) &
                 (prof.threads.astype(str) == "8") & (prof.n == 59)]
        r["profiling_resident_59q_8t_s"] = (float(p["profiling_total_resident_seconds"].iloc[0]), "MEASURED")
        # break-even: hnswlib rows in P6
        b = be[(be.implementation == "hnswlib") & (be.dataset == ds) &
               (be.threads.astype(str) == "8") & (be.n == 59)]
        def _be(col):
            v = b[col].iloc[0]
            try:
                return (float(v), "MEASURED")
            except (ValueError, TypeError):
                return (v, "NO_FINITE_BREAK_EVEN_WORKLOAD")
        r["breakeven_search_only_q"] = _be("search_only_break_even_queries")
        r["breakeven_wall_clock_q"] = _be("wall_clock_break_even_queries")
        r["candidate_family_replay"] = ("NOT_ESTIMABLE", "NOT_ESTIMABLE_NO_TARGET_CERTIFIED_ACTION_LEDGER")
        r["certification_control"] = ("NOT_ESTIMABLE", "NOT_ESTIMABLE_NO_TARGET_CERTIFIED_ACTION_LEDGER")
    elif impl == "faiss":
        p = prof[(prof.implementation == "faiss") & (prof.dataset == ds) &
                 (prof.threads.astype(str) == "8") & (prof.n == 59)]
        r["build_time_d3_median_s"] = ("NOT_ESTIMABLE", "NO_FAISS_DETERMINISTIC_TIER_REGISTERED")
        r["profiling_resident_59q_8t_s"] = (float(p["profiling_total_resident_seconds"].iloc[0]), "MEASURED")
        r["breakeven_search_only_q"] = ("NOT_ESTIMABLE", "TARGET_CERTIFIED_ACTION_LEDGER_ABSENT")
        r["breakeven_wall_clock_q"] = ("NOT_ESTIMABLE", "TARGET_CERTIFIED_ACTION_LEDGER_ABSENT")
        r["candidate_family_replay"] = ("NOT_ESTIMABLE", "NOT_ESTIMABLE_NO_TARGET_CERTIFIED_ACTION_LEDGER")
        r["certification_control"] = ("NOT_ESTIMABLE", "NOT_ESTIMABLE_NO_TARGET_CERTIFIED_ACTION_LEDGER")
    else:  # vamana
        v = vam[(vam.implementation == "DiskANN3 Vamana-style") &
                (vam.dataset == ("SIFT-100K" if ds == "sift_100k" else "Arxiv-Nomic-100K"))]
        r["build_time_d3_median_s"] = ("NOT_ESTIMABLE", "NO_VAMANA_CONTRACT_TIER_REGISTERED")
        r["profiling_resident_59q_8t_s"] = ("NOT_ESTIMABLE", "COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE")
        r["breakeven_search_only_q"] = ("NOT_ESTIMABLE", "COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE")
        r["breakeven_wall_clock_q"] = ("NOT_ESTIMABLE", "COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE")
        r["candidate_family_replay"] = ("NOT_ESTIMABLE", "COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE")
        r["certification_control"] = ("NOT_ESTIMABLE", "COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE")
    rows.append(r)

flat = []
for r in rows:
    base = {"implementation": r["implementation"], "dataset": r["dataset"]}
    for k, v in r.items():
        if k in ("implementation", "dataset"):
            continue
        val, status = v
        flat.append({**base, "component": k, "value": val, "status": status})
with open(OUT / "economics_matrix.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["implementation", "dataset", "component", "value", "status"])
    w.writeheader()
    w.writerows(flat)

summary = {}
for row in flat:
    summary[row["status"]] = summary.get(row["status"], 0) + 1
(OUT / "economics_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
meas = [x for x in flat if x["status"] == "MEASURED"]
print(f"measured cells: {len(meas)}")
for x in meas:
    print(f"  {x['implementation']:8s} {x['dataset']:18s} {x['component']:32s} = {x['value']}")
