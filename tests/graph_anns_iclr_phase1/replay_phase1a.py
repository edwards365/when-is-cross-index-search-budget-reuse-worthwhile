#!/usr/bin/env python3
import csv,gzip,hashlib,io,json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/graph_anns_iclr_phase1'; OUT.mkdir(parents=True,exist_ok=True)
EVAL=range(250,1000); TAUS=[.90,.95,.99]; RNGSEED=991; NBOOT=5000
def gitcsv(c,p):return pd.read_csv(io.BytesIO(subprocess.check_output(['git','show',f'{c}:{p}'])))
def csvbuild(path,grid,role=None,eval_ids=EVAL):
 x=pd.read_csv(path)
 if role:x=x[x.query_role==role]
 x=x[x.query_id.isin(eval_ids)].groupby(['query_id','ef_search'],as_index=False).agg(recall=('recall_at_10','first'),cost=('ndc','first'),lat=('latency_ns','median'))
 return {'id':path.parent.name,'rec':x.pivot(index='query_id',columns='ef_search',values='recall').reindex(index=eval_ids,columns=grid).to_numpy(),'cost':x.pivot(index='query_id',columns='ef_search',values='cost').reindex(index=eval_ids,columns=grid).to_numpy(),'lat':x.pivot(index='query_id',columns='ef_search',values='lat').reindex(index=eval_ids,columns=grid).to_numpy()}
def load_hnsw():
 bm=gitcsv('dd160731','results/graph_anns_e4/build_manifest.csv');g=np.array([10,20,40,80,120,200]);root=Path('/home/wlk/data500/graph_anns_e4/raw'); out={}
 for ds in ['sift_100k','arxiv_nomic_100k']:out[ds]=[csvbuild(root/x.build_id/'queries.csv.gz',g) for _,x in bm[bm.dataset==ds].iterrows()]
 return out,g,'hnswlib HNSW','ALL_DIRECTED'
def load_faiss():
 root=Path('/home/wlk/data500/graph_anns_faiss_external_validity/run');bm=pd.read_csv(root/'build_registry.csv');g=np.array([16,32,64,128,256,512]);out={}
 for ds in ['sift_100k','arxiv_nomic_100k']:out[ds]=[csvbuild(root/'raw'/x.build_id/'queries.csv.gz',g,'confirmatory_evaluation',range(750)) for _,x in bm[bm.dataset==ds].iterrows()]
 return out,g,'Faiss HNSW','ALL_DIRECTED'
def load_vamana():
 g=np.array([16,32,64,128,256,512]);out={}
 for ds,root in [('sift_100k',Path('/home/wlk/data500/icba_vamana_stage1')),('arxiv_nomic_100k',Path('/home/wlk/data500/icba_vamana_stage1_arxiv'))]:
  a=[]
  for i in range(1,13):
   x=json.loads((root/f'builds/V{i:02d}/run_report.json').read_text())[0]['results']['search']['Topk'];a.append({'id':f'V{i:02d}','rec':np.array([z['query_recalls'] for z in x]).T,'cost':np.array([z['query_cmps'] for z in x]).T,'lat':np.array([z['search_latencies'] for z in x]).T})
  out[ds]=a
 return out,g,'DiskANN3/Vamana-style','SPLIT_6X6'
def budgets(rec,tau,suffix=True):
 good=rec>=tau
 if suffix:good=np.logical_and.accumulate(good[:,::-1],axis=1)[:,::-1]
 ok=good.any(1);idx=np.argmax(good,axis=1);return ok,idx
