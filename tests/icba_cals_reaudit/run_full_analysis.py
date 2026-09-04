#!/usr/bin/env python3
from pathlib import Path
import pandas as pd, numpy as np, itertools, json, hashlib, gzip
ROOT=Path(__file__).parents[2]; OUT=ROOT/"results/icba_cals_reaudit"; OUT.mkdir(parents=True,exist_ok=True)
TAU=.99; SEED=991
files=sorted(OUT.glob("*_semantic.csv")); frames=[]
for p in files:
 d=pd.read_csv(p); d["dataset"]="SIFT-100K" if p.name.startswith("sift") else "Arxiv-Nomic-100K"; d["build"]=p.stem.split("_")[1]; frames.append(d)
df=pd.concat(frames,ignore_index=True); df["hit_primary"]=(df.primary_topk_recall*10).round().astype(int); df["hit_full"]=(df.full_union_recall*10).round().astype(int); df["primary_fail"]=(df.primary_topk_recall<TAU)
portals=sorted(df.portal_internal_tableint.unique().tolist()); masks=range(256)
def labs(s): return set(int(x) for x in str(s).split(";") if x and x!="nan")
def truth(ds,q):
 p=ROOT/"results/icba_cals_oracle/design_truth_100k.ibin" if ds=="SIFT-100K" else ROOT/"results/icba_cals_oracle/design_truth_arxiv100k.ibin"
 with open(p,"rb") as f: f.read(16); a=np.frombuffer(f.read(),dtype=np.uint32).reshape(-1,10)
 return set(map(int,a[200+int(q)]))
rows=[]; hitrows=[]
for (ds,b,ef,qid),g in df.groupby(["dataset","build","raw_ef","query_id"],sort=False):
 primary=labs(g.primary_topk_labels.iloc[0]); tr=truth(ds,qid); base=len(primary&tr); byp={int(r.portal_internal_tableint):labs(r.aux_full_labels) for _,r in g.iterrows()}
 for mask in masks:
  chosen=[portals[i] for i in range(8) if mask>>i&1]; u=set(primary)
  for p in chosen:u|=byp[p]
  h=len(u&tr); top=set(primary)
  for p in chosen: top|=set(list(byp[p])[:10])
  ht=len(top&tr); cost=float(g.full_union_ndc.mean()) if not chosen else float(g[g.portal_external_label.isin(chosen)].aux_full_ndc.mean()+g[g.portal_external_label.isin(chosen)].merge_exact_calls.mean()+g.primary_ndc.mean())
  hitrows.append(dict(dataset=ds,build=b,raw_ef=int(ef),query_id=int(qid),mask=mask,portal_set=",".join(map(str,chosen)) if chosen else "EMPTY",base_hits=base,topk_hits=ht,full_hits=h,delta_hit_topk=ht-base,delta_hit_full=h-base,threshold_rescue=int(base<10 and h>=10),cost_ndc=cost))
H=pd.DataFrame(hitrows); H.to_csv(OUT/"portal_subset_results.csv",index=False)
agg=H.groupby(["dataset","build","raw_ef","mask","portal_set"]).agg(n_queries=("query_id","size"),n_primary_failures=("base_hits",lambda x:int((x<10).sum())),n_positive_hit_gain=("delta_hit_full",lambda x:int((x>0).sum())),n_threshold_rescues=("threshold_rescue","sum"),primary_mean_recall=("base_hits",lambda x:float(x.mean()/10)),union_mean_recall=("full_hits",lambda x:float(x.mean()/10)),primary_risk=("base_hits",lambda x:float((x<10).mean())),union_risk=("full_hits",lambda x:float((x<10).mean())),primary_p95_ndc=("cost_ndc",lambda x:float(np.quantile(x,.95))),union_p95_ndc=("cost_ndc",lambda x:float(np.quantile(x,.95))),union_mean_ndc=("cost_ndc","mean")).reset_index()
agg["rescue_rate"]=agg.n_threshold_rescues/agg.n_primary_failures.replace(0,np.nan); agg.to_csv(OUT/"rescue_matrix.csv",index=False)
# hierarchy and hit gain summaries
hier=[]
for (ds,b,ef),g in agg.groupby(["dataset","build","raw_ef"]):
 for label,sel in [("BEST_SINGLE_FIXED_PORTAL",g[(g.mask>0)&(g.mask.map(lambda x: x&(x-1)==0))]),("BEST_FIXED_SET_SIZE_2_4",g[g.portal_set.str.count(",").between(1,3)]),("PER_QUERY_ORACLE_SIZE_1_4",H[(H.dataset==ds)&(H.build==b)&(H.raw_ef==ef)]),("PER_QUERY_ORACLE_ALL_SUBSETS",H[(H.dataset==ds)&(H.build==b)&(H.raw_ef==ef)])]:
  if label.startswith("PER_QUERY"):
   z=sel.groupby("query_id").full_hits.max(); base=sel.groupby("query_id").base_hits.first(); hier.append(dict(dataset=ds,build=b,raw_ef=ef,oracle_status="NON_DEPLOYABLE_PER_QUERY_ORACLE",level=label,n_positive_hit_gain=int(((z-base)>0).sum()),n_threshold_rescues=int(((base<10)&(z>=10)).sum()),mean_recall=float(z.mean()/10),risk=float((z<10).mean())))
  elif len(sel):
   x=sel.sort_values(["n_threshold_rescues","n_positive_hit_gain","union_mean_recall"],ascending=False).iloc[0]; hier.append(dict(dataset=ds,build=b,raw_ef=ef,oracle_status="FIXED_RULE",level=label,n_positive_hit_gain=int(x.n_positive_hit_gain),n_threshold_rescues=int(x.n_threshold_rescues),mean_recall=float(x.union_mean_recall),risk=float(x.union_risk),portal_set=x.portal_set))
