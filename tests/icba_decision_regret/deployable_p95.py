import os,pandas as pd,numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/icba_decision_regret'
Q=pd.read_csv(R+'/candidate_query_costs.csv.gz');D=pd.read_csv(R+'/action_level_replay.csv.gz');S=pd.read_csv(R+'/decision_regret_summary.csv');H=pd.read_csv(R+'/oracle_pooled_p95.csv')
best=S.sort_values(['relative_h2_gain','gain_ci_low'],ascending=False).groupby('dataset').head(1);rows=[]
for r in best.itertuples():
 d=D[(D.dataset==r.dataset)&(D.lane==r.lane)&(D.total==r.total)&(D.n_selection==r.n_selection)&(D.n_certification==r.n_certification)]
 keys=d[['dataset','cycle','source_build','target_build','method','stage']].drop_duplicates();q=Q.merge(keys,on=['dataset','cycle','source_build','target_build','method','stage'],how='inner',validate='many_to_one');h=float(H[(H.dataset==r.dataset)&(H.lane=='H2')].pooled_p95.iloc[0]);rows.append(dict(dataset=r.dataset,lane=r.lane,total=r.total,n_selection=r.n_selection,n_certification=r.n_certification,deployable_pooled_p95=q.ndc.quantile(.95),h2_pooled_p95=h,p95_not_worse=q.ndc.quantile(.95)<=h,query_rows=len(q),status='ESTIMATED_FROM_QUERY_LEVEL',evidence_label='EXPLORATORY_FIXED_TARGET_DECISION_AUDIT'))
pd.DataFrame(rows).to_csv(R+'/deployable_pooled_p95.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
