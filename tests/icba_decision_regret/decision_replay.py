#!/usr/bin/env python3
import os
import numpy as np,pandas as pd
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/icba_decision_regret';P=ROOT+'/results/active_recovery_headroom_reaudit';rng=np.random.default_rng(991)
E=pd.read_csv(R+'/candidate_episode_statistics.csv.gz');A=pd.read_csv(P+'/active_sentinel_plan_results.csv.gz');O=pd.read_csv(R+'/oracle_H4c_strict_replay.csv');AS=pd.read_csv(ROOT+'/results/asrc_semantic_repair/asrc_repaired_summary.csv')
# Restrict formal deployable audit to positive selection and certifiable plans.
A=A[(~A.lane.str.contains('NON_DEPLOYABLE'))&(A.n_selection>0)&A.certifiable].copy();A[['method','stage']]=A.selected_action.str.split(':',expand=True);A.stage=A.stage.astype(int)
cand=E[['dataset','cycle','source_build','target_build','method','stage','mean_ndc','abs_fail','n','fallback']].rename(columns={'mean_ndc':'selected_ndc','abs_fail':'selected_fail','fallback':'selected_fallback'})
D=A.merge(cand,on=['dataset','cycle','source_build','target_build','method','stage'],how='left',validate='many_to_one')
# Enforce deployed semantics: an uncertified proposal becomes FIXED:999.
D['proposed_action']=D.selected_action
fx=E[E.method=='FIXED'][['dataset','cycle','source_build','target_build','mean_ndc','abs_fail','n']].rename(columns={'mean_ndc':'fixed_ndc','abs_fail':'fixed_fail','n':'fixed_n'})
D=D.merge(fx,on=['dataset','cycle','source_build','target_build'],validate='many_to_one')
bad=~D.certified_safe.astype(bool)
D.loc[bad,'selected_ndc']=D.loc[bad,'fixed_ndc'];D.loc[bad,'selected_fail']=D.loc[bad,'fixed_fail'];D.loc[bad,'n']=D.loc[bad,'fixed_n'];D.loc[bad,'selected_fallback']=True;D.loc[bad,'selected_action']='FIXED:999';D.loc[bad,'method']='FIXED';D.loc[bad,'stage']=999
oracle=O[['dataset','source_build','target_build','heldout_cycle','selected_method','selected_stage','mean_ndc','abs_fail','n']].rename(columns={'heldout_cycle':'cycle','mean_ndc':'h4c_policy_ndc','abs_fail':'h4c_policy_fail','n':'h4c_policy_n','selected_method':'oracle_method','selected_stage':'oracle_stage'})
D=D.merge(oracle,on=['dataset','cycle','source_build','target_build'],how='left',validate='many_to_one')
# Omniscient held-out safe cost benchmark. This is non-deployable and used only
# to define nonnegative decision regret; H4c remains the action-label target.
env=[]
for keys,g in E.groupby(['dataset','cycle','source_build','target_build']):
 z=g[g.method!='FIXED']; best=z.sort_values('mean_ndc').iloc[0]
 env.append(dict(zip(['dataset','cycle','source_build','target_build'],keys),env_oracle_ndc=best.mean_ndc,env_oracle_action=f'{best.method}:{int(best.stage)}'))
D=D.merge(pd.DataFrame(env),on=['dataset','cycle','source_build','target_build'],validate='many_to_one')
# Episode-level outcome-independent H2 expectation.
h2=[]
for (ds,cy,s,t),g in E[(E.method=='RM-B2')].groupby(['dataset','cycle','source_build','target_build']):
 L=AS[AS.dataset==ds].target_labels_mean.mean();lo,hi=(80,128) if L<=128 else (128,250);p=(L-lo)/(hi-lo);a=g[g.stage==lo].iloc[0];b=g[g.stage==hi].iloc[0];h2.append(dict(dataset=ds,cycle=cy,source_build=s,target_build=t,h2_ndc=(1-p)*a.mean_ndc+p*b.mean_ndc,h2_fail=(1-p)*a.abs_fail+p*b.abs_fail,h2_n=a.n))
