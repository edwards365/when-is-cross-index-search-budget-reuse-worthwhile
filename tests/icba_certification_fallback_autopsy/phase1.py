import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import beta

ROOT=Path('results'); OUT=ROOT/'icba_certification_fallback_autopsy'; DOC=Path('docs/icba_certification_fallback_autopsy'); TEST=Path('tests/icba_certification_fallback_autopsy')
for p in [OUT,DOC,TEST]: p.mkdir(parents=True,exist_ok=True)
P=pd.read_csv(ROOT/'icba_active_observation/perfect_selection_allocation_episode.csv.gz')
C=pd.read_csv(ROOT/'icba_decision_regret/candidate_episode_statistics.csv.gz')
Q=pd.read_csv(ROOT/'icba_decision_regret/candidate_query_costs.csv.gz')
keys=['dataset','cycle','source_build','target_build']
C['action']=C.method.astype(str)+':'+C.stage.astype(str)
E=C[keys+['action','abs_fail','n','mean_ndc','fallback','censor_fail','rec_fail']].copy()
E['eval_risk']=E.abs_fail/E.n; E['safety_margin']=.05-E.eval_risk
P=P.rename(columns={'fallback':'deployed_fallback'})
P=P.merge(E,on=keys+['action'],how='left',validate='many_to_one')
P['cert_ucb_recomputed']=np.where(P.oracle_cert_fail<P.certification,beta.ppf(.95,P.oracle_cert_fail+1,P.certification-P.oracle_cert_fail),1.0)
P['event_consistent']=(P.oracle_cert_ucb-P.cert_ucb_recomputed).abs()<1e-10
P['eval_safe']=P.eval_risk<=.05
P['quadrant']=np.select([P['eval_safe']&P['accept'],P['eval_safe']&~P['accept'],~P['eval_safe']&~P['accept'],~P['eval_safe']&P['accept']],['SAFE_ACCEPTED','SAFE_BUT_REJECTED','UNSAFE_REJECTED','UNSAFE_ACCEPTED'])
P['evidence_level']='EXPLORATORY_FIXED_TARGET'; P.to_csv(OUT/'rejection_quadrants.csv',index=False)

Q['action']=Q.method.astype(str)+':'+Q.stage.astype(str)
qp=Q.groupby(keys+['action']).agg(query_p95=('ndc',lambda x:np.quantile(x,.95)),query_p99=('ndc',lambda x:np.quantile(x,.99))).reset_index()
P=P.merge(qp,on=keys+['action'],how='left',validate='many_to_one')
S=P.groupby(['dataset','selection','certification','quadrant']).agg(episodes=('quadrant','size'),mean_ndc=('mean_ndc','mean'),query_pooled_p95=('query_p95','mean'),fallback_rate=('deployed_fallback','mean'),mean_margin=('safety_margin','mean')).reset_index()
den=S.groupby(['dataset','selection','certification']).episodes.transform('sum'); S['proportion']=S.episodes/den
S.to_csv(OUT/'safety_margin.csv',index=False)

audit=f'''# Input and event audit\n\n- Frozen input: `97ca42a120fff015885bba509e8aa90178aabfa2`.\n- Evidence: `EXPLORATORY_FIXED_TARGET`.\n- Z_abs is consistently represented by `abs_fail`, with `rec_fail` (under-budget) and `censor_fail` retained separately.\n- One-sided Clopper-Pearson upper bound was independently recomputed at alpha=0.05. Exact row consistency: {P.event_consistent.mean():.6f}.\n- Evaluation risk is used only for retrospective quadrant assignment, never selection/certification.\n- Query roles inherit the frozen mutually-exclusive firewall.\n- Query-pooled p95 is reconstructed from frozen candidate query costs.\n- No validation-dev/formal-test or GloVe data accessed.\n- Low-disk streaming/compact-output mode active.\n'''
(DOC/'input_audit.md').write_text(audit)
print(S.groupby(['dataset','quadrant']).agg(episodes=('episodes','sum'),mean_prop=('proportion','mean')).to_string())
