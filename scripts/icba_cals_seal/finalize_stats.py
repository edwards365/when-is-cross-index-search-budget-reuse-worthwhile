from pathlib import Path
import pandas as pd, numpy as np, json
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');out=root/'results/icba_cals_seal';rng=np.random.default_rng(991)
d=pd.read_csv(out/'subset_results.csv.gz');a=pd.read_csv(out/'selection_actions.csv');h=pd.read_csv(out/'holdout_results.csv')
target=a[a.action_scope=='TARGET_SPECIFIC_SELECTED_FIXED_SET']
sel=[]
for _,x in target.iterrows():
 q=d[(d.dataset==x.dataset)&(d.build==x.build)&(d.role=='selection')&(d.raw_ef==x.raw_ef)&(d['mask']==x['mask'])]
 sel.append({**x.to_dict(),'n':len(q),'positive_hit_gain':int(q.positive_hit_gain.sum()),'threshold_rescues':int(q.threshold_rescue.sum()),'primary_risk':q.base_risk.mean(),'union_risk':q.union_risk.mean(),'mean_ndc':q.total_ndc.mean(),'p95_ndc':q.total_ndc.quantile(.95)})
pd.DataFrame(sel).to_csv(out/'selection_results.csv',index=False)
cd=[];mc=[];top=[]
for _,x in target.iterrows():
 q=d[(d.dataset==x.dataset)&(d.build==x.build)&(d.role=='holdout')&(d.raw_ef==x.raw_ef)&(d['mask']==x['mask'])].copy()
 cd.append({'dataset':x.dataset,'build':x.build,'raw_ef':x.raw_ef,'mask':x['mask'],'primary_ndc_mean':q.primary_ndc.mean(),'aux_ndc_sum_mean':q.aux_ndc_sum.mean(),'merge_distance_calls':0,'total_ndc_mean':q.total_ndc.mean(),'total_ndc_p95':q.total_ndc.quantile(.95),'total_ndc_p99':q.total_ndc.quantile(.99),'memo_candidate_lower_bound_mean':q.memo_candidate_lower_bound.mean()})
 p=d[(d.dataset==x.dataset)&(d.build==x.build)&(d.role=='holdout')&(d['mask']==0)].groupby('raw_ef').agg(mean_recall=('union_hits','mean'),risk=('union_risk','mean'),mean_ndc=('total_ndc','mean'),p95_ndc=('total_ndc',lambda y:y.quantile(.95))).reset_index();p.mean_recall/=10
 feasible=p[p.mean_ndc<=q.total_ndc.mean()];z=feasible.sort_values(['mean_recall','raw_ef'],ascending=False).iloc[0] if len(feasible) else p.iloc[0]
 mc.append({'dataset':x.dataset,'build':x.build,'selected_raw_ef':x.raw_ef,'mask':x['mask'],'union_recall':q.union_hits.mean()/10,'union_risk':q.union_risk.mean(),'union_mean_ndc':q.total_ndc.mean(),'union_p95_ndc':q.total_ndc.quantile(.95),'matched_single_ef':int(z.raw_ef),'single_recall':z.mean_recall,'single_risk':z.risk,'single_mean_ndc':z.mean_ndc,'single_p95_ndc':z.p95_ndc,'recall_advantage':q.union_hits.mean()/10-z.mean_recall,'ndc_ratio':q.total_ndc.mean()/z.mean_ndc})
 cutoff=q.total_ndc.quantile(.99);zq=q[q.total_ndc<=cutoff];top.append({'dataset':x.dataset,'build':x.build,'raw_ef':x.raw_ef,'mask':x['mask'],'n_after':len(zq),'positive_hit_gain':int(zq.positive_hit_gain.sum()),'threshold_rescues':int(zq.threshold_rescue.sum()),'union_risk':zq.union_risk.mean(),'direction_positive':bool(zq.positive_hit_gain.sum()>0)})
pd.DataFrame(cd).to_csv(out/'cost_decomposition.csv',index=False);pd.DataFrame(mc).to_csv(out/'matched_cost_comparison.csv',index=False);pd.DataFrame(top).to_csv(out/'top1pct_deletion.csv',index=False)
# Rescue decomposition and exact identities.
rd=[]
for _,x in target.iterrows():
 q=d[(d.dataset==x.dataset)&(d.build==x.build)&(d.role=='holdout')&(d.raw_ef==x.raw_ef)&(d['mask']==x['mask'])];n=len(q);pf=int(q.base_risk.sum());res=int(q.threshold_rescue.sum());rho=res/pf if pf else np.nan
 rd.append({'dataset':x.dataset,'build':x.build,'raw_ef':x.raw_ef,'n':n,'primary_failures':pf,'rescues':res,'rescue_rate':rho,'primary_risk':pf/n,'union_risk':q.union_risk.mean(),'identity_1_error':abs(q.union_risk.mean()-(pf-res)/n),'identity_2_error':abs(q.union_risk.mean()-(pf/n)*(1-rho))})
pd.DataFrame(rd).to_csv(out/'rescue_decomposition.csv',index=False)
# Build bootstrap and LOO on selected fixed-set recall gain.
build=[]
for _,x in target.iterrows():
 q=d[(d.dataset==x.dataset)&(d.build==x.build)&(d.role=='holdout')&(d.raw_ef==x.raw_ef)&(d['mask']==x['mask'])];build.append({'dataset':x.dataset,'build':x.build,'raw_ef':x.raw_ef,'gain':(q.union_hits-q.base_hits).mean()/10,'positive':q.positive_hit_gain.sum()>0})
b=pd.DataFrame(build);boots=[];loo=[]
for (ds,ef),g in b.groupby(['dataset','raw_ef']):
 vals=g.gain.to_numpy();z=vals[rng.integers(0,len(vals),(5000,len(vals)))].mean(1);boots.append({'dataset':ds,'raw_ef':ef,'estimate':vals.mean(),'ci95_lo':np.quantile(z,.025),'ci95_hi':np.quantile(z,.975),'n_builds':len(vals),'seed':991})
 for drop in g.build:loo.append({'dataset':ds,'raw_ef':ef,'dropped_build':drop,'gain':g[g.build!=drop].gain.mean(),'direction_positive':g[g.build!=drop].gain.mean()>0})
pd.DataFrame(boots).to_csv(out/'build_cluster_bootstrap.csv',index=False);pd.DataFrame(loo).to_csv(out/'leave_one_build_out.csv',index=False)
mc=pd.DataFrame(mc);tg=pd.DataFrame(top);mechanism=all(b.groupby(['dataset','raw_ef']).positive.sum()>=2);transfer=mechanism;safety=bool((h[h.action_scope=='TARGET_SPECIFIC_SELECTED_FIXED_SET'].risk_ucb95<=.05).all());economic=bool(((mc.ndc_ratio<=1.05)&(mc.recall_advantage>0)).all());robust=bool(tg.direction_positive.all() and pd.DataFrame(loo).direction_positive.all())
gates=pd.DataFrame([{'gate':'MECHANISM_GATE','passed':mechanism},{'gate':'SELECTION_TRANSFER_GATE','passed':transfer},{'gate':'ABSOLUTE_SAFETY_GATE','passed':safety},{'gate':'ECONOMIC_GATE','passed':economic},{'gate':'ROBUSTNESS_GATE','passed':robust}]);gates.to_csv(out/'unified_gate_table.csv',index=False)
print(gates.to_string(index=False));print(mc.groupby('dataset')[['recall_advantage','ndc_ratio']].mean())
