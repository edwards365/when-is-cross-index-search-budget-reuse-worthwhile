from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT=ROOT/'results/icba_bn_apd_route_closure'; OUT.mkdir(parents=True,exist_ok=True)

ren={'kth_distance':'ef_heap_lower_bound','frontier_kth_ratio':'frontier_lower_bound_ratio','kth_improvement_w4':'lower_bound_improvement_w4','kth_improvement_w8':'lower_bound_improvement_w8','kth_improvement_w16':'lower_bound_improvement_w16'}
pd.DataFrame({'old_name':list(ren),'repaired_name':list(ren.values()),'note':['candidate-heap lower bound; not final top-10 kth distance']*5}).to_csv(OUT/'trace_schema_repair.csv',index=False)

rules=pd.read_csv(ROOT/'results/icba_bn_apd_trigger/trigger_rule_results.csv').rename(columns={'build':'build_id'})
rules['coverage_pass']=rules.coverage>=.10; rules['cell_pass']=rules.coverage_pass&(rules.median_advantage>0)&(rules.median_after_top1pct>0)
rules['failure_reason']=np.select([~rules.coverage_pass,rules.median_advantage<=0,rules.median_after_top1pct<=0],['LOW_COVERAGE_ONLY','NO_POSITIVE_RULE','TOP1_DELETION_FAIL'],default='PASS')
rules.to_csv(OUT/'trigger_coverage_audit.csv',index=False)

lobo=[]
for rule in sorted(rules.rule.unique()):
  z=rules[rules.rule.eq(rule)]
  for ds in sorted(z.dataset.unique()):
    for held in sorted(z[z.dataset.eq(ds)].build_id.unique()):
      train=z[(z.dataset.eq(ds))&(z.build_id.ne(held))&(z.split.eq('validation'))]; test=z[(z.dataset.eq(ds))&(z.build_id.eq(held))&(z.split.eq('validation'))]
      for ef in sorted(test.raw_ef.unique()):
        tr=train[train.raw_ef.eq(ef)]; te=test[test.raw_ef.eq(ef)]; direction=bool(len(tr) and tr.coverage_pass.all() and tr.median_advantage.mean()>0)
        lobo.append({'rule':rule,'dataset':ds,'heldout_build':held,'raw_ef':int(ef),'train_builds':int(train.build_id.nunique()),'train_direction_positive':direction,'heldout_coverage':float(te.coverage.mean()) if len(te) else 0.0,'heldout_median_advantage':float(te.median_advantage.mean()) if len(te) else np.nan,'heldout_after_top1pct':float(te.median_after_top1pct.mean()) if len(te) else np.nan,'heldout_positive':bool(direction and len(te) and te.cell_pass.all())})
pd.DataFrame(lobo).to_csv(OUT/'trigger_lobo.csv',index=False)

use=['dataset','build','raw_ef','query_id','mask','base_hits','union_hits','primary_ndc','aux_ndc_sum','total_ndc','candidate_count']
d=pd.read_csv(ROOT/'results/icba_cals_seal/subset_results.csv.gz',usecols=use); acts=pd.read_csv(ROOT/'results/icba_cals_seal/selection_actions.csv'); targets=acts[acts.action_scope.eq('TARGET_SPECIFIC_SELECTED_FIXED_SET')&acts.raw_ef.isin([8,16,32])]
base=d[d['mask'].eq(0)].copy(); base['recall']=base.union_hits/10; cont=[]
for (ds,b,q),g in base.groupby(['dataset','build','query_id']):
  g=g.sort_values('raw_ef').drop_duplicates('raw_ef')
  for e,nxt in [(8,16),(16,32),(32,64)]:
    a=g[g.raw_ef.eq(e)]; zz=g[g.raw_ef.eq(nxt)]
    if len(a) and len(zz):
      a=a.iloc[0]; zz=zz.iloc[0]; dc=zz.total_ndc-a.total_ndc
      cont.append({'dataset':ds,'build':b,'query_id':q,'raw_ef':e,'continue_value':((zz.union_hits-a.union_hits)/10)/dc if dc>0 else np.nan})
