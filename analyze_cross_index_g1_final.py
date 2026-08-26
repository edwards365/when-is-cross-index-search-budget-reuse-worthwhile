#!/usr/bin/env python3
import csv,gzip,glob,json,math,hashlib
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr,kendalltau
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k'); BASE=ROOT/'results/cross_index/g1'; DER=BASE/'derived'; DER.mkdir(exist_ok=True)
GRID=np.array([10,16,24,32,48,64,96,128,192,256,384,512]); RNG=np.random.default_rng(991); BOOT=5000
def load():
 G={}
 for idx in ['hnswlib','faiss','vamana']:
  for p in glob.glob(str(BASE/'main'/idx/'*.csv.gz')):
   with gzip.open(p,'rt',newline='') as f: rows=list(csv.DictReader(f))
   if len(rows)!=12000: raise RuntimeError(f'row count {p}:{len(rows)}')
   r0=rows[0]; ds=r0['dataset'];seed=int(r0.get('seed',r0.get('graph_seed')));hist=r0.get('history',r0.get('insertion_order'))
   g={q:{} for q in range(1000)}
   for r in rows:
    q=int(r['query_id']);b=int(r.get('budget',r.get('ef_search')));g[q][b]=(float(r['recall_at_10']),float(r['exact_ndc']))
   if any(set(x)!=set(GRID) for x in g.values()):raise RuntimeError(f'coverage {p}')
   G[(idx,ds,seed,hist)]=g
 if len(G)!=81:raise RuntimeError(f'graphs {len(G)}')
 return G
def stable(curve):
 for b in GRID:
  if all(curve[int(z)][0]>=.9 for z in GRID[GRID>=b]):return int(b)
 return 1024
def ceilgrid(x):return int(next((z for z in GRID if z>=x),512))
def wcsv(name,rows):
 with open(DER/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
G=load(); effort=[];head=[];rank=[];transfer=[];pib=[];summ={}
for idx in ['hnswlib','faiss','vamana']:
 for ds in sorted({k[1] for k in G}):
  keys=sorted(k for k in G if k[0]==idx and k[1]==ds);B={};fixed={}
  for k in keys:
   g=G[k];fixed[k]=int(next((b for b in GRID if np.mean([g[q][int(b)][0] for q in range(250)])>=.9),512));B[k]={q:stable(g[q]) for q in range(1000)}
   for q in range(1000):effort.append({'index':idx,'dataset':ds,'seed':k[2],'history':k[3],'query_id':q,'split':'design' if q<250 else 'confirm','stable_budget':B[k][q],'right_censored':B[k][q]>512,'fixed_budget':fixed[k]})
  Y=np.array([[math.log2(B[k][q]) for k in keys] for q in range(250,1000)]);vary=float(np.mean(np.ptp(Y,axis=1)>0));
  for a in range(len(keys)):
   for b in range(a+1,len(keys)):
    tau=float(kendalltau(Y[:,a],Y[:,b]).statistic);rank.append({'index':idx,'dataset':ds,'source':str(keys[a][2:]),'target':str(keys[b][2:]),'same_history':keys[a][3]==keys[b][3],'spearman':float(spearmanr(Y[:,a],Y[:,b]).statistic),'kendall':tau,'rank_inversion':(1-tau)/2})
  hs=[]
  for k in keys:
   vals=[]
   for q in range(250,1000):
    g=G[k];fc=g[q][fixed[k]][1];oc=g[q][min(B[k][q],512)][1];vals.append((fc-oc)/fc if fc else 0)
   hs.extend(vals);head.append({'index':idx,'dataset':ds,'seed':k[2],'history':k[3],'mean_headroom':float(np.mean(vals)),'trimmed_top1pct':float(np.mean(np.sort(vals)[:-8]))})
  blind=[]
  for q in range(250,1000):
   costs=[]
   mb=max(B[k][q] for k in keys)
   for k in keys:costs.append((G[k][q][min(mb,512)][1]-G[k][q][min(B[k][q],512)][1])/G[k][q][fixed[k]][1])
   blind.append(np.mean(costs))
  pib.append({'index':idx,'dataset':ds,'mean_price':float(np.mean(blind)),'trimmed_top1pct':float(np.mean(np.sort(blind)[:-8]))})
  pv={'same':[],'cross':[]}
  for s in keys:
   for t in keys:
    if s==t:continue
    candidates=sorted({float(b/max(B[s][q],1)) for q in range(250) for b in GRID});base=np.mean([G[t][q][fixed[t]][0] for q in range(250)]);mult=candidates[-1]
    for a in candidates:
     if np.mean([G[t][q][ceilgrid(a*B[s][q])][0] for q in range(250)])>=base-.001:mult=a;break
    vals=[];rd=[]
    for q in range(250,1000):
     pred=ceilgrid(mult*B[s][q]);oracle=min(B[t][q],512);den=G[t][q][fixed[t]][1];vals.append((G[t][q][pred][1]-G[t][q][oracle][1])/den);rd.append(G[t][q][pred][0]-G[t][q][fixed[t]][0])
    cat='same' if s[3]==t[3] else 'cross';pv[cat].append(np.array(vals));transfer.append({'index':idx,'dataset':ds,'source':str(s[2:]),'target':str(t[2:]),'category':cat,'multiplier':mult,'regret':float(np.mean(vals)),'recall_delta':float(np.mean(rd))})
  same=np.mean(pv['same'],axis=0);cross=np.mean(pv['cross'],axis=0);delta=cross-same;boots=delta[RNG.integers(0,len(delta),(BOOT,len(delta)))].mean(1);ri=np.mean([x['rank_inversion'] for x in rank if x['index']==idx and x['dataset']==ds]);trim=float(np.mean(np.sort(delta)[:-8]))
  summ[f'{idx}:{ds}']={'budget_variation_rate':vary,'oracle_headroom':float(np.mean(hs)),'cross_minus_same_regret':float(delta.mean()),'ci95':[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))],'rank_inversion':float(ri),'trimmed_delta':trim,'price_of_blindness':float(np.mean(blind))}
