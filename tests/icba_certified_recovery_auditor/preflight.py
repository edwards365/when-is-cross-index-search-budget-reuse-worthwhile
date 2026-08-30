import json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
SRC=Path('results/icba_ordered_rung_semantic_reaudit'); OUT=Path('results/icba_certified_recovery_auditor'); DOC=Path('docs/icba_certified_recovery_auditor'); MAN=Path('manifests'); TEST=Path('tests/icba_certified_recovery_auditor')
for p in [OUT,DOC,MAN,TEST]: p.mkdir(parents=True,exist_ok=True)
q=pd.read_csv(SRC/'rejection_quadrants_corrected.csv'); tc=pd.read_csv(SRC/'theory_contact_matrix_corrected.csv')
tc.loc[tc.assumption_id.eq('A_NESTED_EVENTS'),['point_estimate','confidence_interval','pass','failure_reason']]=[np.nan,'NOT_ESTIMABLE',False,'Actual per-query budget action absent; old stage/NDC violation is not a rung test']
tc.to_csv(OUT/'theory_contact_matrix_repaired.csv',index=False)
rng=np.random.default_rng(991); rows=[]
for ds,g in q.groupby('dataset'):
 g=g.copy(); g['ua']=g.accept & g.eval_state.eq('CONFIDENTLY_UNSAFE'); clusters=g.target_build.unique(); cm=g.groupby('target_build').ua.mean().to_numpy(); idx=rng.integers(0,len(cm),size=(5000,len(cm))); bs=cm[idx].mean(1); lo,hi=np.quantile(bs,[.025,.975]); cls='COMPATIBLE_WITH_NOMINAL_ALPHA' if hi<=.05 else ('EVIDENCE_OF_EXCESS_ERROR' if lo>.05 else 'INCONCLUSIVE_AROUND_ALPHA')
 rows.append({'dataset':ds,'episodes':len(g),'confidently_unsafe_accepted':int(g.ua.sum()),'ua_point':g.ua.mean(),'cluster_ci_low':lo,'cluster_ci_high':hi,'alpha':.05,'classification':cls,'seed':991,'bootstrap_unit':'target_build'})
pd.DataFrame(rows).to_csv(OUT/'certificate_error_cluster.csv',index=False)
pre='''# Preflight repair\n\nThe 904de53 semantic conclusion is preserved. New derived machines consistently set `A_NESTED_EVENTS`, `actual_budget_action`, and `stable_event_nesting` to `NOT_ESTIMABLE`; the old stage/NDC violation is retained only as a semantic-error record. Certificate error is re-estimated with 5,000 target-build cluster replicates (seed 991). The original branch and scientific outputs are unchanged.\n'''
(DOC/'preflight_repair.md').write_text(pre)
(DOC/'input_audit.md').write_text('''# Input audit\n\nFrozen input `904de537f16798eac9f68da549f2741d92e2b1c2` passed its 47-item SHA256 manifest after sparse read-only checkout. Root disk is below 6 GiB, so `LOW_DISK_PILOT_ONLY` applies. No reusable index binaries were found in the scoped repository checkout; trace source interfaces exist, but no frozen deployable source-policy artifact with actual per-query ef output is present. validation-dev, formal-test, and sealed GloVe data were not accessed.\n''')
pr={'frozen_input':'904de537f16798eac9f68da549f2741d92e2b1c2','method_internal_name':'CERTIFIED_RECOVERY_AUDITOR_WITH_RESIDUAL_LADDER','status':'PREREGISTERED_BEFORE_NEW_PILOT_RESULTS','evidence_level':'EXPLORATORY_DESIGN','datasets':['sift_100k','arxiv_nomic_100k'],'seed':991,'primary_workload':100000,'workloads':[1000,10000,100000,1000000,10000000],'alpha':.05,'delta':.05,'objective_order':['safety','p95','total_cost_N1e5','build_robustness','label_efficiency','complexity'],'rungs':[0,1,2,3],'budget_grid_levels':12,'query_roles':['source_train','target_selection','target_certification','target_evaluation'],'stop_rules':['LOW_DISK_PILOT_ONLY','INVALID_TRACE_INSTRUMENTATION','NO_DEPLOYABLE_BASE_POLICY_CLOSE_RECOVERY_ROUTE'],'sealed_access_prohibited':['validation-dev','formal-test','GloVe'],'full_confirmation_requires_all_pilot_gates':True}
raw=json.dumps(pr,sort_keys=True).encode(); pr['content_sha256']=hashlib.sha256(raw).hexdigest(); (MAN/'icba_certified_recovery_auditor_preregistration.json').write_text(json.dumps(pr,indent=2)+'\n')
(DOC/'preregistration.md').write_text('# Preregistration\n\nPrimary N=100000; lexicographic objective safety→p95→total cost→build robustness→label efficiency→complexity. Fixed seed 991, alpha=delta=.05, four residual rungs, independent query roles, and fail-closed stopping rules.\n')
print(pd.DataFrame(rows).to_string(index=False)); print(pr['content_sha256'])
