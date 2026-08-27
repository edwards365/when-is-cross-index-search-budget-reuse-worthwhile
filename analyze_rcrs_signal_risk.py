#!/usr/bin/env python3
import csv,gzip,glob,json
from pathlib import Path
import numpy as np
from rcrs_signal_risk_dp import risk_monotone_dp,aware_risk_optimum
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');BASE=ROOT/'results/cross_index/g1';OUT=ROOT/'results/rcrs_signal';OUT.mkdir(exist_ok=True);GRID=np.array([10,16,24,32,48,64,96,128,192,256,384,512])
def load():
 G={}
 for idx in ['hnswlib','faiss','vamana']:
  for p in glob.glob(str(BASE/'main'/idx/'*.csv.gz')):
   with gzip.open(p,'rt',newline='') as f:r=list(csv.DictReader(f));z=r[0];k=(idx,z['dataset'],int(z.get('seed',z.get('graph_seed'))),z.get('history',z.get('insertion_order')));a=np.zeros((1000,12,2))
   for z in r:q=int(z['query_id']);b=int(z.get('budget',z.get('ef_search')));j=int(np.where(GRID==b)[0][0]);a[q,j]=float(z['recall_at_10']),float(z['exact_ndc'])
   G[k]=a
 return G
def stable(a):
 o=np.full(1000,1024)
 for q in range(1000):
  for j,b in enumerate(GRID):
   if np.all(a[q,j:,0]>=.9):o[q]=b;break
 return o
def write(p,r):
 with open(p,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=r[0].keys());w.writeheader();w.writerows(r)
G=load();B={k:stable(v) for k,v in G.items()};rows=[];norm=[]
point=list(csv.DictReader(open(ROOT/'results/rcrs_fast/monotone_tax.csv')))
for idx in ['hnswlib','faiss','vamana']:
 for ds in sorted({k[1] for k in G}):
  keys=sorted(k for k in G if k[0]==idx and k[1]==ds)
  for s in keys:
   for t in keys:
    if s==t:continue
    q=np.arange(250,1000);x=B[s][q];y=B[t][q];cost=G[t][q,:,1];fixed_j=next((j for j in range(12) if G[t][:250,j,0].mean()>=.9),11);fixed=float(G[t][q,fixed_j,1].mean())
    try:m=risk_monotone_dp(x,y,cost,GRID,.05);aware=aware_risk_optimum(y,cost,GRID,.05);status='COMPLETE'
    except RuntimeError as e:m={'cost':float('nan'),'failures':'NOT_ESTIMABLE','failure_rate':'NOT_ESTIMABLE'};aware=float('nan');status=str(e)
    rows.append({'index':idx,'dataset':ds,'source_seed':s[2],'source_history':s[3],'target_seed':t[2],'target_history':t[3],'n':750,'allowed_failures':37,'mono_cost':m['cost'],'aware_cost':aware,'risk_matched_tax_ndc':m['cost']-aware,'risk_matched_tax_over_fixed':(m['cost']-aware)/fixed,'empirical_failure_rate':m['failure_rate'],'status':status})
  z=[r for r in point if r['index']==idx and r['dataset']==ds];tax=np.mean([float(r['exact_monotone_ndc_tax']) for r in z]);heads=[]
  # Existing final decision stores graph-averaged Oracle opportunity by index/dataset.
  d=json.load(open(ROOT/'manifests/cross_index_g1_final_decision.json'))['summary'][idx+':'+ds];h=float(d['oracle_headroom']);norm.append({'index':idx,'dataset':ds,'original_tax_unit':'DIMENSIONLESS_FRACTION_OF_FIXED_NDC','tax_over_fixed':tax,'tax_percent_of_fixed':100*tax,'oracle_opportunity':h,'tax_over_positive_oracle_opportunity':tax/h if h>0 else 'NEGATIVE_ORACLE_GAIN_NOT_REPORTED'})
write(OUT/'risk_matched_monotone.csv',rows);write(OUT/'tax_normalization.csv',norm);print(json.dumps({'rows':len(rows),'complete':sum(r['status']=='COMPLETE' for r in rows)},indent=2))
