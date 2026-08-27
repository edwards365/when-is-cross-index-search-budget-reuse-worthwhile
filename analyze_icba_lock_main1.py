#!/usr/bin/env python3
"""Main Result I empirical contact on frozen source/target stable budgets."""
import csv
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
OUT=ROOT/'results/icba_theory_lock'; FIG=ROOT/'figures/icba_theory_lock'; OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
P=ROOT/'results/cross_index/g1/derived/per_query_effort.csv'
D=pd.read_csv(P); D=D[D['split']=='confirm'].copy() if 'confirm' in set(D['split']) else D.copy()
V=pd.read_csv(ROOT/'results/theory_generalization/information_class_values.csv')
keys=['index','dataset','source_seed','source_history','target_seed','target_history']
vmap={tuple(r[k] for k in keys):r for _,r in V.iterrows()}
rows=[]
for (idx,ds),g in D.groupby(['index','dataset']):
    builds=sorted(g[['seed','history']].drop_duplicates().itertuples(index=False,name=None))
    m={(int(s),h):z.set_index('query_id').sort_index() for (s,h),z in g.groupby(['seed','history'])}
    for ss,sh in builds:
      for ts,th in builds:
        if (ss,sh)==(ts,th):continue
        a=m[(ss,sh)][['stable_budget','right_censored','fixed_budget']].join(m[(ts,th)][['stable_budget','right_censored']],lsuffix='_s',rsuffix='_t',how='inner')
        x=a.stable_budget_s.to_numpy();y=a.stable_budget_t.to_numpy();cens=a.right_censored_t.astype(bool).to_numpy()
        levels=np.unique(x); spreads=[]; alias=0; env=np.empty(len(a),dtype=float)
        for level in levels:
            ids=np.where(x==level)[0]; vals=np.unique(y[ids]); spread=float(vals.max()-vals.min());spreads.append(spread)
            alias+=int(len(vals)>1);env[ids]=vals.max()
        ident=np.array_equal(env,y)
        k=(idx,ds,ss,sh,ts,th);vr=vmap[k]
        tax=float(vr['source_envelope_clipped_mean_ndc'])-float(vr['oracle_observed_mean_ndc'])
        frac=tax/float(vr['fixed_mean_ndc'])
        rows.append({'index':idx,'dataset':ds,'source_seed':ss,'source_history':sh,'target_seed':ts,'target_history':th,
          'category':'same_order_cross_seed' if sh==th else 'cross_order','n_queries':len(a),'source_summary_groups':len(levels),
          'aliasing_groups':alias,'aliasing_group_fraction':alias/len(levels),'mean_target_budget_spread':float(np.mean(spreads)),
          'max_target_budget_spread':float(np.max(spreads)),'target_budget_measurable_from_source_empirically':ident,
          'information_tax_ndc_clipped':tax,'information_tax_over_fixed_clipped':frac,'zero_tax':bool(abs(tax)<=1e-12 and not cens.any()),
          'approx_zero_tax_le_1pct_fixed':bool(frac<=.01 and not cens.any()),'right_censoring_rate':float(cens.mean()),
          'censoring_qualification':'CLIPPED_LOWER_BOUND' if cens.any() else 'EXACT_ON_GRID','approx_zero_threshold_preregistered':.01})
R=pd.DataFrame(rows);R.to_csv(OUT/'information_zero_tax.csv',index=False)
agg=R.groupby(['index','dataset','category']).agg(pairs=('zero_tax','size'),zero_tax_pairs=('zero_tax','sum'),approx_zero_pairs=('approx_zero_tax_le_1pct_fixed','sum'),mean_tax=('information_tax_over_fixed_clipped','mean'),mean_alias=('aliasing_group_fraction','mean')).reset_index();agg.to_csv(OUT/'information_zero_tax_summary.csv',index=False)
z=R.groupby(['index','dataset']).information_tax_over_fixed_clipped.mean().unstack(0);ax=z.plot(kind='bar',figsize=(8,4));ax.set_ylabel('Information tax / fixed NDC');ax.set_xlabel('Dataset');ax.set_title('Source-summary information tax (frozen empirical contact)');plt.tight_layout();plt.savefig(FIG/'information_tax_by_implementation.png',dpi=180);plt.savefig(FIG/'information_tax_by_implementation.pdf');plt.close()
print({'pairs':len(R),'zero_tax':int(R.zero_tax.sum()),'approx_zero':int(R.approx_zero_tax_le_1pct_fixed.sum()),'aliasing_pairs':int((R.aliasing_groups>0).sum())})
