#!/usr/bin/env python3
"""Frozen single-prefix realizability diagnostic using existing 100K rows only."""
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');OUT=ROOT/'results/hardness_portability_100k/single_prefix';OUT.mkdir(parents=True,exist_ok=False)
E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);split=json.loads((ROOT/'manifests/hardness_portability_100k/query_split.json').read_text())['splits'];CAL=np.array(split['train_design']);AUD=np.array(split['internal_test'])

def load():
 graphs={}
 for root in ('core_raw','realistic_raw'):
  for path in sorted(glob.glob(str(ROOT/f'results/hardness_portability_100k/{root}/*.csv.gz'))):
   with gzip.open(path,'rt',newline='') as f:rows=list(csv.DictReader(f))
   key=(rows[0]['dataset'],int(rows[0]['graph_seed']),rows[0]['insertion_order']);curves={q:{} for q in range(1000)}
   for r in rows:curves[int(r['query_id'])][int(r['ef_search'])]={'rec':float(r['recall_at_10']),'ndc':float(r['exact_ndc']),'ids':set(map(int,r['returned_top10_ids'].split(';')))}
   graphs[key]=curves
 return graphs
def stable(curve):
 for ef in E:
  if all(curve[int(x)]['rec']>=.9 for x in E[E>=ef]):return int(ef)
 return 1024
def ceilgrid(x):
 z=E[E>=x];return int(z[0]) if len(z) else 512
def features(graph,q):
 a,b=graph[q][16],graph[q][24];inter=len(a['ids']&b['ids'])
 return [1-inter/10,inter/10,math.log1p(a['ndc']),math.log1p(b['ndc']),math.log1p(max(0,b['ndc']-a['ndc']))]

G=load();rows=[]
for key,graph in sorted(G.items()):
 y=np.array([stable(graph[q]) for q in range(1000)]);X=np.array([features(graph,q) for q in range(1000)])
 model=LogisticRegression(C=1.0,max_iter=500,random_state=20260915,multi_class='auto').fit(X[CAL],y[CAL]);proba=model.predict_proba(X);raw=2**(proba@np.log2(model.classes_))
 target=.95 if any(np.mean([graph[int(q)][int(e)]['rec'] for q in CAL])>=.95 for e in E) else .90;fixed=next((int(e) for e in E if np.mean([graph[int(q)][int(e)]['rec'] for q in CAL])>=target),512);baseline=np.mean([graph[int(q)][fixed]['rec'] for q in CAL]);candidates=sorted({float(e/raw[int(q)]) for q in CAL for e in E});mul=candidates[-1]
 for z in candidates:
  if np.mean([graph[int(q)][ceilgrid(z*raw[int(q)])]['rec'] for q in CAL])>=baseline-.001:mul=z;break
 recall=[];no_reuse=[];ideal=[];fixed_cost=[]
 for q in AUD:
  q=int(q);pred=ceilgrid(mul*raw[q]);probe_final=max(24,pred);fc=graph[q][fixed]['ndc'];fixed_cost.append(fc);recall.append(graph[q][pred]['rec']-graph[q][fixed]['rec']);no_reuse.append(graph[q][16]['ndc']+graph[q][24]['ndc']+graph[q][pred]['ndc']);ideal.append(graph[q][probe_final]['ndc'])
 fixed_cost=np.asarray(fixed_cost);no_reuse=np.asarray(no_reuse);ideal=np.asarray(ideal)
 rows.append({'dataset':key[0],'seed':key[1],'order':key[2],'fixed_ef':fixed,'multiplier':mul,'recall_diff':float(np.mean(recall)),'no_reuse_net_gain':float(np.mean((fixed_cost-no_reuse)/fixed_cost)),'ideal_reuse_net_gain':float(np.mean((fixed_cost-ideal)/fixed_cost)),'fixed_p95_ndc':float(np.quantile(fixed_cost,.95)),'ideal_p95_ndc':float(np.quantile(ideal,.95)),'actual_resumable_prefix_available':False})

datasets={}
for ds in sorted({r['dataset'] for r in rows}):
 group=[r for r in rows if r['dataset']==ds];datasets[ds]={'graphs':len(group),'mean_recall_diff':float(np.mean([r['recall_diff'] for r in group])),'worst_recall_diff':float(min(r['recall_diff'] for r in group)),'mean_no_reuse_net_gain':float(np.mean([r['no_reuse_net_gain'] for r in group])),'mean_ideal_reuse_net_gain':float(np.mean([r['ideal_reuse_net_gain'] for r in group])),'all_seed_history_directions_nonnegative_ideal':all(r['ideal_reuse_net_gain']>0 for r in group),'actual_resumable_prefix_available':False}
decision={'schema_version':1,'protocol':'Query Hardness Is Not Portable 100K','status':'REALIZABILITY_GAP_PERSISTS','reason':'Frozen tracer records events but does not serialize candidate/result queues and visited state; existing independent-ef traces cannot identify exact continuation cost. The ideal full-reuse lower bound is reported but cannot authorize a method.','model':'multinomial logistic regression','features':['answer_set_flux_16_24','answer_set_overlap_16_24','log_ndc16','log_ndc24','log_ndc_delta'],'training_split':'train_design_250','evaluation_split':'confirmatory_audit_750_once','actual_candidate_gate_pass':False,'datasets':datasets,'graphs':len(rows),'formal_test_accessed':False}
with (OUT/'per_graph.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(OUT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n');print(json.dumps(decision,indent=2))
