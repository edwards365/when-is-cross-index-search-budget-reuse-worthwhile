#!/usr/bin/env python3
"""Generate the preregistered ICBA PNG/PDF figure set from frozen outputs."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import beta

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
R=ROOT/'results/theory_generalization'; F=R/'figures'; F.mkdir(exist_ok=True)
U=pd.read_csv(R/'unified_theory_table.csv'); V=pd.read_csv(R/'information_class_values.csv')
I=pd.read_csv(R/'inversion_bounds.csv'); C=pd.read_csv(R/'censoring_analysis.csv')
P=pd.read_csv(R/'certification_power.csv'); Q=pd.read_csv(R/'risk_cost_frontier.csv')
plt.rcParams.update({'figure.dpi':140,'savefig.dpi':180,'font.size':9,'axes.grid':True,'grid.alpha':.22})

def save(name):
    plt.tight_layout(); plt.savefig(F/(name+'.png')); plt.savefig(F/(name+'.pdf')); plt.close()

# 1 information hierarchy (partial order, not an unjustified total order)
plt.figure(figsize=(8,3.2)); pos={'Fixed':(.08,.5),'Source summary':(.3,.72),'Target static':(.55,.82),'Target sequential':(.78,.82),'Oracle':(.93,.5),'Source monotone':(.55,.28)}
for n,(x,y) in pos.items(): plt.text(x,y,n,ha='center',va='center',bbox=dict(boxstyle='round',fc='#eef3f8',ec='#52606d'))
for a,b in [('Fixed','Source summary'),('Source summary','Target static'),('Target static','Oracle'),('Target static','Target sequential'),('Target sequential','Oracle'),('Source summary','Source monotone')]:
    xa,ya=pos[a];xb,yb=pos[b];plt.annotate('',(xb-.05,yb),(xa+.06,ya),arrowprops=dict(arrowstyle='->',color='#52606d'))
plt.text(.5,.05,'Arrows denote information refinement only where containment is justified',ha='center');plt.axis('off');plt.title('ICBA information classes (theorem)');save('information_hierarchy')

# 2 implementation-local cost hierarchy
v=V.copy(); cols=['fixed_mean_ndc','source_envelope_clipped_mean_ndc','monotone_clipped_mean_ndc','oracle_observed_mean_ndc']
z=v.groupby(['index','dataset'])[cols].mean(); z=z.div(z['fixed_mean_ndc'],axis=0)
z.plot(kind='bar',figsize=(11,4));plt.ylabel('Mean NDC / fixed NDC');plt.xlabel('Implementation × dataset');plt.title('Information-class cost hierarchy (empirical; clipped where censored)');plt.legend(['Fixed','Source envelope','Source monotone','Oracle observed'],ncol=4);save('information_class_costs')

# 3 inversion vs monotone tax
plt.figure(figsize=(6.5,4.5));
for idx,g in U.groupby('index'):plt.scatter(g.rank_inversion,g.exact_safe_monotone_tax_fraction_observed,s=13,alpha=.55,label=idx)
plt.xlabel('Rank inversion rate');plt.ylabel('Safe monotone tax / fixed NDC');plt.title('Rank inversion and monotone tax (empirical association)');plt.legend();save('inversion_vs_monotone_tax')

# 4 matching bound tightness
plt.figure(figsize=(6.5,4.5)); x=I.matching_budget_gap_bound; y=I.lower_bound_tightness_budget_gap
plt.scatter(x,y,s=12,alpha=.5);plt.xlabel('Matching budget-gap lower bound');plt.ylabel('Bound / realized monotone budget gap');plt.yscale('log');plt.title('Matching lower-bound tightness (computational; T4 proof sketch)');save('matching_bound_tightness')

# 5 risk-cost frontier, feasible rows only
q=Q[pd.to_numeric(Q.monotone_over_fixed,errors='coerce').notna()].copy();q['v']=pd.to_numeric(q.monotone_over_fixed)
g=q.groupby(['index','delta']).v.mean().reset_index();plt.figure(figsize=(6.5,4.5))
for idx,d in g.groupby('index'):plt.plot(d.delta,d.v,marker='o',label=idx)
plt.xlabel('Allowed marginal failure δ');plt.ylabel('Monotone mean NDC / fixed NDC');plt.title('Risk–cost frontier (frozen-grid feasible units)');plt.legend();save('risk_cost_frontier')

# 6 certification probability heatmap, M=16, p rows, n columns
h=P[P.M==16].pivot(index='true_failure_rate',columns='n',values='exact_certification_probability');plt.figure(figsize=(7,4));plt.imshow(h,aspect='auto',origin='lower',vmin=0,vmax=1,cmap='viridis');plt.xticks(range(len(h.columns)),h.columns);plt.yticks(range(len(h.index)),h.index);plt.xlabel('Calibration n');plt.ylabel('True failure p');plt.colorbar(label='Certification probability');plt.title('Certification power, M=16 (exact binomial)');save('certification_probability_heatmap')

# 7 maximum allowed failures
def kstar(n,m):
    ok=[k for k in range(n+1) if beta.ppf(1-.05/m,k+1,n-k)<=.05];return max(ok) if ok else -1
ns=[64,128,256,512,1024];plt.figure(figsize=(6.5,4.5))
for m in [1,4,16]:plt.plot(ns,[kstar(n,m) for n in ns],marker='o',label=f'M={m}')
plt.xlabel('Calibration n');plt.ylabel('Maximum observed failures k*');plt.title('Multiplicity reduces allowable failures (theory)');plt.legend();save('allowed_failures_by_n_m')

# 8 equal ranking, unequal operating risk
import json
payload=json.loads((R/'signal_certification_simulation.json').read_text()); rows=payload.get('models',payload.get('signal_gap'))
ss=pd.DataFrame(rows);plt.figure(figsize=(6.5,4.2));plt.bar(ss.model,100*ss.unsafe_given_stop);plt.ylabel('Unsafe given stop (%)');plt.title(f"Same AUROC={ss.auroc.iloc[0]:.3f}, different threshold risk (simulation)");save('high_auc_noncertifiable_example')

# 9 censoring sensitivity
g=C.groupby(['index','dataset']).right_censoring_rate.mean().unstack(0);g.plot(kind='bar',figsize=(8,4));plt.ylabel('Right-censoring rate');plt.xlabel('Dataset');plt.title('Frozen-grid right censoring (empirical)');save('right_censoring_sensitivity')

# 10 implementation × dataset gate heatmap
g=U.groupby(['index','dataset']).exact_safe_monotone_tax_fraction_observed.mean().unstack(0);plt.figure(figsize=(6.5,4));plt.imshow(g,aspect='auto',cmap='magma');plt.xticks(range(len(g.columns)),g.columns);plt.yticks(range(len(g.index)),g.index);plt.colorbar(label='Safe monotone tax / fixed NDC');plt.title('Implementation × dataset theoretical contact');save('implementation_dataset_gate_heatmap')

files=sorted(str(p.relative_to(ROOT)) for p in F.iterdir());(R/'figure_manifest.txt').write_text('\n'.join(files)+'\n');print(len(files),'figure files')