wcsv('per_query_effort.csv',effort);wcsv('oracle_headroom.csv',head);wcsv('transfer_regret.csv',transfer);wcsv('rank_inversion.csv',rank);wcsv('price_of_index_blindness.csv',pib)
try:
 import pandas as pd;pd.DataFrame(effort).to_parquet(DER/'per_query_effort.parquet',index=False)
except Exception as e:(DER/'per_query_effort.parquet.NOT_ESTIMABLE').write_text(str(e)+'\n')
def g1(v):return v['budget_variation_rate']>0 and v['cross_minus_same_regret']>0 and v['ci95'][0]>0 and v['rank_inversion']>.05 and v['trimmed_delta']>0
def g2(v):return v['oracle_headroom']>.05 and v['budget_variation_rate']>0 and (v['cross_minus_same_regret']>0 or v['ci95'][0]>0) and v['rank_inversion']>.05 and v['ci95'][0]>0
G1={ds:g1(summ[f'faiss:{ds}']) for ds in sorted({k[1] for k in G})};G2={ds:g2(summ[f'vamana:{ds}']) for ds in sorted({k[1] for k in G})};p1=sum(G1.values())>=2;p2=sum(G2.values())>=2
label='KEEP_GRAPH_ANNS_CONSTRUCTION_DEPENDENT_SAFETY_TAX' if p2 else ('KEEP_HNSW_SPECIFIC_CONSTRUCTION_HISTORY_STUDY' if p1 else 'SHRINK_TO_HNSWLIB_IMPLEMENTATION_BOUNDARY')
decision={'status':'FINAL','label':label,'gate_g1_pass':p1,'gate_g2_pass':p2,'g1_by_dataset':G1,'g2_by_dataset':G2,'graphs':81,'rows':972000,'bootstrap':5000,'formal_test_accessed':False,'validation_dev_accessed':False,'summary':summ}
(ROOT/'manifests/cross_index_g1_final_decision.json').write_text(json.dumps(decision,indent=2)+'\n');print(json.dumps(decision,indent=2))
