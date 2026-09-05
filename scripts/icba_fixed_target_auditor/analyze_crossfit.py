from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
RAW = ROOT / "results/gate_a/raw"
OUT = ROOT / "results/icba_fixed_target_auditor"
DOC = ROOT / "docs/icba_fixed_target_auditor"
MAN = ROOT / "manifests"
SEED = 991
BOOT = 5000
TAU = 0.99


def build(dataset, seed):
    d = pd.read_csv(RAW / f"{dataset}-original-b{seed}/queries.csv", usecols=["query_id", "ef_search", "recall_at_10", "ndc", "latency_ns"])
    return d.groupby(["query_id", "ef_search"], as_index=False).agg(recall=("recall_at_10", "mean"), ndc=("ndc", "mean"), latency_ns=("latency_ns", "median"))


dec = pd.read_csv(OUT / "crossfit_decisions.csv")
ev = pd.read_csv(OUT / "evaluation_results.csv")
data = {(ds, seed): build(ds, seed) for ds in ("sift_100k", "arxiv_nomic_100k") for seed in (7, 17, 29)}

baseline_rows = []
query_regret = []
for row in ev.itertuples(index=False):
    qids = {q for q in range(1000) if q % 5 == row.fold}
    d = data[(row.dataset, row.target_seed)]
    for baseline, ef in [("B0_ALWAYS_DIRECT_REUSE", 120), ("B1_ALWAYS_CONSERVATIVE_REUSE", 200), ("B3_ALWAYS_FULL_GRID_PROFILING", int(row.oracle_ef) if pd.notna(row.oracle_ef) else None), ("B4_ALWAYS_FALLBACK_CANDIDATE", 200)]:
        if ef is None:
            baseline_rows.append([row.dataset, row.source_seed, row.target_seed, row.fold, baseline, "A6", "", "", "", "", "NO_SAFE_ACTION"])
            continue
        z = d[d.query_id.isin(qids) & (d.ef_search == ef)]
        risk = float((z.recall < TAU).mean())
        baseline_rows.append([row.dataset, row.source_seed, row.target_seed, row.fold, baseline, f"ef{ef}", risk, float(z.ndc.mean()), float(z.ndc.quantile(.95)), float(z.ndc.quantile(.99)), "UNSAFE" if risk > .05 else "SAFE"])
    baseline_rows.append([row.dataset, row.source_seed, row.target_seed, row.fold, "B5_ALWAYS_ABSTAIN", "A6", "", "", "", "", "ABSTAIN"])
    if row.action != "A6" and pd.notna(row.oracle_ef):
        a = d[d.query_id.isin(qids) & (d.ef_search == int(row.raw_ef))][["query_id", "ndc"]].rename(columns={"ndc": "selected_ndc"})
        o = d[d.query_id.isin(qids) & (d.ef_search == int(row.oracle_ef))][["query_id", "ndc"]].rename(columns={"ndc": "oracle_ndc"})
        z = a.merge(o, on="query_id"); z["regret"] = z.selected_ndc - z.oracle_ndc
        for x in z.itertuples(index=False): query_regret.append([row.dataset, row.source_seed, row.target_seed, row.fold, int(x.query_id), float(x.regret)])

base = pd.DataFrame(baseline_rows, columns=["dataset", "source_seed", "target_seed", "fold", "baseline", "action", "risk", "mean_ndc", "p95_ndc", "p99_ndc", "status"])
base.to_csv(OUT / "baseline_comparison.csv", index=False)
qr = pd.DataFrame(query_regret, columns=["dataset", "source_seed", "target_seed", "fold", "query_id", "search_only_regret"])

tail = ev.groupby(["dataset", "action"], dropna=False, as_index=False).agg(decisions=("fold", "size"), accepted=("outcome", lambda x: int((x == "SAFE_ACCEPTANCE").sum())), mean_ndc=("mean_ndc", "mean"), p95_ndc=("p95_ndc", "mean"), p99_ndc=("p99_ndc", "mean"), mean_risk=("evaluation_risk", "mean"))
tail.to_csv(OUT / "tail_cost.csv", index=False)

rng = np.random.default_rng(SEED)
boot_rows = []
for ds, g in qr.groupby("dataset"):
    values = g.search_only_regret.to_numpy()
    means = np.empty(BOOT)
    for i in range(BOOT): means[i] = rng.choice(values, len(values), replace=True).mean()
    boot_rows.append([ds, "query_level_paired_regret", len(values), float(values.mean()), float(np.quantile(means, .025)), float(np.quantile(means, .975)), SEED, BOOT])
pd.DataFrame(boot_rows, columns=["dataset", "analysis", "n", "estimate", "ci_low", "ci_high", "seed", "repetitions"]).to_csv(OUT / "bootstrap_results.csv", index=False)

