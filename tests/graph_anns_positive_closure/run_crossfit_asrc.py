#!/usr/bin/env python3
import glob,json,math,os,sys,time
from collections import defaultdict
import numpy as np,pandas as pd
from scipy.stats import beta,t as student_t
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));sys.path.insert(0,os.path.join(ROOT,'src/rebuild_portability_recovery'))
from m0_m1 import load,cp,DATASETS,SEED
OUT=os.path.join(ROOT,'results/graph_anns_positive_closure');os.makedirs(OUT,exist_ok=True)
SPLIT=json.load(open(os.path.join(ROOT,'manifests/graph_anns_positive_crossfit_split.json')))
ALPHA=.05;DELTA=.05;AJ=ALPHA/3;STAGES=(80,128,250);REPS=500;N0=100000

def cp_level(f,n,a=AJ):return 1. if f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED));t0=time.perf_counter();m.fit(X[idx],y[idx]);return m,time.perf_counter()-t0
def eval_metric(alloc,y,c,ndc,q,b,idx):
 fail=int(np.sum((alloc[idx]<y[idx])|c[idx]));cost=np.asarray([ndc[(int(q[i]),b[int(alloc[i])])] for i in idx],float)
 return fail,len(idx),float(cost.mean()),float(np.quantile(cost,.95)),float(np.mean(alloc[idx]==len(b)-1)),cost

