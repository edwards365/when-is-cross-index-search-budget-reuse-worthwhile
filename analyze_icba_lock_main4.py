#!/usr/bin/env python3
"""Non-deployable target-state Oracle and resumability values from frozen traces."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib.pyplot as plt
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');OUT=ROOT/'results/icba_theory_lock';FIG=ROOT/'figures/icba_theory_lock';OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
runs=[('sift_100k',7,ROOT/'results/rcrs_signal/sift_trace_labels.csv',ROOT/'results/rcrs_signal/sift_prefix_equivalence.csv')]
for seed in [7,17,29]:runs.append(('glove100_100k',seed,ROOT/f'results/rcrs_signal/glove/seed{seed}_trace.csv',ROOT/f'results/rcrs_signal/glove/seed{seed}_equivalence.csv'))
detail=[];summary=[];res=[]
for ds,seed,tp,ep in runs:
 t=pd.read_csv(tp);e=pd.read_csv(ep).set_index('query_id')
 for q,g in t.groupby('query_id'):
  g=g.sort_values('checkpoint');fixed=float(e.loc[q,'native_ndc']);safe=g[g.safe_label.astype(int)==1]
  if len(safe):chosen=safe.iloc[0];prefix=float(chosen.ndc);repeated=float(g[g.checkpoint<=chosen.checkpoint].ndc.sum());stop=int(chosen.checkpoint);cens=False
  else:prefix=fixed;repeated=float(g.ndc.sum()+fixed);stop='FALLBACK';cens=True
  detail.append({'dataset':ds,'build_seed':seed,'query_id':q,'fixed_ndc':fixed,'oracle_stop_checkpoint':stop,'prefix_preserving_oracle_ndc':prefix,'repeated_probe_oracle_ndc':repeated,'oracle_saving_ndc':fixed-prefix,'resumability_value_ndc':repeated-prefix,'right_censored_no_safe_checkpoint':cens,'control_overhead_break_even_upper_ndc':max(0,fixed-prefix),'wall_clock_control_overhead':'NOT_ESTIMABLE','evidence':'NON_DEPLOYABLE_TARGET_STATE_ORACLE_VALUE'})
d=pd.DataFrame(detail);d.to_csv(OUT/'target_information_value_per_query.csv',index=False)
for (ds,seed),g in d.groupby(['dataset','build_seed']):
 summary.append({'dataset':ds,'build_seed':seed,'queries':len(g),'fixed_mean_ndc':g.fixed_ndc.mean(),'perfect_label_prefix_mean_ndc':g.prefix_preserving_oracle_ndc.mean(),'oracle_target_state_saving_fraction':(g.fixed_ndc.mean()-g.prefix_preserving_oracle_ndc.mean())/g.fixed_ndc.mean(),'right_censoring_rate':g.right_censored_no_safe_checkpoint.mean(),'wall_clock_control_overhead':'NOT_ESTIMABLE','evidence':'NON_DEPLOYABLE_TARGET_STATE_ORACLE_VALUE'})
 res.append({'dataset':ds,'build_seed':seed,'queries':len(g),'prefix_preserving_mean_ndc':g.prefix_preserving_oracle_ndc.mean(),'repeated_probe_mean_ndc':g.repeated_probe_oracle_ndc.mean(),'resumability_value_mean_ndc':g.resumability_value_ndc.mean(),'repeated_over_prefix':g.repeated_probe_oracle_ndc.mean()/g.prefix_preserving_oracle_ndc.mean(),'prefix_equivalence_all_queries':True,'evidence':'NON_DEPLOYABLE_TARGET_STATE_ORACLE_VALUE'})
S=pd.DataFrame(summary);R=pd.DataFrame(res);S.to_csv(OUT/'target_information_value.csv',index=False);R.to_csv(OUT/'resumability_value.csv',index=False)
x=np.arange(len(S));w=.36;plt.figure(figsize=(8,4));plt.bar(x-w/2,S.fixed_mean_ndc,w,label='fixed');plt.bar(x+w/2,S.perfect_label_prefix_mean_ndc,w,label='perfect-label prefix Oracle');plt.xticks(x,[f'{a}\nseed {b}' for a,b in zip(S.dataset,S.build_seed)]);plt.ylabel('Mean NDC');plt.title('Cost-adjusted target-state Oracle contact');plt.legend();plt.tight_layout();plt.savefig(FIG/'cost_adjusted_information_value.png',dpi=180);plt.savefig(FIG/'cost_adjusted_information_value.pdf');plt.close()
print(S[['dataset','build_seed','oracle_target_state_saving_fraction','right_censoring_rate']].to_dict('records'))
