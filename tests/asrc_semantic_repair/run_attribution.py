#!/usr/bin/env python3
import os,sys,glob,json,hashlib
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
sys.path.insert(0,os.path.join(ROOT,'src/rebuild_portability_recovery'))
sys.path.insert(0,os.path.join(ROOT,'src/asrc_semantic_repair'))
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
OUT=os.path.join(ROOT,'results/asrc_semantic_repair');os.makedirs(OUT,exist_ok=True)
SPLIT=json.load(open(os.path.join(ROOT,'manifests/graph_anns_positive_crossfit_split.json')))
NS=(80,128,250); rows=[]; diag=[]

def ids_for(dataset,cycle,role,n):
 fold=SPLIT['datasets'][dataset]['cycles'][str(cycle)][role]
 ids=np.asarray(SPLIT['datasets'][dataset]['folds'][fold],int)
 # deterministic role-local ordering, independent of outcomes
 seed=SEED+cycle*1009+sum(ord(x) for x in dataset+role)
 return ids[np.random.default_rng(seed).permutation(len(ids))[:n]]

for ds in DATASETS:
 paths=sorted(glob.glob(os.path.join(ROOT,'results/cross_index/g1/main/hnswlib',f'{ds}__*.csv.gz')))
 builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths}
 for cycle in range(4):
  train_ids=ids_for(ds,cycle,'source_train',250);eval_ids=ids_for(ds,cycle,'target_evaluation',250)
  models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};tr=np.asarray([pos[int(v)] for v in train_ids]);m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[tr],y[tr]);models[name]=m
  for sname,model in models.items():
   sd,sb,sq,sX,sy,sc,sndc=builds[sname];spos={int(v):i for i,v in enumerate(sq)}
   for tname,(td,tb,tq,tX,ty,tc,tndc) in builds.items():
    if sname==tname:continue
    tpos={int(v):i for i,v in enumerate(tq)};raw_s=model.predict(sX).astype(int);raw_t=model.predict(tX).astype(int);ev=np.asarray([tpos[int(v)] for v in eval_ids]);fixed=np.asarray([tndc[(int(tq[i]),tb[-1])] for i in ev],float)
    for n in NS:
     source_ids=ids_for(ds,cycle,'source_calibration',n)
     for mode in ('paired','disjoint'):
      sent_ids=source_ids if mode=='paired' else ids_for(ds,cycle,'target_sentinel',n)
      ca=np.asarray([spos[int(v)] for v in source_ids]);si=np.asarray([tpos[int(v)] for v in sent_ids])
      feasible_ca=ca[~sc[ca]];feasible_si=si[~tc[si]]
      sh1=int(max(0,np.max(sy[feasible_ca]-raw_s[feasible_ca]))) if len(feasible_ca) else 11
      sh2=int(max(0,np.max(ty[feasible_si]-raw_t[feasible_si]))) if len(feasible_si) else 11
      a1=np.minimum(raw_t+sh1,11);a2=np.minimum(raw_t+sh2,11);za1,zr1,_=safety_events(a1[ev],ty[ev],tc[ev]);za2,zr2,_=safety_events(a2[ev],ty[ev],tc[ev])
      c1=np.asarray([tndc[(int(tq[i]),tb[int(a1[i])])] for i in ev]);c2=np.asarray([tndc[(int(tq[i]),tb[int(a2[i])])] for i in ev])
      max1=int(source_ids[np.argmax(sy[ca]-raw_s[ca])]);max2=int(sent_ids[np.argmax(ty[si]-raw_t[si])])
      common={'dataset':ds,'cycle':cycle,'source_build':sname,'target_build':tname,'mode':mode,'n_cal':n,'n_eval':len(ev),'evidence_label':'EXPLORATORY_REPAIR'}
      rows.append(dict(common,b1_shift=sh1,b2_shift=sh2,b1_abs_risk=za1.mean(),b2_abs_risk=za2.mean(),b1_rec_risk=zr1.mean(),b2_rec_risk=zr2.mean(),endpoint_infeasible_rate=tc[ev].mean(),b1_mean_ndc=c1.mean(),b2_mean_ndc=c2.mean(),b2_minus_b1_ndc=c2.mean()-c1.mean(),b2_improvement=1-c2.mean()/c1.mean(),b1_p95_ndc=np.quantile(c1,.95),b2_p95_ndc=np.quantile(c2,.95),fixed_mean_ndc=fixed.mean(),b1_max_query=max1,b2_max_query=max2,b1_cal_censored=int(sc[ca].sum()),b2_cal_censored=int(tc[si].sum())))
      # Remove the outcome-determined maximum only as a registered sensitivity analysis.
      ca2=ca[sy[ca]-raw_s[ca] < np.max(sy[ca]-raw_s[ca])];si2=si[ty[si]-raw_t[si] < np.max(ty[si]-raw_t[si])]
      dsh1=int(max(0,np.max(sy[ca2]-raw_s[ca2]))) if len(ca2) else 11;dsh2=int(max(0,np.max(ty[si2]-raw_t[si2]))) if len(si2) else 11
      diag.append(dict(common,b1_shift=sh1,b2_shift=sh2,b1_shift_dropmax=dsh1,b2_shift_dropmax=dsh2,b1_max_query=max1,b2_max_query=max2))

raw=pd.DataFrame(rows);raw.to_csv(OUT+'/attribution_cells.csv.gz',index=False,compression='gzip');pd.DataFrame(diag).to_csv(OUT+'/max_residual_diagnostics.csv',index=False)
rng=np.random.default_rng(SEED); cal=[]; reuse=[]
for (ds,mode,n),g in raw.groupby(['dataset','mode','n_cal']):
 v=g.groupby('target_build').b2_improvement.mean().to_numpy();sim=v[rng.integers(0,len(v),(5000,len(v)))].mean(1)
 cal.append({'dataset':ds,'mode':mode,'n_cal':n,'point':v.mean(),'ci_low':np.quantile(sim,.025),'ci_high':np.quantile(sim,.975),'positive_fraction':np.mean(sim>0),'bootstrap':5000,'cluster':'target_build','evidence_label':'EXPLORATORY_REPAIR'})
for (ds,n),g in raw.groupby(['dataset','n_cal']):
 p=g[g['mode']=='paired'].groupby('target_build').b2_improvement.mean();d=g[g['mode']=='disjoint'].groupby('target_build').b2_improvement.mean();v=(p-d).to_numpy();sim=v[rng.integers(0,len(v),(5000,len(v)))].mean(1)
 reuse.append({'dataset':ds,'n_cal':n,'paired_minus_disjoint':v.mean(),'ci_low':np.quantile(sim,.025),'ci_high':np.quantile(sim,.975),'direction_stability':np.mean(sim*np.sign(v.mean())>0),'bootstrap':5000,'cluster':'target_build','evidence_label':'EXPLORATORY_REPAIR'})
pd.DataFrame(cal).to_csv(OUT+'/calibration_size_effect.csv',index=False);pd.DataFrame(reuse).to_csv(OUT+'/query_reuse_effect.csv',index=False)
legacy=pd.DataFrame([{'legacy_commit':'81299c9','setting':'paired-query replay / about 750 source calibration queries','role':'DESCRIPTIVE_ANCHOR_ONLY','direct_causal_comparison':False,'reason':'sample size and query reuse differ jointly','evidence_label':'LEGACY'}]);legacy.to_csv(OUT+'/legacy_anchor_comparison.csv',index=False)
print(pd.DataFrame(cal).to_string(index=False));print(pd.DataFrame(reuse).to_string(index=False))
