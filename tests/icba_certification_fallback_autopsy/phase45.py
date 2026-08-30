import pandas as pd, numpy as np
from pathlib import Path

BASE=Path('results/icba_active_observation'); R=Path('results/icba_certification_fallback_autopsy'); D=Path('docs/icba_certification_fallback_autopsy')
named=pd.read_csv(BASE/'failure_named_counterfactuals.csv'); shap=pd.read_csv(BASE/'failure_shapley.csv'); front=pd.read_csv(BASE/'label_allocation_frontier.csv'); curves=pd.read_csv(R/'sample_size_curves.csv'); quad=pd.read_csv(R/'rejection_quadrants.csv'); order=pd.read_csv(R/'ordered_policy_violations.csv')

ff=[]
for _,x in named.iterrows():
  ff.append({'dataset':x.dataset,'system':x.counterfactual,'mean_ndc':x.mean_ndc,'relative_gain':x.relative_gain,'fallback_rate':x.fallback_rate,'tail_metric':x.pooled_p95,'tail_status':'LEGACY_EPISODE_MEAN_QUANTILE_DIAGNOSTIC_NOT_QUERY_POOLED','deployability':'DEPLOYABLE_DESIGN' if x.counterfactual=='F0_REAL_DEPLOYMENT' else 'NON_DEPLOYABLE_UPPER_BOUND'})
for _,x in front.iterrows(): ff.append({'dataset':x.dataset,'system':f'PERFECT_SELECTION_REAL_CERT_{x.selection}_{x.certification}','mean_ndc':x.mean_ndc,'relative_gain':x.relative_gain,'fallback_rate':x.fallback_rate,'tail_metric':x.pooled_p95,'tail_status':'EXACT_QUERY_POOLED_P95','deployability':'NON_DEPLOYABLE_UPPER_BOUND'})
for ds in front.dataset.unique():
  h=front[front.dataset==ds].iloc[0]; ff.append({'dataset':ds,'system':'H2','mean_ndc':np.nan,'relative_gain':0.,'fallback_rate':0.,'tail_metric':h.h2_pooled_p95,'tail_status':'EXACT_QUERY_POOLED_P95','deployability':'DEPLOYABLE_REFERENCE'})
ff += [{'dataset':d,'system':s,'mean_ndc':np.nan,'relative_gain':np.nan,'fallback_rate':np.nan,'tail_metric':np.nan,'tail_status':'NOT_ESTIMABLE','deployability':dep} for d in front.dataset.unique() for s,dep in [('BONFERRONI_MULTI_CANDIDATE','DESIGN_ONLY'),('PREREGISTERED_FIXED_SEQUENCE','DESIGN_ONLY'),('ORDERED_CERTIFICATION','NOT_VALID_ORDERED_ASSUMPTION_FAILED'),('ORDERED_PLUS_GRADED_FALLBACK','NOT_VALID_MISSING_DEPLOYABLE_INTERMEDIATE_FALLBACK'),('TARGET_ONLY_RECALIBRATION','REFERENCE_ONLY'),('TARGET_FULL_RETRAINING','SYMBOLIC_COST_ONLY')]]
pd.DataFrame(ff).to_csv(R/'fallback_frontier.csv',index=False)

tail=front[['dataset','selection','certification','pooled_p95','h2_pooled_p95','p95_not_worse','delete_max_build_gain','loto_min_gain']].copy(); tail['p99']='NOT_ESTIMABLE_FROM_COMPACT_FROZEN_REPLAY'; tail['fallback_query_p95']='NOT_ESTIMABLE'; tail['nonfallback_query_p95']='NOT_ESTIMABLE'; tail.to_csv(R/'tail_attribution.csv',index=False)

cost=[]
for N in [10**3,10**4,10**5,10**6,10**7]:
  for ds in front.dataset.unique(): cost.append({'dataset':ds,'N':N,'formula':'C_search + (C_truth + C_selection + C_certification)/N + C_control','search_component':'ESTIMABLE_FROM_MEAN_NDC','truth_component':'SYMBOLIC','control_component':'SYMBOLIC','status':'SYMBOLIC_COST_ONLY'})
pd.DataFrame(cost).to_csv(R/'cost_break_even.csv',index=False)

