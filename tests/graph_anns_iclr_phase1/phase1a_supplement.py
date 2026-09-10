#!/usr/bin/env python3
import io,subprocess
from pathlib import Path
import pandas as pd
from scipy.stats import beta
ROOT=Path(__file__).resolve().parents[2];O=ROOT/'results/graph_anns_iclr_phase1'
def g(c,p):return pd.read_csv(io.BytesIO(subprocess.check_output(['git','show',f'{c}:{p}'])))
rows=[]
h=g('d2ad714','results/graph_anns_cross_family_hotfix/hnswlib_top1_robustness.csv')
for _,x in h.iterrows():rows.append(['hnswlib HNSW',x.dataset,'TOP1_'+x.deletion_order,x.queries_deleted,x.delta_transport_risk,x.rom_cost_tax,x.risk_ci_low,x.risk_ci_high,'FINAL_552_PAIR_EXACT'])
f=g('8fd7b639','results/graph_anns_faiss_external_validity/contribution_deletion.csv')
for _,x in f.iterrows():rows.append(['Faiss HNSW',x.dataset,'TOP1_SOURCE_REGISTERED_CONTRIBUTION',x.deleted_queries,x.risk_increment,x.safe_rom_ndc_tax,'NOT_REPORTED','NOT_REPORTED','FROZEN_SOURCE_DIAGNOSTIC'])
v=g('47e354d','results/icba_vamana_stage1/robustness.csv')
for _,x in v[v.analysis.str.startswith('drop_top1')].iterrows():rows.append(['DiskANN3/Vamana-style',x.dataset,x.analysis.upper(),8,x.risk,x.cost_tax,'NOT_REPORTED','NOT_REPORTED','FROZEN_SOURCE_DIAGNOSTIC'])
pd.DataFrame(rows,columns=['implementation','dataset','analysis','queries_deleted','risk_increment','cost_tax','risk_ci_low','risk_ci_high','scope']).to_csv(O/'top1_robustness_summary.csv',index=False)
l=[]
for impl,c,p in [('hnswlib HNSW','dd160731','results/graph_anns_e4_hotfix/h2_robustness_corrected.csv'),('Faiss HNSW','8fd7b639','results/graph_anns_faiss_external_validity/leave_one_build_out.csv'),('DiskANN3/Vamana-style','47e354d','results/icba_vamana_stage1/robustness.csv')]:
 z=g(c,p)
 for ds in z.dataset.unique():
  q=z[z.dataset==ds]
  if impl=='hnswlib HNSW':q=q[q.analysis.isin(['leave_one_seed','leave_one_order'])];r='risk_increment';co='safe_rom_ndc_tax'
  elif impl=='Faiss HNSW':r='risk_increment';co='safe_rom_ndc_tax'
  else:q=q[q.analysis=='LOBO'];r='risk';co='cost_tax'
  l.append([impl,ds,len(q),q[r].min(),q[r].max(),q[co].min(),q[co].max(),bool((q[r]>0).all())])
pd.DataFrame(l,columns=['implementation','dataset','deletions','min_risk','max_risk','min_cost_tax','max_cost_tax','risk_direction_all_positive']).to_csv(O/'registered_build_robustness.csv',index=False)
cert=[]
for M in [1,6,24,36]:
 z=int(__import__('math').ceil(__import__('math').log(.05/M)/__import__('math').log(.95)))
 for n in [59,121,129,256,750]:
  ok=[]
  for k in range(n+1):
   u=1.0 if k==n else float(beta.ppf(1-.05/M,k+1,n-k))
   if u<=.05:ok.append(k)
  cert.append([M,n,z,max(ok) if ok else -1,1-(.05/M)**(1/n),.05/M])
pd.DataFrame(cert,columns=['candidate_M','n','zero_failure_sample_threshold','max_failures_allowed','zero_failure_cp_ucb','per_action_alpha']).to_csv(O/'certification_power_table.csv',index=False,float_format='%.12g')
print('PHASE1A_SUPPLEMENT_COMPLETE')
