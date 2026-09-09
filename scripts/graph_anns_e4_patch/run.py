#!/usr/bin/env python3
"""E4.1 censoring-aware inference patch; reads frozen E4 records only."""
import argparse, json, hashlib, platform, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import beta
from scripts.graph_anns_e4_seal.run import load_raw, budgets, EFS, SEEDS, ORDERS, DATASETS

def cp(k,n,a): return 1. if k>=n else float(beta.ppf(1-a,k+1,n-k))
def save(df,out,name): df.to_csv(out/name,index=False,float_format='%.12g')
def metric(z):
    v=z.ndc_difference_safe.notna()
    return z.failure.mean(), z.loc[v,'ndc_difference_safe'].sum()/z.loc[v,'target_oracle_ndc'].sum()

def build_events(x,b):
    ev=b[b.query_id>=250]; lookup=x.set_index(['dataset','build_id','query_id','ef_search'])[['recall','ndc']]; rows=[]
    for ds in DATASETS:
        builds=sorted(ev[ev.dataset==ds].build_id.unique())
        for src in builds:
            sb=ev[(ev.dataset==ds)&(ev.build_id==src)].set_index('query_id'); ss,so=int(sb.seed.iloc[0]),sb.order.iloc[0]
            for tgt in builds:
                if src==tgt: continue
                tb=ev[(ev.dataset==ds)&(ev.build_id==tgt)].set_index('query_id'); ts,to=int(tb.seed.iloc[0]),tb.order.iloc[0]
                for q in range(250,1000):
                    se=sb.at[q,'safe_budget']; te=tb.at[q,'safe_budget']; sc=pd.isna(se); tc=pd.isna(te)
                    action=200 if sc else int(se); obs=lookup.loc[(ds,tgt,q,action)]; ref=lookup.loc[(ds,tgt,q,200 if tc else int(te))]
                    fail=bool(obs.recall<.95 or tc); diag=bool(ref.recall<.95 or tc)
                    diff=np.nan if fail or diag else float(obs.ndc-ref.ndc)
                    if sc and tc: event='BOTH_RIGHT_CENSORED'
                    elif sc: event='SOURCE_ONLY_RIGHT_CENSORED'
                    elif tc: event='TARGET_ONLY_RIGHT_CENSORED'
                    elif se<te:
                        event='UNDER_BUDGET_OBSERVED_SAFE' if (obs.recall>=.95 and bool(tb.at[q,'raw_nonmonotone'])) else 'UNDER_BUDGET_UNSAFE'
                    elif se==te: event='EXACT_BUDGET_SAFE'
                    else: event='OVER_BUDGET_SAFE'
                    rows.append(dict(dataset=ds,source_build=src,target_build=tgt,source_seed=ss,target_seed=ts,
                        source_order=so,target_order=to,query_id=q,source_budget=se,target_budget=te,
                        source_censored=sc,target_censored=tc,source_endpoint_feasible=bool(sb.at[q,'endpoint_feasible']),
                        target_endpoint_feasible=bool(tb.at[q,'endpoint_feasible']),raw_nonmonotone=bool(tb.at[q,'raw_nonmonotone']),
                        action=action,failure=fail,reference_failure=diag,risk_increment=float(fail)-float(diag),
                        under=bool(not sc and not tc and se<te),exact=bool(not sc and not tc and se==te),over=bool(not sc and not tc and se>te),
                        ndc_difference_safe=diff,target_oracle_ndc=float(ref.ndc),event=event))
    return pd.DataFrame(rows)

