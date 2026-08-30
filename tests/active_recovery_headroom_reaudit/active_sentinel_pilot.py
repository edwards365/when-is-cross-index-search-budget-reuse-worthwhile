#!/usr/bin/env python3
import os,sys,glob,json,hashlib
import numpy as np,pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,log_loss,mutual_info_score,top_k_accuracy_score
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')); OUT=ROOT+'/results/active_recovery_headroom_reaudit';os.makedirs(OUT,exist_ok=True)
sys.path[:0]=[ROOT+'/src/rebuild_portability_recovery',ROOT+'/src/asrc_semantic_repair']
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
split=json.load(open(ROOT+'/manifests/graph_anns_positive_crossfit_split.json'));rm=pd.read_csv(ROOT+'/results/asrc_semantic_repair/risk_matched_baselines.csv');truth=pd.read_csv(OUT+'/h4_pair_oracle_crossfit.csv')
plans={80:[(0,80),(16,64)],128:[(0,128),(16,112),(32,96),(64,64)],250:[(0,250),(16,234),(32,218),(64,186),(128,122)]}
def cp(f,n,a=.05): return 1. if n<=0 or f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[idx],y[idx]);return m
records=[];pred=[]
for ds in DATASETS:
 paths=sorted(glob.glob(ROOT+f'/results/cross_index/g1/main/hnswlib/{ds}__*.csv.gz')); builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths};folds={k:np.asarray(v,int) for k,v in split['datasets'][ds]['folds'].items()}
 for cyc in range(4):
  roles=split['datasets'][ds]['cycles'][str(cyc)];trids=folds[roles['source_train']];senids=folds[roles['target_sentinel']];models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};models[name]=fit(X,y,np.asarray([pos[int(v)] for v in trids]))
  for sname,model in models.items():
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    pos={int(v):i for i,v in enumerate(q)};sen=np.asarray([pos[int(v)] for v in senids]);raw=model.predict(X).astype(int);prob=model.predict_proba(X);unc=1-np.max(prob,axis=1)
    cand=[]
    for meth in ['RM-B1','RM-B2']:
     for st in [80,128,250]:
      z=rm[(rm.dataset==ds)&(rm.cycle==cyc)&(rm.source_build==sname)&(rm.target_build==tname)&(rm.method==meth)&(rm.stage==st)].iloc[0];alloc=np.minimum(raw+int(z.selected_shift),11);za,_,_=safety_events(alloc[sen],y[sen],c[sen]);cost=np.asarray([ndc[(int(q[i]),b[int(alloc[i])])] for i in sen]);cand.append((meth,st,za,cost))
    yt=truth[(truth.dataset==ds)&(truth.source_build==sname)&(truth.target_build==tname)&(truth.heldout_cycle==cyc)].iloc[0]; yact=f'{yt.selected_method}:{int(yt.selected_stage)}'
    rng=np.random.default_rng(SEED+cyc+sum(map(ord,sname+tname))); base=rng.permutation(250); budget=np.lexsort((rng.random(250),raw[sen])); uncertainty=np.lexsort((rng.random(250),-unc[sen])); oracle=np.argsort(-np.maximum.reduce([x[2].astype(float) for x in cand]))
    for lane,order in [('uniform',base),('source_budget_stratified',budget),('source_uncertainty_stratified',uncertainty),('target_label_oracle_NON_DEPLOYABLE',oracle)]:
     for total,pp in plans.items():
      for nsel,ncert in pp:
       sel=order[:nsel]; cert=order[nsel:nsel+ncert]; feasible=ncert>=59
       scored=[]
       for meth,st,za,cost in cand:
        sr=za[sel].mean() if nsel else 0.; sm=cost[sel].mean() if nsel else cost.mean(); scored.append((sr>.05,sr,sm,meth,st,za,cost))
       chosen=sorted(scored,key=lambda x:(x[0],x[2],x[1],x[4]))[0];_,_,_,meth,st,za,cost=chosen;f=int(za[cert].sum());u=cp(f,len(cert));safe=feasible and u<=.05;act=f'{meth}:{st}'
       records.append(dict(dataset=ds,cycle=cyc,source_build=sname,target_build=tname,lane=lane,total=total,n_selection=nsel,n_certification=ncert,certifiable=feasible,cert_fail=f,cert_risk=f/max(1,len(cert)),cert_ucb=u,certified_safe=safe,selected_action=act,target_action=yact,correct=act==yact,selection_hash=hashlib.sha256(np.asarray(sel).tobytes()).hexdigest(),certification_hash=hashlib.sha256(np.asarray(cert).tobytes()).hexdigest(),evidence_label='EXPLORATORY_HEADROOM_REAUDIT'))
D=pd.DataFrame(records);D.to_csv(OUT+'/active_sentinel_plan_results.csv.gz',index=False,compression='gzip')
summary=[]
for keys,g in D.groupby(['dataset','lane','total','n_selection','n_certification']):
 ds,lane,total,ns,nc=keys; maj=g.target_action.value_counts(normalize=True).max(); summary.append(dict(dataset=ds,lane=lane,total=total,n_selection=ns,n_certification=nc,certifiable=nc>=59,accuracy=(g.correct.mean()),majority_accuracy=maj,accuracy_gain=g.correct.mean()-maj,balanced_accuracy=balanced_accuracy_score(g.target_action,g.selected_action),macro_f1=f1_score(g.target_action,g.selected_action,average='macro'),mutual_information=mutual_info_score(g.target_action,g.selected_action),certified_safe_rate=g.certified_safe.mean(),mean_cert_ucb=g.cert_ucb.mean(),evidence_label='EXPLORATORY_HEADROOM_REAUDIT'))
S=pd.DataFrame(summary);S.to_csv(OUT+'/active_sentinel_signal_summary.csv',index=False)
deploy=S[(~S.lane.str.contains('NON_DEPLOYABLE'))&S.certifiable];best=deploy.sort_values(['accuracy_gain','certified_safe_rate'],ascending=False).groupby('dataset').head(1);best.to_csv(OUT+'/active_sentinel_best_deployable.csv',index=False)
print(best.to_string(index=False))
