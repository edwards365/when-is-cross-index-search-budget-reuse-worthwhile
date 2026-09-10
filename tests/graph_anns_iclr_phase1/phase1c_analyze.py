#!/usr/bin/env python3
from __future__ import annotations
import csv,gzip,json,statistics
from pathlib import Path
import numpy as np

REPO=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
SCR=Path('/home/wlk/data500/graph_anns_iclr_phase1_scratch/phase1c')
OLD=Path('/home/wlk/data500/graph_anns_e4/raw')
OUT=REPO/'results/graph_anns_iclr_phase1'
GRID=np.array([10,20,40,80,120,200]); TAU=.95

def read(path):
 op=gzip.open if str(path).endswith('.gz') else open
 with op(path,'rt',newline='') as f:return list(csv.DictReader(f))
def write(path,rows):
 with open(path,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def load_build(path):
 rows=read(path); by={}
 for r in rows:
  q=int(r['query_id']);ef=int(r.get('ef_search',r.get('ef')));rec=float(r['recall_at_10'])
  by.setdefault(q,{})[ef]=rec
 return by
def paths(ds,regime):
 if regime=='D0':return sorted(OLD.glob(f'{ds}__seed*__random/queries.csv.gz'))
 return sorted(SCR.glob(f'{ds}/{regime}/*/queries.csv.gz'))
def build_times(ds,regime):
 if regime=='D0':
  return [json.loads(p.read_text())['build_seconds'] for p in sorted(OLD.glob(f'{ds}__seed*__random/COMPLETE.json'))]
 p=OUT/f'phase1c_{ds}_{regime}_registry.csv';return [float(r['build_wall_seconds']) for r in read(p)]
def summarize(ds,regime):
 ps=paths(ds,regime); builds=[load_build(p) for p in ps]; nq=min(750,min(len(x) for x in builds)); builds=[{q:x[q] for q in range(nq)} for x in builds]
 finite=np.zeros((len(builds),nq),bool); budget=np.full((len(builds),nq),np.nan); maxrec=np.zeros((len(builds),nq))
 for b,x in enumerate(builds):
  for q in range(nq):
   vals=x[q];safe=[ef for ef in GRID if vals.get(int(ef),-1)>=TAU];finite[b,q]=bool(safe);budget[b,q]=min(safe) if safe else np.nan;maxrec[b,q]=vals[200]
 cat=np.mean(np.any(finite!=finite[0],axis=0))
 diam=[]
 for q in range(nq):
  z=budget[:,q];z=z[np.isfinite(z)]
  if len(z)>=2:diam.append(float(z.max()-z.min()))
 riskq=np.zeros(nq);refq=np.zeros(nq);pairs=0
 for s in range(len(builds)):
  for t in range(len(builds)):
   if s==t:continue
   pairs+=1
   for q in range(nq):
    action=int(budget[s,q]) if finite[s,q] else 200
    target_fail=(not finite[t,q]) or builds[t][q][action]<TAU
    own_fail=not finite[t,q]
    riskq[q]+=target_fail;refq[q]+=own_fail
 riskq/=pairs;refq/=pairs;deltaq=riskq-refq
 rng=np.random.default_rng(991); boots=np.empty(5000)
 for i in range(5000):boots[i]=deltaq[rng.integers(0,nq,nq)].mean()
 finitevals=budget[np.isfinite(budget)]
 drop=np.argsort(deltaq)[-max(1,int(np.ceil(.01*nq))):];keep=np.ones(nq,bool);keep[drop]=False
 rec={
  'dataset':ds,'regime':regime,'builds':len(builds),'queries':nq,'ordered_pairs':pairs,
  'index_hash_unique':len({json.loads((p.parent/'COMPLETE.json').read_text())['index_sha256'] for p in ps}) if regime!='D0' else len(ps),
  'diagnostic_hash_unique':len({json.loads((p.parent/'COMPLETE.json').read_text())['diagnostic_topk_sha256'] for p in ps}) if regime!='D0' else 'NOT_RECORDED_D0',
  'category_variation':cat,'unresolved_mass':1-finite.mean(),'mean_numeric_diameter':np.mean(diam) if diam else 0,
  'reference_risk':refq.mean(),'transport_risk':riskq.mean(),'incremental_transport_risk':deltaq.mean(),
  'risk_ci_low':np.quantile(boots,.025),'risk_ci_high':np.quantile(boots,.975),
  'drop_top1_incremental_risk':deltaq[keep].mean(),'aggregate_recall_at_max':maxrec.mean(),
  'finite_budget_mean':finitevals.mean(),'finite_budget_p95':np.quantile(finitevals,.95),'finite_budget_p99':np.quantile(finitevals,.99),
  'build_median_seconds':statistics.median(build_times(ds,regime)),'future_roles_accessed':False}
 return rec
def main():
 rows=[summarize(ds,r) for ds in ('sift_100k','arxiv_nomic_100k') for r in ('D0','D1','D2','D3')]
 write(OUT/'deterministic_rebuild_results.csv',rows)
 gates=[]
 for ds in ('sift_100k','arxiv_nomic_100k'):
  d0=next(x for x in rows if x['dataset']==ds and x['regime']=='D0');d3=next(x for x in rows if x['dataset']==ds and x['regime']=='D3')
  checks={
   'category':d3['category_variation']<=.05 or d3['category_variation']<=.2*d0['category_variation'],
   'risk':d3['incremental_transport_risk']<=.02 or d3['incremental_transport_risk']<=.2*d0['incremental_transport_risk'],
   'recall':d3['aggregate_recall_at_max']-d0['aggregate_recall_at_max']>=-.001,
   'mean_cost':d3['finite_budget_mean']<=1.03*d0['finite_budget_mean'],
   'p95_cost':d3['finite_budget_p95']<=1.05*d0['finite_budget_p95'],
   'build':d3['build_median_seconds']<=1.2*d0['build_median_seconds'],
   'top1':d3['drop_top1_incremental_risk']<=.02,
   'byte_identical':d3['index_hash_unique']==1,
   'search_identical':d3['diagnostic_hash_unique']==1}
  gates.append({'dataset':ds,**checks,'all_pass':all(checks.values()),'recall_delta':d3['aggregate_recall_at_max']-d0['aggregate_recall_at_max'],'mean_budget_ratio':d3['finite_budget_mean']/d0['finite_budget_mean'],'p95_budget_ratio':d3['finite_budget_p95']/d0['finite_budget_p95'],'build_time_ratio':d3['build_median_seconds']/d0['build_median_seconds']})
 write(OUT/'deterministic_rebuild_gate.csv',gates)
 label='DETERMINISTIC_REBUILD_ACTIONABLE_MITIGATION' if all(x['all_pass'] for x in gates) else ('DETERMINISTIC_REBUILD_DATA_CONDITIONAL_MITIGATION' if any(x['all_pass'] for x in gates) else 'DETERMINISM_ACHIEVED_SERVICE_TRADEOFF_UNRESOLVED')
 write(OUT/'phase1c_label.csv',[{'component':'Mitigation','label':label,'two_dataset_gate':all(x['all_pass'] for x in gates)}])
 lines=['# Phase 1C deterministic rebuild seal','',f'Registered mitigation label: **{label}**.','',
 'D1 and D2 remain build- and search-variable on both datasets. D3 is byte-identical and search-identical across three repetitions on both datasets. Native finite safe budget is used as the implementation-internal cost because the Python-built indexes do not expose the frozen tracer NDC counter; no wall-clock equivalence claim is made.','']
 for g in gates:
  lines.append(f"- {g['dataset']}: Recall delta {float(g['recall_delta']):.6f}; mean safe-budget ratio {float(g['mean_budget_ratio']):.4f}; p95 ratio {float(g['p95_budget_ratio']):.4f}; build-time ratio {float(g['build_time_ratio']):.4f}; all registered gates={bool(g['all_pass'])}.")
 (REPO/'docs/graph_anns_iclr_phase1/phase1c_deterministic_report.md').write_text('\n'.join(lines)+'\n')
 print(label)
 print(json.dumps(gates,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
if __name__=='__main__':main()
