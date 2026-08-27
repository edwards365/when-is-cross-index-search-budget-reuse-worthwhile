#!/usr/bin/env python3
"""Build-pair and censoring sensitivity without treating 648 pairs as independent builds."""
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib.pyplot as plt
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');OUT=ROOT/'results/icba_theory_lock';FIG=ROOT/'figures/icba_theory_lock';RNG=np.random.default_rng(991)
U=pd.read_csv(ROOT/'results/theory_generalization/unified_theory_table.csv');E=pd.read_csv(OUT/'exact_barrier_decomposition.csv');Q=pd.read_csv(ROOT/'results/theory_generalization/risk_cost_frontier.csv')
keys=['index','dataset','source_seed','source_history','target_seed','target_history'];D=E.merge(U[keys+['exact_safe_monotone_tax_fraction_observed']],on=keys,validate='one_to_one')
D['cluster']=D.apply(lambda r:'|'.join(sorted([f"{int(r.source_seed)}:{r.source_history}",f"{int(r.target_seed)}:{r.target_history}"])),axis=1)
boot=[]
for (idx,ds,cat),g in D.groupby(['index','dataset','category']):
 c=g.groupby('cluster').exact_safe_monotone_tax_fraction_observed.mean();vals=c.to_numpy();draw=vals[RNG.integers(0,len(vals),(5000,len(vals)))].mean(1)
 boot.append({'index':idx,'dataset':ds,'category':cat,'directed_pairs':len(g),'unordered_build_pair_clusters':len(vals),'mean_tax_over_fixed':g.exact_safe_monotone_tax_fraction_observed.mean(),'cluster_boot_ci_low':np.quantile(draw,.025),'cluster_boot_ci_high':np.quantile(draw,.975),'bootstrap':5000,'seed':991,'interpretation':'BUILD_PAIR_SENSITIVITY_NOT_POPULATION_BUILD_CI'})
B=pd.DataFrame(boot);B.to_csv(OUT/'build_sensitivity.csv',index=False)
loo=[]
for (idx,ds),g in D.groupby(['index','dataset']):
 base=g.exact_safe_monotone_tax_fraction_observed.mean()
 for seed in sorted(set(g.source_seed)|set(g.target_seed)):
  z=g[(g.source_seed!=seed)&(g.target_seed!=seed)];loo.append({'index':idx,'dataset':ds,'omission_type':'seed','omitted':int(seed),'remaining_pairs':len(z),'baseline_mean':base,'leave_out_mean':z.exact_safe_monotone_tax_fraction_observed.mean(),'delta_from_baseline':z.exact_safe_monotone_tax_fraction_observed.mean()-base})
 for hist in sorted(set(g.source_history)|set(g.target_history)):
  z=g[(g.source_history!=hist)&(g.target_history!=hist)];loo.append({'index':idx,'dataset':ds,'omission_type':'history','omitted':hist,'remaining_pairs':len(z),'baseline_mean':base,'leave_out_mean':z.exact_safe_monotone_tax_fraction_observed.mean(),'delta_from_baseline':z.exact_safe_monotone_tax_fraction_observed.mean()-base})
 for seed,hist in sorted(set(zip(g.source_seed,g.source_history))|set(zip(g.target_seed,g.target_history))):
  z=g[~(((g.source_seed==seed)&(g.source_history==hist))|((g.target_seed==seed)&(g.target_history==hist)))];loo.append({'index':idx,'dataset':ds,'omission_type':'build','omitted':f'{int(seed)}:{hist}','remaining_pairs':len(z),'baseline_mean':base,'leave_out_mean':z.exact_safe_monotone_tax_fraction_observed.mean(),'delta_from_baseline':z.exact_safe_monotone_tax_fraction_observed.mean()-base})
L=pd.DataFrame(loo);L.to_csv(OUT/'leave_one_out.csv',index=False)
c=[]
for (idx,ds),g in D.groupby(['index','dataset']):
 cens=g.right_censoring_rate.mean();risk=Q[(Q['index']==idx)&(Q.dataset==ds)]
 c.append({'index':idx,'dataset':ds,'pairs':len(g),'mean_right_censoring_rate':cens,'observed_only_mean_tax_over_fixed':g.exact_safe_monotone_tax_fraction_observed.mean(),'clipped_lower_bound_mean_tax_over_fixed':g.exact_safe_monotone_tax_fraction_observed.mean(),'conservative_zero_risk_cost':'UNBOUNDED_WITHOUT_ABOVE_GRID_COST_ASSUMPTION' if cens>0 else 'EXACT_ON_GRID','censoring_interval_lower':g.exact_safe_monotone_tax_fraction_observed.mean(),'censoring_interval_upper':'UNBOUNDED' if cens>0 else g.exact_safe_monotone_tax_fraction_observed.mean(),'risk_cells_exact':int((risk.status=='EXACT').sum()),'risk_cells_censored_mandatory_failure':int((risk.status=='EXACT_WITH_CENSORED_AS_MANDATORY_FAILURE').sum()),'risk_cells_infeasible':int(risk.status.str.startswith('INFEASIBLE').sum())})
C=pd.DataFrame(c);C.to_csv(OUT/'censoring_sensitivity.csv',index=False)
bb=B.copy();bb['label']=bb['index']+'\n'+bb['dataset'].str.replace('_100k','')+'\n'+bb['category'].str.replace('_',' ');x=np.arange(len(bb));y=bb.mean_tax_over_fixed.to_numpy();lo=y-bb.cluster_boot_ci_low.to_numpy();hi=bb.cluster_boot_ci_high.to_numpy()-y;plt.figure(figsize=(12,5));plt.errorbar(x,y,yerr=[lo,hi],fmt='o',capsize=2);plt.xticks(x,bb.label,rotation=70,ha='right');plt.ylabel('Safe monotone tax / fixed NDC');plt.title('Build-pair cluster sensitivity (not a population build CI)');plt.tight_layout();plt.savefig(FIG/'build_uncertainty.png',dpi=180);plt.savefig(FIG/'build_uncertainty.pdf');plt.close()
print({'build_rows':len(B),'loo_rows':len(L),'censor_rows':len(C),'max_abs_loo_delta':float(L.delta_from_baseline.abs().max())})