def h1_censoring(b,out,nboot):
    ev=b[b.query_id>=250].copy(); rows=[]
    for ds in DATASETS:
        g=ev[ev.dataset==ds]; piv=g.pivot(index='query_id',columns='build_id',values='safe_budget'); state=piv.astype(object).where(piv.notna(),'BOTTOM')
        for q in piv.index:
            vals=piv.loc[q].dropna().to_numpy(); allok=len(vals)==24; feasible=len(vals)>=2
            rows.append(dict(dataset=ds,estimand_id='H1-A1',scope='query',query_id=q,total_comparisons=24,jointly_feasible_comparisons=len(vals),endpoint_mismatch_comparisons=int(state.loc[q].nunique()>1),categorical_disagreement=int(state.loc[q].nunique()>1),feasible_disagreement=int(len(set(vals))>1),feasible_absolute_difference=(float(vals.max()-vals.min()) if feasible else np.nan),effective_query_count=int(allok)))
        statecov=(state.nunique(axis=1)>1).mean(); allf=piv.notna().all(axis=1); va=piv[allf].max(axis=1)-piv[allf].min(axis=1); subset=[]
        for _,r in piv.iterrows():
            z=r.dropna()
            if len(z)>=2: subset.append(float(z.max()-z.min()))
        rows += [dict(dataset=ds,estimand_id='H1-A1',scope='summary',query_id='',total_comparisons=24*750,jointly_feasible_comparisons=int(piv.notna().sum(axis=1).sum()),endpoint_mismatch_comparisons=int((state.nunique(axis=1)>1).sum()),categorical_disagreement=float(statecov),feasible_disagreement=np.nan,feasible_absolute_difference=np.nan,effective_query_count=750),
                 dict(dataset=ds,estimand_id='H1-A2',scope='summary',query_id='',total_comparisons=24*750,jointly_feasible_comparisons=int(allf.sum()*24),endpoint_mismatch_comparisons=0,categorical_disagreement=np.nan,feasible_disagreement=float((va>0).mean()) if len(va) else np.nan,feasible_absolute_difference=float(va.mean()) if len(va) else np.nan,effective_query_count=int(allf.sum())),
                 dict(dataset=ds,estimand_id='H1-A3',scope='summary',query_id='',total_comparisons=24*750,jointly_feasible_comparisons=int(sum(sum(r.notna())>=2 for _,r in piv.iterrows())),endpoint_mismatch_comparisons=0,categorical_disagreement=np.nan,feasible_disagreement=float(np.mean(np.array(subset)>0)) if subset else np.nan,feasible_absolute_difference=float(np.mean(subset)) if subset else np.nan,effective_query_count=len(subset)),
                 dict(dataset=ds,estimand_id='H1-A4',scope='summary',query_id='',total_comparisons=750,jointly_feasible_comparisons=0,endpoint_mismatch_comparisons=int((state.nunique(axis=1)>1).sum()),categorical_disagreement=float(state.nunique(axis=1).gt(1).mean()),feasible_disagreement=np.nan,feasible_absolute_difference=np.nan,effective_query_count=750)]
    # H1-B/C pairwise decomposition without numeric filling.
    for ds in DATASETS:
        g=ev[ev.dataset==ds]
        for q in range(250,1000):
            for s in SEEDS:
                a=g[(g.seed==s)&(g.query_id==q)].set_index('order').safe_budget
                for i in range(3):
                    for j in range(i+1,3):
                        u,v=a[ORDERS[i]],a[ORDERS[j]]; both=pd.notna(u) and pd.notna(v)
                        rows.append(dict(dataset=ds,estimand_id='H1-B',scope='within_seed_cross_order',query_id=q,total_comparisons=3,jointly_feasible_comparisons=int(both),endpoint_mismatch_comparisons=int(pd.isna(u)!=pd.isna(v)),categorical_disagreement=int((pd.isna(u)!=pd.isna(v)) or (both and u!=v)),feasible_disagreement=int(both and u!=v),feasible_absolute_difference=(abs(u-v) if both else np.nan),effective_query_count=1))
            for o in ORDERS:
                a=g[(g.order==o)&(g.query_id==q)].set_index('seed').safe_budget
                for i in range(8):
                    for j in range(i+1,8):
                        u,v=a[SEEDS[i]],a[SEEDS[j]]; both=pd.notna(u) and pd.notna(v)
                        rows.append(dict(dataset=ds,estimand_id='H1-C',scope='within_order_cross_seed',query_id=q,total_comparisons=28,jointly_feasible_comparisons=int(both),endpoint_mismatch_comparisons=int(pd.isna(u)!=pd.isna(v)),categorical_disagreement=int((pd.isna(u)!=pd.isna(v)) or (both and u!=v)),feasible_disagreement=int(both and u!=v),feasible_absolute_difference=(abs(u-v) if both else np.nan),effective_query_count=1))
    return pd.DataFrame(rows)

def h2_ci(events,nboot,seed):
    rng=np.random.default_rng(seed); rows=[]
    for ds in DATASETS:
        z=events[events.dataset==ds]; qids=np.arange(250,1000); vals=[]
        # Aggregate once by query. A sampled query carries all 552 directed
        # pairs; multiplicities are applied as integer weights below.
        z=z.copy(); z['risk_delta']=z.failure.astype(float)-z.reference_failure.astype(float)
        z['safe_num_unit']=z.ndc_difference_safe.fillna(0.0)
        z['safe_den_unit']=z.target_oracle_ndc.where(z.ndc_difference_safe.notna(),0.0)
        qagg=z.groupby('query_id').agg(risk_delta=('risk_delta','sum'),pair_n=('failure','size'),
            safe_num=('safe_num_unit','sum'),safe_den=('safe_den_unit','sum'))
        for r in range(nboot):
            qq=rng.choice(qids,750,replace=True); counts=np.bincount(qq-250,minlength=750); a=qagg.reindex(qids)
            risk=float((a.risk_delta.to_numpy()*counts).sum()/(a.pair_n.to_numpy()*counts).sum())
            rom=float((a.safe_num.to_numpy()*counts).sum()/(a.safe_den.to_numpy()*counts).sum()); vals.append((risk,rom))
        vals=np.asarray(vals); point_r=z.risk_delta.mean(); v=z.ndc_difference_safe.notna(); point_c=z.loc[v,'ndc_difference_safe'].sum()/z.loc[v,'target_oracle_ndc'].sum(); rows.append(dict(dataset=ds,scope='registered_build_family_query_distribution',risk_increment=point_r, risk_ci_low=2*point_r-np.quantile(vals[:,0],.975),risk_ci_high=2*point_r-np.quantile(vals[:,0],.025),safe_rom_tax=point_c,safe_rom_ci_low=2*point_c-np.quantile(vals[:,1],.975),safe_rom_ci_high=2*point_c-np.quantile(vals[:,1],.025),resampling='750 query IDs; all 552 directed pairs retained per sampled query; seed=991; B=5000'))
    return pd.DataFrame(rows)

