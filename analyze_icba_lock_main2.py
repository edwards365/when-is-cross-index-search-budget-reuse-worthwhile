#!/usr/bin/env python3
"""Exact barrier decomposition on frozen 81-build Graph-ANNS records."""
import csv,gzip,glob
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib.pyplot as plt
from rcrs_fast_theory import safe_monotone_majorant

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs'); BASE=ROOT/'results/cross_index/g1'
OUT=ROOT/'results/icba_theory_lock';FIG=ROOT/'figures/icba_theory_lock';OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
GRID=np.array([10,16,24,32,48,64,96,128,192,256,384,512])
def load():
 G={}
 for idx in ['hnswlib','faiss','vamana']:
  for p in glob.glob(str(BASE/'main'/idx/'*.csv.gz')):
   with gzip.open(p,'rt',newline='') as f:rows=list(csv.DictReader(f))
   r=rows[0];k=(idx,r['dataset'],int(r.get('seed',r.get('graph_seed'))),r.get('history',r.get('insertion_order')));a=np.zeros((1000,12,2))
   for z in rows:
    q=int(z['query_id']);b=int(z.get('budget',z.get('ef_search')));j=int(np.where(GRID==b)[0][0]);a[q,j]=float(z['recall_at_10']),float(z['exact_ndc'])
   G[k]=a
 return G
def stable(a):
 o=np.full(1000,1024)
 for q in range(1000):
  for j,b in enumerate(GRID):
   if np.all(a[q,j:,0]>=.9):o[q]=b;break
 return o.astype(int)
G=load();B={k:stable(a) for k,a in G.items()}; old=pd.read_csv(ROOT/'results/theory_generalization/inversion_bounds.csv')
oldmap={(r['index'],r['dataset'],int(r['source_seed']),r['source_history'],int(r['target_seed']),r['target_history']):r for _,r in old.iterrows()}
pair=[];levels=[];t4=[]
for idx in ['hnswlib','faiss','vamana']:
 for ds in sorted({k[1] for k in G if k[0]==idx}):
  ks=sorted(k for k in G if k[0]==idx and k[1]==ds)
  for s in ks:
   for t in ks:
    if s==t:continue
    q=np.arange(250,1000);x=B[s][q];y=B[t][q];obs=y<=512;M,_=safe_monotone_majorant(x,y);tar=G[t]
    total=np.zeros(len(q));by=np.zeros(len(GRID))
    for ii in np.where(obs)[0]:
     jy=int(np.where(GRID==y[ii])[0][0]);jm=int(np.where(GRID==min(M[ii],512))[0][0])
     for l in range(jy+1,jm+1):
      inc=tar[q[ii],l,1]-tar[q[ii],l-1,1];total[ii]+=inc;by[l]+=inc
    direct=np.zeros(len(q));
    for ii in np.where(obs)[0]:
     jy=int(np.where(GRID==y[ii])[0][0]);jm=int(np.where(GRID==min(M[ii],512))[0][0]);direct[ii]=tar[q[ii],jm,1]-tar[q[ii],jy,1]
    if not np.allclose(total[obs],direct[obs]):raise AssertionError('barrier telescoping failed')
    trimmed=total[obs];cut=np.quantile(trimmed,.99);trimmed=trimmed[trimmed<=cut]
    common={'index':idx,'dataset':ds,'source_seed':s[2],'source_history':s[3],'target_seed':t[2],'target_history':t[3],'category':'same_order_cross_seed' if s[3]==t[3] else 'cross_order'}
    om=oldmap[(idx,ds,s[2],s[3],t[2],t[3])]
    pair.append(common|{'n':len(q),'observed_n':int(obs.sum()),'right_censoring_rate':float(1-obs.mean()),'exact_barrier_tax_total_ndc_observed':float(total[obs].sum()),'exact_barrier_tax_mean_ndc_observed':float(total[obs].mean()),'trim_top1pct_mean_ndc':float(trimmed.mean()),'positive_tax_query_rate':float(np.mean(total[obs]>0)),'matching_budget_gap_bound':float(om['matching_budget_gap_bound']),'matching_tightness_budget_gap':float(om['lower_bound_tightness_budget_gap']),'identity_check':True})
    for l,e in enumerate(GRID):levels.append(common|{'budget_level':int(e),'increment_from':int(GRID[l-1]) if l else 'BASE','barrier_contribution_ndc':float(by[l]),'fraction_of_pair_tax':float(by[l]/total[obs].sum()) if total[obs].sum()>0 else 0.0,'forced_crossing_query_count':int(sum(obs & (y<e) & (e<=M)))})
    t4.append(common|{'disposition':'PROVED_UNDER_EXPLICIT_CONDITIONS_RESTRICTED_PROPOSITION','conditions':'finite uncensored grid; additive linear budget-gap weights; vertex-disjoint inversion matching','general_claim':False,'computational_check':'n<=8,budget<=6 plus random property tests','exact_barrier_is_main_theorem':True})
P=pd.DataFrame(pair);L=pd.DataFrame(levels);T=pd.DataFrame(t4);P.to_csv(OUT/'exact_barrier_decomposition.csv',index=False);L.to_csv(OUT/'barrier_level_contributions.csv',index=False);T.to_csv(OUT/'t4_disposition.csv',index=False)
g=L.groupby('budget_level').barrier_contribution_ndc.sum();ax=g.plot(kind='bar',figsize=(8,4));ax.set_ylabel('Total forced incremental NDC');ax.set_title('Exact barrier contribution by budget level');plt.tight_layout();plt.savefig(FIG/'barrier_waterfall.png',dpi=180);plt.savefig(FIG/'barrier_waterfall.pdf');plt.close()
ax=P.plot.scatter(x='matching_budget_gap_bound',y='matching_tightness_budget_gap',logy=True,alpha=.5,figsize=(6,4));ax.set_title('Restricted matching-bound tightness');plt.tight_layout();plt.savefig(FIG/'matching_tightness.png',dpi=180);plt.savefig(FIG/'matching_tightness.pdf');plt.close()
print({'pairs':len(P),'identity':bool(P.identity_check.all()),'positive_pairs':int((P.exact_barrier_tax_total_ndc_observed>0).sum()),'t4':T.disposition.iloc[0]})
