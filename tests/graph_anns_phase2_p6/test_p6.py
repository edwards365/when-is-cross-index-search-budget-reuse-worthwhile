"""P6 deterministic checks. Run after sift1m pipeline completes:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib .venv/bin/python tests/graph_anns_phase2_p6/test_p6.py
"""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p6"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

# ---- preregistration integrity
pre = json.loads((OUT / "preregistration.json").read_text())
check("prereg_grid", pre["action_grid"]["ef_search"] == [10, 20, 40, 80, 120, 200])
check("prereg_eval_n", pre["query_roles"]["evaluation_n"] == 500)

# ---- 1M cell
summ = json.loads((OUT / "sift1m_summary.json").read_text())
check("forensics_zero", summ["forensics_query_base_raw_overlap"] == 0)
check("eight_builds", summ["builds"] == 8)
check("sanity_risk_band", 0.005 < summ["incremental_transport_risk"] < 0.45)
check("variation_positive", summ["finite_action_variation"] > 0.10)
check("endpoint_much_smaller", summ["endpoint_variation"] < 0.2 * summ["finite_action_variation"] + 0.05)
check("ci_orders_risk", summ["bootstrap_ci"][0] < summ["incremental_transport_risk"] < summ["bootstrap_ci"][1])
check("pooling_monotone",
      all(a["mean_risk"] >= b["mean_risk"] - 1e-9 for a, b in
          zip(summ["pooling"], summ["pooling"][1:])))
check("pooling_1m_k7_insufficient_scale_boundary",
      0.08 < summ["pooling"][-1]["mean_risk"] < 0.13,
      )  # 1M finding: 7 pooled sources still leave >8% risk (vs 0.96% at 100K w/ 22 sources)
check("identity_check_equal", summ["identity_byte_identical"] is True)

# ---- predictor probe (B)
ps = pd.read_csv(OUT / "predictor_probe_summary.csv").set_index("dataset")
check("B_transfer_not_better_than_naive",
      (ps["transfer_risk"] >= ps["naive_risk"] - 0.01).all())
check("B_intarget_still_poor", (ps["intarget_cv_risk"] > 0.10).all())

# ---- distinguishability (C)
ds = json.loads((OUT / "distinguishability_summary.json").read_text())
for k, v in ds.items():
    check(f"C_{k}_chance_accuracy", v["acc_k6_median"] < 0.55)
    check(f"C_{k}_tv_bounded", v["tv_plugin_k6_max"] < 0.5)

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