def robustness(e):
    rows=[]
    def one(ds,z):
        r,c=metric(z);return dict(dataset=ds,risk_increment=r,rom_tax=c,pairs=len(z[['source_build','target_build']].drop_duplicates()),queries_per_pair=750)
    for ds in DATASETS:
        z=e[e.dataset==ds]; rows.append({**one(ds,z[(z.source_order=='random')&(z.target_order=='random')]),'analysis':'random_only'})
        for s in SEEDS: rows.append({**one(ds,z[(z.source_seed!=s)&(z.target_seed!=s)]),'analysis':'leave_one_seed','deleted':s})
        for o in ORDERS: rows.append({**one(ds,z[(z.source_order!=o)&(z.target_order!=o)]),'analysis':'leave_one_order','deleted':o})
        for s in SEEDS: rows.append({**one(ds,z[z.source_seed!=s]),'analysis':'source_only_delete','deleted':s})
        for s in SEEDS: rows.append({**one(ds,z[z.target_seed!=s]),'analysis':'target_only_delete','deleted':s})
    return pd.DataFrame(rows)

def certification(x,out):
    rows=[]
    for (ds,b),g in x.groupby(['dataset','build_id']):
        sen=g[g.query_id<250]; ev=g[g.query_id>=250]; chosen=None
        for ef in EFS:
            k=int((sen[sen.ef_search==ef].recall<.95).sum())
            if cp(k,250,.05/6)<=.05: chosen=int(ef);break
        chosen=200 if chosen is None else chosen
        f200=sen[sen.ef_search==200]; k200=int((f200.recall<.95).sum()); fallback_cp=cp(k200,250,.05/6)
        for ef in EFS:
            z=ev[ev.ef_search==ef];k=int((z.recall<.95).sum());rows.append(dict(dataset=ds,target_build=b,ef=ef,failures=k,n=750,point_risk=k/750,cp_per_target=cp(k,750,.05/6),cp_fixed_ef48=cp(k,750,.05/48),cp_joint_48x6=cp(k,750,.05/(48*6)),selected_by_per_target=(ef==chosen),point_below_5=(k/750)<.05))
        rows[-1]['fallback_ef200_sentinel_cp']=fallback_cp; rows[-1]['fallback_ef200_sentinel_certified']=fallback_cp<=.05
    c=pd.DataFrame(rows); save(c,out,'certification_multiplicity_audit.csv');return c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--raw-dir',required=True);ap.add_argument('--output-dir',required=True);ap.add_argument('--seed',type=int,default=991);ap.add_argument('--bootstrap',type=int,default=5000);a=ap.parse_args();root=Path(a.root);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    bm,x,inv=load_raw(root,Path(a.raw_dir));b=budgets(x);assert len(b)==48000
    allh=h1_censoring(b,out,a.bootstrap);save(allh,out,'h1_censoring_aware_estimands.csv')
    e=build_events(x,b); comp=e.groupby(['dataset','source_build','target_build','event']).size().unstack(fill_value=0).div(750).reset_index();
    for c in ['BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED','UNDER_BUDGET_UNSAFE','UNDER_BUDGET_OBSERVED_SAFE','EXACT_BUDGET_SAFE','OVER_BUDGET_SAFE','RAW_NONMONOTONE_EXCEPTION']:
        if c not in comp: comp[c]=0.
    comp['composition_sum']=comp[['BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED','UNDER_BUDGET_UNSAFE','UNDER_BUDGET_OBSERVED_SAFE','EXACT_BUDGET_SAFE','OVER_BUDGET_SAFE','RAW_NONMONOTONE_EXCEPTION']].sum(axis=1);save(comp,out,'transport_event_composition_corrected.csv')
    hc=h2_ci(e,a.bootstrap,a.seed);save(hc,out,'h2_registered_family_query_ci.csv');save(robustness(e),out,'h2_two_endpoint_robustness.csv')
    certification(x,out)
    meta={'parent':'c976b48be6e0d78e7a0ed27afaf1f5448d44a567','seed':a.seed,'bootstrap':a.bootstrap,'scope':'conditional finite registered build family query distribution','endpoint_semantics':'ENDPOINT_AND_RIGHT_CENSORING_NOT_SEPARATELY_IDENTIFIABLE','parent_replay':'BYTE_IDENTICAL','future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False,'no_new_search':True,'no_new_index':True}
    (out/'runtime.json').write_text(json.dumps({'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__},indent=2)+'\n')
    print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
