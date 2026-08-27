#!/usr/bin/env python3
"""Unified ICBA analysis using only frozen Cross-Index training/design records."""
import csv, gzip, glob, json
from pathlib import Path
import numpy as np
from scipy.stats import kendalltau
from rcrs_fast_theory import safe_monotone_majorant
from rcrs_signal_risk_dp import risk_monotone_dp, aware_risk_optimum

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
BASE=ROOT/'results/cross_index/g1'; OUT=ROOT/'results/theory_generalization'; OUT.mkdir(exist_ok=True)
GRID=np.array([10,16,24,32,48,64,96,128,192,256,384,512]); RNG=np.random.default_rng(991)
DELTA=(0.0,.01,.05,.10); BOOT=5000

def write(name,rows):
    with open(OUT/name,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

def load():
    graphs={}
    for idx in ('hnswlib','faiss','vamana'):
        for p in glob.glob(str(BASE/'main'/idx/'*.csv.gz')):
            with gzip.open(p,'rt',newline='') as f: rows=list(csv.DictReader(f))
            r=rows[0]; key=(idx,r['dataset'],int(r.get('seed',r.get('graph_seed'))),r.get('history',r.get('insertion_order')))
            a=np.zeros((1000,len(GRID),2),dtype=float)
            for z in rows:
                q=int(z['query_id']); b=int(z.get('budget',z.get('ef_search'))); j=int(np.where(GRID==b)[0][0])
                a[q,j]=float(z['recall_at_10']),float(z['exact_ndc'])
            graphs[key]=a
    return graphs

def stable(a):
    out=np.full(len(a),1024,dtype=int)
    for q in range(len(a)):
        for j,b in enumerate(GRID):
            if np.all(a[q,j:,0]>=.9): out[q]=b; break
    return out

def fixed_j(a):
    return next((j for j in range(len(GRID)) if a[:250,j,0].mean()>=.9),len(GRID)-1)

def ci(v):
    v=np.asarray(v,float); n=len(v); vals=[]
    for _ in range(10):
        ids=RNG.integers(0,n,size=(BOOT//10,n)); vals.append(v[ids].mean(1))
    z=np.concatenate(vals); return float(np.quantile(z,.025)),float(np.quantile(z,.975))

def selected_cost(target,q,budget):
    jj=np.searchsorted(GRID,np.minimum(budget,GRID[-1])); return target[q,jj,1]

G=load(); B={k:stable(v) for k,v in G.items()}
mono_old={(r['index'],r['dataset'],int(r['source_seed']),r['source_history'],int(r['target_seed']),r['target_history']):r
          for r in csv.DictReader(open(ROOT/'results/rcrs_fast/monotone_tax.csv'))}
unified=[]; front=[]; invout=[]; censor=[]; values=[]
for idx in ('hnswlib','faiss','vamana'):
  for ds in sorted({k[1] for k in G if k[0]==idx}):
    keys=sorted(k for k in G if k[0]==idx and k[1]==ds)
    for s in keys:
      for t in keys:
        if s==t: continue
        q=np.arange(250,1000); x=B[s][q]; y=B[t][q]; tar=G[t]; fj=fixed_j(tar)
        fixed=tar[q,fj,1]; fixed_mean=float(fixed.mean()); cens=y>GRID[-1]; obs=~cens
        oracle=selected_cost(tar,q,y); oracle_mean=float(oracle[obs].mean()) if obs.any() else float('nan')
        # Arbitrary source-summary safe envelope and monotone refinement, conservatively clipped only for observed targets.
        envmap={v:int(y[x==v].max()) for v in np.unique(x)}; env=np.array([envmap[v] for v in x])
        mon,_=safe_monotone_majorant(x,y)
        envcost=selected_cost(tar,q,env); moncost=selected_cost(tar,q,mon)
        envtax=(envcost-oracle)/fixed; montax=(moncost-oracle)/fixed
        lo,hi=ci(montax[obs]) if obs.any() else (float('nan'),float('nan'))
        change=float(np.mean(x!=y)); tau=float(kendalltau(x,y,nan_policy='omit').statistic); rankinv=(1-tau)/2 if np.isfinite(tau) else float('nan')
        old=mono_old[(idx,ds,s[2],s[3],t[2],t[3])]; bound=float(old['matching_budget_gap_bound'])
        exact=float(old['exact_monotone_ndc_tax']); tight=bound/(float(np.sum(np.maximum(mon-y,0))) or np.nan)
        category='same_order_cross_seed' if s[3]==t[3] else 'cross_order'
        common={'index':idx,'dataset':ds,'source_seed':s[2],'source_history':s[3],'target_seed':t[2],'target_history':t[3],'category':category}
        unified.append(common|{'n':len(q),'oracle_headroom_fraction':(fixed_mean-oracle_mean)/fixed_mean,'budget_change_rate':change,'rank_inversion':rankinv,'information_coarsening_tax_fraction_observed':float(envtax[obs].mean()),'exact_safe_monotone_tax_fraction_observed':float(montax[obs].mean()),'monotone_tax_ci_low':lo,'monotone_tax_ci_high':hi,'matching_budget_gap_bound':bound,'lower_bound_tightness_budget_gap':tight,'right_censoring_rate':float(cens.mean()),'price_of_index_blindness':(fixed_mean-oracle_mean)/oracle_mean,'bootstrap':BOOT,'bootstrap_seed':991,'evidence':'FROZEN_TRAIN_DESIGN_EMPIRICAL'})
        invout.append(common|{'rank_inversion':rankinv,'matching_budget_gap_bound':bound,'exact_monotone_ndc_tax_fraction':exact,'lower_bound_tightness_budget_gap':tight,'theorem_status':'LOWER_BOUND_PROOF_SKETCH_ONLY_COMPUTATIONALLY_CHECKED'})
        censor.append(common|{'n':len(q),'observed_n':int(obs.sum()),'right_censored_n':int(cens.sum()),'right_censoring_rate':float(cens.mean()),'observed_only_oracle_mean_ndc':oracle_mean,'conservative_safe_cost':'NOT_IDENTIFIED_ABOVE_FROZEN_GRID' if cens.any() else oracle_mean,'oracle_cost_interval_lower':float(oracle.mean()),'oracle_cost_interval_upper':'UNBOUNDED_WITHOUT_COST_ASSUMPTION' if cens.any() else float(oracle.mean())})
        values.append(common|{'fixed_mean_ndc':fixed_mean,'oracle_observed_mean_ndc':oracle_mean,'source_envelope_clipped_mean_ndc':float(envcost.mean()),'monotone_clipped_mean_ndc':float(moncost.mean()),'censoring_qualification':'CLIPPED_LOWER_BOUND' if cens.any() else 'EXACT_ON_GRID'})
        # Exact finite-grid risk optimization. Right-censored units are mandatory failures.
        cost=tar[q,:,1]
        for d in DELTA:
            try:
                rr=risk_monotone_dp(x,y,cost,GRID,d); aware=aware_risk_optimum(y,cost,GRID,d)
                status='EXACT' if not cens.any() else 'EXACT_WITH_CENSORED_AS_MANDATORY_FAILURE'
                front.append(common|{'delta':d,'monotone_mean_ndc':rr['cost'],'oracle_aware_mean_ndc':aware,'fixed_mean_ndc':fixed_mean,'monotone_over_fixed':rr['cost']/fixed_mean,'oracle_over_fixed':aware/fixed_mean,'failures':rr['failures'],'failure_rate':rr['failure_rate'],'right_censoring_rate':float(cens.mean()),'status':status})
            except RuntimeError:
                front.append(common|{'delta':d,'monotone_mean_ndc':'NOT_FEASIBLE','oracle_aware_mean_ndc':'NOT_FEASIBLE','fixed_mean_ndc':fixed_mean,'monotone_over_fixed':'NOT_FEASIBLE','oracle_over_fixed':'NOT_FEASIBLE','failures':'NOT_FEASIBLE','failure_rate':'NOT_FEASIBLE','right_censoring_rate':float(cens.mean()),'status':'INFEASIBLE_RIGHT_CENSORING_OR_RISK_BUDGET'})

write('unified_theory_table.csv',unified); write('risk_cost_frontier.csv',front); write('inversion_bounds.csv',invout); write('censoring_analysis.csv',censor); write('information_class_values.csv',values)
summary={'graphs':len(G),'raw_rows':len(G)*1000*len(GRID),'source_target_pairs':len(unified),'risk_rows':len(front),'bootstrap':BOOT,'seed':991,'validation_dev_accessed':False,'formal_test_accessed':False,'split':'frozen design-eval queries 250:1000','notes':['NDC is implementation-local','right-censored safe cost above grid is not identified','T4 remains proof-sketch-only']}
(OUT/'unified_analysis_summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
