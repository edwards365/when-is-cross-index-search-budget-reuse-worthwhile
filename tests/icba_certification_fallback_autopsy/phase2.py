import numpy as np, pandas as pd
from pathlib import Path

R=Path('results/icba_certification_fallback_autopsy'); rng=np.random.default_rng(991)
P=pd.read_csv(R/'rejection_quadrants.csv')
requested=[59,64,90,96,122,128,154,186,218,234,250]
rows=[]; boots=[]
for ds in sorted(P.dataset.unique()):
  for m in requested:
    g=P[(P.dataset==ds)&(P.certification==m)].copy()
    if g.empty:
      rows.append({'dataset':ds,'certification_m':m,'estimable':False,'status':'NOT_ESTIMABLE_IN_FROZEN_MUTUALLY_EXCLUSIVE_SPLIT'})
      continue
    g['false_reject']=(g.quadrant=='SAFE_BUT_REJECTED'); g['unsafe_accept']=(g.quadrant=='UNSAFE_ACCEPTED')
    cm=g.groupby('target_build').agg(acceptance=('accept','mean'),false_rejection=('false_reject','mean'),unsafe_acceptance=('unsafe_accept','mean'),mean_ndc=('eval_cost','mean'),fallback=('deployed_fallback','mean')).to_numpy()
    idx=rng.integers(0,len(cm),size=(5000,len(cm))); a=cm[idx].mean(axis=1)
    rec={'dataset':ds,'certification_m':m,'estimable':True,'episodes':len(g),'acceptance_rate':g['accept'].mean(),'false_rejection_rate':g.false_reject.mean(),'unsafe_acceptance_rate':g.unsafe_accept.mean(),'max_cert_risk_ucb':g.oracle_cert_ucb.max(),'mean_ndc':g.eval_cost.mean(),'fallback_rate':g.deployed_fallback.mean(),'status':'EXPLORATORY_FIXED_TARGET'}
    for j,n in enumerate(['acceptance','false_rejection','unsafe_acceptance','mean_ndc','fallback']): rec[n+'_ci_low'],rec[n+'_ci_high']=np.quantile(a[:,j],[.025,.975])
    rows.append(rec)
pd.DataFrame(rows).to_csv(R/'sample_size_curves.csv',index=False)
print(pd.DataFrame(rows)[['dataset','certification_m','estimable','acceptance_rate','false_rejection_rate','unsafe_acceptance_rate','fallback_rate']].to_string(index=False))
