#!/usr/bin/env python3
"""Censoring-aware analysis for the registered Faiss-HNSW build family."""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

GRID=np.array([16,32,64,128,256,512]); DATASETS=["sift_100k","arxiv_nomic_100k"]
EVENTS=["BOTH_RIGHT_CENSORED","SOURCE_ONLY_RIGHT_CENSORED","TARGET_ONLY_RIGHT_CENSORED","UNDER_BUDGET_UNSAFE","UNDER_BUDGET_OBSERVED_SAFE","EXACT_BUDGET_SAFE","OVER_BUDGET_SAFE"]

def save(x,o,n): x.to_csv(o/n,index=False,float_format="%.12g")

def load(work):
    xs=[]
    for p in sorted((work/"raw").glob("*/queries.csv.gz")):
        x=pd.read_csv(p); xs.append(x[x.query_role.eq("confirmatory_evaluation")])
    return pd.concat(xs,ignore_index=True)

def budgets(x):
    rows=[]
    for (ds,b,q),g in x.groupby(["dataset","build_id","query_id"],sort=False):
        g=g.set_index("ef_search").loc[GRID]; good=g.recall_at_10.to_numpy()>=.95; suffix=np.logical_and.accumulate(good[::-1])[::-1]; hit=np.flatnonzero(suffix)
        rows.append((ds,b,q,float(GRID[hit[0]]) if len(hit) else np.nan,not bool(good[-1]),bool(np.any(good[:-1]&~good[1:]))))
    return pd.DataFrame(rows,columns=["dataset","build_id","query_id","safe_budget","right_censored","raw_nonmonotone"])

def h1(b):
    cat=[]; num=[]
    for ds in DATASETS:
        p=b[b.dataset.eq(ds)].pivot(index="query_id",columns="build_id",values="safe_budget"); cens=p.isna(); nf=p.notna().sum(1); allf=nf.eq(p.shape[1]); allc=nf.eq(0); mixed=(nf.gt(0)&nf.lt(p.shape[1])); varied=(p.nunique(axis=1,dropna=False)>1)
        cat.append(dict(dataset=ds,build_count=p.shape[1],query_count=len(p),category_variation_rate=varied.mean(),mixed_feasible_censored_rate=mixed.mean(),all_feasible_count=int(allf.sum()),all_censored_count=int(allc.sum()),endpoint_rate=cens.to_numpy().mean(),raw_nonmonotone_rate=b[b.dataset.eq(ds)].raw_nonmonotone.mean()))
        for scope,mask in [("all_builds_feasible",allf),("at_least_two_feasible",nf.ge(2))]:
            d=p[mask].max(1)-p[mask].min(1); vals=[]
            for _,r in p[mask].iterrows():
                z=r.dropna().to_numpy(); vals.extend(abs(z[i]-z[j]) for i in range(len(z)) for j in range(i+1,len(z)))
            num.append(dict(dataset=ds,scope=scope,effective_queries=len(d),positive_diameter_rate=(d>0).mean(),mean_diameter=d.mean(),median_diameter=d.median(),p90_diameter=d.quantile(.9),p95_diameter=d.quantile(.95),pairwise_disagreement_rate=np.mean(np.asarray(vals)>0),jointly_feasible_mean_abs_diff=np.mean(vals)))
    return pd.DataFrame(cat),pd.DataFrame(num)

def events(x,b):
    look=x.set_index(["dataset","build_id","query_id","ef_search"])[["recall_at_10","ndc"]]; rows=[]
    for ds in DATASETS:
        z=b[b.dataset.eq(ds)]; builds=sorted(z.build_id.unique())
        by={u:z[z.build_id.eq(u)].set_index("query_id") for u in builds}
        for s in builds:
            sb=by[s]
            for t in builds:
                if s==t: continue
                tb=by[t]
                for q in sb.index:
                    se=sb.at[q,"safe_budget"]; te=tb.at[q,"safe_budget"]; sc=pd.isna(se);tc=pd.isna(te); action=512 if sc else int(se)
                    obs=look.loc[(ds,t,q,action)]; ref=look.loc[(ds,t,q,512 if tc else int(te))]; fail=bool(obs.recall_at_10<.95 or tc);rf=bool(ref.recall_at_10<.95 or tc)
                    if sc and tc: ev=EVENTS[0]
                    elif sc: ev=EVENTS[1]
                    elif tc: ev=EVENTS[2]
                    elif se<te: ev=EVENTS[4] if (obs.recall_at_10>=.95 and tb.at[q,"raw_nonmonotone"]) else EVENTS[3]
                    elif se==te: ev=EVENTS[5]
                    else: ev=EVENTS[6]
                    diff=np.nan if fail or rf else float(obs.ndc-ref.ndc)
                    rows.append((ds,s,t,q,se,te,ev,fail,rf,float(fail)-float(rf),diff,float(ref.ndc),bool(tb.at[q,"raw_nonmonotone"])))
    return pd.DataFrame(rows,columns=["dataset","source_build","target_build","query_id","source_budget","target_budget","event","failure","reference_failure","risk_increment","ndc_difference_safe","target_oracle_ndc","raw_nonmonotone"])

