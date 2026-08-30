#!/usr/bin/env python3
import os,sys,glob,json,hashlib
import numpy as np,pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));OUT=ROOT+'/results/active_recovery_headroom_reaudit';os.makedirs(OUT,exist_ok=True)
sys.path[:0]=[ROOT+'/src/rebuild_portability_recovery',ROOT+'/src/asrc_semantic_repair']
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
split=json.load(open(ROOT+'/manifests/graph_anns_positive_crossfit_split.json'));rm=pd.read_csv(ROOT+'/results/asrc_semantic_repair/risk_matched_baselines.csv');asrc=pd.read_csv(ROOT+'/results/asrc_semantic_repair/asrc_repaired_summary.csv')
def cp(f,n,a=.05):return 1. if f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty='l2',solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[idx],y[idx]);return m
episodes=[];qcost={}
for ds in DATASETS:
 paths=sorted(glob.glob(ROOT+f'/results/cross_index/g1/main/hnswlib/{ds}__*.csv.gz'));builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths};folds={k:np.asarray(v,int) for k,v in split['datasets'][ds]['folds'].items()}
 for cycle in range(4):
  roles=split['datasets'][ds]['cycles'][str(cycle)];trids=folds[roles['source_train']];evids=folds[roles['target_evaluation']];models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};tr=np.asarray([pos[int(v)] for v in trids]);models[name]=fit(X,y,tr)
  for sname,model in models.items():
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    pos={int(v):i for i,v in enumerate(q)};ev=np.asarray([pos[int(v)] for v in evids]);raw=model.predict(X).astype(int)
    for method in ['RM-B1','RM-B2']:
     for stage in [80,128,250]:
      z=rm[(rm.dataset==ds)&(rm.cycle==cycle)&(rm.source_build==sname)&(rm.target_build==tname)&(rm.method==method)&(rm.stage==stage)].iloc[0];sh=int(z.selected_shift);alloc=np.minimum(raw+sh,11);za,zr,ce=safety_events(alloc[ev],y[ev],c[ev]);cost=np.asarray([ndc[(int(q[i]),b[int(alloc[i])])] for i in ev],float);key=(ds,cycle,sname,tname,method,stage);qcost[key]=cost
      episodes.append({'dataset':ds,'cycle':cycle,'source_build':sname,'target_build':tname,'method':method,'stage':stage,'labels':stage,'abs_fail':int(za.sum()),'rec_fail':int(zr.sum()),'endpoint_fail':int(ce.sum()),'n':len(ev),'mean_ndc':cost.mean(),'p95_ndc':np.quantile(cost,.95),'fallback':z.action=='B6_FALLBACK','design_safe':True,'evidence_label':'EXPLORATORY_HEADROOM_REAUDIT'})
E=pd.DataFrame(episodes);E.to_csv(OUT+'/episode_candidate_statistics.csv.gz',index=False,compression='gzip')
# H2 episode-randomized envelopes at each dataset's frozen ASRC mean labels.
draws=[];h2=[];tbboot=[]
for ds in DATASETS:
 L=asrc[asrc.dataset==ds].target_labels_mean.mean();lo,hi=(80,128) if L<=128 else (128,250);p=(L-lo)/(hi-lo)
 for method in ['RM-B1','RM-B2']:
  G=E[(E.dataset==ds)&(E.method==method)];eps=G[['cycle','source_build','target_build']].drop_duplicates().reset_index(drop=True);rng=np.random.default_rng(SEED+sum(ord(x) for x in ds+method));risk_draw=[];p95_draw=[];means=[]
  # Exact marginal query-cost p95 from episode-level randomization weights.
  all_lo=np.concatenate([qcost[(ds,int(r.cycle),r.source_build,r.target_build,method,lo)] for r in eps.itertuples()]);all_hi=np.concatenate([qcost[(ds,int(r.cycle),r.source_build,r.target_build,method,hi)] for r in eps.itertuples()]);vals=np.concatenate([all_lo,all_hi]);w=np.concatenate([np.full(len(all_lo),(1-p)/len(all_lo)),np.full(len(all_hi),p/len(all_hi))]);order=np.argsort(vals);marginal_p95=float(vals[order][np.searchsorted(np.cumsum(w[order]),.95)])
  idx=['cycle','source_build','target_build'];gl=G[G.stage==lo].set_index(idx).loc[pd.MultiIndex.from_frame(eps[idx])];gh=G[G.stage==hi].set_index(idx).loc[pd.MultiIndex.from_frame(eps[idx])];choices=rng.random((5000,len(eps)))<p
  failmat=np.where(choices,gh.abs_fail.to_numpy(),gl.abs_fail.to_numpy());meanmat=np.where(choices,gh.mean_ndc.to_numpy(),gl.mean_ndc.to_numpy());den=float(gl.n.sum());risk_draw=(failmat.sum(1)/den).tolist();means=meanmat.mean(1).tolist()
  for rep,choose in enumerate(choices):draws.append({'dataset':ds,'method':method,'rep':rep,'seed':SEED+sum(ord(x) for x in ds+method),'upper_stage_count':int(choose.sum()),'action_hash':hashlib.sha256(choose.tobytes()).hexdigest(),'evidence_label':'EXPLORATORY_HEADROOM_REAUDIT'})
  # Bootstrap target builds using expected episode mixture failures.
  bstats=[]
  for b,g in G.groupby('target_build'):
   a=g[g.stage==lo];c=g[g.stage==hi];bstats.append(((1-p)*a.abs_fail.sum()+p*c.abs_fail.sum(),a.n.sum()))
  rngb=np.random.default_rng(SEED);bs=np.asarray(bstats,float);sim=[]
  for _ in range(5000):
   x=bs[rngb.integers(0,len(bs),len(bs))];sim.append(x[:,0].sum()/x[:,1].sum())
  u=float(np.quantile(sim,.95));point=float(np.mean(risk_draw));h2.append({'dataset':ds,'method':method,'target_labels':L,'lower_stage':lo,'upper_stage':hi,'prob_upper':p,'abs_risk':point,'target_build_risk_ucb95':u,'mean_ndc':float(np.mean(means)),'p95_ndc':marginal_p95,'draws':5000,'randomization_unit':'recovery_episode','evidence_label':'EXPLORATORY_HEADROOM_REAUDIT'});tbboot.append({'dataset':ds,'method':method,'point':point,'ucb95':u,'bootstrap':5000,'cluster':'target_build'})
