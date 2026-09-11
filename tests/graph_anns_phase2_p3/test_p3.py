"""P3 deterministic checks. Run:
LD_LIBRARY_PATH=/home/wlk/miniconda3/lib .venv/bin/python tests/graph_anns_phase2_p3/test_p3.py
"""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p3"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

ab = pd.read_csv(OUT / "contract_ablation.csv")
check("8_rows", len(ab) == 8)
d3 = ab[ab.regime == "D3"]
check("D3_zero_variation", (d3["min_safe_action_variation"] == 0).all())
check("D3_byte_identical", (d3["byte_identical_within_tier"].astype(str) == "True").all())
d2 = ab[ab.regime == "D2"]
check("D2_not_byte_identical_key_finding", (d2["byte_identical_within_tier"].astype(str) == "False").all())
check("D2_variation_persists", (d2["min_safe_action_variation"] > 0.25).all())

me = pd.read_csv(OUT / "chain_marginal_effects.csv")
for ds in ("sift_100k", "arxiv_nomic_100k"):
    g = me[me.dataset == ds].set_index("chain_step")
    check(f"{ds}_order_halves_variation",
          abs(g.loc["order_pinning_D0C_to_D1", "variation_change"]) > 0.30)
    check(f"{ds}_seed_negligible",
          abs(g.loc["seed_pinning_D1_to_D2", "variation_change"]) < 0.05)
    check(f"{ds}_threads_kill_variation",
          abs(g.loc["single_threading_D2_to_D3", "variation_change"]) > 0.25)
    check(f"{ds}_order_pinning_not_slower",
          g.loc["order_pinning_D0C_to_D1", "build_time_ratio_vs_prev"] < 1.0)
    check(f"{ds}_single_thread_costs",
          g.loc["single_threading_D2_to_D3", "build_time_ratio_vs_prev"] > 1.5)

man = json.loads((OUT / "decision_manifest.json").read_text())
check("manifest_label", man["final_label"] ==
      "P3_CONTRACT_ABLATION_ORDER_CHEAP_THREADS_LOAD_BEARING_SEED_MINOR")

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
