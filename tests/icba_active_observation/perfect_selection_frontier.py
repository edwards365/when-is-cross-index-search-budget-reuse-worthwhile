#!/usr/bin/env python3
import os,sys,glob,json
import numpy as np,pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));OUT=ROOT+'/results/icba_active_observation';sys.path[:0]=[ROOT+'/src/rebuild_portability_recovery',ROOT+'/src/asrc_semantic_repair']
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
split=json.load(open(ROOT+'/manifests/graph_anns_positive_crossfit_split.json'));rm=pd.read_csv(ROOT+'/results/asrc_semantic_repair/risk_matched_baselines.csv');D=pd.read_csv(ROOT+'/results/icba_decision_regret/action_level_replay.csv.gz');Q=pd.read_csv(ROOT+'/results/icba_decision_regret/candidate_query_costs.csv.gz');H=pd.read_csv(ROOT+'/results/icba_decision_regret/oracle_pooled_p95.csv')
D=D[(D.lane=='source_uncertainty_stratified')&(D.total==250)&(D.n_selection==64)&(D.n_certification==186)].copy();budgets=[16,32,64,96,128,160,191]
def cp(f,n,a=.05):return 1. if n<=0 or f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[idx],y[idx]);return m
rows=[]
for ds in DATASETS:
 paths=sorted(glob.glob(ROOT+f'/results/cross_index/g1/main/hnswlib/{ds}__*.csv.gz'));builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths};folds={k:np.asarray(v,int) for k,v in split['datasets'][ds]['folds'].items()}
 for cyc in range(4):
  roles=split['datasets'][ds]['cycles'][str(cyc)];trids=folds[roles['source_train']];senids=folds[roles['target_sentinel']];models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};models[name]=fit(X,y,np.asarray([pos[int(v)] for v in trids]))
  for sname,model in models.items():
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    zrow=D[(D.dataset==ds)&(D.cycle==cyc)&(D.source_build==sname)&(D.target_build==tname)].iloc[0];meth,st=zrow.env_oracle_action.split(':');st=int(st);rz=rm[(rm.dataset==ds)&(rm.cycle==cyc)&(rm.source_build==sname)&(rm.target_build==tname)&(rm.method==meth)&(rm.stage==st)].iloc[0]
    pos={int(v):i for i,v in enumerate(q)};sen=np.asarray([pos[int(v)] for v in senids]);raw=model.predict(X).astype(int);unc=1-model.predict_proba(X).max(1);rng=np.random.default_rng(SEED+cyc+sum(map(ord,sname+tname)));order=np.lexsort((rng.random(250),-unc[sen]));alloc=np.minimum(raw+int(rz.selected_shift),11);za,_,_=safety_events(alloc[sen],y[sen],c[sen])
    for m in budgets:
     ci=order[m:250];f=int(za[ci].sum());u=cp(f,len(ci));accept=u<=.05;rows.append(dict(dataset=ds,cycle=cyc,source_build=sname,target_build=tname,selection=m,certification=250-m,certifiable=250-m>=59,oracle_cert_fail=f,oracle_cert_ucb=u,accept=accept,eval_cost=zrow.env_oracle_ndc if accept else zrow.fixed_ndc,h2_ndc=zrow.h2_ndc,gain=zrow.h2_ndc-(zrow.env_oracle_ndc if accept else zrow.fixed_ndc),fallback=not accept,action=meth+':'+str(st)))
E=pd.DataFrame(rows);E.to_csv(OUT+'/perfect_selection_allocation_episode.csv.gz',index=False,compression='gzip')
summ=[]
for (ds,m),g in E.groupby(['dataset','selection']):
 # Exact query pooled p95 by joining deployed action per episode.
 acts=[]
 for r in g.itertuples():acts.append(dict(dataset=ds,cycle=r.cycle,source_build=r.source_build,target_build=r.target_build,method=(r.action.split(':')[0] if r.accept else 'FIXED'),stage=(int(r.action.split(':')[1]) if r.accept else 999)))
 q=Q.merge(pd.DataFrame(acts),on=['dataset','cycle','source_build','target_build','method','stage'],validate='many_to_one');h=float(H[(H.dataset==ds)&(H.lane=='H2')].pooled_p95.iloc[0]);tb=g.groupby('target_build').gain.mean();summ.append(dict(dataset=ds,probe='NON_DEPLOYABLE_PERFECT_SELECTION_UPPER_BOUND',selection=m,certification=250-m,mean_ndc=g.eval_cost.mean(),relative_gain=g.gain.mean()/g.h2_ndc.mean(),accept_rate=g.accept.mean(),fallback_rate=g.fallback.mean(),risk_ucb=g.oracle_cert_ucb.max(),pooled_p95=q.ndc.quantile(.95),h2_pooled_p95=h,p95_not_worse=q.ndc.quantile(.95)<=h,delete_max_build_gain=tb.drop(tb.idxmax()).mean(),loto_min_gain=min(tb.drop(x).mean() for x in tb.index),main_gate_eligible=250-m>=59,evidence='NON_DEPLOYABLE_ORACLE_UPPER_BOUND'))
S=pd.DataFrame(summ);S.to_csv(OUT+'/label_allocation_frontier.csv',index=False);S.to_csv(OUT+'/active_probe_results.csv',index=False);print(S.to_string(index=False))
