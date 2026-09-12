"""P11 checks: A-series + B-series verdicts."""
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT11 = REPO / "results/graph_anns_phase2_p11"
checks = []
def check(name, cond):
    checks.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}")

pm = pd.read_csv(OUT11 / "probe_matrix_pairs.csv")
check("probe_exhaustion_stack_near_chance", pm["acc_F4"].median() < 0.60)
check("curve_family_chance_for_attribution", pm["acc_F3"].median() < 0.52)
fm = pd.read_csv(OUT11 / "probe_matrix_families.csv")
r2 = fm.dropna(subset=["transfer_r2_target0"])
check("curve_r2_high_but_truthlocked",
      ((r2[r2.family == "F3"]["transfer_r2_target0"] > 0.99).all()))
check("runtime_r2_low", ((r2[r2.family == "F2"]["transfer_r2_target0"] < 0.05).all()))

q = pd.read_csv(OUT11 / "m2_coverage_rho.csv")
m = q.groupby(["dataset", "rho"])["effective_risk"].mean().unstack()
check("rho_monotone_down", all(m.loc[d].is_monotonic_decreasing for d in m.index))
check("rho0_below_delta", (m[0.0] < 0.05).all())

b = pd.read_csv(OUT11 / "build_population_bound.csv")
check("population_bound_trivially_1", (b["hoeffding_p_newbuild_above_gate_ub95"] == 1.0).all())

n = pd.read_csv(OUT11 / "no_truth_rule.csv")
s = n[(n.rule == "visited_saturation") & (pd.to_numeric(n.theta, errors="coerce") <= 1.10)]
check("no_truth_degenerates_to_max", (s["chosen_mean_ef"] > 190).all())
check("no_truth_risk_near_max", (abs(s["realized_risk"] - 0.013) < 0.02).all())

h = pd.read_csv(OUT11 / "online_head_to_head.csv")
check("h2h_naive_fails", h["M1_naive_risk"].mean() > 0.20)
check("h2h_m5_safe", h["M5_risk"].mean() < 0.02)
check("h2h_m3_partial", (h["M3_cert_pass_prob"].between(0.3, 0.8)).all())
check("h2h_cold_cost_recorded",
      json.loads((OUT11 / "b1_cold_cost.json").read_text())["cold_graded_us"] > 1e6)

mm = json.loads((OUT11 / "a_series_manifest.json").read_text())
check("a_manifest", mm["final_label"] == "P11_AB_COMPLETE_THEOREM3_CERTIFIED_POOLING")


c = pd.read_csv(OUT11 / "conformal_pooling_validity.csv")
nonvac = c[(c.alpha * (c.k + 1) >= 1.0 - 1e-12) | (c["realized_failure_rate"] <= c["nominal_alpha"])]
cert = c[(c.alpha == 0.05) & (c.k == 23)]
check("thm3_validity_all_nonvacuous", (nonvac["realized_failure_rate"] <= nonvac["nominal_alpha"] + 1e-12).all())
check("thm3_cert_point_distcomp", cert["mean_distcomp"].between(1.2, 1.6).all())
check("thm3_cert_risk_under_gate", (cert["realized_failure_rate"] < 0.02).all())

failed = [x for x, ok in checks if not ok]
print(f"\n{len(checks)-len(failed)}/{len(checks)} checks passed")
if failed:
    raise SystemExit(1)
