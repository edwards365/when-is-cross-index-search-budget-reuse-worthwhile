#!/usr/bin/env python3
import glob,os,sys
import numpy as np,pandas as pd

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
sys.path.insert(0,os.path.join(ROOT,'src/rebuild_portability_recovery'))
from m0_m1 import load,DATASETS,SEED
OUT=os.path.join(ROOT,'results/icba_positive_recovery');os.makedirs(OUT,exist_ok=True)
b1=pd.read_csv(os.path.join(OUT,'b1_source_robust.csv'))
b2=pd.read_csv(os.path.join(OUT,'b2_true_target_only.csv'))
old=pd.read_csv(os.path.join(ROOT,'results/rebuild_portability_recovery/m2_m3_looh.csv'))
b3=old[old.method=='M2'].copy(); b3['method']='B3'; b3['outer_label']='OUTER_BUILD_NOT_CERTIFIED'; b3['evidence_label']='PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION'; b3['used_history_donors']=True; b3['used_target_evaluation_for_calibration']=False
b3.to_csv(os.path.join(OUT,'b3_history_assisted.csv'),index=False)

keys=['dataset','source_build','target_build','k']
cmp=b2.merge(b3,on=keys,suffixes=('_b2','_b3'))
cmp['b3_minus_b2_saving_fixed']=cmp.mean_ndc_saving_vs_fixed-cmp.ndc_saving_vs_fixed
cmp['b3_online_ndc']=cmp.fixed_safe_mean_ndc*(1-cmp.mean_ndc_saving_vs_fixed)
cmp['b3_vs_b2_online_reduction']=1-cmp.b3_online_ndc/cmp.mean_ndc
cmp['both_gate_s_pass']=(cmp.gate_s_b2=='PASS')&(cmp.gate_s_b3=='PASS')
cmp.to_csv(os.path.join(OUT,'paired_method_comparison.csv'),index=False)

# Expected exhaustive 12-budget search NDC for a uniform without-replacement sentinel sample.
cal=[]
for dataset in DATASETS:
    for p in sorted(glob.glob(os.path.join(ROOT,'results/cross_index/g1/main/hnswlib',f'{dataset}__*.csv.gz'))):
        name=os.path.basename(p).replace('.csv.gz',''); d,b,q,X,y,c,ndc=load(p)
        sentinel=sorted(set(d[d.query_id.isin(range(1000))].query_id.astype(int))) # overwritten below
        import json
        split=json.load(open(os.path.join(ROOT,'manifests/icba_micro_closure_query_split.json')))
        sentinel=sorted(map(int,split['datasets'][dataset]['sentinel_query_ids']))
        full=sum(ndc[(qid,budget)] for qid in sentinel for budget in b)
        for k in (32,64,128,256): cal.append({'dataset':dataset,'target_build':name,'k':k,'sentinel_truth_count':k,'query_budget_evaluations':12*k,'expected_calibration_search_ndc':full*k/256.,'ground_truth_generation_cost':'NOT_ESTIMABLE','truth_storage_read_cost':'NOT_ESTIMABLE','certificate_compute_cost':'NOT_ESTIMABLE','evidence_label':'EXPLORATORY_DESIGN'})
cal=pd.DataFrame(cal);cal.to_csv(os.path.join(OUT,'calibration_cost.csv'),index=False)

# Search-side cost and break-even; external truth/training costs remain unknown.
cost=[]
for _,r in cmp.iterrows():
    z=cal[(cal.dataset==r.dataset)&(cal.target_build==r.target_build)&(cal.k==r.k)].iloc[0]
    b1n=float(b1[(b1.dataset==r.dataset)&(b1.source_build==r.source_build)&(b1.target_build==r.target_build)].mean_ndc.iloc[0])
    for method,online in [('B2',r.mean_ndc),('B3',r.b3_online_ndc)]:
        denom_b1=b1n-online; denom_b6=r.fixed_safe_mean_ndc-online
        be_b1=z.expected_calibration_search_ndc/denom_b1 if denom_b1>0 else np.inf
        be_b6=z.expected_calibration_search_ndc/denom_b6 if denom_b6>0 else np.inf
        for N in (1000,10000,100000,1000000,10000000):
            cost.append({'method':method,'dataset':r.dataset,'source_build':r.source_build,'target_build':r.target_build,'k':r.k,'workload_N':N,'online_search_ndc_total':N*online,'calibration_search_ndc':z.expected_calibration_search_ndc,'search_side_total_ndc':N*online+z.expected_calibration_search_ndc,'break_even_vs_b1_N':be_b1,'break_even_vs_b6_N':be_b6,'break_even_vs_b5_N':'NOT_ESTIMABLE','ground_truth_generation_cost':'NOT_ESTIMABLE','full_retrain_cost':'NOT_ESTIMABLE','evidence_label':'EXPLORATORY_DESIGN'})
pd.DataFrame(cost).to_csv(os.path.join(OUT,'break_even.csv'),index=False)

# Target-build cluster bootstrap. Resample the nine target builds, retaining all source directions.
rng=np.random.default_rng(SEED); boots=[]
base=cmp[cmp.k==256].copy()
base=base.merge(b1[['dataset','source_build','target_build','mean_ndc']],on=['dataset','source_build','target_build'],suffixes=('','_b1'))
for dataset,g in base.groupby('dataset'):
    targets=sorted(g.target_build.unique())
    effects={'B2_vs_B1':1-g.mean_ndc/g.mean_ndc_b1,'B3_vs_B2':1-g.b3_online_ndc/g.mean_ndc}
    for contrast,v in effects.items():
        gg=g.assign(effect=np.asarray(v))
        vals=[]
        for _ in range(5000):
            chosen=rng.choice(targets,size=len(targets),replace=True)
            vals.append(float(np.mean([gg[gg.target_build==t].effect.mean() for t in chosen])))
        boots.append({'dataset':dataset,'contrast':contrast,'bootstrap_reps':5000,'target_build_clusters':len(targets),'mean_effect':float(gg.effect.mean()),'ci95_lower':float(np.quantile(vals,.025)),'ci95_upper':float(np.quantile(vals,.975)),'outer_build_certified':False,'evidence_label':'DESIGN_STAGE_BUILD_CLUSTER_BOOTSTRAP'})
pd.DataFrame(boots).to_csv(os.path.join(OUT,'build_cluster_bootstrap.csv'),index=False)
print(pd.DataFrame(boots).to_string(index=False))
