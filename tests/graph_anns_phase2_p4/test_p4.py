"""P4 deterministic checks. Run:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib .venv/bin/python tests/graph_anns_phase2_p4/test_p4.py
"""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p4"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

em = pd.read_csv(OUT / "economics_matrix.csv")
check("36_cells_6x6", len(em) == 36)
meas = em[em.status == "MEASURED"]
check("8_measured_cells", len(meas) == 8)
check("sift_breakeven_no_finite_labeled",
      ((em.dataset == "sift_100k") & (em.component.str.startswith("breakeven")) &
       (em.status == "NO_FINITE_BREAK_EVEN_WORKLOAD")).sum() == 2)
check("vamana_all_not_estimable",
      (em[(em.implementation == "vamana") & (em.component != "build_time_d3_median_s")]["status"]
       == "COST_ONLY_QUERY_REPLAY_INTERFACE_NOT_AVAILABLE").all())

gs = pd.read_csv(OUT / "grid_sensitivity.csv")
full = gs[gs.grid_variant == "FULL"].set_index(["implementation", "dataset"])["mean_family_transport_risk"]
check("full_grid_reproduces_frozen_absolute_risk",
      abs(full[("hnswlib", "sift_100k")] - 0.2237342995) < 1e-6 and
      abs(full[("hnswlib", "arxiv_nomic_100k")] - 0.1837608696) < 1e-6 and
      abs(full[("faiss", "sift_100k")] - 0.2367149758) < 1e-6 and
      abs(full[("faiss", "arxiv_nomic_100k")] - 0.1793236715) < 1e-6)
summ = pd.read_csv(OUT / "grid_sensitivity_summary.csv")
check("phenomenon_robust_all_variants_above_2pct",
      (summ[["COARSE", "DROP_MIN", "DROP_MAX"]].values > 0.02).all())

man = json.loads((OUT / "decision_manifest.json").read_text())
check("manifest_label", man["final_label"] ==
      "P4_ECONOMICS_LEDGER_COMPLETE_GRID_SENSITIVITY_ROBUST")

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