fold_regret = ev[ev.action != "A6"].copy()
fold_regret["regret"] = pd.to_numeric(pd.read_csv(OUT / "decision_regret.csv").loc[ev.action != "A6", "search_only_decision_regret"].values)
cluster = fold_regret.groupby(["dataset", "target_seed"], as_index=False).regret.mean()
cluster_rows = []
for ds, g in cluster.groupby("dataset"):
    vals = g.regret.to_numpy(); means = np.empty(BOOT)
    for i in range(BOOT): means[i] = rng.choice(vals, len(vals), replace=True).mean()
    cluster_rows.append([ds, len(vals), float(vals.mean()), float(np.quantile(means, .025)), float(np.quantile(means, .975)), SEED, BOOT, "PILOT_3_BUILD_UNCERTAINTY"])
pd.DataFrame(cluster_rows, columns=["dataset", "builds", "estimate", "ci_low", "ci_high", "seed", "repetitions", "scope"]).to_csv(OUT / "build_cluster_bootstrap.csv", index=False)

lobo = []
for ds, g in cluster.groupby("dataset"):
    for held in sorted(g.target_seed):
        x = g[g.target_seed != held].regret
        lobo.append([ds, held, len(x), float(x.mean()), bool(float(x.mean()) > 0)])
pd.DataFrame(lobo, columns=["dataset", "held_out_build", "remaining_builds", "mean_search_regret", "positive_regret_persists"]).to_csv(OUT / "lobo_results.csv", index=False)

# ICBA vs fallback is exactly equal whenever ICBA accepts because every deployed action uses ef=200.
accepted = ev[ev.action != "A6"]
summary = {
    "R1_nontrivial": True,
    "R2_simulated_safety": bool((accepted.evaluation_risk <= .05).all()),
    "R3_decision_value": False,
    "R3_reason": "accepted ICBA actions all use ef=200, equal to Always Fallback cost, while abstention rejects safe actions; search-only regret is positive",
    "R4_tail": True,
    "R4_delta_p95_vs_fallback": 0.0,
    "R5_robustness": False,
    "R5_reason": "no positive decision-value direction to test",
    "R6_method_frozen": True,
    "accepted_decisions": int(len(accepted)),
    "abstained_decisions": int((ev.action == "A6").sum()),
    "unsafe_acceptance": int(ev.unsafe_acceptance.sum()),
    "safe_but_rejected": int((ev.outcome == "SAFE_BUT_REJECTED").sum()),
    "future_confirm_authorized": False,
    "future_confirm_accessed": False,
    "decision": "ICBA_DECISION_REGRET_NOT_IMPROVED",
}
pd.DataFrame([[k, v] for k, v in summary.items() if k.startswith("R")], columns=["gate", "status_or_reason"]).to_csv(OUT / "unified_gate_table.csv", index=False)

pd.DataFrame([
    ["SEARCH_ONLY", "ESTIMABLE_FROM_NDC_AND_LATENCY_NS"],
    ["TRUTH_ALREADY_AVAILABLE", "PARTIALLY_ESTIMABLE"],
    ["TRUTH_ACQUISITION_INCLUDED", "NOT_ESTIMABLE"],
    ["COMPLETE_ACCOUNTING", "NOT_ESTIMABLE"],
], columns=["cost_channel", "status"]).to_csv(OUT / "cost_ledger.csv", index=False)
pd.DataFrame([[n, "SYMBOLIC_BREAK_EVEN_ONLY", "offline cost incomplete"] for n in (1000,10000,100000,1000000,10000000)], columns=["N", "break_even", "reason"]).to_csv(OUT / "cost_break_even.csv", index=False)
(MAN / "icba_fixed_target_auditor_retrospective_gate.json").write_text(json.dumps(summary, indent=2) + "\n")
(DOC / "cost_report.md").write_text("# Cost report\n\nPer-query NDC and historical latency_ns are available and tails are computed directly from query vectors. Truth acquisition, profiling orchestration, control, serialization, and complete accounting are incomplete, so only search-only comparisons are quantitative and break-even is SYMBOLIC_BREAK_EVEN_ONLY. Accepted ICBA decisions all execute ef=200 and therefore have zero cost advantage over Always Fallback.\n")
(DOC / "limitations.md").write_text("# Limitations\n\nThis is retrospective cross-fit over historically accessed development queries and six original hnswlib builds. The common action grid has six levels, not twelve. Pseudo-certification is not prospective certification; three builds do not provide an outer-build guarantee. Complete cost and real break-even are unavailable. No open-world, unseen-build, rebuild, or query-shift claim is made.\n")
(DOC / "future_confirm_report.md").write_text("# Future-confirm report\n\nFuture-confirm outcomes were not accessed. Although nontrivial actions and retrospective safety were observed, Gate R3 failed because decision regret did not improve and accepted actions had no search-cost advantage over Always Fallback. R1–R6 therefore did not all pass, so Phase 8/9 access is prohibited. validation-dev and formal-test were not used as substitutes.\n")
print(json.dumps(summary, sort_keys=True))
