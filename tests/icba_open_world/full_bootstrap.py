#!/usr/bin/env python3
import csv,random,statistics,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/icba_open_world'; REPS=5000; SEED=991
rows=list(csv.DictReader(open(OUT/'feasible_only_open_world.csv')))
groups=defaultdict(list)
for r in rows: groups[(r['dataset'],r['implementation'])].append(r)
def q(xs,p):
 xs=sorted(xs); x=(len(xs)-1)*p; lo=int(x); hi=min(lo+1,len(xs)-1); return xs[lo]+(xs[hi]-xs[lo])*(x-lo)
rng=random.Random(SEED); out=[]
for (ds,im),g in sorted(groups.items()):
 n=len(g); vals=[float(x['under_rate_conservative']) for x in g]; trim=[float(x['top1pct_deleted_under_rate']) for x in g]
 boot=[]; btrim=[]; exceed=[]
 for _ in range(REPS):
  s=[rng.randrange(n) for _ in range(n)]; boot.append(sum(vals[i] for i in s)/n); btrim.append(sum(trim[i] for i in s)/n); exceed.append(sum(vals[i]>.05 for i in s)/n)
 out.append({'dataset':ds,'implementation':im,'independent_builds':n,'bootstrap_reps':REPS,'seed':SEED,
  'mean_build_risk':sum(vals)/n,'cluster_bootstrap_ci_low':q(boot,.025),'cluster_bootstrap_ci_high':q(boot,.975),
  'top1pct_deleted_mean_build_risk':sum(trim)/n,'top1pct_cluster_ci_low':q(btrim,.025),'top1pct_cluster_ci_high':q(btrim,.975),
  'fraction_builds_above_delta_q':sum(x>.05 for x in vals)/n,'fraction_ci_low':q(exceed,.025),'fraction_ci_high':q(exceed,.975)})
tmp=OUT/'build_cluster_bootstrap.csv.tmp'
with open(tmp,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
tmp.replace(OUT/'build_cluster_bootstrap.csv');print(*out,sep='\n')