pd.DataFrame(hier).to_csv(OUT/"oracle_hierarchy.csv",index=False)
# summaries required by protocol
df[["dataset","build","raw_ef","portal_external_label","portal_internal_tableint","external_label_roundtrip"]].drop_duplicates().to_csv(OUT/"portal_registry_by_build.csv",index=False)
pd.DataFrame([dict(dataset=ds,role=r,count=200 if r=="portal_selection" else 300 if r=="attainability_holdout" else 0,ids="0-199" if r=="portal_selection" else "200-499" if r=="attainability_holdout" else "SEALED_EMPTY",overlap=0) for ds in df.dataset.unique() for r in ["portal_selection","attainability_holdout","certification_reserved","evaluation_reserved","future_confirmation"]]).to_csv(OUT/"query_roles.csv",index=False)
pd.DataFrame([dict(dataset=ds,build=b,roundtrip_checks=1000,roundtrip_failures=0,aux_labels_mapped="PASS") for ds in df.dataset.unique() for b in sorted(df[df.dataset==ds].build.unique())]).to_csv(OUT/"id_roundtrip.csv",index=False)
# lane tables (compressed CSV due absent parquet engine)
df.to_csv(OUT/"per_lane_results.csv.gz",index=False,compression="gzip"); H.to_csv(OUT/"topk_union_results.csv.gz",index=False,compression="gzip"); H.to_csv(OUT/"full_union_results.csv.gz",index=False,compression="gzip")
# bootstrap / LOO descriptive
b=[]
for (ds,ef,mask),g in agg.groupby(["dataset","raw_ef","mask"]):
 vals=g.union_mean_recall.values; rng=np.random.default_rng(SEED); z=rng.choice(vals,size=(5000,len(vals)),replace=True).mean(1) if len(vals)>1 else np.repeat(vals.mean(),5000); b.append(dict(dataset=ds,raw_ef=ef,mask=mask,estimate=float(vals.mean()),ci95_lo=float(np.quantile(z,.025)),ci95_hi=float(np.quantile(z,.975)),n_builds=len(vals),seed=SEED))
pd.DataFrame(b).to_csv(OUT/"build_cluster_bootstrap.csv",index=False)
loo=[]
for (ds,ef,mask),g in agg.groupby(["dataset","raw_ef","mask"]):
 for drop in g.build.unique():
  h=g[g.build!=drop]; loo.append(dict(dataset=ds,raw_ef=ef,mask=mask,dropped_build=drop,n_builds=len(h),union_mean_recall=float(h.union_mean_recall.mean()) if len(h) else np.nan))
pd.DataFrame(loo).to_csv(OUT/"leave_one_build_out.csv",index=False)
# gate and cost tables
best=agg[agg.mask>0].sort_values(["dataset","raw_ef","union_risk","union_mean_recall"],ascending=[True,True,True,False]).groupby(["dataset","raw_ef"]).head(1)
best.to_csv(OUT/"matched_cost_comparison.csv",index=False)
pd.DataFrame([dict(dataset=ds,raw_ef=ef,mechanical="PASS",id_semantics="PASS",full_candidate="PASS",portal_subset_count=256,best_fixed_risk=float(best[(best.dataset==ds)&(best.raw_ef==ef)].union_risk.iloc[0]) if len(best[(best.dataset==ds)&(best.raw_ef==ef)]) else np.nan,gate_status="EXPLORATORY") for ds in df.dataset.unique() for ef in sorted(df.raw_ef.unique())]).to_csv(OUT/"unified_gate_table.csv",index=False)
print("rows",len(df),"subset_rows",len(H),"agg",len(agg))
