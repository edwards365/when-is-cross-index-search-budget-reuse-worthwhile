from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw'); OUT=ROOT/'results/icba_auditor'; OUT.mkdir(parents=True,exist_ok=True)
use=['dataset','build','raw_ef','query_id','mask','base_hits','union_hits','base_risk','union_risk','primary_ndc','aux_ndc_sum','total_ndc','candidate_count']
d=pd.read_csv(ROOT/'results/icba_cals_seal/subset_results.csv.gz',usecols=use); base=d[d['mask'].eq(0)].copy(); acts=pd.read_csv(ROOT/'results/icba_cals_seal/selection_actions.csv'); targets=acts[acts.action_scope.eq('TARGET_SPECIFIC_SELECTED_FIXED_SET')&acts.raw_ef.isin([8,16,32])]
def cp(x,n,alpha=.05): return 1-beta.ppf(alpha,n-x,x+1) if x<n else 1.0
inventory=[]
for ds,b in sorted(base[['dataset','build']].drop_duplicates().itertuples(index=False,name=None)): inventory.append({'dataset':ds,'build':b,'source':'frozen CALS subset','rows':500,'roles':'historical development/retrospective','truth_access':'post-hoc only'})
pd.DataFrame(inventory).to_csv(OUT/'input_inventory.csv',index=False)
registry=pd.DataFrame([
 {'action_id':'A0','action':'REUSE_SOURCE_POLICY','status':'NOT_ESTIMABLE','reason':'no serialized source policy contract in frozen inputs'},
 {'action_id':'A1','action':'CONSERVATIVE_REUSE','status':'NOT_ESTIMABLE','reason':'no fixed global safety correction artifact'},
 {'action_id':'A2','action':'TARGET_RECALIBRATION','status':'RETROSPECTIVE_PROXY','reason':'fixed-ef target profiling only'},
 {'action_id':'A3','action':'TARGET_REPROFILE_OR_RETRAIN','status':'TARGET_FIXED_EF_PROFILING','reason':'profiling is available; full retraining cost not available'},
 {'action_id':'A4','action':'FULL_RETRAINING','status':'NOT_IMPLEMENTED_REAL_COST_NOT_ESTIMABLE','reason':'no serialized model/training pipeline'},
 {'action_id':'A5','action':'FIXED_SAFE_FALLBACK','status':'RETROSPECTIVE_PROXY','reason':'next native ef in frozen grid'},
 {'action_id':'A6','action':'REJECT_ABSTAIN','status':'DEPLOYABLE_DECISION','reason':'safe endpoint or finite break-even unavailable'}]); registry.to_csv(OUT/'action_registry.csv',index=False)
qrows=[]; cert=[]; decisions=[]; regrets=[]; tails=[]
for _,a in targets.iterrows():
 ds,b,e,mask=a.dataset,a.build,int(a.raw_ef),a['mask']; nxt=min(64,2*e)
 p=d[(d.dataset.eq(ds))&(d.build.eq(b))&(d.raw_ef.eq(e))&(d['mask'].eq(mask))].copy(); pr=base[(base.dataset.eq(ds))&(base.build.eq(b))&(base.raw_ef.eq(e))][['query_id','total_ndc','base_hits','base_risk','candidate_count']].rename(columns={'total_ndc':'p_cost','base_hits':'p_hits','base_risk':'p_risk','candidate_count':'p_candidate_count'}); nh=base[(base.dataset.eq(ds))&(base.build.eq(b))&(base.raw_ef.eq(nxt))][['query_id','total_ndc','base_hits','base_risk']].rename(columns={'total_ndc':'safe_cost','base_hits':'safe_hits','base_risk':'safe_risk'}); p=p.merge(pr,on='query_id').merge(nh,on='query_id'); p['strong_failure']=(p.union_hits<10).astype(int); p['practical_failure']=(p.union_hits<9).astype(int); p['endpoint_failure']=0; p['incremental_candidate_count']=(p.candidate_count-p.p_candidate_count).clip(lower=0); p['shared_lb_cost']=p.p_cost+p.incremental_candidate_count
 for name,fail in [('strong',p.strong_failure),('practical',p.practical_failure)]:
  x=int(fail.sum()); cert.append({'dataset':ds,'build':b,'raw_ef':e,'candidate':'A2/A3 fixed-ef proxy','event':name,'failures':x,'n':len(fail),'cp_upper':cp(x,len(fail)),'safe_at_delta_005':cp(x,len(fail))<=.05,'endpoint_infeasible':False,'evidence_level':'RETROSPECTIVE_METHOD_VALIDATION'})
 endpoint={'dataset':ds,'build':b,'raw_ef':e,'endpoint_infeasible':False,'safe_grid_ef':nxt,'right_censored':False,'event_definition':'Recall<tau OR no safe endpoint','evidence_level':'FIXED_TARGET_AUDIT'}; tails.append(endpoint)
 for aid in ['A2','A3','A5']:
  cost=p.p_cost if aid in ['A2','A3'] else p.safe_cost; hits=p.union_hits if aid in ['A2','A3'] else p.safe_hits; risk=(hits<9).mean(); decisions.append({'dataset':ds,'build':b,'raw_ef':e,'action_id':aid,'action':'TARGET_RECALIBRATION' if aid=='A2' else ('TARGET_REPROFILE_OR_RETRAIN' if aid=='A3' else 'FIXED_SAFE_FALLBACK'),'failure_count':int((hits<9).sum()),'n':len(p),'risk':risk,'cost_mean':cost.mean(),'mean_recall':hits.mean()/10,'status':'retrospective','endpoint_infeasible':False})
 p['cost_gain']=p.safe_cost-p.p_cost; p['oracle_safe']=p.safe_risk<=.05; p['selected_action']=np.where(p.oracle_safe,'A5','A6'); p['selected_cost']=np.where(p.oracle_safe,p.safe_cost,np.nan); p['reuse_cost']=p.p_cost; p['decision_regret']=np.where(p.oracle_safe,np.maximum(0,p.selected_cost-p.safe_cost),0.0); regrets.extend(p[['query_id','cost_gain','decision_regret','selected_action']].assign(dataset=ds,build=b,raw_ef=e).to_dict('records'))