D=D.merge(pd.DataFrame(h2),on=['dataset','cycle','source_build','target_build'],validate='many_to_one')
# Dataset-majority strict Oracle action and its realized cost.
maj=O.assign(action=O.selected_method+':'+O.selected_stage.astype(int).astype(str)).groupby('dataset').action.agg(lambda x:x.value_counts().index[0]).to_dict();D['majority_action']=D.dataset.map(maj);D[['maj_method','maj_stage']]=D.majority_action.str.split(':',expand=True);D.maj_stage=D.maj_stage.astype(int)
mc=E.rename(columns={'method':'maj_method','stage':'maj_stage','mean_ndc':'majority_ndc','abs_fail':'majority_fail'})[['dataset','cycle','source_build','target_build','maj_method','maj_stage','majority_ndc','majority_fail']];D=D.merge(mc,on=['dataset','cycle','source_build','target_build','maj_method','maj_stage'],validate='many_to_one')
D['oracle_action']=D.oracle_method+':'+D.oracle_stage.astype(int).astype(str);D['exact_correct']=D.selected_action==D.oracle_action;D['majority_correct']=D.majority_action==D.oracle_action
D['decision_regret']=D.selected_ndc-D.env_oracle_ndc;D['observable_gain']=D.h2_ndc-D.selected_ndc;D['oracle_headroom']=D.h2_ndc-D.env_oracle_ndc;D['identifiability_gap']=D.selected_ndc-D.env_oracle_ndc;D['decomposition_error']=D.oracle_headroom-(D.observable_gain+D.identifiability_gap);D['near_1pct']=D.selected_ndc<=1.01*D.env_oracle_ndc;D['near_5pct']=D.selected_ndc<=1.05*D.env_oracle_ndc;D['selected_abs_risk']=D.selected_fail/D.n;D['evidence_label']='EXPLORATORY_FIXED_TARGET_DECISION_AUDIT'
try:
 D.to_parquet(R+'/action_level_replay.parquet',index=False)
except ImportError:
 D.to_csv(R+'/action_level_replay.csv.gz',index=False,compression='gzip')
 open(R+'/action_level_replay.parquet.NOT_ESTIMABLE','w').write('PARQUET_ENGINE_NOT_AVAILABLE; canonical replay is action_level_replay.csv.gz\n')
summ=[];boot=[];conf=[]
for keys,g in D.groupby(['dataset','lane','total','n_selection','n_certification']):
 ds,lane,total,ns,nc=keys; tb=g.groupby('target_build').agg(observable_gain=('observable_gain','mean'),regret=('decision_regret','mean'))
 sims=[]
 for i in range(5000):
  z=tb.iloc[rng.integers(0,len(tb),len(tb))];v=z.observable_gain.mean();sims.append(v);boot.append(dict(dataset=ds,lane=lane,total=total,n_selection=ns,n_certification=nc,draw=i,observable_gain=v))
 summ.append(dict(dataset=ds,lane=lane,total=total,n_selection=ns,n_certification=nc,exact_accuracy=g.exact_correct.mean(),majority_accuracy=g.majority_correct.mean(),mean_decision_regret=g.decision_regret.mean(),median_decision_regret=g.decision_regret.median(),p95_decision_regret=g.decision_regret.quantile(.95),mean_observable_gain=g.observable_gain.mean(),relative_h2_gain=g.observable_gain.mean()/g.h2_ndc.mean(),gain_ci_low=np.quantile(sims,.025),gain_ci_high=np.quantile(sims,.975),near_1pct=g.near_1pct.mean(),near_5pct=g.near_5pct.mean(),abs_risk=g.selected_fail.sum()/g.n.sum(),fallback_rate=g.selected_fallback.mean(),pooled_p95_proxy='SEE_QUERY_LEVEL_ACTION_REPLAY_REQUIRED',decomposition_max_error=g.decomposition_error.abs().max(),delete_max_build_gain=tb.drop(tb.observable_gain.idxmax()).observable_gain.mean(),evidence_label='EXPLORATORY_FIXED_TARGET_DECISION_AUDIT'))
 for (a,b),z in g.groupby(['oracle_action','selected_action']):conf.append(dict(dataset=ds,lane=lane,total=total,n_selection=ns,n_certification=nc,oracle_action=a,selected_action=b,count=len(z),cost_weight=z.decision_regret.sum(),mean_regret=z.decision_regret.mean()))
S=pd.DataFrame(summ);S.to_csv(R+'/decision_regret_summary.csv',index=False);pd.DataFrame(conf).to_csv(R+'/cost_weighted_confusion.csv',index=False);S[['dataset','lane','total','n_selection','n_certification','near_1pct','near_5pct']].to_csv(R+'/near_optimal_action_rates.csv',index=False);pd.DataFrame(boot).to_csv(R+'/observable_gain_bootstrap.csv.gz',index=False,compression='gzip')
# Risk cluster bootstrap UCB for strict lanes.
RB=pd.read_csv(R+'/oracle_risk_bounds.csv');Oall=pd.concat([pd.read_csv(R+f'/oracle_{x}_strict_replay.csv').assign(lane=x) for x in ['H3b','H4b','H3c','H4c']]);out=[]
for (ds,lane),g in Oall.groupby(['dataset','lane']):
 b=g.groupby('target_build').agg(f=('abs_fail','sum'),n=('n','sum')).reset_index();sim=[]
 for _ in range(5000):
  z=b.iloc[rng.integers(0,len(b),len(b))];sim.append(z.f.sum()/z.n.sum())
 out.append(dict(dataset=ds,lane=lane,cluster_bootstrap_ucb=np.quantile(sim,.95)))
RB=RB.drop(columns='cluster_bootstrap_ucb').merge(pd.DataFrame(out),on=['dataset','lane']);RB.to_csv(R+'/oracle_risk_bounds.csv',index=False)
best=S.sort_values(['relative_h2_gain','gain_ci_low'],ascending=False).groupby('dataset').head(5);print(best.to_string(index=False))
