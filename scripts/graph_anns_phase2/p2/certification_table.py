#!/usr/bin/env python
"""P2/B2: six-method constructive decision table from frozen hnswlib per-query records
(retrospective replay, seed 991). Methods per target build:

  M1 naive single-source transport (k=1 random source, mean over draws)
  M2 max-over-source robust pooling (23 sources; abstain when no jointly safe action)
  M3 frozen-action CP certification (M=1, m=59, zero-failure Clopper-Pearson; fixed action
     = maximum registered ef, no selection)
  M4 target select-then-certify (selection 375 / certification 94 / evaluation 281 disjoint
     queries; M=6 actions; Bonferroni alpha_l=0.05/6 -> m_min=94)
  M5 maximum registered action (always deploy)
  M6 per-query oracle B_t(q) (non-deployable reference)

DistComp = mean distance computations vs per-query oracle cost (hnswlib only).
"""
import gzip
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

from max_over_source import (DATA500, H, REPO, OUT, SEED, load_hnswlib,
                             min_safe_actions)

ALPHA, DELTA, M_ACTIONS = 0.05, 0.05, 6
M1_CERT_N = math.ceil(math.log(ALPHA) / math.log(1 - DELTA))            # 59
M4_CERT_N = math.ceil(math.log(ALPHA / M_ACTIONS) / math.log(1 - DELTA))  # 94
SEL_N, EVAL_N = 375, 750 - 375 - M4_CERT_N  # 281
GRID = [10, 20, 40, 80, 120, 200]
MAXA = 200
DRAWS_K1 = 50


def cp_zero_failure_ub(m, alpha_l):
    return 1.0 - alpha_l ** (1.0 / m)


