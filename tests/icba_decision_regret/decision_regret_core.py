#!/usr/bin/env python3
import os,sys,glob,json
import numpy as np,pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));OUT=ROOT+'/results/icba_decision_regret';os.makedirs(OUT,exist_ok=True)
sys.path[:0]=[ROOT+'/src/rebuild_portability_recovery',ROOT+'/src/asrc_semantic_repair']
from m0_m1 import load,DATASETS,SEED
from safety_events import safety_events
split=json.load(open(ROOT+'/manifests/graph_anns_positive_crossfit_split.json'));rm=pd.read_csv(ROOT+'/results/asrc_semantic_repair/risk_matched_baselines.csv');asrc=pd.read_csv(ROOT+'/results/asrc_semantic_repair/asrc_repaired_summary.csv')
def cp(f,n,a=.05):return 1. if n<=0 or f>=n else float(beta.ppf(1-a,f+1,n-f))
def fit(X,y,idx):
 m=make_pipeline(StandardScaler(),LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,random_state=SEED));m.fit(X[idx],y[idx]);return m
episodes=[]; Q={}
for ds in DATASETS:
 paths=sorted(glob.glob(ROOT+f'/results/cross_index/g1/main/hnswlib/{ds}__*.csv.gz'));builds={os.path.basename(p).replace('.csv.gz',''):load(p) for p in paths};folds={k:np.asarray(v,int) for k,v in split['datasets'][ds]['folds'].items()}
 for cyc in range(4):
  roles=split['datasets'][ds]['cycles'][str(cyc)];trids=folds[roles['source_train']];evids=folds[roles['target_evaluation']];models={}
  for name,(d,b,q,X,y,c,ndc) in builds.items():
   pos={int(v):i for i,v in enumerate(q)};models[name]=fit(X,y,np.asarray([pos[int(v)] for v in trids]))
  for sname,model in models.items():
   for tname,(d,b,q,X,y,c,ndc) in builds.items():
    if sname==tname:continue
    pos={int(v):i for i,v in enumerate(q)};ev=np.asarray([pos[int(v)] for v in evids]);raw=model.predict(X).astype(int)
    actions=[]
    for meth in ['RM-B1','RM-B2']:
     for st in [80,128,250]:
      z=rm[(rm.dataset==ds)&(rm.cycle==cyc)&(rm.source_build==sname)&(rm.target_build==tname)&(rm.method==meth)&(rm.stage==st)].iloc[0];actions.append((meth,st,np.minimum(raw+int(z.selected_shift),11),z.action=='B6_FALLBACK'))
    actions.append(('FIXED',999,np.full_like(raw,11),True))
    for meth,st,alloc,fb in actions:
      za,zr,ce=safety_events(alloc[ev],y[ev],c[ev]);cost=np.asarray([ndc[(int(q[i]),b[int(alloc[i])])] for i in ev],float);key=(ds,cyc,sname,tname,meth,st);Q[key]=dict(cost=cost,za=za.astype(int),zr=zr.astype(int),ce=ce.astype(int),qid=q[ev])
      episodes.append(dict(dataset=ds,cycle=cyc,source_build=sname,target_build=tname,method=meth,stage=st,abs_fail=za.sum(),rec_fail=zr.sum(),censor_fail=ce.sum(),n=len(ev),mean_ndc=cost.mean(),fallback=fb))
E=pd.DataFrame(episodes);E.to_csv(OUT+'/candidate_episode_statistics.csv.gz',index=False,compression='gzip')
qrows=[]
for k,v in Q.items():
 ds,cy,s,t,m,st=k
 qrows.append(pd.DataFrame({'dataset':ds,'cycle':cy,'source_build':s,'target_build':t,'method':m,'stage':st,'query_id':v['qid'],'ndc':v['cost'],'z_abs':v['za'],'z_rec':v['zr'],'censor':v['ce']}))