def analyze(builds,grid,impl,pairmode):
 sem=[];work=[];unres=[];tails=[]
 for ds,bb in builds.items():
  nb=len(bb);pairs=[(i,j) for i in range(nb) for j in range(nb) if i!=j] if pairmode=='ALL_DIRECTED' else [(i,j) for i in range(6) for j in range(6,12)]
  for tau in TAUS:
   state=[budgets(b['rec'],tau,impl!='DiskANN3/Vamana-style') for b in bb]; ok=np.stack([s[0] for s in state],1);ix=np.stack([s[1] for s in state],1); unresolved=1-ok.mean();mixed=((ok.any(1))&(~ok.all(1))).mean();allfinite=ok.all(1);atleast2=ok.sum(1)>=2
   a1=np.mean([len(set([('F',int(ix[q,k])) if ok[q,k] else ('U',-1) for k in range(nb)]))>1 for q in range(750)]);a2=np.mean([(grid[ix[q]].max()-grid[ix[q]].min()) for q in np.where(allfinite)[0]]) if allfinite.any() else np.nan;a3=np.mean([(grid[ix[q,ok[q]]].max()-grid[ix[q,ok[q]]].min()) for q in np.where(atleast2)[0]]) if atleast2.any() else np.nan
   qr=np.zeros(750);qref=np.zeros(750);qjf=np.zeros(750);qjfn=np.zeros(750);qnum=np.zeros(750);qden=np.zeros(750);costunits=[]
   for s,t in pairs:
    so,si=state[s];to,ti=state[t];q=np.arange(750);act=np.where(so,si,len(grid)-1);ref=np.where(to,ti,len(grid)-1);obs=bb[t]['rec'][q,act];base=bb[t]['rec'][q,ref];fail=(obs<tau)|(~to)
    if impl=='DiskANN3/Vamana-style':fail=fail|(~so)
    rf=(base<tau)|(~to) if impl!='DiskANN3/Vamana-style' else np.zeros(750,bool);qr+=fail;qref+=rf;jf=so&to;qjf+=fail&jf;qjfn+=jf;valid=(so&to) if impl=='DiskANN3/Vamana-style' else ~(fail|rf);d=bb[t]['cost'][q,act]-bb[t]['cost'][q,ref];qnum+=np.where(valid,d,0);qden+=np.where(valid,bb[t]['cost'][q,ref],0);costunits.extend(d[valid])
   npair=len(pairs);absr=qr.mean()/npair;refr=qref.mean()/npair;delta=absr-refr;jfr=qjf.sum()/qjfn.sum();tax=qnum.sum()/qden.sum();rng=np.random.default_rng(RNGSEED);boot=[]
   for _ in range(NBOOT):
    z=rng.integers(0,750,750);boot.append((qr[z].sum()-qref[z].sum())/(750*npair))
   lo,hi=np.quantile(boot,[.025,.975]);work.append([impl,ds,tau,nb,len(pairs),750,a1,a2,a3,mixed,unresolved,ok.all(1).mean(),absr,refr,delta,lo,hi,jfr,tax])
   if tau==.95:
    sem.append([impl,ds,nb,len(pairs),750,';'.join(map(str,grid)),a1,a2,a3,mixed,absr,refr,delta,jfr,tax]);unres.append([impl,ds,unresolved,mixed,ok.all(1).mean(),'REGISTERED_GRID_UNRESOLVED' if impl!='DiskANN3/Vamana-style' else 'JOINT_ENDPOINT_OR_GRID_UNRESOLVED'])
    cu=np.array(costunits);tails.append([impl,ds,len(cu),np.quantile(cu,.5),np.quantile(cu,.95),np.quantile(cu,.99),'implementation_native_cost_difference_on_safe_units'])

 return sem,work,unres,tails
allsem=[];allwork=[];allu=[];allt=[]
for loader in [load_hnsw,load_faiss,load_vamana]:
 a,g,i,p=loader();s,w,u,t=analyze(a,g,i,p);allsem+=s;allwork+=w;allu+=u;allt+=t
pd.DataFrame(allsem,columns=['implementation','dataset','builds','pairs','queries','budget_grid','A1_category_variation','A2_all_finite_mean_diameter','A3_at_least_two_finite_mean_diameter','A4_state_heterogeneity','absolute_transport_risk','reference_risk','incremental_transport_risk','jointly_feasible_violation','internal_cost_tax']).to_csv(OUT/'cross_family_semantic_table.csv',index=False,float_format='%.12g')
pd.DataFrame(allwork,columns=['implementation','dataset','tau','builds','pairs','queries','A1','A2','A3','A4','unresolved_mass','jointly_feasible_mass','absolute_transport_risk','reference_risk','incremental_transport_risk','ci_low','ci_high','jointly_feasible_violation','internal_cost_tax']).to_csv(OUT/'workpoint_sensitivity.csv',index=False,float_format='%.12g')
pd.DataFrame(allu,columns=['implementation','dataset','target_unresolved_mass','mixed_state_mass','all_builds_finite_mass','semantic_label']).to_csv(OUT/'unresolved_mass.csv',index=False,float_format='%.12g')
pd.DataFrame(allt,columns=['implementation','dataset','safe_pair_query_units','cost_delta_p50','cost_delta_p95','cost_delta_p99','scope']).to_csv(OUT/'tail_cost_summary.csv',index=False,float_format='%.12g')
print('PHASE1A_CORE_TABLES_COMPLETE')
