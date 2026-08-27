#!/usr/bin/env python3
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import Bounds,LinearConstraint,milp
from scipy.sparse import coo_matrix
from rcrs_fast_theory import safe_monotone_majorant
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs'); BASE=ROOT/'results/cross_index/g1'; OUT=ROOT/'results/rcrs_fast';OUT.mkdir(exist_ok=True)
GRID=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);RNG=np.random.default_rng(991)
def load():
 G={}
 for idx in ['hnswlib','faiss','vamana']:
  for p in glob.glob(str(BASE/'main'/idx/'*.csv.gz')):
   with gzip.open(p,'rt',newline='') as f:rows=list(csv.DictReader(f))
   r=rows[0];k=(idx,r['dataset'],int(r.get('seed',r.get('graph_seed'))),r.get('history',r.get('insertion_order')));a=np.zeros((1000,12,2))
   for x in rows:
    q=int(x['query_id']);b=int(x.get('budget',x.get('ef_search')));j=int(np.where(GRID==b)[0][0]);a[q,j]=float(x['recall_at_10']),float(x['exact_ndc'])
   G[k]=a
 return G
def stable(a):
 out=np.full(1000,1024)
 for q in range(1000):
  for j,b in enumerate(GRID):
   if np.all(a[q,j:,0]>=.9):out[q]=b;break
 return out
def compressed_matching(x,y):
 types=[]
 for a in sorted(set(zip(x.tolist(),y.tolist()))):types.append((a[0],a[1],int(np.sum((x==a[0])&(y==a[1])))))
 edges=[]
 for i,(xi,yi,_) in enumerate(types):
  for j,(xj,yj,_) in enumerate(types):
   if i<j:
    w=max((yi-yj if xi<=xj else 0),(yj-yi if xj<=xi else 0))
    if w>0:edges.append((i,j,float(w)))
 if not edges:return 0
 rr=[];cc=[]
 for e,(i,j,w) in enumerate(edges):rr.extend([i,j]);cc.extend([e,e])
 A=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(types),len(edges))).tocsr();cap=np.array([t[2] for t in types])
 z=milp(c=-np.array([e[2] for e in edges]),integrality=np.ones(len(edges)),bounds=Bounds(0,np.inf),constraints=LinearConstraint(A,0,cap),options={'time_limit':30})
 return float(-z.fun) if z.success else float('nan')
def boot(v):
 v=np.asarray(v);means=v[RNG.integers(0,len(v),(1000,len(v)))].mean(1);return float(np.quantile(means,.025)),float(np.quantile(means,.975))
def write(name,rows):
 with open(OUT/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
G=load();B={k:stable(a) for k,a in G.items()};mono=[];absreg=[];by={}
for idx in ['hnswlib','faiss','vamana']:
 for ds in sorted({k[1] for k in G}):
  keys=sorted(k for k in G if k[0]==idx and k[1]==ds);cats={'same':[],'cross':[]};taxes=[]
  for s in keys:
   for t in keys:
    if s==t:continue
    q=np.arange(250,1000);x=B[s][q];y=B[t][q];alloc,_=safe_monotone_majorant(x,y);alloc=np.minimum(alloc,512).astype(int);yo=np.minimum(y,512).astype(int)
    ji=np.searchsorted(GRID,alloc);jo=np.searchsorted(GRID,yo);target=G[t];oracle=target[q,jo,1];cost=target[q,ji,1];fixed_j=next((j for j in range(12) if target[:250,j,0].mean()>=.9),11);fixed=target[q,fixed_j,1]
    tax=(cost-oracle)/fixed;cat='same' if s[3]==t[3] else 'cross';cats[cat].append(tax);taxes.append(tax)
    inv=[]
    for i in range(len(q)):
     for j in range(i+1,len(q)):
      inv.append((x[i]-x[j])*(y[i]-y[j])<0)
    mb=compressed_matching(x,y)
    mono.append({'index':idx,'dataset':ds,'source_seed':s[2],'source_history':s[3],'target_seed':t[2],'target_history':t[3],'category':cat,'raw_inversion_rate':float(np.mean(inv)),'matching_budget_gap_bound':mb,'exact_monotone_ndc_tax':float(tax.mean()),'censored_rate':float(np.mean(y>512)),'evidence':'EXPLORATORY_FAST_BOOTSTRAP'})
  same=np.mean(cats['same'],axis=0);cross=np.mean(cats['cross'],axis=0);delta=cross-same;lo,hi=boot(delta)
  by[(idx,ds)]=delta
  absreg.append({'index':idx,'dataset':ds,'absolute_same_regret':float(same.mean()),'absolute_cross_regret':float(cross.mean()),'cross_minus_same':float(delta.mean()),'ci_low':lo,'ci_high':hi,'mean_exact_monotone_tax':float(np.mean(taxes)),'bootstrap':1000,'seed':991,'evidence':'EXPLORATORY_FAST_BOOTSTRAP'})
contrast=[]
for ds in sorted({k[1] for k in G}):
 for a,b in [('hnswlib','faiss'),('hnswlib','vamana')]:
  v=by[(a,ds)]-by[(b,ds)];lo,hi=boot(v);contrast.append({'dataset':ds,'contrast':a+'-'+b,'estimate':float(v.mean()),'ci_low':lo,'ci_high':hi,'bootstrap':1000,'seed':991})
write('monotone_tax.csv',mono);write('absolute_regret.csv',absreg);write('implementation_contrast.csv',contrast)
# Existing Tournament results are a distinct-query descriptive comparison only.
T=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rebuild-tournament/results/rebuild_algorithm/tournament');globc=list(csv.DictReader(open(T/'cost_autopsy.csv')));gcc=list(csv.DictReader(open(T/'gcc_results.csv')));gaps=[]
for ds in sorted({r['dataset'] for r in absreg}):
 opt=next(float(r['mean_exact_monotone_tax']) for r in absreg if r['index']=='hnswlib' and r['dataset']==ds)
 g=next(float(r['vs_fixed_fraction']) for r in globc if r['dataset']==ds and int(r['n'])==32 and float(r['delta'])==.05 and int(r['workload'])==100000)
 c=next(float(r['net_fraction']) for r in gcc if r['dataset']==ds and int(r['n'])==64)
 gaps.append({'dataset':ds,'optimal_monotone_tax':opt,'global_conformal_cost_fraction':g,'global_gap':g-opt,'gcc_cost_fraction':c,'gcc_gap':c-opt,'comparison':'DESCRIPTIVE_DISTINCT_QUERY_SPLITS'})
write('monotone_gap.csv',gaps)
summary={'status':'SPRINT_C_COMPLETE','graphs':81,'rows':972000,'bootstrap':1000,'seed':991,'formal_test_accessed':False,'validation_dev_accessed':False}
(OUT/'sprint_c_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