pd.concat(qrows,ignore_index=True).to_csv(OUT+'/candidate_query_costs.csv.gz',index=False,compression='gzip')
def agg(g):return pd.Series(dict(abs_fail=g.abs_fail.sum(),rec_fail=g.rec_fail.sum(),censor_fail=g.censor_fail.sum(),n=g.n.sum(),abs_risk=g.abs_fail.sum()/g.n.sum(),risk_ucb=cp(g.abs_fail.sum(),g.n.sum()),mean_ndc=np.average(g.mean_ndc,weights=g.n),fallback_rate=g.fallback.mean()))
def select(scope,strict):
 out=[]
 group=['dataset','target_build'] if scope=='H3' else ['dataset','source_build','target_build']
 for keys,g in E.groupby(group):
  if not isinstance(keys,tuple):keys=(keys,)
  base=dict(zip(group,keys))
  for held in range(4):
   sel=g[(g.cycle!=held)&(g.method!='FIXED')];ev=g[g.cycle==held]; cand=sel.groupby(['method','stage']).apply(agg,include_groups=False).reset_index();safe=cand[cand.risk_ucb<=.05] if strict else cand[cand.abs_risk<=.05]
   if len(safe):best=safe.sort_values('mean_ndc').iloc[0];meth,st=best.method,int(best.stage);fb=False
   else:meth,st='FIXED',999;fb=True
   z=ev[(ev.method==meth)&(ev.stage==st)];a=agg(z);out.append({**base,'heldout_cycle':held,'selected_method':meth,'selected_stage':st,'selection_rule':'design_risk_ucb' if strict else 'design_point_risk','forced_fallback':fb,**a.to_dict()})
 return pd.DataFrame(out)
lanes={n:select(n[:2],n.endswith('c')) for n in ['H3b','H3c','H4b','H4c']}
for n,d in lanes.items():d.to_csv(OUT+f'/oracle_{n}_strict_replay.csv',index=False)
# Query-level pooled p95 and build-level means; H2 is frozen outcome-independent mixture expectation.
h2rows=[];p95=[];buildrows=[]
for ds in DATASETS:
 L=asrc[asrc.dataset==ds].target_labels_mean.mean();lo,hi=(80,128) if L<=128 else (128,250);p=(L-lo)/(hi-lo);method='RM-B2'
 keys=[k for k in Q if k[0]==ds and k[4]==method and k[5]==lo]
 vals=[];weights=[]
 for k in keys:
  a=Q[k]['cost'];b=Q[k[:-1]+(hi,)]['cost'];vals.extend([a,b]);weights.extend([np.full(len(a),(1-p)/sum(len(Q[x]['cost']) for x in keys)),np.full(len(b),p/sum(len(Q[x]['cost']) for x in keys))])
 v=np.concatenate(vals);w=np.concatenate(weights);o=np.argsort(v);h2p=float(v[o][np.searchsorted(np.cumsum(w[o]),.95)]);h2mean=float(np.sum(v*w));p95.append(dict(dataset=ds,lane='H2',pooled_p95=h2p,mean_ndc=h2mean,status='ESTIMATED_FROM_QUERY_LEVEL'))
 for tb in sorted(E[E.dataset==ds].target_build.unique()):
  gl=E[(E.dataset==ds)&(E.target_build==tb)&(E.method==method)&(E.stage==lo)];gh=E[(E.dataset==ds)&(E.target_build==tb)&(E.method==method)&(E.stage==hi)];buildrows.append(dict(dataset=ds,lane='H2',target_build=tb,mean_ndc=(1-p)*gl.mean_ndc.mean()+p*gh.mean_ndc.mean(),abs_fail=(1-p)*gl.abs_fail.sum()+p*gh.abs_fail.sum(),n=gl.n.sum()))
 for name,d in lanes.items():
  costs=[];zs=[];rs=[];cs=[]
  for r in d[d.dataset==ds].itertuples():
   src=r.source_build if hasattr(r,'source_build') else None
   ks=[k for k in Q if k[0]==ds and k[1]==r.heldout_cycle and k[3]==r.target_build and k[4]==r.selected_method and k[5]==r.selected_stage and (src is None or k[2]==src)]
   for k in ks:costs.append(Q[k]['cost']);zs.append(Q[k]['za']);rs.append(Q[k]['zr']);cs.append(Q[k]['ce'])
  c=np.concatenate(costs);z=np.concatenate(zs);rr=np.concatenate(rs);cc=np.concatenate(cs);p95.append(dict(dataset=ds,lane=name,pooled_p95=np.quantile(c,.95),mean_ndc=c.mean(),abs_risk=z.mean(),risk_ucb=cp(z.sum(),len(z)),z_rec=rr.mean(),endpoint_censoring=cc.mean(),status='ESTIMATED_FROM_QUERY_LEVEL'))
  for tb,g in d[d.dataset==ds].groupby('target_build'):buildrows.append(dict(dataset=ds,lane=name,target_build=tb,mean_ndc=np.average(g.mean_ndc,weights=g.n),abs_fail=g.abs_fail.sum(),n=g.n.sum()))
