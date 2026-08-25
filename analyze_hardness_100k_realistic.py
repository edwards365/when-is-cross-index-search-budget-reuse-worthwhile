#!/usr/bin/env python3
"""Frozen realistic-history Gate analysis, committed before result inspection."""
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr,kendalltau

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
CORE=ROOT/'results/hardness_portability_100k/core_raw';REAL=ROOT/'results/hardness_portability_100k/realistic_raw';OUT=ROOT/'results/hardness_portability_100k/realistic_derived';OUT.mkdir(parents=True,exist_ok=False)
E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);split=json.loads((ROOT/'manifests/hardness_portability_100k/query_split.json').read_text())['splits'];CAL=np.array(split['train_design']);AUD=np.array(split['internal_test']);RNG=np.random.default_rng(991)

def load(root):
 graphs={}
 for path in sorted(glob.glob(str(root/'*.csv.gz'))):
  with gzip.open(path,'rt',newline='') as f:rows=list(csv.DictReader(f))
  if len(rows)!=12000:raise RuntimeError('coverage '+path)
  key=(rows[0]['dataset'],int(rows[0]['graph_seed']),rows[0]['insertion_order']);curves={q:{} for q in range(1000)}
  for r in rows:curves[int(r['query_id'])][int(r['ef_search'])]={'rec':float(r['recall_at_10']),'ndc':float(r['exact_ndc'])}
  if any(set(curves[q])!=set(E) for q in curves):raise RuntimeError('grid '+path)
  graphs[key]=curves
 return graphs
def stable(curve):
 for ef in E:
  if all(curve[int(x)]['rec']>=.9 for x in E[E>=ef]):return int(ef)
 return 1024
def ceilgrid(value):
 z=E[E>=value];return int(z[0]) if len(z) else 512
def ci(values):return [float(np.quantile(values,.025)),float(np.quantile(values,.975))]

G=load(CORE);G.update(load(REAL));DS=sorted({k[0] for k in G});budgets={k:{q:stable(g[q]) for q in range(1000)} for k,g in G.items()};fixed={}
for k,g in G.items():
 target=.95 if any(np.mean([g[int(q)][int(e)]['rec'] for q in CAL])>=.95 for e in E) else .90
 fixed[k]=next((int(e) for e in E if np.mean([g[int(q)][int(e)]['rec'] for q in CAL])>=target),512)

def transfer(source,target):
 gt=G[target];f=fixed[target];baseline=np.mean([gt[int(q)][f]['rec'] for q in CAL]);candidates=sorted({float(e/budgets[source][int(q)]) for q in CAL for e in E});mul=candidates[-1]
 for z in candidates:
  if np.mean([gt[int(q)][ceilgrid(z*budgets[source][int(q)])]['rec'] for q in CAL])>=baseline-.001:mul=z;break
 regrets=[];recall=[]
 for q in AUD:
  q=int(q);pred=ceilgrid(mul*budgets[source][q]);oracle=min(budgets[target][q],512);den=gt[q][f]['ndc'];regrets.append((gt[q][pred]['ndc']-gt[q][oracle]['ndc'])/den);recall.append(gt[q][pred]['rec']-gt[q][f]['rec'])
 return mul,np.asarray(regrets),float(np.mean(recall))

rows=[];summary={}
for ds in DS:
 random_keys=[(ds,s,'random') for s in (43,59,71)];baseline_vectors=[]
 for source in random_keys:
  for target in random_keys:
   if source!=target:baseline_vectors.append(transfer(source,target)[1])
 baseline=np.mean(baseline_vectors,axis=0);summary[ds]={}
 for order in ('natural_source_order','cluster_block_order'):
  vectors=[];recalls=[];rhos=[];taus=[]
  for seed in (43,59,71):
   random=(ds,seed,'random');real=(ds,seed,order)
   for source,target,direction in ((random,real,'random_to_realistic'),(real,random,'realistic_to_random')):
    mul,reg,rd=transfer(source,target);vectors.append(reg);recalls.append(rd)
    x=np.array([math.log2(budgets[source][int(q)]) for q in AUD]);y=np.array([math.log2(budgets[target][int(q)]) for q in AUD]);rho=float(spearmanr(x,y).statistic);tau=float(kendalltau(x,y).statistic);rhos.append(rho);taus.append(tau)
    rows.append({'dataset':ds,'order':order,'seed':seed,'direction':direction,'multiplier':mul,'mean_regret':float(reg.mean()),'recall_diff':rd,'spearman':rho,'kendall':tau,'rank_reversal_rate':float((1-tau)/2)})
  realistic=np.mean(vectors,axis=0);excess=realistic-baseline;boot=[float(excess[RNG.integers(0,len(excess),len(excess))].mean()) for _ in range(5000)]
  summary[ds][order]={'mean_realistic_regret':float(realistic.mean()),'random_cross_seed_regret':float(baseline.mean()),'excess_regret':float(excess.mean()),'ci95':ci(boot),'mean_recall_diff':float(np.mean(recalls)),'mean_spearman':float(np.mean(rhos)),'mean_rank_reversal':float(np.mean((1-np.asarray(taus))/2)),'globally_calibrated_residual_positive':bool(ci(boot)[0]>0)}

gate_by_dataset={ds:any(v['excess_regret']>0 and v['ci95'][0]>0 and v['globally_calibrated_residual_positive'] for v in orders.values()) for ds,orders in summary.items()};passed=sum(gate_by_dataset.values())>=2;status='KEEP_REALISTIC_HNSW_HISTORY_NONPORTABILITY' if passed else 'SHRINK_TO_ADVERSARIAL_ORDER_CONDITIONALITY'
decision={'schema_version':1,'protocol':'Query Hardness Is Not Portable 100K','status':status,'gate_pass':passed,'gate_by_dataset':gate_by_dataset,'summary':summary,'graphs':18,'rows':216000,'bootstrap_replicates':5000,'bootstrap_seed':991,'formal_test_accessed':False}
with (OUT/'realistic_transfer.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(OUT/'realistic_history_decision.json').write_text(json.dumps(decision,indent=2)+'\n');print(json.dumps(decision,indent=2))