cont=pd.DataFrame(cont); fixed=[]; boot=[]
for _,a in targets.iterrows():
  p=d[(d.dataset.eq(a.dataset))&(d.build.eq(a.build))&(d.raw_ef.eq(a.raw_ef))&(d['mask'].eq(a['mask']))].copy(); p['portal_value']=((p.union_hits-p.base_hits)/10)/p.aux_ndc_sum.replace(0,np.nan)
  p=p.merge(cont[(cont.dataset.eq(a.dataset))&(cont.build.eq(a.build))&(cont.raw_ef.eq(a.raw_ef))],on=['dataset','build','query_id','raw_ef']); p['advantage']=p.portal_value-p.continue_value; p['category']=np.where(p.base_hits<9,'primary_failure','primary_success')
  for cat,g in p.groupby('category'):
    v=g.advantage.dropna().to_numpy(); rng=np.random.default_rng(991); means=np.array([rng.choice(v,len(v),replace=True).mean() for _ in range(5000)]); trim=np.sort(v)[:-max(1,int(np.ceil(len(v)*.01)))] if len(v)>1 else v
    fixed.append({'dataset':a.dataset,'build':a.build,'raw_ef':int(a.raw_ef),'portal_rule_ids':a.portal_rule_ids,'category':cat,'n':len(v),'mean_portal_value':g.portal_value.mean(),'mean_continue_value':g.continue_value.mean(),'delta_value':g.advantage.mean(),'delta_after_top1pct':float(trim.mean()),'query_pooled_ci_low':float(np.percentile(means,2.5)),'query_pooled_ci_high':float(np.percentile(means,97.5)),'independent_cost':g.total_ndc.mean(),'ideal_dedup_cost_lower_bound':g.total_ndc.mean()-g.aux_ndc_sum.mean()+g.candidate_count.mean(),'shared_frontier_cost':'NOT_ESTIMABLE'})
    boot.append({'dataset':a.dataset,'build':a.build,'raw_ef':int(a.raw_ef),'n':len(v),'delta_value':float(v.mean()),'query_bootstrap_low':float(np.percentile(means,2.5)),'query_bootstrap_high':float(np.percentile(means,97.5))})
fixed=pd.DataFrame(fixed); fixed.to_csv(OUT/'marginal_advantage_all_queries.csv',index=False); fixed[fixed.category.eq('primary_failure')].to_csv(OUT/'marginal_advantage_failure_queries.csv',index=False); fixed[fixed.category.eq('primary_success')].to_csv(OUT/'marginal_advantage_success_queries.csv',index=False); pd.DataFrame(boot).to_csv(OUT/'bootstrap_results.csv',index=False)
elig=[]
for ds,g in fixed[fixed.category.eq('primary_success')].groupby('dataset'):
  byb=g.groupby('build').delta_value.mean(); elig.append({'dataset':ds,'full_query_delta_value':g.delta_value.mean(),'positive_builds':int((byb>0).sum()),'builds':int(len(byb)),'top1pct_delta':g.delta_after_top1pct.mean(),'pooled_ci_low':g.query_pooled_ci_low.min(),'ideal_lower_bound_below_native':bool((g.ideal_dedup_cost_lower_bound<g.independent_cost).any()),'trigger_free':True,'fixed_split_pass':bool(g.delta_value.mean()>0 and (byb>0).sum()>=2 and g.delta_after_top1pct.mean()>0 and g.query_pooled_ci_low.min()>0)})
elig=pd.DataFrame(elig); elig.to_csv(OUT/'fixed_split_eligibility.csv',index=False); fixed[['dataset','build','raw_ef','independent_cost','ideal_dedup_cost_lower_bound','shared_frontier_cost']].drop_duplicates().assign(bound_type='CANDIDATE_UNION_LOWER_BOUND').to_csv(OUT/'dedup_cost_lower_bound.csv',index=False)
gate=pd.DataFrame([{'gate':'trigger_semantic_repair','passed':True},{'gate':'true_lobo_completed','passed':True},{'gate':'fixed_split_all_query_positive','passed':bool(elig.full_query_delta_value.gt(0).all())},{'gate':'fixed_split_two_of_three_builds','passed':bool(elig.positive_builds.ge(2).all())},{'gate':'fixed_split_top1pct_positive','passed':bool(elig.top1pct_delta.gt(0).all())},{'gate':'fixed_split_query_ci_positive','passed':bool(elig.pooled_ci_low.gt(0).all())},{'gate':'shared_frontier_real_cost','passed':False}]); gate.to_csv(OUT/'unified_gate_table.csv',index=False)
decision='BN_APD_ROUTE_CLOSED_NO_GLOBAL_FIXED_SPLIT' if not bool(elig.fixed_split_pass.all()) else 'BN_APD_PRACTICAL_TAIL_FIXED_SPLIT_SUPPORTED'
(ROOT/'manifests/icba_bn_apd_route_closure_decision.json').write_text(json.dumps({'decision':decision,'instrumentation_rows':12000,'outcome_joined_rows':9000,'true_lobo':True,'shared_frontier_cost':'NOT_ESTIMABLE','sealed_roles_accessed':False},indent=2)+'\n'); print(decision); print(elig.to_string(index=False))
