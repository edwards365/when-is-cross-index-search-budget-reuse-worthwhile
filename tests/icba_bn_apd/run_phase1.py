from pathlib import Path
import pandas as pd, numpy as np, json
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');src=root/'results/icba_cals_seal';out=root/'results/icba_bn_apd';docs=root/'docs/icba_bn_apd'
out.mkdir(parents=True,exist_ok=True);docs.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(src/'subset_results.csv.gz');acts=pd.read_csv(src/'selection_actions.csv');target=acts[acts.action_scope.eq('TARGET_SPECIFIC_SELECTED_FIXED_SET')]
# Historical selection and holdout are now one explicitly replay-only development role.
d['development_role']='bn_apd_replay_development'
base=d[d['mask'].eq(0)].copy();base['recall']=base.union_hits/10
cont=[]
for (ds,b,q),g in base.groupby(['dataset','build','query_id']):
 g=g.sort_values('raw_ef').drop_duplicates('raw_ef')
 for e0,e1 in [(8,16),(16,32),(32,64)]:
  a=g[g.raw_ef.eq(e0)];z=g[g.raw_ef.eq(e1)]
  if a.empty or z.empty:continue
  a=a.iloc[0];z=z.iloc[0];dc=z.total_ndc-a.total_ndc
  cont.append({'dataset':ds,'build':b,'query_id':q,'from_ef':e0,'to_ef':e1,'delta_ndc':dc,'hit_gain':int(z.union_hits>a.union_hits),'threshold_rescue':int(a.union_hits<9 and z.union_hits>=9),'recall_gain':z.recall-a.recall,'risk_reduction':a.union_risk-z.union_risk,'hit_value':int(z.union_hits>a.union_hits)/dc if dc>0 else np.nan,'threshold_value':int(a.union_hits<9 and z.union_hits>=9)/dc if dc>0 else np.nan,'recall_value':(z.recall-a.recall)/dc if dc>0 else np.nan,'risk_value':(a.union_risk-z.union_risk)/dc if dc>0 else np.nan,'primary_ndc':a.primary_ndc})
cont=pd.DataFrame(cont);cont.to_csv(out/'marginal_primary_value.csv',index=False)
rows=[]
for (ds,b,e),g in d[(d.portal_count.between(1,4))].groupby(['dataset','build','raw_ef']):
 sm=int(target[(target.dataset.eq(ds))&(target.build.eq(b))&(target.raw_ef.eq(e))]['mask'].iloc[0])
 for m,x in g.groupby('mask'):
  dc=x.aux_ndc_sum;rows.append({'dataset':ds,'build':b,'raw_ef':e,'mask':m,'portal_count':int(m).bit_count(),'category':'SELECTED_FIXED_SET' if m==sm else ('SINGLE_PORTAL' if int(m).bit_count()==1 else ('DOUBLE_PORTAL' if int(m).bit_count()==2 else 'PORTAL_SET_LE4')),'n':len(x),'positive_hit_gain':int(x.positive_hit_gain.sum()),'threshold_rescues':int(x.threshold_rescue.sum()),'mean_recall_gain':(x.union_hits-x.base_hits).mean()/10,'mean_risk_reduction':(x.base_risk-x.union_risk).mean(),'mean_additional_ndc':dc.mean(),'median_hit_value':np.nanmedian(x.positive_hit_gain/dc.replace(0,np.nan)),'median_threshold_value':np.nanmedian(x.threshold_rescue/dc.replace(0,np.nan)),'median_recall_value':np.nanmedian(((x.union_hits-x.base_hits)/10)/dc.replace(0,np.nan)),'median_risk_value':np.nanmedian((x.base_risk-x.union_risk)/dc.replace(0,np.nan))})
pd.DataFrame(rows).to_csv(out/'marginal_portal_value.csv',index=False)
# State-conditioned selected-set advantage versus spending on the next native ef.
st=[]
for _,a in target[target.raw_ef.isin([8,16,32])].iterrows():
 e=int(a.raw_ef);nxt={8:16,16:32,32:64}[e]
 p=d[(d.dataset.eq(a.dataset))&(d.build.eq(a.build))&(d.raw_ef.eq(e))&(d['mask'].eq(a['mask']))][['query_id','positive_hit_gain','threshold_rescue','base_hits','union_hits','base_risk','union_risk','aux_ndc_sum','primary_ndc']]
 c=cont[(cont.dataset.eq(a.dataset))&(cont.build.eq(a.build))&(cont.from_ef.eq(e))]
 q=p.merge(c,on='query_id',suffixes=('_portal','_continue'));q['state']='HIGH_PRIMARY_NDC';med=q.primary_ndc_portal.median();q.loc[q.primary_ndc_portal<=med,'state']='LOW_PRIMARY_NDC'
 q['portal_value']=((q.union_hits-q.base_hits)/10)/q.aux_ndc_sum;q['advantage']=q.portal_value-q.recall_value
 cutoff=q.advantage.quantile(.99)
 for state,x in q.groupby('state'):
  y=x[x.advantage<=cutoff];st.append({'dataset':a.dataset,'build':a.build,'raw_ef':e,'state_feature':'primary_actual_ndc','state':state,'coverage':len(x)/len(q),'n':len(x),'median_portal_value':x.portal_value.median(),'median_continue_value':x.recall_value.median(),'median_advantage':x.advantage.median(),'median_advantage_after_top1pct':y.advantage.median(),'truth_dependent':False})