b0=[];b1=[];b2=[];b5=[];stage_rows=[];rep_store=defaultdict(list)
for dataset in DATASETS:
 paths=sorted(glob.glob(os.path.join(ROOT,'results/cross_index/g1/main/hnswlib',f'{dataset}__*.csv.gz')));builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths}
 folds={k:np.asarray(v,int) for k,v in SPLIT['datasets'][dataset]['folds'].items()}
 for cycle in range(4):
  roles=SPLIT['datasets'][dataset]['cycles'][str(cycle)];train_ids=folds[roles['source_train']];cal_ids=folds[roles['source_calibration']];sent_ids=folds[roles['target_sentinel']];eval_ids=folds[roles['target_evaluation']]
  assert not(set(train_ids)&set(cal_ids)|set(train_ids)&set(sent_ids)|set(train_ids)&set(eval_ids)|set(cal_ids)&set(sent_ids)|set(cal_ids)&set(eval_ids)|set(sent_ids)&set(eval_ids))
  source_models={};target_models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};tr=np.asarray([pos[int(v)] for v in train_ids]);ca=np.asarray([pos[int(v)] for v in cal_ids])
   sm,stime=fit(X,y,tr);raw=sm.predict(X).astype(int);ssh=int(max(0,np.max(y[ca]-raw[ca])));source_models[name]=(sm,ssh,stime)
   tm,ttime=fit(X,y,tr);traw=tm.predict(X).astype(int);tsh=int(max(0,np.max(y[ca]-traw[ca])));target_models[name]=(traw,tsh,ttime)
  for sname,(source_model,source_shift,source_time) in source_models.items():
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    pos={int(v):i for i,v in enumerate(q)};sidx=np.asarray([pos[int(v)] for v in sent_ids]);eidx=np.asarray([pos[int(v)] for v in eval_ids]);raw=source_model.predict(X).astype(int);grid=[]
    for sh in range(12):grid.append(eval_metric(np.minimum(raw+sh,11),y,c,ndc,q,b,eidx))
    fixed=float(np.mean([ndc[(int(q[i]),b[-1])] for i in eidx]));common={'dataset':dataset,'cycle':cycle,'source_build':sname,'target_build':tname,'n_eval':250,'source_shift':source_shift,'outer_label':'OUTER_BUILD_NOT_CERTIFIED','evidence_label':'CROSS_FITTED_DESIGN_EVIDENCE'}
    for method,sh,store in [('B0',0,b0),('B1',source_shift,b1)]:
     f,n,mn,p95,en,_=grid[min(sh,11)];store.append(dict(common,method=method,selected_shift=sh,underbudget=f,risk=f/n,cp95_upper=cp(f,n),mean_ndc=mn,p95_ndc=p95,endpoint_fraction=en,saving_vs_fixed=1-mn/fixed,gate_s='PASS' if cp(f,n)<=.05 else 'FAIL'))
    target_shift=int(max(0,np.max(y[sidx]-raw[sidx])));f,n,mn,p95,en,_=grid[min(target_shift,11)];b2.append(dict(common,method='B2-250',selected_shift=target_shift,target_labels=250,qbe=3000,underbudget=f,risk=f/n,cp95_upper=cp(f,n),mean_ndc=mn,p95_ndc=p95,endpoint_fraction=en,saving_vs_fixed=1-mn/fixed,gate_s='PASS' if cp(f,n)<=.05 else 'FAIL'))
    traw,tshift,ttime=target_models[tname];alloc5=np.minimum(traw+tshift,11);f5,n5,m5,p5,e5,_=eval_metric(alloc5,y,c,ndc,q,b,eidx);b5.append(dict(common,method='B5',selected_shift=tshift,target_labels=500,qbe=6000,training_seconds=ttime,underbudget=f5,risk=f5/n5,cp95_upper=cp(f5,n5),mean_ndc=m5,p95_ndc=p5,endpoint_fraction=e5,saving_vs_fixed=1-m5/fixed,gate_s='PASS' if cp(f5,n5)<=.05 else 'FAIL'))
    # Full-grid NDC for nested calibration prefixes.
    q_full=np.asarray([sum(ndc[(int(q[i]),bb)] for bb in b) for i in sidx],float);pairseed=SEED+cycle*100000+sum(ord(z) for z in sname+'|'+tname)
    stage_acc={k:defaultdict(list) for k in STAGES}
    for rep in range(REPS):
     order=np.random.default_rng(pairseed+rep).permutation(250);final=None
     for stage in STAGES:
      si=sidx[order[:stage]];cert=[];first_fail=False;t0=time.perf_counter()
      for sh in range(11,-1,-1):
       fails=int(np.sum(y[si]>np.minimum(raw[si]+sh,11)))
       ok=cp_level(fails,stage)<=DELTA
       if ok and not first_fail:cert.append(sh)
       else:first_fail=True;break
      selected=min(cert) if cert else None;cal_cost=float(q_full[order[:stage]].sum());stop=False;benefit_lcb=-np.inf
      if selected is not None and selected<source_shift and selected<11:
       c_b1=np.asarray([ndc[(int(q[i]),b[int(min(raw[i]+source_shift,11))])] for i in si]);c_sel=np.asarray([ndc[(int(q[i]),b[int(min(raw[i]+selected,11))])] for i in si]);diff=c_b1-c_sel
       benefit_lcb=float(diff.mean()-student_t.ppf(.95,stage-1)*diff.std(ddof=1)/math.sqrt(stage)) if stage>1 else -np.inf
       stop=(benefit_lcb>0 and cal_cost+N0*c_sel.mean()<N0*c_b1.mean())
      stage_acc[stage]['selected'].append(-1 if selected is None else selected);stage_acc[stage]['certified'].append(selected is not None);stage_acc[stage]['stop'].append(stop);stage_acc[stage]['benefit_lcb'].append(benefit_lcb);stage_acc[stage]['cal_cost'].append(cal_cost);stage_acc[stage]['control_seconds'].append(time.perf_counter()-t0)
      if stop:
       sh=selected;action='ASRC';labels=stage;break
     else:
      # Frozen terminal rule: retain B1 only if target-stage certified, otherwise B6.
      fails_b1=int(np.sum(y[sidx]>np.minimum(raw[sidx]+source_shift,11)))
      if cp_level(fails_b1,250)<=DELTA:sh=source_shift;action='B1_RETAIN';labels=250
      else:sh=11;action='B6_FALLBACK';labels=250
     f,n,mn,p95,en,_=grid[min(sh,11)];rep_store[(dataset,sname,tname,rep)].append({'cycle':cycle,'fail':f,'n':n,'mean_ndc':mn,'p95_ndc':p95,'endpoint':en,'labels':labels,'action':action,'shift':sh,'fixed':fixed,'source_ndc':grid[min(source_shift,11)][2]})
    for stage in STAGES:
     a=stage_acc[stage];stage_rows.append(dict(common,method='ASRC',stage=stage,reps=REPS,certified_rate=float(np.mean(a['certified'])),stop_rate=float(np.mean(a['stop'])),mean_selected_shift=float(np.mean([x for x in a['selected'] if x>=0])) if any(x>=0 for x in a['selected']) else np.nan,mean_benefit_lcb=float(np.mean([x for x in a['benefit_lcb'] if np.isfinite(x)])) if any(np.isfinite(x) for x in a['benefit_lcb']) else np.nan,mean_calibration_ndc=float(np.mean(a['cal_cost'])),mean_control_seconds=float(np.mean(a['control_seconds'])),alpha_stage=AJ,delta=DELTA,candidate_order='11_to_0_fixed_sequence',used_history=False,used_fingerprint=False,used_source_shift_as_floor=False,used_target_evaluation=False))