P=pd.DataFrame(p95);P.to_csv(OUT+'/oracle_pooled_p95.csv',index=False);B=pd.DataFrame(buildrows);B.to_csv(OUT+'/oracle_build_level.csv',index=False)
# Paired target-build bootstrap, risk bounds, LOTO and delete-max.
rng=np.random.default_rng(991);br=[];risk=[];loto=[]
for ds in DATASETS:
 h=B[(B.dataset==ds)&(B.lane=='H2')].set_index('target_build')
 for lane in ['H3b','H4b','H3c','H4c']:
  o=B[(B.dataset==ds)&(B.lane==lane)].set_index('target_build').loc[h.index];delta=(h.mean_ndc-o.mean_ndc).to_numpy();sim=np.asarray([delta[rng.integers(0,len(delta),len(delta))].mean() for _ in range(5000)]);mx=int(np.argmax(delta));br.append(dict(dataset=ds,lane=lane,mean_gain=delta.mean(),relative_gain=delta.mean()/h.mean_ndc.mean(),ci_low=np.quantile(sim,.025),ci_high=np.quantile(sim,.975),delete_max_gain=np.delete(delta,mx).mean(),build_variance=delta.var(ddof=1),bootstrap=5000))
  for tb in h.index:loto.append(dict(dataset=ds,lane=lane,omitted_target_build=tb,mean_gain=(h.drop(tb).mean_ndc-o.drop(tb).mean_ndc).mean()))
  q=P[(P.dataset==ds)&(P.lane==lane)].iloc[0];gg=lanes[lane][lanes[lane].dataset==ds];mxrisk=max(gg.groupby('target_build').apply(lambda x:x.abs_fail.sum()/x.n.sum(),include_groups=False));risk.append(dict(dataset=ds,lane=lane,point_risk=q.abs_risk,binomial_ucb=q.risk_ucb,cluster_bootstrap_ucb=np.nan,max_loto_build_risk=mxrisk,z_rec=q.z_rec,endpoint_censoring=q.endpoint_censoring,certificate='FIXED_TARGET_EMPIRICALLY_CERTIFIED' if q.risk_ucb<=.05 else 'FIXED_TARGET_LOW_POINT_RISK_ONLY'))
pd.DataFrame(br).to_csv(OUT+'/oracle_paired_bootstrap.csv',index=False);pd.DataFrame(loto).to_csv(OUT+'/oracle_loto.csv',index=False);pd.DataFrame(risk).to_csv(OUT+'/oracle_risk_bounds.csv',index=False)
pd.concat([d.assign(lane=n) for n,d in lanes.items()]).to_csv(OUT+'/oracle_strict_lane.csv.gz',index=False,compression='gzip')
print(pd.DataFrame(br).to_string(index=False));print(P.to_string(index=False));print(pd.DataFrame(risk).to_string(index=False))