def summary(e):
    rows=[]
    for ds in DATASETS:
        z=e[e.dataset.eq(ds)]; v=z.ndc_difference_safe.notna()
        rows.append(dict(dataset=ds,absolute_transport_risk=z.failure.mean(),source_reference_risk=z.reference_failure.mean(),incremental_transport_risk=z.risk_increment.mean(),safe_rom_ndc_tax=z.loc[v,"ndc_difference_safe"].sum()/z.loc[v,"target_oracle_ndc"].sum(),safe_mean_of_ratios=(z.loc[v,"ndc_difference_safe"]/z.loc[v,"target_oracle_ndc"]).mean(),pairs=len(z[["source_build","target_build"]].drop_duplicates()),queries_per_pair=z.query_id.nunique()))
    return pd.DataFrame(rows)

def bootstrap(e,B=5000,seed=991):
    rng=np.random.default_rng(seed);rows=[]
    for ds in DATASETS:
        z=e[e.dataset.eq(ds)].copy();z["num"]=z.ndc_difference_safe.fillna(0);z["den"]=z.target_oracle_ndc.where(z.ndc_difference_safe.notna(),0); q=z.groupby("query_id").agg(risk=("risk_increment","sum"),n=("risk_increment","size"),num=("num","sum"),den=("den","sum")); ids=q.index.to_numpy(); vals=[]
        for _ in range(B):
            ii=rng.integers(0,len(ids),len(ids)); a=q.iloc[ii];vals.append((a.risk.sum()/a.n.sum(),a.num.sum()/a.den.sum()))
        a=np.asarray(vals); rows.append(dict(dataset=ds,risk_ci_low=np.quantile(a[:,0],.025),risk_ci_high=np.quantile(a[:,0],.975),rom_ci_low=np.quantile(a[:,1],.025),rom_ci_high=np.quantile(a[:,1],.975),bootstrap=B,seed=seed,scope="registered_build_family_conditional_query_distribution"))
    return pd.DataFrame(rows)

def lobo(e):
    rows=[]
    for ds in DATASETS:
        z=e[e.dataset.eq(ds)]; builds=sorted(set(z.source_build))
        for b in builds:
            a=z[(z.source_build.ne(b))&(z.target_build.ne(b))];v=a.ndc_difference_safe.notna();rows.append(dict(dataset=ds,deleted_build=b,risk_increment=a.risk_increment.mean(),safe_rom_ndc_tax=a.loc[v,"ndc_difference_safe"].sum()/a.loc[v,"target_oracle_ndc"].sum()))
    return pd.DataFrame(rows)

