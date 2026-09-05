from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
RAW = ROOT / "results/gate_a/raw"
OUT = ROOT / "results/icba_fixed_target_auditor"
DOC = ROOT / "docs/icba_fixed_target_auditor"
MAN = ROOT / "manifests"
GRID = [10, 20, 40, 80, 120, 200]
TAU = 0.99
DELTA = 0.05
ALPHA_SHARE = 0.025
SEED = 991


def stable_hash(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def cp_upper(x: int, n: int, alpha: float = ALPHA_SHARE) -> float:
    return 1.0 if x == n else float(beta.ppf(1 - alpha, x + 1, n - x))


def load_build(dataset: str, seed: int) -> pd.DataFrame:
    path = RAW / f"{dataset}-original-b{seed}/queries.csv"
    d = pd.read_csv(path, usecols=["query_id", "ef_search", "recall_at_10", "ndc", "latency_ns"])
    d = d[d.ef_search.isin(GRID)]
    return d.groupby(["query_id", "ef_search"], as_index=False).agg(
        recall=("recall_at_10", "mean"), ndc=("ndc", "mean"), latency_ns=("latency_ns", "median")
    )


def choose_ef(data: pd.DataFrame, query_ids: set[int], efs: list[int]):
    z = data[data.query_id.isin(query_ids) & data.ef_search.isin(efs)]
    s = z.groupby("ef_search", as_index=False).agg(
        risk=("recall", lambda x: float((x < TAU).mean())), mean_ndc=("ndc", "mean")
    )
    safe = s[s.risk <= DELTA].sort_values(["mean_ndc", "ef_search"])
    return None if safe.empty else int(safe.iloc[0].ef_search)


policies = pd.read_csv(OUT / "source_policy_registry.csv")
build_data = {(ds, seed): load_build(ds, seed) for ds in ("sift_100k", "arxiv_nomic_100k") for seed in (7, 17, 29)}

# Historical role forensics and deterministic five-fold replay roles.
forensic = []
ledger = []
overlap = []
for ds in ("sift_100k", "arxiv_nomic_100k"):
    for qid in range(1000):
        forensic.append([ds, qid, "development", "RETROSPECTIVE_CROSSFIT_ONLY", "historically accessed by Gate-A"])
    for fold in range(5):
        evaluation = {q for q in range(1000) if q % 5 == fold}
        pseudo_cert = {q for q in range(1000) if q % 5 == (fold + 1) % 5}
        selection = set(range(1000)) - evaluation - pseudo_cert
        roles = {"selection": selection, "pseudo_certification": pseudo_cert, "evaluation": evaluation}
        for role, ids in roles.items():
            ledger.append([ds, fold, role, len(ids), stable_hash(sorted(ids)), "RETROSPECTIVE_CROSSFIT_ONLY"])
        for a, ai in roles.items():
            for b, bi in roles.items(): overlap.append([ds, fold, a, b, len(ai & bi)])

pd.DataFrame(forensic, columns=["dataset", "query_id", "manifest_role", "forensic_role", "reason"]).to_csv(OUT / "query_role_forensics.csv", index=False)
pd.DataFrame(ledger, columns=["dataset", "fold", "role", "n", "query_ids_hash", "evidence_scope"]).to_csv(OUT / "query_access_ledger.csv", index=False)
pd.DataFrame(overlap, columns=["dataset", "fold", "role_a", "role_b", "overlap"]).to_csv(OUT / "query_overlap_matrix.csv", index=False)

# Endpoint audit on all original builds using only the registered common finite grid.
endpoint_rows = []
endpoint_summary = []
for (ds, seed), d in build_data.items():
    counts = {"SAFE_ENDPOINT": 0, "RIGHT_CENSORED": 0}
    for qid, q in d.groupby("query_id"):
        safe = q[q.recall >= TAU].sort_values("ef_search")
        if safe.empty:
            status, budget = "RIGHT_CENSORED", ""
        else:
            status, budget = "SAFE_ENDPOINT", int(safe.iloc[0].ef_search)
        counts[status] += 1
        endpoint_rows.append([ds, f"{ds}-original-b{seed}", int(qid), budget, status, int(status == "RIGHT_CENSORED")])
    endpoint_summary.append([ds, f"{ds}-original-b{seed}", counts["SAFE_ENDPOINT"], counts["RIGHT_CENSORED"], counts["RIGHT_CENSORED"] / 1000])
with gzip.open(OUT / "endpoint_query_level.csv.gz", "wt", newline="") as handle:
    w = csv.writer(handle); w.writerow(["dataset", "build", "query_id", "B_G", "endpoint_status", "right_censored"]); w.writerows(endpoint_rows)
pd.DataFrame(endpoint_summary, columns=["dataset", "build", "safe_endpoint_queries", "right_censored_queries", "right_censored_rate"]).to_csv(OUT / "endpoint_build_summary.csv", index=False)

action_registry = pd.DataFrame([
    ["A0", "DIRECT_REUSE_SOURCE_EF", "FROZEN"], ["A1", "CONSERVATIVE_REUSE_ONE_RUNG_UP", "FROZEN"],
    ["A2", "TARGET_NEIGHBORHOOD_RECALIBRATION", "FROZEN"], ["A3", "TARGET_FULL_GRID_PROFILING", "FROZEN"],
    ["A4", "TARGET_RETRAIN", "NOT_IMPLEMENTED"], ["A5", "PREDECLARED_FALLBACK_CANDIDATE", "FROZEN_NOT_SAFE_UNTIL_CERTIFIED"],
    ["A6", "ABSTAIN_NO_SAFE_ACTION", "FROZEN"],
], columns=["action_id", "action", "status"])
action_registry["action_hash"] = [stable_hash(x) for x in action_registry.to_dict("records")]
action_registry.to_csv(OUT / "action_registry.csv", index=False)

fallback_registry = pd.DataFrame([[ds, f"{ds}-original-b{seed}", 200, "FALLBACK_CANDIDATE", ALPHA_SHARE] for ds in ("sift_100k", "arxiv_nomic_100k") for seed in (7, 17, 29)], columns=["dataset", "target_build", "raw_ef", "status_before_certification", "alpha_share"])
fallback_registry.to_csv(OUT / "fallback_candidate_registry.csv", index=False)

decision_rows = []
cert_rows = []
eval_rows = []
regret_rows = []
cost_rows = []
for ds in ("sift_100k", "arxiv_nomic_100k"):
    for source_seed in (7, 17, 29):
        source_ef = int(policies[(policies.dataset == ds) & (policies.source_build.str.endswith(f"b{source_seed}"))].iloc[0].raw_ef)
        for target_seed in (7, 17, 29):
            if source_seed == target_seed:
                continue
            target = build_data[(ds, target_seed)]
            for fold in range(5):
                eval_ids = {q for q in range(1000) if q % 5 == fold}
                cert_ids = {q for q in range(1000) if q % 5 == (fold + 1) % 5}
                select_ids = set(range(1000)) - eval_ids - cert_ids
                a2_ef = choose_ef(target, select_ids, [80, 120, 200])
                a3_ef = choose_ef(target, select_ids, GRID)
                candidates = [("A0", source_ef), ("A1", 200), ("A2", a2_ef), ("A3", a3_ef)]
                scored = []
                for aid, ef in candidates:
                    if ef is None: continue
                    q = target[target.query_id.isin(select_ids) & (target.ef_search == ef)]
                    risk = float((q.recall < TAU).mean())
                    if risk <= DELTA: scored.append((float(q.ndc.mean()), aid, ef, risk))
                if not scored:
                    selected_aid, selected_ef = "A6", None
                else:
                    _, selected_aid, selected_ef, _ = sorted(scored)[0]
                action_hash = stable_hash({"dataset": ds, "source": source_seed, "target": target_seed, "fold": fold, "action": selected_aid, "ef": selected_ef})
                fallback_ef = 200
                def certify(ef):
                    q = target[target.query_id.isin(cert_ids) & (target.ef_search == ef)]
                    failures = int((q.recall < TAU).sum()); n = len(q); ucb = cp_upper(failures, n)
                    return failures, n, ucb, ucb <= DELTA
                if selected_ef is None:
                    sf, sn, su, spass = "", 0, "", False
                else:
                    sf, sn, su, spass = certify(selected_ef)
                ff, fn, fu, fpass = certify(fallback_ef)
                if spass:
                    deployed, deployed_ef = selected_aid, selected_ef
                elif fpass:
                    deployed, deployed_ef = "A5", fallback_ef
                else:
                    deployed, deployed_ef = "A6", None
                cert_rows += [[ds, source_seed, target_seed, fold, "selected", selected_aid, selected_ef, sf, sn, su, spass, ALPHA_SHARE, action_hash], [ds, source_seed, target_seed, fold, "fallback", "A5", fallback_ef, ff, fn, fu, fpass, ALPHA_SHARE, stable_hash({"target": target_seed, "ef": fallback_ef})]]
                eq = target[target.query_id.isin(eval_ids)]
                oracle_stats = []
                for ef in GRID:
                    z = eq[eq.ef_search == ef]
                    r = float((z.recall < TAU).mean())
                    if r <= DELTA: oracle_stats.append((float(z.ndc.mean()), ef, r))
                oracle = None if not oracle_stats else sorted(oracle_stats)[0]
                if deployed_ef is None:
                    eval_risk = ""; mean_ndc = p95 = p99 = ""; unsafe = False
                    outcome = "CORRECT_ABSTENTION" if oracle is None else "SAFE_BUT_REJECTED"
                    search_regret = "NOT_ESTIMABLE_ABSTENTION"
                else:
                    z = eq[eq.ef_search == deployed_ef]
                    eval_risk = float((z.recall < TAU).mean()); mean_ndc = float(z.ndc.mean()); p95 = float(z.ndc.quantile(.95)); p99 = float(z.ndc.quantile(.99)); unsafe = eval_risk > DELTA
                    outcome = "UNSAFE_ACCEPTANCE" if unsafe else "SAFE_ACCEPTANCE"
                    search_regret = "SAFETY_FAILURE" if unsafe else ("NOT_ESTIMABLE_NO_SAFE_ORACLE" if oracle is None else mean_ndc - oracle[0])
                    for row in z.itertuples(index=False): cost_rows.append([ds, source_seed, target_seed, fold, int(row.query_id), deployed, deployed_ef, float(row.ndc), float(row.latency_ns)])
                decision_rows.append([ds, source_seed, target_seed, fold, selected_aid, selected_ef, deployed, deployed_ef, outcome, action_hash])
                eval_rows.append([ds, source_seed, target_seed, fold, deployed, deployed_ef, eval_risk, mean_ndc, p95, p99, unsafe, outcome, None if oracle is None else oracle[1]])
                regret_rows.append([ds, source_seed, target_seed, fold, deployed, search_regret, "NOT_ESTIMABLE"])

pd.DataFrame(decision_rows, columns=["dataset", "source_seed", "target_seed", "fold", "selected_action", "selected_ef", "deployed_action", "deployed_ef", "evaluation_outcome", "frozen_action_hash"]).to_csv(OUT / "crossfit_decisions.csv", index=False)
pd.DataFrame(cert_rows, columns=["dataset", "source_seed", "target_seed", "fold", "certificate_role", "action", "raw_ef", "failures", "n", "cp_upper", "passed", "alpha_share", "action_hash"]).to_csv(OUT / "certification_results.csv", index=False)
pd.DataFrame(eval_rows, columns=["dataset", "source_seed", "target_seed", "fold", "action", "raw_ef", "evaluation_risk", "mean_ndc", "p95_ndc", "p99_ndc", "unsafe_acceptance", "outcome", "oracle_ef"]).to_csv(OUT / "evaluation_results.csv", index=False)
pd.DataFrame(regret_rows, columns=["dataset", "source_seed", "target_seed", "fold", "action", "search_only_decision_regret", "complete_cost_decision_regret"]).to_csv(OUT / "decision_regret.csv", index=False)
with gzip.open(OUT / "per_query_cost.csv.gz", "wt", newline="") as handle:
    w = csv.writer(handle); w.writerow(["dataset", "source_seed", "target_seed", "fold", "query_id", "action", "raw_ef", "ndc", "latency_ns"]); w.writerows(cost_rows)

dec = pd.DataFrame(decision_rows, columns=["dataset", "source_seed", "target_seed", "fold", "selected_action", "selected_ef", "deployed_action", "deployed_ef", "evaluation_outcome", "frozen_action_hash"])
ev = pd.DataFrame(eval_rows, columns=["dataset", "source_seed", "target_seed", "fold", "action", "raw_ef", "evaluation_risk", "mean_ndc", "p95_ndc", "p99_ndc", "unsafe_acceptance", "outcome", "oracle_ef"])
summary = {"decisions": len(dec), "deployed_action_counts": dec.deployed_action.value_counts().to_dict(), "outcomes": ev.outcome.value_counts().to_dict(), "future_confirm_accessed": False, "evidence": "RETROSPECTIVE_CROSSFIT"}
(MAN / "icba_fixed_target_auditor_crossfit.json").write_text(json.dumps(summary, indent=2) + "\n")
(DOC / "query_role_report.md").write_text("# Query role report\n\nAll Gate-A query outcomes are historical development evidence. Five deterministic folds provide mutually exclusive selection, pseudo-certification, and evaluation roles within each retrospective replay, with zero off-diagonal overlap. This computational separation does not make the data prospective. Future-confirm, validation-dev, and formal-test remain unopened.\n")
(DOC / "endpoint_fallback_report.md").write_text("# Endpoint and fallback report\n\nEndpoints are reconstructed per query from raw Recall@10 on the registered common six-level grid. Queries without a successful observed budget are right-censored; ef=200 is never imputed as success. Ef=200 is only a predeclared fallback candidate and is promoted within a fold only when its pseudo-certification Clopper–Pearson upper bound at alpha 0.025 is at most 0.05.\n")
(DOC / "retrospective_crossfit_report.md").write_text("# Retrospective cross-fit report\n\nThe replay covers 12 directed source-to-target pairs and five folds per pair. Each fold freezes one fixed action on 600 selection queries, pseudo-certifies selected and fallback actions on 200 disjoint queries, and evaluates once on the remaining 200 queries. Oracle use is pair-level and evaluation-only. Evidence scope is RETROSPECTIVE_CROSSFIT.\n\n" + json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, sort_keys=True))