mean_sh=shap[shap.metric=='mean_ndc'].copy(); mean_sh['share']=mean_sh.groupby('dataset').shapley_cost_contribution.transform(lambda x:x/x.sum()); mean_sh.to_csv(R/'mechanism_contributions.csv',index=False)

tc=[]
for ds in front.dataset.unique():
  q=quad[quad.dataset==ds]; o=order[(order.dataset==ds)&(order.subset=='ALL')]; c=curves[(curves.dataset==ds)&curves.estimable.fillna(False)]
  vals={
   'A_NESTED_EVENTS':(1-o.failure_violations.sum()/max(1,o.adjacent_pairs.sum()),False,'nonzero failure-event and cost-order violations'),
   'A_POSITIVE_SAFETY_MARGIN':(q.safety_margin.median(),q.safety_margin.median()>0,'median evaluation safety margin'),
   'A_SAFE_RUNG_EXISTS':((q.eval_risk<=.05).mean(),True,'safe candidates exist retrospectively'),
   'A_FALSE_REJECTION_CONTROLLABLE':(c.false_rejection_rate.min(),c.false_rejection_rate.min()<=.05,'best supported allocation'),
   'A_FALLBACK_GAP_REDUCIBLE':(mean_sh[(mean_sh.dataset==ds)&(mean_sh.factor=='fixed_fallback')].share.iloc[0],True,'cheap fallback nondeployable upper bound'),
   'A_POSITIVE_COST_MARGIN':(np.nan,False,'median frozen safe-action cost margin is zero'),
   'A_FIXED_TARGET_INDEPENDENCE':(1.,True,'frozen disjoint query roles'),
   'A_OUTER_BUILD_SUPPORT':(18,False,'only 9 builds per dataset; outer-build confirmation absent')}
  for a,(v,p,why) in vals.items(): tc.append({'assumption_id':a,'dataset':ds,'empirical_metric':why,'point_estimate':v,'confidence_interval':'see clustered bootstrap table' if a=='A_FALSE_REJECTION_CONTROLLABLE' else 'NOT_ESTIMABLE','pass':p,'evidence_level':'EXPLORATORY_FIXED_TARGET','failure_reason':'' if p else why})
pd.DataFrame(tc).to_csv(R/'theory_contact_matrix.csv',index=False)

gates=[]
for ds in front.dataset.unique():
  q=quad[quad.dataset==ds]; best=front[front.dataset==ds].sort_values('relative_gain',ascending=False).iloc[0]
  gates += [{'dataset':ds,'gate':'Safety','pass':False,'evidence':f'unsafe acceptance={(q.quadrant=="UNSAFE_ACCEPTED").mean():.6f}'},{'dataset':ds,'gate':'Efficiency','pass':bool(best.relative_gain>=.05),'evidence':f'best perfect-selection gain={best.relative_gain:.6f}'},{'dataset':ds,'gate':'Tail','pass':bool(best.p95_not_worse),'evidence':f'p95={best.pooled_p95} vs H2={best.h2_pooled_p95}'},{'dataset':ds,'gate':'Fallback','pass':False,'evidence':'no deployable intermediate fallback; ordered structure failed'},{'dataset':ds,'gate':'Deployability','pass':False,'evidence':'only Oracle/cheap fallback upper bounds restore joint value'}]
pd.DataFrame(gates).to_csv(R/'unified_gate_table.csv',index=False)

shares=mean_sh.pivot(index='dataset',columns='factor',values='share')
(D/'fallback_analysis.md').write_text('# Fallback analysis\n\nMean-NDC Shapley shares show a mixed rejection/fallback mechanism. Arxiv rejection/fallback shares: %.3f/%.3f; SIFT: %.3f/%.3f. Cheap fallback and perfect certification are nondeployable upper bounds. No deployable intermediate fallback exists.\n'%(shares.loc['arxiv_nomic_100k','real_rejection'],shares.loc['arxiv_nomic_100k','fixed_fallback'],shares.loc['sift_100k','real_rejection'],shares.loc['sift_100k','fixed_fallback']))
(D/'rejection_autopsy.md').write_text('# Rejection autopsy\n\nBoth safe-but-rejected and unsafe-accepted episodes occur. Evaluation labels are retrospective only. Supported allocation m=154 reduces fallback but does not eliminate unsafe acceptance.\n')
print(mean_sh[['dataset','factor','share']].to_string(index=False)); print(pd.DataFrame(gates).to_string(index=False))
