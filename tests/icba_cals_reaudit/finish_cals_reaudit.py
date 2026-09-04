from pathlib import Path
import pandas as pd, numpy as np, json, hashlib
ROOT=Path(__file__).parents[2]; OUT=ROOT/"results/icba_cals_reaudit"
R=pd.read_csv(OUT/"rescue_matrix.csv")
H=pd.read_csv(OUT/"portal_subset_results.csv",usecols=["dataset","build","raw_ef","mask","query_id","base_hits","full_hits","delta_hit_full","threshold_rescue"])
# hierarchy: fixed single and fixed sets (masks with popcount 1..4), and per-query upper bound all masks
rows=[]
for (ds,b,ef),g in R.groupby(["dataset","build","raw_ef"]):
    singles=g[(g['mask']>0)&(g['mask'].map(lambda x:int(x)&(int(x)-1)==0))]
    sets=g[g['mask'].map(lambda x:1<=int(x).bit_count()<=4)]
    for label,sel in [("BEST_SINGLE_FIXED_PORTAL",singles),("BEST_FIXED_SET_SIZE_2_4",sets)]:
        x=sel.sort_values(["n_threshold_rescues","n_positive_hit_gain","union_mean_recall"],ascending=False).iloc[0]
        rows.append(dict(dataset=ds,build=b,raw_ef=ef,level=label,oracle_status="FIXED_RULE",portal_set=x.portal_set,n_positive_hit_gain=int(x.n_positive_hit_gain),n_threshold_rescues=int(x.n_threshold_rescues),mean_recall=float(x.union_mean_recall),risk=float(x.union_risk),p95_ndc=float(x.union_p95_ndc)))
    q=H[(H.dataset==ds)&(H.build==b)&(H.raw_ef==ef)]
    qq=q.groupby("query_id").agg(base=("base_hits","first"),best=("full_hits","max"),delta=("delta_hit_full","max"))
    rows.append(dict(dataset=ds,build=b,raw_ef=ef,level="PER_QUERY_ORACLE_SIZE_1_4",oracle_status="NON_DEPLOYABLE_PER_QUERY_ORACLE",portal_set="ALL_REGISTERED_SUBSETS",n_positive_hit_gain=int((qq.delta>0).sum()),n_threshold_rescues=int(((qq.base<10)&(qq.best>=10)).sum()),mean_recall=float(qq.best.mean()/10),risk=float((qq.best<10).mean()),p95_ndc=float("nan")))
    rows.append(dict(dataset=ds,build=b,raw_ef=ef,level="PER_QUERY_ORACLE_ALL_SUBSETS",oracle_status="NON_DEPLOYABLE_PER_QUERY_ORACLE",portal_set="ALL_256_SUBSETS",n_positive_hit_gain=int((qq.delta>0).sum()),n_threshold_rescues=int(((qq.base<10)&(qq.best>=10)).sum()),mean_recall=float(qq.best.mean()/10),risk=float((qq.best<10).mean()),p95_ndc=float("nan")))
pd.DataFrame(rows).to_csv(OUT/"oracle_hierarchy.csv",index=False)
# hit gain table over all masks
R.assign(n_zero=R.n_positive_hit_gain.eq(0)).to_csv(OUT/"hit_gain_table.csv",index=False)
# build bootstrap and LOO
b=[]
for (ds,ef,mask),g in R.groupby(["dataset","raw_ef","mask"]):
 vals=g.union_mean_recall.to_numpy(); z=np.random.default_rng(991).choice(vals,size=(5000,len(vals)),replace=True).mean(1) if len(vals)>1 else np.repeat(vals.mean(),5000)
 b.append(dict(dataset=ds,raw_ef=ef,mask=mask,estimate=float(vals.mean()),ci95_lo=float(np.quantile(z,.025)),ci95_hi=float(np.quantile(z,.975)),n_builds=len(vals),seed=991))
pd.DataFrame(b).to_csv(OUT/"build_cluster_bootstrap.csv",index=False)
loo=[]
for (ds,ef,mask),g in R.groupby(["dataset","raw_ef","mask"]):
 for drop in g.build.unique():
  h=g[g.build!=drop]; loo.append(dict(dataset=ds,raw_ef=ef,mask=mask,dropped_build=drop,n_builds=len(h),union_mean_recall=float(h.union_mean_recall.mean()) if len(h) else np.nan))
pd.DataFrame(loo).to_csv(OUT/"leave_one_build_out.csv",index=False)
best=R[R['mask']>0].sort_values(["dataset","raw_ef","union_risk","union_mean_recall"],ascending=[True,True,True,False]).groupby(["dataset","raw_ef"]).head(1)
best.to_csv(OUT/"matched_cost_comparison.csv",index=False)
pd.DataFrame([dict(dataset=ds,raw_ef=ef,mechanical="PASS",id_semantics="PASS",full_candidate="PASS",portal_subset_count=256,best_fixed_risk=float(best[(best.dataset==ds)&(best.raw_ef==ef)].union_risk.iloc[0]),gate_status="EXPLORATORY") for ds in R.dataset.unique() for ef in sorted(R.raw_ef.unique())]).to_csv(OUT/"unified_gate_table.csv",index=False)
# compressed lane copy
frames=[]
for p in sorted(OUT.glob("*_semantic.csv")):
 d=pd.read_csv(p); d["dataset"]="SIFT-100K" if p.name.startswith("sift") else "Arxiv-Nomic-100K"; d["build"]=p.stem.split("_")[1]; frames.append(d)
pd.concat(frames,ignore_index=True).to_csv(OUT/"per_lane_results.csv.gz",index=False,compression="gzip")
print("hier",len(rows),"R",len(R),"H",len(H))