def deletions(e):
    rows=[]
    for ds in DATASETS:
        z=e[e.dataset.eq(ds)].copy(); q=z.groupby("query_id").risk_increment.mean().sort_values(ascending=False); drop=set(q.head(max(1,int(np.ceil(.01*len(q))))).index); a=z[~z.query_id.isin(drop)];v=a.ndc_difference_safe.notna(); rows.append(dict(dataset=ds,analysis="delete_top_contribution_1pct_queries",deleted_queries=len(drop),risk_increment=a.risk_increment.mean(),safe_rom_ndc_tax=a.loc[v,"ndc_difference_safe"].sum()/a.loc[v,"target_oracle_ndc"].sum()))
    return pd.DataFrame(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument("--work",required=True);p.add_argument("--output",required=True);p.add_argument("--hnswlib",required=True);a=p.parse_args();work=Path(a.work);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    x=load(work);b=budgets(x);c,n=h1(b);e=events(x,b);s=summary(e);ci=bootstrap(e);lo=lobo(e);de=deletions(e)
    save(c,out,"h1_category_variation.csv");save(n,out,"h1_numeric_dispersion.csv");save(pd.DataFrame({"factor":["registered_build_permutation"],"seed_factor_estimable":[False],"reason":["Faiss does not expose a reproducible HNSW construction RNG seed"]}),out,"h1_factor_decomposition.csv")
    compact=e.copy()
    compact["source_build_index"]=compact.source_build.str.extract(r"perm(\d+)")[0].astype(int)
    compact["target_build_index"]=compact.target_build.str.extract(r"perm(\d+)")[0].astype(int)
    compact=compact[["dataset","source_build_index","target_build_index","query_id","source_budget","target_budget","event","failure","reference_failure","risk_increment","ndc_difference_safe","target_oracle_ndc","raw_nonmonotone"]]
    save(compact,out,"h2_transport_events.csv");save(s,out,"h2_risk_cost_summary.csv");save(ci,out,"bootstrap_intervals.csv");save(lo,out,"leave_one_build_out.csv");save(de,out,"contribution_deletion.csv")
    ep=c[["dataset","endpoint_rate","mixed_feasible_censored_rate","all_censored_count","raw_nonmonotone_rate"]];save(ep,out,"endpoint_audit.csv")
    comp=e.groupby(["dataset","source_build","target_build","event"]).size().unstack(fill_value=0)
    for col in EVENTS:
        if col not in comp: comp[col]=0
    comp=comp[EVENTS].div(comp[EVENTS].sum(1),axis=0).reset_index();comp["composition_sum"]=comp[EVENTS].sum(1);save(comp,out,"h2_event_composition.csv")
    old=pd.read_csv(Path(a.hnswlib)/"h2_robustness_corrected.csv");old=old[old.analysis.eq("all_registered")][["dataset","risk_increment","safe_rom_ndc_tax"]].rename(columns={"risk_increment":"hnswlib_risk_increment","safe_rom_ndc_tax":"hnswlib_rom_ndc_tax"}); cross=s.merge(old,on="dataset");cross["faiss_to_hnswlib_risk_ratio"]=cross.incremental_transport_risk/cross.hnswlib_risk_increment;cross["faiss_to_hnswlib_rom_ratio"]=cross.safe_rom_ndc_tax/cross.hnswlib_rom_ndc_tax;save(cross,out,"cross_implementation_comparison.csv")
    g=c.merge(s,on="dataset").merge(ci,on="dataset").merge(lo.groupby("dataset").agg(lobo_min_risk=("risk_increment","min"),lobo_min_rom=("safe_rom_ndc_tax","min")).reset_index(),on="dataset").merge(de,on="dataset");g["h1_gate"]=g.category_variation_rate.gt(0)&g.lobo_min_risk.notna();g["h2_gate"]=((g.risk_ci_low>0)&(g.rom_ci_low>=0))|((g.rom_ci_low>0)&(g.risk_ci_low>=0));g["mechanism_gate"]=g.h1_gate&g.h2_gate&(g.lobo_min_risk>0)&(g.lobo_min_rom>0);save(g,out,"gate_table.csv")
    label="FAISS_HNSW_STRONG_EXTERNAL_REPLICATION_TWO_DATASETS" if g.mechanism_gate.all() else ("FAISS_HNSW_CONDITIONAL_DATA_OPERATOR_REPLICATION" if g.mechanism_gate.any() else "HNSWLIB_SPECIFIC_EFFECT_NOT_REPLICATED_IN_FAISS")
    (out/"analysis_decision.json").write_text(json.dumps({"pilot_label":label,"expand_authorized":bool(g.mechanism_gate.all()),"scope":"REGISTERED_HNSW_IMPLEMENTATIONS" if g.mechanism_gate.all() else "DATA_OPERATOR_CONDITIONAL_GRAPH_ANNS_EVIDENCE","bootstrap":5000,"seed":991},indent=2)+"\n")
    print(json.dumps({"label":label,"expand":bool(g.mechanism_gate.all()),"summary":s.to_dict("records")},indent=2))
if __name__=="__main__":main()