summary=[]
for (ds,s,t,rep),vals in rep_store.items():
 fail=sum(v['fail'] for v in vals);n=sum(v['n'] for v in vals);labels=sum(v['labels'] for v in vals)/4;online=np.mean([v['mean_ndc'] for v in vals]);source=np.mean([v['source_ndc'] for v in vals]);fixed=np.mean([v['fixed'] for v in vals]);actions=[v['action'] for v in vals]
 summary.append({'dataset':ds,'source_build':s,'target_build':t,'rep':rep,'cycles':4,'target_labels_mean':labels,'qbe_mean':12*labels,'underbudget':fail,'n_eval':n,'risk':fail/n,'cp95_upper':cp(fail,n),'mean_ndc':online,'saving_vs_b1':1-online/source,'saving_vs_fixed':1-online/fixed,'stage80_fraction':sum(v['labels']==80 for v in vals)/4,'stage128_fraction':sum(v['labels']==128 for v in vals)/4,'stage250_fraction':sum(v['labels']==250 for v in vals)/4,'b1_retain_fraction':actions.count('B1_RETAIN')/4,'b6_fallback_fraction':actions.count('B6_FALLBACK')/4,'gate_s':'PASS' if cp(fail,n)<=.05 else 'FAIL','evidence_label':'CROSS_FITTED_DESIGN_EVIDENCE'})

pd.DataFrame(b0).to_csv(os.path.join(OUT,'b0_crossfit.csv'),index=False);pd.DataFrame(b1).to_csv(os.path.join(OUT,'b1_crossfit.csv'),index=False);pd.DataFrame(b2).to_csv(os.path.join(OUT,'b2_fixed250_crossfit.csv'),index=False);pd.DataFrame(b5).to_csv(os.path.join(OUT,'b5_target_retrain.csv'),index=False);pd.DataFrame(stage_rows).to_csv(os.path.join(OUT,'asrc_stage_results.csv'),index=False);S=pd.DataFrame(summary);S.to_csv(os.path.join(OUT,'asrc_summary.csv'),index=False)
print(S.groupby('dataset').agg(rows=('rep','size'),pass_fraction=('gate_s',lambda x:(x=='PASS').mean()),mean_labels=('target_labels_mean','mean'),median_labels=('target_labels_mean','median'),p95_labels=('target_labels_mean',lambda x:np.quantile(x,.95)),mean_saving_b1=('saving_vs_b1','mean'),mean_saving_fixed=('saving_vs_fixed','mean'),stage80=('stage80_fraction','mean'),stage128=('stage128_fraction','mean'),stage250=('stage250_fraction','mean'),b1retain=('b1_retain_fraction','mean'),b6fallback=('b6_fallback_fraction','mean')).to_string())