def run(dataset):
    builds = load_hnswlib(dataset)
    B, tables = min_safe_actions(builds, GRID)
    names = sorted(B)
    qids = tables[names[0]][0].index.values
    nq = len(qids)
    Bmat = np.stack([B[n] for n in names]).astype(float)
    Bmat[Bmat < 0] = np.nan
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(nq)
    sel_idx, cert_idx, eval_idx = perm[:SEL_N], perm[SEL_N:SEL_N + M4_CERT_N], perm[SEL_N + M4_CERT_N:]
    # fixed 59-query certification set for M3 (disjoint from M4's roles by construction:
    # first 59 of the selection block are not reused for M3 certification; M3 uses its own
    # permutation draw)
    rng3 = np.random.default_rng(SEED + 1)
    perm3 = rng3.permutation(nq)
    m3_cert, m3_eval = perm3[:M1_CERT_N], perm3[M1_CERT_N:]

    rows = []
    for ti, t in enumerate(names):
        hit, ndc, ef_idx = tables[t]
        hv = hit.loc[qids].values          # (nq, 6) hit counts
        nv = ndc.loc[qids].values if ndc is not None else None
        tgt = Bmat[ti]
        src = np.delete(Bmat, ti, axis=0)
        feas = ~np.isnan(tgt)
        oracle_cost = np.array([nv[i, np.searchsorted(ef_idx, tgt[i])] if feas[i] else np.nan
                                for i in range(nq)]) if nv is not None else None

        def deploy_eval(a, idx):
            """Return (risk, mean_cost_ratio) of deploying actions a on query subset idx."""
            j = np.clip(np.searchsorted(ef_idx, a[idx]), 0, len(ef_idx) - 1)
            z = hv[idx, j] < H
            if nv is None:
                return float(z.mean()), None, None, None
            cost = nv[idx, j]
            oc = oracle_cost[idx]
            ok = ~np.isnan(oc)
            ratio = float(np.mean(cost[ok] / oc[ok]))
            p95 = float(np.percentile(cost[ok] / oc[ok], 95)) if ok.any() else float("nan")
            return float(z.mean()), ratio, p95, None

        # M1 naive k=1
        risks1, costs1 = [], []
        for _ in range(DRAWS_K1):
            s = src[rng.integers(0, len(src))]
            a = np.where(np.isnan(s), MAXA, s).astype(int)
            rz, cz, _, _ = deploy_eval(a, np.arange(nq))
            risks1.append(rz)
            if cz is not None:
                costs1.append(cz)
        m1_risk = float(np.mean(risks1))
        m1_cost = float(np.mean(costs1)) if costs1 else None

        # M2 max-over-source (abstain variant evaluated on deployable)
        any_bot = np.isnan(src).any(axis=0)
        a2 = np.where(any_bot, MAXA, np.nanmax(src, axis=0)).astype(int)
        m2_risk, m2_cost, m2_p95, _ = deploy_eval(a2, np.arange(nq))
        m2_risk_dep = deploy_eval(a2, np.where(~any_bot)[0])[0]
        m2_overall = m2_risk_dep * (1.0 - float(any_bot.mean()))  # P(unsafe execution)

        # M3 frozen-action certification: a=MAXA, 59 zero-failure queries, repeated draws
        fail_at_max = hv[:, len(ef_idx) - 1] < H
        rng_m3 = np.random.default_rng(SEED + 100 + ti)
        certs = []
        for _ in range(100):
            draw = rng_m3.choice(nq, size=M1_CERT_N, replace=False)
            certs.append(int(fail_at_max[draw].sum()) == 0)
        certify_prob3 = float(np.mean(certs))
        certified3 = certify_prob3 >= 0.5
        m3_risk, m3_cost, m3_p95, _ = deploy_eval(np.full(nq, MAXA, dtype=int), m3_eval)
        # structural: fraction of max-action failures concentrated in queries failing on
        # ALL builds (endpoint-infeasible mass shared across targets)
        fail_all = (np.isnan(Bmat).all(axis=0))
        conc = float(fail_at_max[fail_all].sum() / max(fail_at_max.sum(), 1))

        # M4a select-then-certify, point-risk screening (min cost among point risk <= delta)
        # M4b Theorem-2 screening: min cost among actions with zero-failure CP upper bound
        #    on the selection block <= delta  (i.e., a screening margin rule)
        hv_sel = hv[sel_idx]
        n_sel = len(sel_idx)
        fails_sel = (hv_sel < H).sum(axis=0)
        risk_sel = fails_sel / n_sel
        ub_sel_vec = beta_dist.ppf(1 - ALPHA, fails_sel + 1, n_sel - fails_sel)

        def select_then_certify(screening):
            if screening == "point":
                feasible = np.where(risk_sel <= DELTA)[0]
            else:  # Theorem-2 screening: r_hat + epsilon_R <= delta, i.e. selection-block
                   # zero/low-failure CP upper bound (alpha_sel = ALPHA/2) must be <= delta
                ub_screen = beta_dist.ppf(1 - ALPHA / 2, fails_sel + 1, n_sel - fails_sel)
                feasible = np.where(ub_screen <= DELTA)[0]
            if len(feasible) == 0:
                return {"certified": False, "abstain": True, "risk": None, "cost": None,
                        "chosen_ef": None,
                        "cert_fail_reason": "NO_FEASIBLE_ACTION_ON_SELECTION"}
            if nv is not None:
                cost_sel = nv[sel_idx].mean(axis=0)
                pick = feasible[np.argmin(cost_sel[feasible])]
            else:
                pick = feasible[0]
            z_cert = hv[cert_idx, pick] < H
            certified = int(z_cert.sum()) == 0
            out = {"certified": bool(certified), "abstain": False,
                   "chosen_ef": int(ef_idx[pick]),
                   "cert_fail_reason": None if certified
                   else f"ZERO_FAILURE_VIOLATED_AT_ef{ef_idx[pick]}"}
            if certified:
                a4 = np.full(nq, ef_idx[pick], dtype=int)
                out["risk"], out["cost"], out["p95"], _ = deploy_eval(a4, eval_idx)
            return out

        m4 = select_then_certify("point")
        m4b = select_then_certify("cp_ub")

        # M5 always max action
        m5_risk, m5_cost, m5_p95, _ = deploy_eval(np.full(nq, MAXA, dtype=int), np.arange(nq))

        # M6 oracle
        a6 = np.where(feas, tgt, MAXA).astype(int)
        m6_risk, m6_cost, m6_p95, _ = deploy_eval(a6, np.arange(nq))

        rows.append({
            "dataset": dataset, "target": t,
            "M1_naive_k1_risk": m1_risk, "M1_distcomp": m1_cost,
            "M2_maxsource_risk_deployable": m2_risk_dep,
            "M2_overall_unsafe_execution": m2_overall,
            "M2_maxsource_abstain_rate": float(any_bot.mean()),
            "M2_distcomp": m2_cost, "M2_distcomp_p95": m2_p95,
            "M3_certified": certified3, "M3_certify_prob": certify_prob3,
            "M3_risk_eval": m3_risk, "M3_distcomp": m3_cost,
            "M3_cp_upper_bound": cp_zero_failure_ub(M1_CERT_N, ALPHA),
            "max_action_failure_concentrated_in_always_infeasible": conc,
            "M4_certified": m4["certified"], "M4_abstain": m4["abstain"],
            "M4_risk_eval": m4.get("risk"), "M4_distcomp": m4.get("cost"),
            "M4_chosen_ef": m4.get("chosen_ef"), "M4_fail_reason": m4.get("cert_fail_reason"),
            "M4_cp_upper_bound": cp_zero_failure_ub(M4_CERT_N, ALPHA / M_ACTIONS),
            "M4b_certified": m4b["certified"], "M4b_abstain": m4b["abstain"],
            "M4b_risk_eval": m4b.get("risk"), "M4b_distcomp": m4b.get("cost"),
            "M4b_chosen_ef": m4b.get("chosen_ef"), "M4b_fail_reason": m4b.get("cert_fail_reason"),
            "M5_max_action_risk": m5_risk, "M5_distcomp": m5_cost, "M5_distcomp_p95": m5_p95,
            "M6_oracle_risk": m6_risk, "M6_distcomp": m6_cost,
            "M6_infeasible_rate": float((~feas).mean()),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"six_method_table_{dataset}.csv", index=False)
    agg = {
        "dataset": dataset,
        "M1_naive_k1_risk": df["M1_naive_k1_risk"].mean(),
        "M2_risk_deployable": df["M2_maxsource_risk_deployable"].mean(),
        "M2_abstain_rate": df["M2_maxsource_abstain_rate"].mean(),
        "M2_distcomp": df["M2_distcomp"].mean(),
        "M3_certify_rate": df["M3_certified"].mean(),
        "M3_certify_prob_mean": df["M3_certify_prob"].mean(),
        "max_action_failure_concentration": df["max_action_failure_concentrated_in_always_infeasible"].mean(),
        "M3_risk_eval": df.loc[df["M3_certified"], "M3_risk_eval"].mean(),
        "M3_distcomp": df.loc[df["M3_certified"], "M3_distcomp"].mean(),
        "M4_certify_rate": df["M4_certified"].mean(),
        "M4_abstain_rate": df["M4_abstain"].mean(),
        "M4_risk_eval": df.loc[df["M4_certified"], "M4_risk_eval"].mean(),
        "M4_distcomp": df.loc[df["M4_certified"], "M4_distcomp"].mean(),
        "M4b_certify_rate": df["M4b_certified"].mean(),
        "M4b_abstain_rate": df["M4b_abstain"].mean(),
        "M4b_risk_eval": df.loc[df["M4b_certified"], "M4b_risk_eval"].mean(),
        "M4b_distcomp": df.loc[df["M4b_certified"], "M4b_distcomp"].mean(),
        "M5_risk": df["M5_max_action_risk"].mean(), "M5_distcomp": df["M5_distcomp"].mean(),
        "M6_oracle_distcomp": df["M6_distcomp"].mean(),
        "M6_infeasible_rate": df["M6_infeasible_rate"].mean(),
    }
    print(json.dumps(agg, indent=1))
    return agg


if __name__ == "__main__":
    aggs = [run(ds) for ds in ("sift_100k", "arxiv_nomic_100k")]
    pd.DataFrame(aggs).to_csv(OUT / "six_method_table_summary.csv", index=False)
