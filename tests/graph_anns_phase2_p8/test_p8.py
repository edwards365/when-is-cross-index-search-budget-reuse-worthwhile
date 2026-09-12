"""P8 checks."""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "graph_anns_phase2_p8"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

h = pd.read_csv(OUT / "h_sensitivity.csv")
check("h8_all_above_2pct", (h[h.h == 8]["family_transport_risk"] > 0.02).all())
check("h_monotone_in_h",
      all(g.sort_values("h")["family_transport_risk"].is_monotonic_increasing
          for _, g in h.groupby(["cell", "dataset"])))

g = pd.read_csv(OUT / "gamma_sensitivity.csv")
s = g[g.dataset == "sift_100k"].set_index("gamma")
a = g[g.dataset == "arxiv_nomic_100k"].set_index("gamma")
check("gamma_0.005_sift_16", s.loc[0.005, "targets_with_margin_passing_nonmax_action"] == 16)
check("gamma_0.005_arxiv_21", a.loc[0.005, "targets_with_margin_passing_nonmax_action"] == 21)
check("gamma_0.02_zero", (g[g.gamma == 0.02]["targets_with_margin_passing_nonmax_action"] == 0).all())

r = json.loads((OUT / "rich_probe_summary.json").read_text())
check("hits_chance", all(r[d]["F1_median"] < 0.52 for d in r))
check("runtime_weak_moderate",
      all(0.55 < r[d]["F2_median"] < 0.60 for d in r))
check("runtime_max_bounded", all(r[d]["F2_max"] < 0.75 for d in r))

q = pd.read_csv(OUT / "quantile_pooling.csv")
k22 = q[(q.k == 22) & (q.dataset == "sift_100k")].set_index("quantile")
check("q09_close_to_max", abs(k22.loc[0.9, "mean_risk"] - k22.loc[1.0, "mean_risk"]) < 0.005)
check("median_unusable", k22.loc[0.5, "mean_risk"] > 0.10)
check("max_matches_P2", abs(k22.loc[1.0, "mean_risk"] - 0.0096) < 0.003)

m = json.loads((OUT / "decision_manifest.json").read_text())
check("manifest_label", m["final_label"] == "P8_REBUTTAL_EVIDENCE_COMPLETE_H_GAMMA_PROBE_POOLING")

failed = [n for n, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
