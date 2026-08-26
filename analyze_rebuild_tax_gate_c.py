#!/usr/bin/env python3
import csv,gzip,glob,json,math
from pathlib import Path
import numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');RAW=ROOT/'results/rebuild_tax/validation_raw';OUT=ROOT/'results/rebuild_tax/derived';E=np.array([10,16,24,32,48,64,96,128,192,256,384,512]);NS=[32,64,128,256,512,1000];DELTAS=[.05,.01,.005,.001];WORK=[10**3,10**4,10**5,10**6,10**7];RNG=np.random.default_rng(991)
def load():
 G={}
 for p in glob.glob(str(RAW/'*.csv.gz')):
  with gzip.open(p,'rt',newline='') as f:rows=list(csv.DictReader(f))
  k=(rows[0]['dataset'],int(rows[0]['graph_seed']),rows[0]['insertion_order']);g={q:{} for q in range(2000)}
  for r in rows:g[int(r['query_id'])][int(r['ef_search'])]=(float(r['recall_at_10']),float(r['exact_ndc']))
  G[k]=g
 return G
def ceilgrid(x):return int(next((e for e in E if e>=x),512))
def wilson_upper(x,n,z=1.6448536269514722):
 p=x/n;d=1+z*z/n;return (p+z*z/(2*n)+z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
def main():
 G=load();cal=range(1000);audit=range(1000,2000);fixed={};B={}
 for k,g in G.items():
  target=.95 if any(np.mean([g[q][int(e)][0] for q in cal])>=.95 for e in E) else .90;fixed[k]=int(next((e for e in E if np.mean([g[q][int(e)][0] for q in cal])>=target),512));B[k]={}
  for q in range(2000):
   t=g[q][fixed[k]][0];B[k][q]=int(next((e for e in E if all(g[q][int(z)][0]>=t for z in E[E>=e])),1024))
 coverage=[];amort=[];boots=[];detail={}
 for n in NS:
  for delta in DELTAS:
   rank=math.ceil((n+1)*(1-delta))
   if rank>n:continue
   detail[(n,delta)]={}
   for ds in sorted({k[0] for k in G}):
    keys=sorted(k for k in G if k[0]==ds);under=[];rd=[];online=[];fixc=[];oracle=[];calcost=[];target_hist=[];target_seed=[]
    for s in keys:
     for t in keys:
      if s==t:continue
      ratios=sorted(B[t][q]/max(B[s][q],1) for q in range(n));a=ratios[rank-1];calcost.append(sum(sum(G[t][q][int(e)][1] for e in E) for q in range(n)))
      for q in audit:
       alloc=ceilgrid(a*B[s][q]);under.append(alloc<B[t][q]);online.append(G[t][q][alloc][1]);fixc.append(G[t][q][fixed[t]][1]);oracle.append(G[t][q][min(B[t][q],512)][1]);rd.append(G[t][q][alloc][0]-G[t][q][fixed[t]][0]);target_hist.append(t[2]);target_seed.append(t[1])
    under=np.asarray(under);rd=np.asarray(rd);online=np.asarray(online);fixc=np.asarray(fixc);oracle=np.asarray(oracle);ret=(fixc.mean()-online.mean())/(fixc.mean()-oracle.mean()) if fixc.mean()!=oracle.mean() else float('nan');wu=wilson_upper(int(under.sum()),len(under));p95ok=np.quantile(online,.95)<=np.quantile(fixc,.95);histok=all(np.mean(fixc[np.asarray(target_hist)==h]-online[np.asarray(target_hist)==h])>0 for h in set(target_hist));seedok=all(np.mean(fixc[np.asarray(target_seed)==s]-online[np.asarray(target_seed)==s])>0 for s in set(target_seed))
    row={'dataset':ds,'n':n,'delta':delta,'under_budget_rate':under.mean(),'under_budget_wilson_upper':wu,'recall_delta':rd.mean(),'online_mean_ndc':online.mean(),'fixed_mean_ndc':fixc.mean(),'oracle_mean_ndc':oracle.mean(),'headroom_retention':ret,'online_p95_ndc':np.quantile(online,.95),'fixed_p95_ndc':np.quantile(fixc,.95),'p95_nonworse':p95ok,'history_direction_consistent':histok,'seed_direction_consistent':seedok,'calibration_ndc':np.mean(calcost)};coverage.append(row);detail[(n,delta)][ds]=row
    # Query-level paired bootstrap after averaging ordered pairs within each query.
    m=72; qr=rd.reshape(m,1000).mean(0); qn=(fixc-online).reshape(m,1000).mean(0); idx=RNG.integers(0,1000,(5000,1000));boots.append({'dataset':ds,'n':n,'delta':delta,'recall_ci_low':np.quantile(qr[idx].mean(1),.025),'recall_ci_high':np.quantile(qr[idx].mean(1),.975),'ndc_saving_ci_low':np.quantile(qn[idx].mean(1),.025),'ndc_saving_ci_high':np.quantile(qn[idx].mean(1),.975)})
    for N in WORK:amort.append({'dataset':ds,'n':n,'delta':delta,'workload':N,'total_mean_ndc':online.mean()+np.mean(calcost)/N,'vs_fixed_fraction':(online.mean()+np.mean(calcost)/N)/fixc.mean()-1})
 candidates=[]
 for key,byds in detail.items():
  n,d=key;safe=bool(all(x['under_budget_wilson_upper']<=d for x in byds.values()));rec=bool(np.mean([x['recall_delta'] for x in byds.values()])>=-.001);ret=bool(sum(x['headroom_retention']>.2 for x in byds.values())>=2);p95=bool(all(x['p95_nonworse'] for x in byds.values()));direction=bool(all(x['history_direction_consistent'] and x['seed_direction_consistent'] for x in byds.values()));net=bool(any(np.mean([next(a['vs_fixed_fraction'] for a in amort if a['dataset']==ds and a['n']==n and a['delta']==d and a['workload']==N) for ds in byds])<-.01 for N in WORK if N>=100000));candidates.append({'n':n,'delta':d,'safe':safe,'recall_noninferior':rec,'retention':ret,'p95_nonworse':p95,'direction':direction,'net_benefit':net,'pass_all':safe and rec and ret and p95 and direction and net})
 passed=[x for x in candidates if x['pass_all']];safe_recall=[x for x in candidates if x['safe'] and x['recall_noninferior']]
 if passed:status='LIMITED_TO_RELAXED_RISK_REGIME' if all(x['delta']==.05 for x in passed) else 'AUTHORIZE_CERTIFIED_REBUILD_CALIBRATION'
 elif safe_recall:status='KEEP_BOUNDARY_STUDY_CERTIFICATION_IS_COSTLY'
 else:status='RECALIBRATION_CANNOT_CERTIFY_TRANSFER'
 def write(name,rows):
  with open(OUT/name,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 write('conformal_coverage.csv',coverage);write('calibration_amortization.csv',amort);write('gate_c_bootstrap.csv',boots);summary={'status':status,'candidates':candidates,'gate_m':'PASS','gate_t':'PASS','graphs':27,'raw_rows':648000,'validation_calibration_queries':1000,'validation_audit_queries':1000,'formal_test_accessed':False};(OUT/'gate_c_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
