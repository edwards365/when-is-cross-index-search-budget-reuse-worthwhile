#!/usr/bin/env python3
import csv, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"results/icba_micro_closure"; OUT=ROOT/"results/icba_open_world"; OUT.mkdir(exist_ok=True)

def binom_cdf(k,n,p):
    if k>=n:return 1.0
    if k<0:return 0.0
    if p<=0:return 1.0
    if p>=1:return 0.0
    q=1-p; lt=math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*math.log(p)+(n-k)*math.log(q)
    term=math.exp(lt) if lt>-745 else 0.0; total=term
    for i in range(k,0,-1):term*=i/(n-i+1)*q/p; total+=term
    return min(1,max(0,total))
def upper(x,n,alpha=.05):
    if x>=n:return 1.0
    lo,hi=x/n,1.0
    for _ in range(70):
        m=(lo+hi)/2
        if binom_cdf(x,n,m)>alpha:lo=m
        else:hi=m
    return (lo+hi)/2

ep=list(csv.DictReader((SRC/"endpoint_audit.csv").open()))
status_map={"CURRENT_ENDPOINT_CERTIFIABLY_SAFE":"CERTIFIED_ENDPOINT_FEASIBLE","GRID_RIGHT_CENSORED":"RIGHT_CENSORED_AT_MAX_BUDGET","NO_PRACTICAL_SAFE_ENDPOINT":"NO_PRACTICAL_SAFE_ENDPOINT"}
strata=[]; key={}
for r in ep:
    z=dict(r); z["endpoint_stratum"]=status_map[r["endpoint_status"]]
    z["glove_interpretation"]="RIGHT_CENSORING_PREVENTS_IDENTIFICATION" if r["dataset"]=="glove100_100k" else ""
    strata.append(z); key[(r["implementation"],r["dataset"],r["history"],r["seed"])]=z["endpoint_stratum"]
with (OUT/"endpoint_strata.csv.tmp").open("w",newline="") as h:
    w=csv.DictWriter(h,fieldnames=list(strata[0]));w.writeheader();w.writerows(strata)
(OUT/"endpoint_strata.csv.tmp").replace(OUT/"endpoint_strata.csv")

ow=list(csv.DictReader((SRC/"open_world_leave_build_out.csv").open())); feasible=[]
for r in ow:
    if key[(r["implementation"],r["dataset"],r["history"],r["seed"])]!="CERTIFIED_ENDPOINT_FEASIBLE":continue
    n=int(r["queries"]); failures=round(float(r["under_rate_conservative"])*n); trimmed_n=n-math.ceil(.01*n); trimmed_fail=round(float(r["top1pct_deleted_under_rate"])*trimmed_n)
    feasible.append({**r,"under_failures":failures,"under_cp95_upper":upper(failures,n),
                     "top1pct_deleted_queries":trimmed_n,"top1pct_deleted_failures":trimmed_fail,
                     "top1pct_deleted_cp95_upper":upper(trimmed_fail,trimmed_n),"endpoint_control":"CERTIFIED_ENDPOINT_FEASIBLE"})
with (OUT/"feasible_only_open_world.csv.tmp").open("w",newline="") as h:
    w=csv.DictWriter(h,fieldnames=list(feasible[0]));w.writeheader();w.writerows(feasible)
(OUT/"feasible_only_open_world.csv.tmp").replace(OUT/"feasible_only_open_world.csv")
print({"strata":{s:sum(x["endpoint_stratum"]==s for x in strata) for s in status_map.values()},"feasible_open_world_rows":len(feasible)})
