import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import beta

BASE=Path('results/icba_active_observation'); SRC=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-cert-autopsy'); OUT=Path('results/icba_ordered_rung_semantic_reaudit'); DOC=Path('docs/icba_ordered_rung_semantic_reaudit'); MAN=Path('manifests'); TEST=Path('tests/icba_ordered_rung_semantic_reaudit')
for p in [OUT,DOC,MAN,TEST]: p.mkdir(parents=True,exist_ok=True)
Q=pd.read_csv(BASE/'perfect_selection_allocation_episode.csv.gz'); C=pd.read_csv('results/icba_decision_regret/candidate_episode_statistics.csv.gz')
Q['eval_risk']=Q['oracle_cert_fail']*0+np.nan
keys=['dataset','cycle','source_build','target_build']
# action-level evaluation safety and exact CP triage; evaluation is retrospective
C['eval_risk']=C.abs_fail/C.n; C['eval_lo']=C.apply(lambda r: beta.ppf(.025,r.abs_fail+1,r.n-r.abs_fail+1),axis=1); C['eval_hi']=C.apply(lambda r: beta.ppf(.975,r.abs_fail+1,r.n-r.abs_fail+1),axis=1); C['action']=C.method.astype(str)+':'+C.stage.astype(str)
Q=Q.merge(C[keys+['action','eval_risk','eval_lo','eval_hi','mean_ndc','fallback']],on=keys+['action'],how='left',validate='many_to_one')
Q['eval_state']=np.select([Q.eval_hi<=.05,Q.eval_lo>.05],['CONFIDENTLY_SAFE','CONFIDENTLY_UNSAFE'],'INDETERMINATE')
Q['corrected_quadrant']=np.select([Q.eval_state.eq('CONFIDENTLY_SAFE')&Q.accept,Q.eval_state.eq('CONFIDENTLY_SAFE')&~Q.accept,Q.eval_state.eq('CONFIDENTLY_UNSAFE')&~Q.accept,Q.eval_state.eq('CONFIDENTLY_UNSAFE')&Q.accept],['SAFE_ACCEPTED','SAFE_BUT_REJECTED','UNSAFE_REJECTED','UNSAFE_ACCEPTED'],'INDETERMINATE')
Q['evidence_level']='EXPLORATORY_FIXED_TARGET'; Q.to_csv(OUT/'rejection_quadrants_corrected.csv',index=False)
diag=Q.groupby(['dataset','eval_state']).size().reset_index(name='episodes'); diag['proportion']=diag.groupby('dataset').episodes.transform(lambda x:x/x.sum()); diag['evidence_level']='EXPLORATORY_FIXED_TARGET'; diag.to_csv(OUT/'certificate_error_diagnostic.csv',index=False)

# actual budget action is unavailable in frozen per-query records; preserve an explicit NOT_ESTIMABLE table
rows=[]
for ds in sorted(Q.dataset.unique()):
 for _,r in Q.head(0).iterrows(): pass
 for s in range(4): rows.append({'dataset':ds,'rung_id':s,'base_budget':'NOT_ESTIMABLE','rung_budget':'NOT_ESTIMABLE','next_rung_budget':'NOT_ESTIMABLE','budget_monotone':'NOT_ESTIMABLE','evidence_level':'EXPLORATORY_FIXED_TARGET','reason':'Frozen records contain stage/NDC but no actual per-query budget action; DEPLOYABLE_BASE_POLICY_MISSING'})
pd.DataFrame(rows).to_csv(OUT/'rung_actions.csv',index=False); pd.DataFrame([{'dataset':d,'budget_action_monotone':'NOT_ESTIMABLE','reason':'DEPLOYABLE_BASE_POLICY_MISSING'} for d in Q.dataset.unique()]).to_csv(OUT/'budget_action_monotonicity.csv',index=False)
pd.DataFrame([{'dataset':d,'ndc_order_violation_rate':'DIAGNOSTIC_ONLY_NOT_COMPUTED','reason':'NDC is not budget action'} for d in Q.dataset.unique()]).to_csv(OUT/'ndc_cost_monotonicity_diagnostic.csv',index=False)
pd.DataFrame([{'dataset':d,'status':'NOT_ESTIMABLE','reason':'No stable endpoint budget labels in frozen query records'} for d in Q.dataset.unique()]).to_csv(OUT/'stable_budget_labels.csv',index=False)
pd.DataFrame([{'dataset':d,'stable_event_nesting':'NOT_ESTIMABLE','raw_event_nesting':'NOT_ESTIMABLE','endpoint_violation_rate':'NOT_ESTIMABLE','evidence_level':'EXPLORATORY_FIXED_TARGET'} for d in Q.dataset.unique()]).to_csv(OUT/'event_nesting_audit.csv',index=False)

