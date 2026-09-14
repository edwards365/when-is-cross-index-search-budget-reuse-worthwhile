#!/usr/bin/env python3
"""Quantify preregistered ICBA audit-before-deploy value from sealed M1/M3 tables."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path("results/graph_anns_score8/darth_comparison")
CELLS = {
    "rebuild_0pct": ROOT / "m1_multibuild_summary.csv",
    "refresh_1pct": ROOT / "m3_refresh_01_summary.csv",
    "refresh_5pct": ROOT / "m3_refresh_05_summary.csv",
    "refresh_10pct": ROOT / "m3_refresh_10_summary.csv",
}

rows = []
for cell, path in CELLS.items():
    frame = pd.read_csv(path)
    if cell == "rebuild_0pct":
        pairs = [("DARTH_TARGET_TRAINED_RAW", "DARTH_AUDITED_DEPLOYED"),
                 ("TCP_RAW_MAX9", "TCP_AUDITED_DEPLOYED")]
    else:
        pairs = [("DARTH_OLD_MODEL_RAW", "DARTH_OLD_MODEL_AUDITED_DEPLOYED"),
                 ("DARTH_REFRESH_RETRAINED_RAW", "DARTH_REFRESH_RETRAINED_AUDITED_DEPLOYED"),
                 ("TCP_OLD_POOL_RAW", "TCP_OLD_POOL_AUDITED_DEPLOYED"),
                 ("TCP_REFRESHED_POOL_RAW", "TCP_REFRESHED_POOL_AUDITED_DEPLOYED")]
    fixed = frame[frame.method == "FIXED_CERTIFIED"].set_index("seed")
    for raw_name, deployed_name in pairs:
        raw = frame[frame.method == raw_name].set_index("seed")
        deployed = frame[frame.method == deployed_name].set_index("seed")
        common = sorted(set(raw.index) & set(deployed.index) & set(fixed.index))
        raw, deployed, base = raw.loc[common], deployed.loc[common], fixed.loc[common]
        accepted = raw["accepted"].astype(bool)
        unsafe = raw.eval_risk > .05
        rows.append({
            "cell": cell, "raw_policy": raw_name, "builds": len(common),
            "blind_deployed_builds": len(common),
            "raw_certified_builds": int(accepted.sum()),
            "raw_eval_unsafe_builds": int(unsafe.sum()),
            "unsafe_deployments_avoided_by_audit": int((unsafe & ~accepted).sum()),
            "audit_fallback_builds": int((~accepted).sum()),
            "certification_labels": 500 * len(common),
            "blind_mean_eval_risk": raw.eval_risk.mean(),
            "audited_mean_eval_risk": deployed.eval_risk.mean(),
            "blind_mean_dists": raw.mean_dists.mean(),
            "audited_mean_dists": deployed.mean_dists.mean(),
            "fixed_mean_dists": base.mean_dists.mean(),
            "audited_dists_reduction_vs_fixed_pct": 100*(base.mean_dists.mean()-deployed.mean_dists.mean())/base.mean_dists.mean(),
            "audited_p95_delta_vs_fixed": deployed.p95_dists.mean()-base.p95_dists.mean(),
        })

out = pd.DataFrame(rows)
out.to_csv(ROOT / "m4_audit_before_deploy_value.csv", index=False)
assert (out.audited_mean_eval_risk <= .05).all()
assert (out.unsafe_deployments_avoided_by_audit <= out.raw_eval_unsafe_builds).all()
decision = {
    "module": "M4_ICBA_AUDIT_BEFORE_DEPLOY",
    "safety_threshold": 0.05,
    "certification_queries_per_build": 500,
    "darth_strategy_build_decisions": int(out.raw_policy.str.startswith("DARTH").sum() * 10),
    "darth_unsafe_deployments_avoided": int(out.loc[out.raw_policy.str.startswith("DARTH"), "unsafe_deployments_avoided_by_audit"].sum()),
    "tcp_strategy_build_decisions": int(out.raw_policy.str.startswith("TCP").sum() * 10),
    "tcp_unsafe_deployments_observed": int(out.loc[out.raw_policy.str.startswith("TCP"), "raw_eval_unsafe_builds"].sum()),
    "tcp_best_audited_mean_reduction_pct_by_cell": {
        cell: float(group.audited_dists_reduction_vs_fixed_pct.max())
        for cell, group in out[out.raw_policy.str.startswith("TCP")].groupby("cell")
    },
    "interpretation": "Audit-before-deploy blocks unsafe DARTH use and conditionally preserves TCP efficiency; at 10% refresh TCP safely collapses to fixed-safe rather than claiming recovery.",
    "wall_clock_status": "DESCRIPTIVE_ONLY_NOT_PRIMARY",
    "formal_tcp_95pct_exchangeable_build_certificate": False,
    "safety_source": "INDEPENDENT_TARGET_QUERY_CERTIFICATION",
}
(ROOT / "m4_audit_before_deploy_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
print(out.to_csv(index=False))