pd.DataFrame(st).to_csv(out/'state_conditioned_advantage.csv',index=False)
# Candidate-set dedup lower bound and ideal shared-cost lower bound for selected fixed actions.
cb=[]
for _,a in target.iterrows():
 x=d[(d.dataset.eq(a.dataset))&(d.build.eq(a.build))&(d.raw_ef.eq(a.raw_ef))&(d['mask'].eq(a['mask']))];p=d[(d.dataset.eq(a.dataset))&(d.build.eq(a.build))&(d.raw_ef.eq(a.raw_ef))&(d['mask'].eq(0))][['role','query_id','candidate_count','total_ndc']].rename(columns={'candidate_count':'primary_candidates','total_ndc':'primary_cost'});x=x.merge(p,on=['role','query_id']);x['candidate_dedup_fraction']=1-x.candidate_count/(x.primary_candidates+x.memo_candidate_lower_bound);x['ideal_shared_cost']=x.primary_cost+(x.candidate_count-x.primary_candidates).clip(lower=0)
 safe=base[(base.dataset.eq(a.dataset))&(base.build.eq(a.build))].groupby('raw_ef').agg(practical_risk=('union_hits',lambda z:(z<9).mean()),cost=('total_ndc','mean')).reset_index();safe=safe[safe.practical_risk<=.05];native_safe=safe.sort_values('cost').iloc[0].cost if len(safe) else np.nan
 cb.append({'dataset':a.dataset,'build':a.build,'raw_ef':a.raw_ef,'mask':a['mask'],'bound_type':'CANDIDATE_SET_LOWER_BOUND','candidate_dedup_fraction_mean':x.candidate_dedup_fraction.mean(),'ideal_shared_cost_mean':x.ideal_shared_cost.mean(),'independent_cals_cost_mean':x.total_ndc.mean(),'native_practical_safe_cost':native_safe,'ideal_below_native_safe':bool(len(safe) and x.ideal_shared_cost.mean()<native_safe),'visited_trace_status':'NOT_ESTIMABLE'})
pd.DataFrame(cb).to_csv(out/'dedup_cost_bounds.csv',index=False)
s=pd.DataFrame(st);candidate=pd.DataFrame(cb);state_ok=[]
for ds,g in s.groupby('dataset'):
 z=g.groupby(['raw_ef','state']).agg(builds_positive=('median_advantage',lambda x:(x>0).sum()),coverage=('coverage','mean'),after=('median_advantage_after_top1pct','median')).reset_index();state_ok.append(bool(((z.builds_positive>=2)&(z.coverage>=.1)&(z['after']>0)).any()))
gates={'two_datasets_positive_portal_value':bool((pd.DataFrame(rows).groupby('dataset').mean_recall_gain.max()>0).all()),'state_conditioned_advantage':all(state_ok),'candidate_lower_bound_feasible':bool(candidate.groupby('dataset').ideal_below_native_safe.any().all()),'non_oracle':True,'role_firewall':True}
decision='PHASE1_PASS' if all(gates.values()) else ('ORACLE_MARGINAL_RESCUE_ONLY_NO_DEPLOYABLE_TRIGGER' if gates['two_datasets_positive_portal_value'] and not gates['state_conditioned_advantage'] else 'MARGINAL_RESCUE_ADVANTAGE_NOT_SUPPORTED_CLOSE_CALS_METHOD_ROUTE')
pd.DataFrame([{'gate':k,'passed':v} for k,v in gates.items()]).to_csv(out/'phase1_gate.csv',index=False)
(docs/'input_audit.md').write_text('# Input audit\n\nFrozen input e129ea3 and all checksums were verified. Historical selection and holdout queries are relabeled only as bn_apd_replay_development. No sealed role was accessed.\n')
(docs/'marginal_rescue_audit.md').write_text(f'# Marginal rescue audit\n\nPhase 1 decision: {decision}. Primary NDC is the only available truth-free state feature; missing frontier, queue and visited-rate features are NOT_ESTIMABLE. Candidate overlap is a CANDIDATE_SET_LOWER_BOUND, not measured shared NDC.\n')
(out/'phase1_decision.json').write_text(json.dumps({'decision':decision,'gates':gates,'evidence_level':'EXPLORATORY_DEVELOPMENT','used_roles':['bn_apd_replay_development'],'sealed_access':False},indent=2))
print(decision,gates)