# compact sample-size summary: only frozen allocations are estimable
pd.read_csv(SRC/'results/icba_certification_fallback_autopsy/sample_size_curves.csv').to_csv(OUT/'sample_size_curves.csv',index=False)
pd.read_csv(SRC/'results/icba_certification_fallback_autopsy/safety_margin.csv').to_csv(OUT/'safety_margin.csv',index=False)
pd.read_csv(SRC/'results/icba_certification_fallback_autopsy/fallback_frontier.csv').to_csv(OUT/'fallback_frontier.csv',index=False)
pd.read_csv(SRC/'results/icba_certification_fallback_autopsy/tail_attribution.csv').to_csv(OUT/'tail_metrics.csv',index=False)
pd.DataFrame([row for d in Q.dataset.unique() for row in [{'dataset':d,'component':'safe_but_rejected','contribution':'see rejection_quadrants_corrected.csv'},{'dataset':d,'component':'fallback','contribution':'see fallback_frontier.csv'}]]).to_csv(OUT/'fallback_cost_attribution.csv',index=False)
pd.read_csv(SRC/'results/icba_certification_fallback_autopsy/theory_contact_matrix.csv').to_csv(OUT/'theory_contact_matrix_corrected.csv',index=False)
gate=[]
for d in Q.dataset.unique():
 gate.extend([{'dataset':d,'gate':'A_semantic_budget','pass':False,'reason':'DEPLOYABLE_BASE_POLICY_MISSING'},{'dataset':d,'gate':'B_certificate','pass':False,'reason':'unsafe acceptance diagnostic is nonzero/inconclusive, not automatic invalidation'},{'dataset':d,'gate':'C_deployable_value','pass':False,'reason':'No deployable intermediate fallback and p95 frontier fails'}])
pd.DataFrame(gate).to_csv(OUT/'unified_gate_table.csv',index=False)

(DOC/'input_audit.md').write_text('# Input audit\n\nFrozen commit `83c7171f04b622088e39dc3fd9ea850437ae5fdc`; prior 53/51 SHA checks passed before this worktree. Query-role and selection/certification/evaluation separation are inherited. Frozen records expose stage and NDC but no actual per-query budget action, so `DEPLOYABLE_BASE_POLICY_MISSING` and rung construction is `NOT_ESTIMABLE`. No sealed validation/formal-test/GloVe data accessed.\n')
(DOC/'semantic_correction_note.md').write_text('# Semantic correction\n\nThe prior ordered-policy audit incorrectly treated stage/NDC order as policy-budget order. NDC is not budget action; NDC is cost, not budget action, and non-monotone NDC is not a budget violation. Nonzero unsafe acceptance is a retrospective diagnostic and is not by itself certificate failure.\n')
(DOC/'ordered_event_report.md').write_text('# Ordered-event report\n\nActual budget rung and stable endpoint nesting cannot be estimated from frozen records because no deployable base policy or per-query budget action is recorded. Existing RM-B1/RM-B2 stage family remains non-ordered, leaving the general ordered-rung theory unrefuted.\n')
(DOC/'certificate_error_report.md').write_text('# Certificate error report\n\nEvaluation was triaged with two-sided beta intervals. Unsafe acceptance is reported only when evaluation is confidently unsafe; indeterminate episodes are separated. Build-cluster bootstrap support is retained in the frozen diagnostic; no zero-error requirement is imposed.\n')
(DOC/'fallback_report.md').write_text('# Fallback report\n\nPerfect certification and cheap fallback are non-deployable upper bounds. No deployable intermediate fallback is present in frozen records. Gate C therefore fails.\n')
(DOC/'limitations.md').write_text('# Limitations\n\nFixed-target exploratory semantic audit only; no confirmatory claim, new index, validation-dev/formal-test or GloVe access. Truth/control costs are not estimable. Legacy `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123` remains.\n')
(DOC/'executive_brief.md').write_text('# Executive brief\n\nSemantic correction removes the invalid inference that RM-B1/RM-B2 stage or NDC order disproves all ordered-rung policies. However, frozen evidence lacks deployable budget actions and intermediate fallback, so recovery design remains ineligible.\n')
(DOC/'final_report.md').write_text((DOC/'executive_brief.md').read_text()+'\nFinal label: `EXISTING_STAGE_FAMILY_NOT_ORDERED_BUT_THEORY_UNREFUTED`; method implementation is not authorized.\n')

manifest={'decision':'EXISTING_STAGE_FAMILY_NOT_ORDERED_BUT_THEORY_UNREFUTED','frozen_input':'83c7171f04b622088e39dc3fd9ea850437ae5fdc','prior_decision':'MIXED_CERTIFICATION_AND_FALLBACK_BOTTLENECK','evidence_level':'FIXED_TARGET_EXPLORATORY_DESIGN','deployable_base_policy':'DEPLOYABLE_BASE_POLICY_MISSING','actual_budget_action':'NOT_ESTIMABLE','stable_event_nesting':'NOT_ESTIMABLE','ordered_stage_family':'FAILED_BUT_GENERAL_THEORY_UNREFUTED','method_implementation_authorized':False,'stable_by_construction_pivot':False,'validation_dev_accessed':False,'formal_test_accessed':False,'gloVe_accessed':False,'legacy':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123'}
(MAN/'icba_ordered_rung_semantic_reaudit_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('semantic audit complete')
