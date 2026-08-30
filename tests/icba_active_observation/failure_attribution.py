#!/usr/bin/env python3
import os,sys,glob,json,itertools,math
import numpy as np,pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));OUT=ROOT+'/results/icba_active_observation';os.makedirs(OUT,exist_ok=True)
sys.path[:0]=[ROOT+'/src/rebuild_portability_recovery',ROOT+'/src/asrc_semantic_repair']
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
split=json.load(open(ROOT+'/manifests/graph_anns_positive_crossfit_split.json'));rm=pd.read_csv(ROOT+'/results/asrc_semantic_repair/risk_matched_baselines.csv');D=pd.read_csv(ROOT+'/results/icba_decision_regret/action_level_replay.csv.gz')
# Fixed best unified lane from prior closure.
D=D[(D.lane=='source_uncertainty_stratified')&(D.total==250)&(D.n_selection==64)&(D.n_certification==186)].copy()
E=pd.read_csv(ROOT+'/results/icba_decision_regret/candidate_episode_statistics.csv.gz');D[['proposal_method','proposal_stage']]=D.proposed_action.str.split(':',expand=True);D.proposal_stage=D.proposal_stage.astype(int);pe=E.rename(columns={'method':'proposal_method','stage':'proposal_stage','mean_ndc':'proposal_raw_ndc','abs_fail':'proposal_raw_fail','n':'proposal_raw_n'})[['dataset','cycle','source_build','target_build','proposal_method','proposal_stage','proposal_raw_ndc','proposal_raw_fail','proposal_raw_n']];D=D.merge(pe,on=['dataset','cycle','source_build','target_build','proposal_method','proposal_stage'],validate='one_to_one')
def cp(f,n,a=.05):return 1. if f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[idx],y[idx]);return m
cert=[]
for ds in DATASETS:
 paths=sorted(glob.glob(ROOT+f'/results/cross_index/g1/main/hnswlib/{ds}__*.csv.gz'));builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths};folds={k:np.asarray(v,int) for k,v in split['datasets'][ds]['folds'].items()}
 for cyc in range(4):
  roles=split['datasets'][ds]['cycles'][str(cyc)];trids=folds[roles['source_train']];senids=folds[roles['target_sentinel']];models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};ids=np.asarray([pos[int(v)] for v in trids]);models[name]=fit(X,y,ids)
  for sname,model in models.items():
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    zrow=D[(D.dataset==ds)&(D.cycle==cyc)&(D.source_build==sname)&(D.target_build==tname)].iloc[0];meth,st=zrow.env_oracle_action.split(':');st=int(st);rz=rm[(rm.dataset==ds)&(rm.cycle==cyc)&(rm.source_build==sname)&(rm.target_build==tname)&(rm.method==meth)&(rm.stage==st)].iloc[0]
    pos={int(v):i for i,v in enumerate(q)};sen=np.asarray([pos[int(v)] for v in senids]);raw=model.predict(X).astype(int);unc=1-model.predict_proba(X).max(1);rng=np.random.default_rng(SEED+cyc+sum(map(ord,sname+tname)));order=np.lexsort((rng.random(250),-unc[sen]));ci=sen[order[64:250]];alloc=np.minimum(raw+int(rz.selected_shift),11);za,_,_=safety_events(alloc[ci],y[ci],c[ci]);u=cp(int(za.sum()),len(ci));cert.append(dict(dataset=ds,cycle=cyc,source_build=sname,target_build=tname,oracle_cert_fail=int(za.sum()),oracle_cert_ucb=u,oracle_cert_accept=u<=.05))
D=D.merge(pd.DataFrame(cert),on=['dataset','cycle','source_build','target_build'],validate='one_to_one')
D['proposal_eval_ndc']=D.proposal_raw_ndc
D['proposal_eval_safe']=D.proposal_raw_fail/D.proposal_raw_n<=.05
def scenario(row,mis,rej,fb):
 # mis=1 real proposal, 0 oracle; rej=1 real certification, 0 perfect truth; fb=1 fixed, 0 cheap H2.
 action_cost=row.proposal_eval_ndc if mis else row.env_oracle_ndc
 if rej: accept=bool(row.certified_safe) if mis else bool(row.oracle_cert_accept)
 else: accept=bool(row.proposal_eval_safe) if mis else True
 return action_cost if accept else (row.fixed_ndc if fb else row.h2_ndc)
rows=[]
for bits in itertools.product([0,1],repeat=3):
 mis,rej,fb=bits;cost=D.apply(lambda r:scenario(r,mis,rej,fb),axis=1);z=D.copy();z['cost']=cost;z['gain']=z.h2_ndc-z.cost
 for ds,g in z.groupby('dataset'):rows.append(dict(dataset=ds,misselection=mis,real_rejection=rej,fixed_fallback=fb,mean_ndc=g.cost.mean(),pooled_p95=g.cost.quantile(.95),observable_gain=g.gain.mean(),relative_gain=g.gain.mean()/g.h2_ndc.mean(),fallback_rate=(g.cost==g.fixed_ndc).mean(),evidence='COUNTERFACTUAL_2X2X2'))
C=pd.DataFrame(rows);C.to_csv(OUT+'/failure_counterfactuals.csv',index=False)
# Named F0-F5.
named=[]
maps={'F0_REAL_DEPLOYMENT':(1,1,1),'F1_PERFECT_SELECTION_REAL_CERT':(0,1,1),'F2_REAL_SELECTION_PERFECT_CERT':(1,0,1),'F3_BOTH_PERFECT':(0,0,1),'F5_PERFECT_CHEAP_FALLBACK':(1,1,0)}
for name,bits in maps.items():
 x=C[(C.misselection==bits[0])&(C.real_rejection==bits[1])&(C.fixed_fallback==bits[2])].copy();x['counterfactual']=name;named.append(x)
N=pd.concat(named);N.to_csv(OUT+'/failure_named_counterfactuals.csv',index=False)
# Shapley contributions from perfect/cheap (0,0,0) to real (1,1,1).
facts=['misselection','real_rejection','fixed_fallback'];sh=[]
for ds,g in C.groupby('dataset'):
 val={tuple(int(getattr(r,f)) for f in facts):r for r in g.itertuples()}
 for metric in ['mean_ndc','pooled_p95']:
  for i,f in enumerate(facts):
   phi=0
   others=[j for j in range(3) if j!=i]
   for n in range(3):
    for S in itertools.combinations(others,n):
     a=[0,0,0]
     for j in S:a[j]=1
     b=a.copy();b[i]=1;w=math.factorial(n)*math.factorial(2-n)/math.factorial(3);phi+=w*(getattr(val[tuple(b)],metric)-getattr(val[tuple(a)],metric))
   sh.append(dict(dataset=ds,metric=metric,factor=f,shapley_cost_contribution=phi))
pd.DataFrame(sh).to_csv(OUT+'/failure_shapley.csv',index=False)
tail=N[['dataset','counterfactual','pooled_p95','mean_ndc','fallback_rate']];tail.to_csv(OUT+'/fallback_tail_attribution.csv',index=False)
print(N[['dataset','counterfactual','relative_gain','pooled_p95','fallback_rate']].to_string(index=False));print(pd.DataFrame(sh).to_string(index=False))