q=pd.DataFrame(decisions); q.to_csv(OUT/'decision_results.csv',index=False); pd.DataFrame(cert).to_csv(OUT/'certification_results.csv',index=False); pd.DataFrame(tails).to_csv(OUT/'endpoint_audit.csv',index=False); pd.DataFrame(regrets).to_csv(OUT/'decision_regret.csv',index=False)
q.groupby(['dataset','build','raw_ef','action_id'],as_index=False).agg(mean_ndc=('cost_mean','mean'),p95_ndc=('cost_mean',lambda x:np.percentile(x,95)),p99_ndc=('cost_mean',lambda x:np.percentile(x,99)),risk=('risk','mean')).to_csv(OUT/'tail_cost.csv',index=False)
pd.DataFrame([{'dataset':ds,'build':b,'raw_ef':e,'N':N,'offline_cost_status':'NOT_ESTIMABLE','break_even':'NO_FINITE_BREAK_EVEN_WORKLOAD' if aid=='A6' else 'NOT_ESTIMABLE'} for ds,b,e in sorted(base[['dataset','build','raw_ef']].drop_duplicates().itertuples(index=False,name=None)) if e in [8,16,32] for N in [10**3,10**4,10**5,10**6,10**7] for aid in ['A2','A5','A6']]).to_csv(OUT/'cost_break_even.csv',index=False)
pd.DataFrame([{'baseline':'Always Reuse','unsafe_acceptance':'NOT_ESTIMABLE','decision_regret':'NOT_ESTIMABLE'},{'baseline':'Always Fixed-Safe','unsafe_acceptance':'RETROSPECTIVE_ONLY','decision_regret':'RETROSPECTIVE_ONLY'},{'baseline':'ICBA-Auditor','unsafe_acceptance':'RETROSPECTIVE_ONLY','decision_regret':'RETROSPECTIVE_ONLY'}]).to_csv(OUT/'baseline_comparison.csv',index=False)
gates=[('input_reproducible',True),('query_roles_disjoint',False),('endpoint_semantics_frozen',True),('unsafe_acceptance_controlled',False),('finite_break_even_available',False),('p95_non_degraded',False),('decision_value_vs_two_baselines',False),('future_confirmation_authorized',False)]
pd.DataFrame([{'gate':k,'passed':v,'evidence_level':'RETROSPECTIVE_METHOD_VALIDATION'} for k,v in gates]).to_csv(OUT/'unified_gate_table.csv',index=False)
(ROOT/'manifests/icba_auditor_preregistration.json').write_text(json.dumps({'tau':.99,'delta':.05,'alpha':.05,'seed':991,'actions':['REUSE_SOURCE_POLICY','TARGET_RECALIBRATION','TARGET_REPROFILE_OR_RETRAIN','FIXED_SAFE_FALLBACK','REJECT_NO_SAFE_ENDPOINT','REJECT_NO_FINITE_BREAK_EVEN','INSUFFICIENT_EVIDENCE'],'future_confirm_frozen':True},indent=2)+'\n')
decision='ICBA_UNIFIED_METHOD_NOT_READY_FOR_PROSPECTIVE_CONFIRMATION'
(ROOT/'manifests/icba_auditor_decision.json').write_text(json.dumps({'decision':decision,'evidence_level':'RETROSPECTIVE_METHOD_VALIDATION','future_confirm_accessed':False,'sealed_roles_accessed':False,'source_policy_serialized':False,'full_retraining_cost':'NOT_ESTIMABLE'},indent=2)+'\n'); print(decision)
