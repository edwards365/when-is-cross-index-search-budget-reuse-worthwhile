#!/usr/bin/env python3
import os,sys,glob,json,math
from collections import defaultdict
import numpy as np,pandas as pd
from scipy.stats import beta,t as student_t
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));sys.path[:0]=[os.path.join(ROOT,'src/rebuild_portability_recovery'),os.path.join(ROOT,'src/asrc_semantic_repair')]
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
OUT=os.path.join(ROOT,'results/asrc_semantic_repair');os.makedirs(OUT,exist_ok=True)
SPLIT=json.load(open(os.path.join(ROOT,'manifests/graph_anns_positive_crossfit_split.json')))
ALPHA=.05;DELTA=.05;AJ=ALPHA/3;STAGES=(80,128,250);REPS=500;N0=100000
def cp(f,n,a=.05): return 1. if f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[idx],y[idx]);return m
def select(raw,y,c,idx):
 cert=[]
 for sh in range(11,-1,-1):
  za,_,_=safety_events(np.minimum(raw[idx]+sh,11),y[idx],c[idx]);ok=cp(int(za.sum()),len(idx),AJ)<=DELTA
  if ok:cert.append(sh)
  else:break
 return min(cert) if cert else None
def metrics(raw,sh,y,c,ndc,q,b,idx):
 alloc=np.minimum(raw+sh,11);za,zr,ce=safety_events(alloc[idx],y[idx],c[idx]);cost=np.asarray([ndc[(int(q[i]),b[int(alloc[i])])] for i in idx],float)
 return {'abs_fail':int(za.sum()),'rec_fail':int(zr.sum()),'endpoint_fail':int(ce.sum()),'n':len(idx),'mean_ndc':cost.mean(),'p50_ndc':np.median(cost),'p95_ndc':np.quantile(cost,.95),'endpoint_fraction':ce.mean(),'alloc':alloc,'cost':cost}

rm=[];reps=defaultdict(list)
for ds in DATASETS:
 paths=sorted(glob.glob(os.path.join(ROOT,'results/cross_index/g1/main/hnswlib',f'{ds}__*.csv.gz')));builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths};folds={k:np.asarray(v,int) for k,v in SPLIT['datasets'][ds]['folds'].items()}
 for cycle in range(4):
  roles=SPLIT['datasets'][ds]['cycles'][str(cycle)];trids=folds[roles['source_train']];caids=folds[roles['source_calibration']];seids=folds[roles['target_sentinel']];evids=folds[roles['target_evaluation']]
  models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};tr=np.asarray([pos[int(v)] for v in trids]);models[name]=fit(X,y,tr)
  for sname,model in models.items():
   sd,sb,sq,sX,sy,sc,sndc=builds[sname];spos={int(v):i for i,v in enumerate(sq)};sca=np.asarray([spos[int(v)] for v in caids]);sraw=model.predict(sX).astype(int)
   feasible=sca[~sc[sca]];max1=int(max(0,np.max(sy[feasible]-sraw[feasible]))) if len(feasible) else 11
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    pos={int(v):i for i,v in enumerate(q)};si=np.asarray([pos[int(v)] for v in seids]);ev=np.asarray([pos[int(v)] for v in evids]);raw=model.predict(X).astype(int);fixed=np.mean([ndc[(int(q[i]),b[-1])] for i in ev]);pairseed=SEED+cycle*100000+sum(ord(z) for z in sname+'|'+tname)
    # Risk-matched fixed-stage baselines.
    for stage in STAGES:
     ssel=select(sraw,sy,sc,sca[:stage]);tsel=select(raw,y,c,si[:stage])
     for method,sh in [('RM-B1',ssel),('RM-B2',tsel)]:
      action='CERTIFIED' if sh is not None else 'B6_FALLBACK';sh=11 if sh is None else sh;m=metrics(raw,sh,y,c,ndc,q,b,ev)
      rm.append({'dataset':ds,'cycle':cycle,'source_build':sname,'target_build':tname,'method':method,'stage':stage,'selected_shift':sh,'action':action,'abs_risk':m['abs_fail']/m['n'],'rec_risk':m['rec_fail']/m['n'],'endpoint_infeasible_rate':m['endpoint_fail']/m['n'],'cp95_abs_upper':cp(m['abs_fail'],m['n']),'mean_ndc':m['mean_ndc'],'p50_ndc':m['p50_ndc'],'p95_ndc':m['p95_ndc'],'saving_vs_fixed':1-m['mean_ndc']/fixed,'evidence_label':'SEMANTIC_REPAIR'})
    qfull=np.asarray([sum(ndc[(int(q[i]),bb)] for bb in b) for i in si])
    for rep in range(REPS):
     order=np.random.default_rng(pairseed+rep).permutation(250);action=None
     for stage in STAGES:
      idx=si[order[:stage]];sh=select(raw,y,c,idx)
      if sh is not None and sh<max1 and sh<11:
       cb=np.asarray([ndc[(int(q[i]),b[int(min(raw[i]+max1,11))])] for i in idx]);cs=np.asarray([ndc[(int(q[i]),b[int(min(raw[i]+sh,11))])] for i in idx]);diff=cb-cs;lcb=diff.mean()-student_t.ppf(.95,stage-1)*diff.std(ddof=1)/math.sqrt(stage)
       if lcb>0 and qfull[order[:stage]].sum()+N0*cs.mean()<N0*cb.mean():action='ASRC';labels=stage;break
     if action is None:
      sh1=select(raw,y,c,si)
      if sh1 is not None and sh1==max1:sh=max1;action='B1_RETAIN'
      else:sh=11;action='B6_FALLBACK'
      labels=250
     m=metrics(raw,sh,y,c,ndc,q,b,ev);bm=metrics(raw,max1,y,c,ndc,q,b,ev)
     reps[(ds,sname,tname,rep)].append({'cycle':cycle,'action':action,'labels':labels,'shift':sh,'abs_fail':m['abs_fail'],'rec_fail':m['rec_fail'],'endpoint_fail':m['endpoint_fail'],'n':m['n'],'mean_ndc':m['mean_ndc'],'p50_ndc':m['p50_ndc'],'p95_ndc':m['p95_ndc'],'b1_ndc':bm['mean_ndc'],'fixed':fixed})

