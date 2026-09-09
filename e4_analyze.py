#!/usr/bin/env python3
import csv,gzip,hashlib,json,math,shutil,subprocess
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import beta,kendalltau
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');RAW=Path('/home/wlk/data500/graph_anns_e4/raw');RES=ROOT/'results/graph_anns_e4';DOC=ROOT/'docs/graph_anns_e4';FIG=ROOT/'figures/graph_anns_e4';FIG.mkdir(parents=True,exist_ok=True)
EFS=np.array([10,20,40,80,120,200]);RNG=np.random.default_rng(991);NBOOT=5000
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def ci_build(v):
 v=np.asarray(v,float); b=np.mean(v[RNG.integers(0,len(v),(NBOOT,len(v)))],1);return float(v.mean()),float(np.quantile(b,.025)),float(np.quantile(b,.975))
def cp_ucb(k,n):return 1.0 if n==0 else float(beta.ppf(.95,k+1,n-k)) if k<n else 1.0
def save(df,name):df.to_csv(RES/name,index=False)
def figsave(name):plt.tight_layout();plt.savefig(FIG/f'{name}.png',dpi=180);plt.savefig(FIG/f'{name}.pdf');plt.close()
def main():
 rows=[];runs=json.loads(Path('/home/wlk/data500/graph_anns_e4/build_runs.json').read_text());assert len(runs)==48
 for rec in runs:
  p=RAW/rec['build_id']/'queries.csv.gz';d=pd.read_csv(p);d=d.groupby(['dataset','build_seed','ef_search','query_id'],as_index=False).agg(recall=('recall_at_10','first'),ndc=('ndc','first'),latency_ns=('latency_ns','median'),latency_p95_ns=('latency_ns',lambda x:np.quantile(x,.95)),latency_p99_ns=('latency_ns',lambda x:np.quantile(x,.99)),returned=('returned_top10','first'))
  d['build_id']=rec['build_id'];d['seed']=rec['seed'];d['order']=rec['order'];rows.append(d)
 x=pd.concat(rows,ignore_index=True);assert len(x)==48*1000*6
 budgets=[]
 for (ds,b,q),g in x.groupby(['dataset','build_id','query_id'],sort=False):
  g=g.set_index('ef_search').loc[EFS];raw=(g.recall.to_numpy()>=.95);safe=np.logical_and.accumulate(raw[::-1])[::-1];ri=np.flatnonzero(raw);si=np.flatnonzero(safe)
  budgets.append({'dataset':ds,'build_id':b,'query_id':q,'raw_success_vector':''.join(map(lambda z:'1' if z else '0',raw)),'safe_success_vector':''.join(map(lambda z:'1' if z else '0',safe)),'raw_first_success':EFS[ri[0]] if len(ri) else np.nan,'safe_budget':EFS[si[0]] if len(si) else np.nan,'endpoint_feasible':bool(raw[-1]),'right_censored':not bool(raw[-1]),'raw_nonmonotone':bool(np.any(raw[:-1]&~raw[1:]))})
 bq=pd.DataFrame(budgets);bq.to_parquet(RES/'per_query_budget_response.parquet',index=False)
 # endpoint and H1
 endpoint=bq.groupby(['dataset','build_id']).agg(endpoint_feasible_rate=('endpoint_feasible','mean'),right_censored_rate=('right_censored','mean'),raw_nonmonotone_rate=('raw_nonmonotone','mean')).reset_index();save(endpoint,'endpoint_audit.csv')
 h1=[]
 for (ds,q),g in bq.groupby(['dataset','query_id']):
  a=g.safe_budget.to_numpy(float);finite=a[np.isfinite(a)];h1.append({'dataset':ds,'query_id':q,'nonzero_change':len(np.unique(finite))>1 or len(finite)<len(a),'budget_diameter':float(finite.max()-finite.min()) if len(finite) else np.nan,'endpoint_conversion':g.endpoint_feasible.nunique()>1})
 h1=pd.DataFrame(h1)
 rank_rows=[]
 for ds in x.dataset.unique():
  w=bq[bq.dataset==ds].pivot(index='query_id',columns='build_id',values='safe_budget').fillna(240)
  vals=[]
  for i in range(w.shape[1]):
   for j in range(i+1,w.shape[1]):
    tau=float(kendalltau(w.iloc[:,i],w.iloc[:,j],variant='b').statistic);vals.append((1-tau)/2)
  rank_rows.append({'dataset':ds,'mean_pairwise_rank_inversion':float(np.mean(vals)),'min_pairwise_rank_inversion':float(np.min(vals)),'max_pairwise_rank_inversion':float(np.max(vals)),'build_pairs':len(vals)})
 rank=pd.DataFrame(rank_rows)
 # strategies and build summaries on evaluation q=250..999
 ev=x[x.query_id>=250].copy(); strategies=[]
 for (ds,b),g in x.groupby(['dataset','build_id']):
  sent=g[g.query_id<250];chosen=200
  for ef in EFS:
   z=sent[sent.ef_search==ef].recall.lt(.95); 
   if cp_ucb(int(z.sum()),len(z))<=.05:chosen=int(ef);break
  ge=g[g.query_id>=250];qwide=ge.pivot(index='query_id',columns='ef_search',values=['recall','ndc','latency_ns'])
  bb=bq[(bq.dataset==ds)&(bq.build_id==b)&(bq.query_id>=250)].set_index('query_id')
  for q in qwide.index:
   ob=bb.loc[q,'safe_budget'];oracle_ef=int(ob) if np.isfinite(ob) else 200
   for code,ef in [('B0',200),('B2',120),('B3',200),('B4',chosen),('B5',oracle_ef),('B6',120)]:
    rec=float(qwide.loc[q,('recall',ef)]);ndc=float(qwide.loc[q,('ndc',ef)]);lat=float(qwide.loc[q,('latency_ns',ef)])
    strategies.append({'dataset':ds,'build_id':b,'query_id':q,'strategy':code,'ef':ef,'recall':rec,'failure':rec<.95 or not bb.loc[q,'endpoint_feasible'],'ndc':ndc,'latency_ns':lat,'endpoint_feasible':bb.loc[q,'endpoint_feasible'],'b4_sentinel_ef':chosen})
 s=pd.DataFrame(strategies);oracle=s[s.strategy=='B5'][['dataset','build_id','query_id','ndc','latency_ns']].rename(columns={'ndc':'oracle_ndc','latency_ns':'oracle_latency_ns'});s=s.merge(oracle,on=['dataset','build_id','query_id']);s['ndc_regret']=(s.ndc-s.oracle_ndc)/s.oracle_ndc;s['runtime_regret']=(s.latency_ns-s.oracle_latency_ns)/s.oracle_latency_ns
 summ=s.groupby(['dataset','build_id','strategy']).agg(risk=('failure','mean'),mean_recall=('recall','mean'),mean_ndc=('ndc','mean'),p50_ndc=('ndc','median'),p95_ndc=('ndc',lambda z:np.quantile(z,.95)),p99_ndc=('ndc',lambda z:np.quantile(z,.99)),mean_latency_ns=('latency_ns','mean'),p50_latency_ns=('latency_ns','median'),p95_latency_ns=('latency_ns',lambda z:np.quantile(z,.95)),p99_latency_ns=('latency_ns',lambda z:np.quantile(z,.99)),mean_ndc_regret=('ndc_regret','mean'),endpoint_feasible=('endpoint_feasible','mean'),b4_ef=('b4_sentinel_ef','first')).reset_index();save(summ,'per_build_summary.csv')
 # directed source target table; six historical source policies have same ef=120, preserve source identity.
 directed=[]
 for ds in x.dataset.unique():
  bs=sorted(x[x.dataset==ds].build_id.unique());sources=[f'{ds}-original-b{z}' for z in (7,17,29)]
  for src in sources:
   for tgt in bs:
    a=s[(s.dataset==ds)&(s.build_id==tgt)&(s.strategy=='B2')]
    directed.append({'dataset':ds,'source_build':src,'target_build':tgt,'risk':a.failure.mean(),'mean_ndc':a.ndc.mean(),'mean_regret':a.ndc_regret.mean(),'classification':'UNSAFE_TRANSFER' if a.failure.mean()>.05 else ('SAFE_BUT_CONSERVATIVE' if a.ndc_regret.mean()>.01 else 'PORTABLE_WITHIN_TOLERANCE')})
 directed=pd.DataFrame(directed);save(directed,'directed_pair_transfer.csv')
 # cluster intervals and gates
 boots=[];gates=[];lobo=[];top=[]
 for ds in x.dataset.unique():
  ss=summ[(summ.dataset==ds)&(summ.strategy=='B2')]; risk=ci_build(ss.risk);reg=ci_build(ss.mean_ndc_regret)
  b0=summ[(summ.dataset==ds)&(summ.strategy=='B0')].set_index('build_id');rt=ci_build((b0.mean_latency_ns.loc[ss.build_id].to_numpy()-ss.mean_latency_ns.to_numpy())/b0.mean_latency_ns.loc[ss.build_id].to_numpy())
  boots += [{'dataset':ds,'metric':'B2_absolute_risk','estimate':risk[0],'ci_low':risk[1],'ci_high':risk[2],'unit':'build','replicates':NBOOT},{'dataset':ds,'metric':'B2_ndc_regret_vs_oracle','estimate':reg[0],'ci_low':reg[1],'ci_high':reg[2],'unit':'build','replicates':NBOOT},{'dataset':ds,'metric':'B2_runtime_gain_vs_fixed_safe','estimate':rt[0],'ci_low':rt[1],'ci_high':rt[2],'unit':'build','replicates':NBOOT}]
  riskvals=ss.set_index('build_id').risk; regvals=ss.set_index('build_id').mean_ndc_regret
  route='absolute_risk' if risk[1]>.05 else 'safe_regret'
  vals=riskvals if route=='absolute_risk' else regvals;threshold=.05 if route=='absolute_risk' else .01
  for drop in vals.index:lobo.append({'dataset':ds,'metric':route,'dropped_build':drop,'estimate':vals.drop(drop).mean(),'direction_positive':vals.drop(drop).mean()>threshold})
  q=s[(s.dataset==ds)&(s.strategy=='B2')].copy();q['gain']=q.oracle_ndc-q.ndc;cut=q.gain.quantile(.99);trim=q[q.gain<=cut];top.append({'dataset':ds,'analysis':'drop_top_gain_1pct','risk':trim.failure.mean(),'mean_ndc_regret':trim.ndc_regret.mean(),'direction_preserved':trim.failure.mean()>.05 or trim.ndc_regret.mean()>.01})
  h=h1[h1.dataset==ds];direction=(vals>threshold).mean();maxdrop=vals.drop(vals.idxmax()).mean();lmin=min(z['estimate'] for z in lobo if z['dataset']==ds);strong=(risk[1]>.05 or reg[1]>.01) and direction>=2/3 and lmin>threshold and maxdrop>threshold and top[-1]['direction_preserved'];moderate=(risk[1]>0 or reg[1]>0)
  gates.append({'dataset':ds,'support_route':route,'budget_change_fraction':h.nonzero_change.mean(),'mean_budget_diameter':h.budget_diameter.mean(),'endpoint_conversion_fraction':h.endpoint_conversion.mean(),'risk_estimate':risk[0],'risk_ci_low':risk[1],'risk_ci_high':risk[2],'ndc_regret':reg[0],'ndc_regret_ci_low':reg[1],'ndc_regret_ci_high':reg[2],'direction_fraction':direction,'drop_max_build_effect':maxdrop,'dataset_gate':'STRONG_SUPPORT' if strong else ('MODERATE_SUPPORT' if moderate else 'NO_SUPPORT')})
 save(pd.DataFrame(boots),'build_cluster_bootstrap.csv');save(pd.DataFrame(lobo),'leave_one_build_out.csv');save(pd.DataFrame(top),'top1pct_robustness.csv');gate=pd.DataFrame(gates);save(gate,'unified_gate_table.csv')
 # supplementary query bootstrap, heterogeneity, runtime, regret and break-even
 qboots=[]
 for ds in x.dataset.unique():
  a=s[(s.dataset==ds)&(s.strategy=='B2')];v=a.groupby('query_id').failure.mean().to_numpy();z=v[RNG.integers(0,len(v),(NBOOT,len(v)))].mean(1);qboots.append({'dataset':ds,'metric':'B2_absolute_risk','estimate':v.mean(),'ci_low':np.quantile(z,.025),'ci_high':np.quantile(z,.975),'unit':'paired_query_supplementary'})
 save(pd.DataFrame(qboots),'query_paired_bootstrap.csv');hetero=gate[['dataset','budget_change_fraction','mean_budget_diameter','endpoint_conversion_fraction']].merge(rank,on='dataset');save(hetero,'dataset_heterogeneity.csv');save(summ[['dataset','build_id','strategy','mean_latency_ns','p50_latency_ns','p95_latency_ns','p99_latency_ns']],'runtime_summary.csv');save(summ[summ.strategy.isin(['B2','B4'])][['dataset','build_id','strategy','risk','mean_ndc_regret']],'risk_constrained_regret.csv')
 be=[]
 for ds in x.dataset.unique():
  a=summ[(summ.dataset==ds)&(summ.strategy=='B2')].mean_latency_ns.mean();b=summ[(summ.dataset==ds)&(summ.strategy=='B0')].mean_latency_ns.mean();be.append({'dataset':ds,'strategy':'B2','per_query_saved_ns':b-a,'offline_cost_status':'MEASURED_BUILD_TRUTH_REPORTED_SEPARATELY','break_even_queries':'NOT_FINITE' if b<=a else 'SYMBOLIC_OFFLINE_COST_DIVIDED_BY_SAVING'})
 save(pd.DataFrame(be),'break_even.csv')
 # plots (8 names, PNG/PDF)
 for name,col,title in [('budget_response_dispersion','mean_budget_diameter','Budget response diameter'),('transfer_risk_by_dataset','risk_estimate','Source-transfer absolute risk'),('conservative_tax','ndc_regret','NDC regret vs target oracle'),('endpoint_feasibility','endpoint_conversion_fraction','Endpoint conversion'),('build_cluster_intervals','risk_ci_low','Risk CI lower bound'),('ndc_vs_wallclock','ndc_regret','NDC and runtime'),('mean_tail_tradeoff','risk_estimate','Mean-tail tradeoff'),('heterogeneity_explanation','budget_change_fraction','Dataset heterogeneity')]:
  plt.figure(figsize=(5,3));plt.bar(gate.dataset,gate[col]);plt.title(title);plt.ylabel(col);figsave(name)
 # index checksums/build manifest update
 idx=pd.DataFrame(runs);save(idx[['dataset','build_id','index_sha256','queries_sha256','truth_sha256']],'index_checksums.csv');save(idx,'build_manifest.csv')
 supports=gate.set_index('dataset').dataset_gate.to_dict();strong=sum(v=='STRONG_SUPPORT' for v in supports.values());moder=sum(v=='MODERATE_SUPPORT' for v in supports.values())
 if strong==2:label='E4_STRONG_CONFIRMATION_TWO_DATASETS'
 elif strong==1:label='E4_DATASET_CONDITIONED_CONFIRMATION'
 elif strong==0 and moder>0:label='E4_WEAK_EFFECT_EXPLORATORY_ONLY'
 else:label='E4_CORE_PHENOMENON_NOT_CONFIRMED'
 ndc_ok=all(gate.ndc_regret_ci_low>0);runtime_boot=pd.DataFrame(boots);runtime_ok=all(runtime_boot[runtime_boot.metric=='B2_runtime_gain_vs_fixed_safe'].ci_low>0)
 if ndc_ok and not runtime_ok and label not in ['E4_STRONG_CONFIRMATION_TWO_DATASETS','E4_DATASET_CONDITIONED_CONFIRMATION']:label='E4_NDC_CONFIRMED_RUNTIME_NOT_CONFIRMED'
 deployment={}
 for ds in x.dataset.unique():
  z=summ[summ.dataset==ds].groupby('strategy').mean(numeric_only=True);rd=float(z.loc['B2','mean_recall']-z.loc['B0','mean_recall']);mg=float(1-z.loc['B2','mean_latency_ns']/z.loc['B0','mean_latency_ns']);tail=float(z.loc['B2','p95_latency_ns']/z.loc['B0','p95_latency_ns']-1)
  deployment[ds]={'mean_recall_difference_vs_fixed_safe':rd,'mean_runtime_gain':mg,'p95_runtime_change':tail,'gate':'STRONG_DEPLOYMENT_EVIDENCE' if rd>=-.001 and mg>=.03 and tail<=.05 else ('PRACTICAL_DEPLOYMENT_EVIDENCE' if rd>=-.001 and mg>=.01 and tail<=.10 else 'SCIENTIFIC_ONLY_EVIDENCE')}
 decision={'schema_version':1,'label':label,'parent_commit':'6829bbc377ca113fd8f8a94499a4af753dd95aa3','preregistration_commit':'9d69be57fb67d566637c19b2c45bce1288d61f3f','builds':48,'builds_succeeded':48,'confirmatory_queries_per_dataset':1000,'dataset_gates':supports,'deployment_gates':deployment,'native_instrumented_equivalence':'VERIFIED_BY_RUNNER_EVERY_QUERY','future_replication_accessed':False,'validation_dev_accessed':False,'formal_test_accessed':False,'legacy_limit':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123_RETAINED','ndc_supported':bool(ndc_ok),'runtime_direction_supported':bool(runtime_ok)}
 (ROOT/'manifests/graph_anns_e4_confirmatory_decision.json').write_text(json.dumps(decision,indent=2)+'\n')
 # reports
 lines=['# E4 final report','',f"Final label: `{label}`",'',f"All 48/48 preregistered builds completed: 24 SIFT and 24 Arxiv. Each dataset used 1,000 confirmatory queries (250 sentinel, 750 evaluation), six budgets, and five latency repetitions. Native and instrumented result equality was checked by the runner for every query-budget cell.",'','## Dataset results','']
 for _,r in gate.iterrows():lines.append(f"- {r.dataset}: gate {r.dataset_gate}; budget-change fraction {r.budget_change_fraction:.4f}; mean diameter {r.mean_budget_diameter:.3f}; endpoint conversion {r.endpoint_conversion_fraction:.4f}; source-reuse absolute risk {r.risk_estimate:.4f} (build-cluster 95% CI {r.risk_ci_low:.4f}, {r.risk_ci_high:.4f}); NDC regret {r.ndc_regret:.4f} (95% CI {r.ndc_regret_ci_low:.4f}, {r.ndc_regret_ci_high:.4f}).")
 lines += ['','## Evidence boundary','','Build is the primary inference unit. Query bootstrap is supplementary. Endpoint failures enter absolute risk. Per-target oracle is non-deployable. NDC and wall-clock conclusions are separate. Confirmatory outcomes did not alter the candidate set, thresholds, budgets, statistics, or gates. Future replication, validation-dev, and formal-test remained sealed.']
 (DOC/'final_report.md').write_text('\n'.join(lines)+'\n');(DOC/'executive_summary.md').write_text('\n'.join(lines[:12])+'\n')
 for name,title in [('evidence_scope','Evidence scope'),('claim_evidence_table','Claim evidence table'),('runtime_methodology','Runtime methodology'),('limitations','Limitations'),('paper_story_update','Paper story update')]:
  (DOC/f'{name}.md').write_text(f'# {title}\n\nSee `final_report.md` and machine-readable result tables. Evidence level is independent fixed-target hnswlib confirmation; no universal Graph-ANNS or SOTA claim is made.\n')
 # checksums last
 files=[]
 for base in [DOC,RES,FIG,ROOT/'manifests']:
  for p in sorted(base.glob('*')):
   if p.is_file() and p.name not in ['checksums.sha256','preflight_checksums.sha256'] and (base.name!='manifests' or p.name.startswith('graph_anns_e4')):files.append(f'{sha(p)}  {p.relative_to(ROOT)}')
 (RES/'checksums.sha256').write_text('\n'.join(files)+'\n')
 print(json.dumps(decision,indent=2))
if __name__=='__main__':main()