pd.DataFrame(draws).to_csv(OUT+'/h2_randomized_episode_draws.csv.gz',index=False,compression='gzip');H2=pd.DataFrame(h2);H2.to_csv(OUT+'/h2_randomized_summary.csv',index=False);pd.DataFrame(tbboot).to_csv(OUT+'/h2_target_build_bootstrap.csv',index=False);H2.to_csv(OUT+'/h2_pareto_envelope.csv',index=False)
# Oracle selection/evaluation summaries.
def aggregate(g):
 return pd.Series({'abs_fail':g.abs_fail.sum(),'n':g.n.sum(),'abs_risk':g.abs_fail.sum()/g.n.sum(),'mean_ndc':np.average(g.mean_ndc,weights=g.n),'p95_ndc':np.average(g.p95_ndc,weights=g.n),'labels':np.average(g.labels,weights=g.n),'fallback_rate':g.fallback.mean()})
def h3(insample=True):
 out=[]
 for (ds,t),g in E.groupby(['dataset','target_build']):
  for held in ([None] if insample else range(4)):
   sel=g if held is None else g[g.cycle!=held];ev=g if held is None else g[g.cycle==held];cand=sel.groupby(['method','stage']).apply(aggregate,include_groups=False).reset_index();safe=cand[cand.abs_risk<=.05];best=(safe if len(safe) else cand).sort_values('mean_ndc').iloc[0];z=ev[(ev.method==best.method)&(ev.stage==best.stage)];a=aggregate(z);out.append({'dataset':ds,'target_build':t,'heldout_cycle':held if held is not None else -1,'selected_method':best.method,'selected_stage':best.stage,**a.to_dict(),'oracle':'NON_DEPLOYABLE_'+('INSAMPLE' if insample else 'CROSSFIT')+'_ENVIRONMENT_ORACLE','evidence_label':'EXPLORATORY_HEADROOM_REAUDIT'})
 return pd.DataFrame(out)
def h4(insample=True):
 out=[]
 for (ds,s,t),g in E.groupby(['dataset','source_build','target_build']):
  for held in ([None] if insample else range(4)):
   sel=g if held is None else g[g.cycle!=held];ev=g if held is None else g[g.cycle==held];cand=sel.groupby(['method','stage']).apply(aggregate,include_groups=False).reset_index();safe=cand[cand.abs_risk<=.05];best=(safe if len(safe) else cand).sort_values('mean_ndc').iloc[0];z=ev[(ev.method==best.method)&(ev.stage==best.stage)];a=aggregate(z);out.append({'dataset':ds,'source_build':s,'target_build':t,'heldout_cycle':held if held is not None else -1,'selected_method':best.method,'selected_stage':best.stage,**a.to_dict(),'oracle':'NON_DEPLOYABLE_'+('INSAMPLE' if insample else 'CROSSFIT')+'_PAIR_ORACLE','evidence_label':'EXPLORATORY_HEADROOM_REAUDIT'})
 return pd.DataFrame(out)
H3a,H3b,H4a,H4b=h3(True),h3(False),h4(True),h4(False);H3a.to_csv(OUT+'/h3_environment_oracle_insample.csv',index=False);H3b.to_csv(OUT+'/h3_environment_oracle_crossfit.csv',index=False);H4a.to_csv(OUT+'/h4_pair_oracle_insample.csv',index=False);H4b.to_csv(OUT+'/h4_pair_oracle_crossfit.csv',index=False)
head=[]
for ds in DATASETS:
 base=float(H2[H2.dataset==ds].mean_ndc.min())
 for name,g in [('H3a',H3a),('H3b',H3b),('H4a',H4a),('H4b',H4b)]:
  x=g[g.dataset==ds];ndc=np.average(x.mean_ndc,weights=x.n);head.append({'dataset':ds,'oracle':name,'h2_mean_ndc':base,'oracle_mean_ndc':ndc,'headroom':1-ndc/base,'abs_risk':x.abs_fail.sum()/x.n.sum(),'p95_ndc':np.average(x.p95_ndc,weights=x.n),'labels':np.average(x.labels,weights=x.n),'evidence_label':'EXPLORATORY_HEADROOM_REAUDIT'})
pd.DataFrame(head).to_csv(OUT+'/corrected_recovery_headroom.csv',index=False);print(pd.DataFrame(head).to_string(index=False))