summary=[]
for (ds,s,t,rep),v in reps.items():
 n=sum(x['n'] for x in v);af=sum(x['abs_fail'] for x in v);rf=sum(x['rec_fail'] for x in v);ef=sum(x['endpoint_fail'] for x in v);online=np.mean([x['mean_ndc'] for x in v]);b1=np.mean([x['b1_ndc'] for x in v]);fixed=np.mean([x['fixed'] for x in v])
 summary.append({'dataset':ds,'source_build':s,'target_build':t,'rep':rep,'cycles':4,'target_labels_mean':np.mean([x['labels'] for x in v]),'qbe_mean':12*np.mean([x['labels'] for x in v]),'abs_fail':af,'rec_fail':rf,'endpoint_fail':ef,'n_eval':n,'abs_risk':af/n,'rec_risk':rf/n,'endpoint_infeasible_rate':ef/n,'cp95_abs_upper':cp(af,n),'mean_ndc':online,'p50_ndc':np.mean([x['p50_ndc'] for x in v]),'p95_ndc':np.mean([x['p95_ndc'] for x in v]),'saving_vs_b1max':1-online/b1,'saving_vs_fixed':1-online/fixed,'fallback_fraction':sum(x['action']=='B6_FALLBACK' for x in v)/4,'b1_retain_fraction':sum(x['action']=='B1_RETAIN' for x in v)/4,'evidence_label':'SEMANTIC_REPAIR'})
R=pd.DataFrame(rm);S=pd.DataFrame(summary);R.to_csv(OUT+'/risk_matched_baselines.csv',index=False);S.to_csv(OUT+'/asrc_repaired_summary.csv',index=False,compression=None)
target=S.groupby(['dataset','target_build']).agg(abs_risk=('abs_risk','mean'),rec_risk=('rec_risk','mean'),endpoint_infeasible_rate=('endpoint_infeasible_rate','mean'),mean_ndc=('mean_ndc','mean'),mean_labels=('target_labels_mean','mean'),fallback_rate=('fallback_fraction','mean'),saving_vs_b1max=('saving_vs_b1max','mean')).reset_index();target.to_csv(OUT+'/asrc_target_build_results.csv',index=False)
rng=np.random.default_rng(SEED);boot=[]
for ds,g in target.groupby('dataset'):
 for col in ['abs_risk','saving_vs_b1max']:
  x=g[col].to_numpy();z=x[rng.integers(0,len(x),(5000,len(x)))].mean(1);boot.append({'dataset':ds,'metric':col,'point':x.mean(),'ci_low':np.quantile(z,.025),'ci_high':np.quantile(z,.975),'bootstrap':5000,'cluster':'target_build','evidence_label':'SEMANTIC_REPAIR'})
pd.DataFrame(boot).to_csv(OUT+'/asrc_build_cluster_bootstrap.csv',index=False)
ep=S.groupby('dataset').agg(endpoint_infeasible_rate=('endpoint_infeasible_rate','mean'),absolute_risk=('abs_risk','mean'),recoverable_risk=('rec_risk','mean'),conditional_feasible_risk=('rec_risk',lambda x:x.mean())).reset_index();ep.to_csv(OUT+'/endpoint_stratified_risk.csv',index=False)
print(pd.DataFrame(boot).to_string(index=False));print(S.groupby('dataset').agg(labels=('target_labels_mean','mean'),saving=('saving_vs_b1max','mean'),fallback=('fallback_fraction','mean'),abs_risk=('abs_risk','mean')).to_string())
