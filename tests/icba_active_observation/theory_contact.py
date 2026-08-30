import numpy as np
import pandas as pd
from pathlib import Path

ROOT=Path('results/icba_decision_regret'); OUT=Path('results/icba_active_observation'); OUT.mkdir(parents=True,exist_ok=True)
C=pd.read_csv(ROOT/'candidate_episode_statistics.csv.gz')
Q=pd.read_csv(ROOT/'candidate_query_costs.csv.gz')
keys=['dataset','cycle','source_build','target_build']
rows=[]; risk=[]
for k,g in C.groupby(keys):
    g=g.copy(); g['risk']=g.abs_fail/g.n
    safe=g[g.risk<=.05].sort_values('mean_ndc')
    if len(safe):
        b=safe.iloc[0]; second=safe.mean_ndc.iloc[1] if len(safe)>1 else np.nan
        rows.append(dict(zip(keys,k))|{'best_method':b.method,'best_stage':b.stage,'cost_margin':second-b.mean_ndc if len(safe)>1 else np.nan,'near_1pct_actions':int((safe.mean_ndc<=b.mean_ndc*1.01).sum()),'near_5pct_actions':int((safe.mean_ndc<=b.mean_ndc*1.05).sum()),'safe_actions':len(safe)})
    for _,r in g.iterrows(): risk.append(dict(zip(keys,k))|{'method':r.method,'stage':r.stage,'risk':r.risk,'risk_margin':abs(r.risk-.05),'zero_margin':abs(r.risk-.05)<1e-12,'censor_rate':r.censor_fail/r.n,'under_budget_rate':r.rec_fail/r.n})
M=pd.DataFrame(rows); R=pd.DataFrame(risk); M.to_csv(OUT/'cost_margin.csv',index=False); R.to_csv(OUT/'risk_margin.csv',index=False)

rng=np.random.default_rng(991); us=[]
for k,g in Q.groupby(keys+['method','stage']):
    full_cost=g.ndc.mean(); full_risk=g.z_abs.mean(); ids=np.arange(len(g))
    for m in [16,32,64,96,128,191]:
        if len(g)<m: continue
        take=rng.choice(ids,m,replace=False); s=g.iloc[take]
        us.append(dict(zip(keys+['method','stage'],k))|{'m':m,'cost_abs_error':abs(s.ndc.mean()-full_cost),'risk_abs_error':abs(s.z_abs.mean()-full_risk)})
U=pd.DataFrame(us); U.to_csv(OUT/'uniform_estimation.csv',index=False)

contact=[]
for ds in sorted(C.dataset.unique()):
    mm=M[M.dataset==ds]; rr=R[R.dataset==ds]; uu=U[U.dataset==ds]
    ent=-(mm.groupby(['best_method','best_stage']).size()/len(mm)).pipe(lambda p:(p*np.log2(p)).sum())
    contact += [
      {'dataset':ds,'assumption':'positive_cost_margin','metric':mm.cost_margin.median(),'status':'EMPIRICALLY_SUPPORTED' if (mm.cost_margin>0).mean()>=.8 else 'PARTIALLY_SUPPORTED'},
      {'dataset':ds,'assumption':'risk_separation_from_0.05','metric':rr.risk_margin.median(),'status':'EMPIRICALLY_SUPPORTED' if rr.risk_margin.median()>.01 else 'PARTIALLY_SUPPORTED'},
      {'dataset':ds,'assumption':'uniform_cost_estimation_m191','metric':uu[uu.m==191].cost_abs_error.median(),'status':'PARTIALLY_SUPPORTED'},
      {'dataset':ds,'assumption':'oracle_action_entropy_bits','metric':ent,'status':'EMPIRICALLY_SUPPORTED' if ent>0 else 'FAILED'},
      {'dataset':ds,'assumption':'deployable_active_identification','metric':np.nan,'status':'FAILED','note':'Perfect-selection upper bound fails joint mean/tail gate'},
    ]
pd.DataFrame(contact).to_csv(OUT/'theory_assumption_contact.csv',index=False)
print(pd.DataFrame(contact).to_string(index=False))
