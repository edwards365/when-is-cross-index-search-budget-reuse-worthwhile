import pandas as pd, numpy as np
from pathlib import Path

SRC=Path('results/icba_decision_regret/candidate_query_costs.csv.gz'); OUT=Path('results/icba_certification_fallback_autopsy'); DOC=Path('docs/icba_certification_fallback_autopsy')
Q=pd.read_csv(SRC)
idk=['dataset','cycle','source_build','target_build','method','query_id']
def audit(d,label):
  out=[]; idx=['dataset','cycle','source_build','target_build','query_id']
  for method,g in d.groupby('method'):
    nd=g.pivot(index=idx,columns='stage',values='ndc').sort_index(axis=1)
    zz=g.pivot(index=idx,columns='stage',values='z_abs').reindex(columns=nd.columns)
    cc=g.pivot(index=idx,columns='stage',values='censor').reindex(columns=nd.columns)
    valid=nd.notna().to_numpy(); n=nd.to_numpy(); z=zz.to_numpy(); c=cc.to_numpy()
    pair=valid[:,:-1]&valid[:,1:]; bd=(np.diff(n,axis=1)<0)&pair; fv=(np.diff(z,axis=1)>0)&pair; cv=fv&(c[:,1:]>0)
    x=nd.index.to_frame(index=False); x['method']=method; x['subset']=label; x['pairs']=pair.sum(axis=1); x['budget_violations']=bd.sum(axis=1); x['failure_violations']=fv.sum(axis=1); x['censor_linked_violations']=cv.sum(axis=1); out.append(x)
  return pd.concat(out,ignore_index=True)
A=audit(Q,'ALL')
cut=Q.groupby('dataset').ndc.transform(lambda x:x.quantile(.99)); B=audit(Q[Q.ndc<=cut],'DROP_TOP_1PCT_NDC')
Z=pd.concat([A,B],ignore_index=True)
G=Z.groupby(['dataset','cycle','target_build','method','subset']).agg(query_ladders=('pairs','size'),adjacent_pairs=('pairs','sum'),budget_violations=('budget_violations','sum'),failure_violations=('failure_violations','sum'),censor_linked_violations=('censor_linked_violations','sum')).reset_index()
for c in ['budget','failure','censor_linked']:
  G[c+'_violation_rate']=G[c+'_violations']/G.adjacent_pairs
G['evidence_level']='EXPLORATORY_FIXED_TARGET'; G.to_csv(OUT/'ordered_policy_violations.csv',index=False)
S=G.groupby(['dataset','method','subset']).agg(pairs=('adjacent_pairs','sum'),budget_rate=('budget_violations','sum'),failure_rate=('failure_violations','sum'),censor_rate=('censor_linked_violations','sum')).reset_index()
S[['budget_rate','failure_rate','censor_rate']]=S[['budget_rate','failure_rate','censor_rate']].div(S.pairs,axis=0)
failed=bool((S[S.subset=='ALL'].failure_rate>0).any() or (S[S.subset=='ALL'].budget_rate>0).any())
(DOC/'ordered_policy_audit.md').write_text('# Ordered policy audit\n\nFrozen RM-B1/RM-B2 stage ladders were checked query-by-query. Exact nesting requires zero budget and failure-event violations. Result: **'+('ORDERED_POLICY_ASSUMPTION_FAILED' if failed else 'ORDERED_POLICY_ASSUMPTION_SUPPORTED')+'**. No post-hoc reordering was performed. Top-1% removal is robustness-only.\n')
print(S.to_string(index=False)); print('DECISION', 'ORDERED_POLICY_ASSUMPTION_FAILED' if failed else 'SUPPORTED')
