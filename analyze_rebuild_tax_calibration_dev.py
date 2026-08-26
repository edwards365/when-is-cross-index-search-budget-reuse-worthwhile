#!/usr/bin/env python3
"""Development-only conformal calibration; never reads audit/validation/test members."""
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]); NS=[32,64,128,256,512,1000]; DS=[.05,.01,.005,.001]; WORK=[10**3,10**4,10**5,10**6,10**7]
split=json.load(open(ROOT/'manifests/hardness_portability_100k/query_split.json'))['splits']; CAL=[int(x) for x in split['train_design']]; assert len(CAL)==250 and set(CAL).isdisjoint(split['internal_test'])

def load():
 g={}
 for p in glob.glob(str(ROOT/'results/hardness_portability_100k/realistic_raw/*.csv.gz')):
  with gzip.open(p,'rt',newline='') as f:r=list(csv.DictReader(f))
  k=(r[0]['dataset'],int(r[0]['graph_seed']),r[0]['insertion_order']);g[k]={q:{} for q in CAL}
  for x in r:
   q=int(x['query_id'])
   if q in g[k]:g[k][q][int(x['ef_search'])]=(float(x['recall_at_10']),float(x['exact_ndc']))
 return g

def ceil_grid(x):return int(next((e for e in E if e>=x),512))
def main():
 G=load(); budgets={}; fixed={}
 for k,g in G.items():
  target=.95 if any(np.mean([g[q][int(e)][0] for q in CAL])>=.95 for e in E) else .90
  fixed[k]=int(next((e for e in E if np.mean([g[q][int(e)][0] for q in CAL])>=target),512));budgets[k]={}
  for q in CAL:
   t=g[q][fixed[k]][0];budgets[k][q]=int(next((e for e in E if all(g[q][int(z)][0]>=t for z in E[E>=e])),1024))
 rows=[];amort=[]
 for ds in sorted({k[0] for k in G}):
  keys=sorted(k for k in G if k[0]==ds)
  for source in keys:
   for target in keys:
    if source==target:continue
    for n in NS:
     for delta in DS:
      kq=math.ceil((n+1)*(1-delta))
      if n>len(CAL) or kq>n:
       rows.append({'dataset':ds,'source':f'{source[1]}_{source[2]}','target':f'{target[1]}_{target[2]}','n':n,'delta':delta,'status':'FINITE_SAMPLE_INFEASIBLE','coverage':'','online_mean_ndc':'','calibration_ndc':'','fixed_mean_ndc':'','oracle_mean_ndc':'','headroom_retention':''});continue
      sentinel=CAL[:n]; evaluation=CAL[n:]
      if not evaluation:
       rows.append({'dataset':ds,'source':f'{source[1]}_{source[2]}','target':f'{target[1]}_{target[2]}','n':n,'delta':delta,'status':'FINITE_SAMPLE_INFEASIBLE','coverage':'','online_mean_ndc':'','calibration_ndc':'','fixed_mean_ndc':'','oracle_mean_ndc':'','headroom_retention':''});continue
      ratios=sorted(budgets[target][q]/max(budgets[source][q],1) for q in sentinel);a=ratios[kq-1]
      alloc={q:ceil_grid(a*budgets[source][q]) for q in evaluation};cov=np.mean([alloc[q]>=budgets[target][q] for q in evaluation]);online=np.mean([G[target][q][alloc[q]][1] for q in evaluation]);fix=np.mean([G[target][q][fixed[target]][1] for q in evaluation]);oracle=np.mean([G[target][q][min(budgets[target][q],512)][1] for q in evaluation]);cal=sum(sum(G[target][q][int(e)][1] for e in E) for q in sentinel);ret=(fix-online)/(fix-oracle) if fix!=oracle else float('nan')
      base={'dataset':ds,'source':f'{source[1]}_{source[2]}','target':f'{target[1]}_{target[2]}','n':n,'delta':delta,'status':'EVALUATED_DEV_ONLY','coverage':cov,'online_mean_ndc':online,'calibration_ndc':cal,'fixed_mean_ndc':fix,'oracle_mean_ndc':oracle,'headroom_retention':ret};rows.append(base)
      for N in WORK:amort.append({**{z:base[z] for z in ('dataset','source','target','n','delta')},'workload':N,'amortized_mean_ndc':online+cal/N,'vs_fixed_fraction':(online+cal/N)/fix-1})
 out=ROOT/'results/rebuild_tax/derived';out.mkdir(parents=True,exist_ok=True)
 for name,data in [('conformal_coverage_dev.csv',rows),('calibration_amortization_dev.csv',amort)]:
  with open(out/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
 summary={'status':'DEVELOPMENT_ONLY_COMPLETE','calibration_queries_only':True,'calibration_count':250,'audit_queries_read':0,'validation_dev_accessed':False,'formal_test_accessed':False,'evaluated_cells':sum(r['status']=='EVALUATED_DEV_ONLY' for r in rows),'infeasible_cells':sum(r['status']=='FINITE_SAMPLE_INFEASIBLE' for r in rows),'new_hnsw_queries':0}
 (out/'calibration_dev_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
