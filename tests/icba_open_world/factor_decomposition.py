#!/usr/bin/env python3
import csv, math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "results/icba_micro_closure"
OUT = ROOT / "results/icba_open_world"

def read(name):
    with open(SRC / name, newline="") as f:
        return list(csv.DictReader(f))

def cp_upper(failures, n, alpha=0.05):
    if failures >= n:
        return 1.0
    def cdf(k, p):
        if p <= 0: return 1.0
        if p >= 1: return 0.0
        q=1-p
        lt=math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log(q)
        term=math.exp(lt) if lt > -745 else 0.0; total=term
        for i in range(k,0,-1):
            term *= i/(n-i+1)*q/p; total += term
        return min(1.0,max(0.0,total))
    lo,hi=failures/n,1.0
    for _ in range(70):
        mid=(lo+hi)/2
        if cdf(failures,mid)>alpha: lo=mid
        else: hi=mid
    return (lo+hi)/2

closed = read("graph_replay.csv")
opened = read("open_world_leave_build_out.csv")
rows = []
for env, data in [("CLOSED_WORLD_TARGET_INCLUDED", closed), ("OPEN_WORLD_LEAVE_ONE_BUILD_OUT", opened)]:
    for scope in ("ALL_GRAPHS_WITH_CENSORING_BOUNDS", "FEASIBLE_ONLY"):
        selected = [r for r in data if scope.startswith("ALL_") or r["endpoint_certified"] == "True"]
        groups = defaultdict(list)
        for r in selected:
            groups[(r["dataset"], r["implementation"])].append(r)
        for (dataset, impl), g in sorted(groups.items()):
            n = sum(int(r["queries"]) for r in g)
            failures = sum(round(float(r["under_rate_conservative"])*int(r["queries"])) for r in g)
            obs = sum(int(r["observed_queries"]) for r in g)
            cens = sum(int(r["right_censored_queries"]) for r in g)
            wmean = lambda k: sum(float(r[k])*int(r["queries"]) for r in g)/n
            rows.append({
                "environment_range": env, "source_policy": "PER_QUERY_SOURCE_ORACLE",
                "target_information": "LABELED_TARGET_SENTINEL", "endpoint_range": scope,
                "dataset": dataset, "implementation": impl, "builds": len(g), "queries": n,
                "observed_queries": obs, "right_censored_queries": cens,
                "under_failures": failures, "under_rate": failures/n,
                "under_cp95_upper": cp_upper(failures,n), "mean_recall": wmean("mean_recall"),
                "mean_ndc": wmean("mean_ndc"), "p95_ndc_build_median": sorted(float(r["p95_ndc"]) for r in g)[len(g)//2],
                "early_action_rate": "NOT_ESTIMABLE", "fallback_rate": "NOT_ESTIMABLE",
                "oracle_retention": "NOT_ESTIMABLE", "top1pct_deleted_under_rate": wmean("top1pct_deleted_under_rate"),
                "deployability": "NON_DEPLOYABLE_ORACLE_LANE"
            })

fields = list(rows[0])
with open(OUT/"factorial_cells.csv", "w", newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

idx={(r["environment_range"],r["endpoint_range"],r["dataset"],r["implementation"]):r for r in rows}
dec=[]
for dataset in sorted(set(r["dataset"] for r in rows)):
  for impl in sorted(set(r["implementation"] for r in rows)):
    try:
      ca=idx[("CLOSED_WORLD_TARGET_INCLUDED","ALL_GRAPHS_WITH_CENSORING_BOUNDS",dataset,impl)]
      cf=idx[("CLOSED_WORLD_TARGET_INCLUDED","FEASIBLE_ONLY",dataset,impl)]
      oa=idx[("OPEN_WORLD_LEAVE_ONE_BUILD_OUT","ALL_GRAPHS_WITH_CENSORING_BOUNDS",dataset,impl)]
      of=idx[("OPEN_WORLD_LEAVE_ONE_BUILD_OUT","FEASIBLE_ONLY",dataset,impl)]
    except KeyError: continue
    endpoint_closed=float(ca["under_rate"])-float(cf["under_rate"])
    endpoint_open=float(oa["under_rate"])-float(of["under_rate"])
    env_all=float(oa["under_rate"])-float(ca["under_rate"])
    env_feasible=float(of["under_rate"])-float(cf["under_rate"])
    interaction=env_all-env_feasible
    dec.append({"dataset":dataset,"implementation":impl,"endpoint_contrast_closed":endpoint_closed,
      "endpoint_contrast_open":endpoint_open,"environment_contrast_all":env_all,
      "environment_contrast_feasible":env_feasible,"endpoint_environment_interaction":interaction,
      "source_policy_contribution":"NOT_IDENTIFIABLE_FROM_FROZEN_DATA",
      "target_information_contribution":"NOT_IDENTIFIABLE_FROM_FROZEN_DATA",
      "interpretation":"DESCRIPTIVE_NON_CAUSAL"})
with open(OUT/"risk_decomposition.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(dec[0])); w.writeheader(); w.writerows(dec)
with open(OUT/"factor_interactions.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(dec[0])); w.writeheader(); w.writerows(dec)
print({"factorial_cells":len(rows),"decomposition_rows":len(dec)})
