#!/usr/bin/env python3
"""Certification-aware frontier and frozen GloVe 16-policy autopsy."""
import math
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import beta,binom
import matplotlib.pyplot as plt
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');OUT=ROOT/'results/icba_theory_lock';FIG=ROOT/'figures/icba_theory_lock';OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
ALPHA=.05; ONLINE_RATIO=.5
def upper(k,n,a):return 1.0 if k>=n else float(beta.ppf(1-a,k+1,n-k))
def kstar(n,m,d):
 ok=[k for k in range(n+1) if upper(k,n,ALPHA/m)<=d];return max(ok) if ok else -1
rows=[]
for d in [.01,.05,.10]:
 for n in [64,128,256,512,1024]:
  for m in [1,4,16]:
   k=kstar(n,m,d)
   for p in [.005,.01,.02,.028,.03,.04,.05,.06,.10]:
    pc=float(binom.cdf(k,n,p)) if k>=0 else 0.; expected=1-pc*(1-ONLINE_RATIO);gain=pc*(1-ONLINE_RATIO)
    rows.append({'delta':d,'n':n,'M':m,'true_failure_rate':p,'k_star':k,'P_cert':pc,'true_safe_but_not_certified_probability':1-pc if p<=d else 'NOT_APPLICABLE','true_unsafe_but_certified_probability':pc if p>d else 'NOT_APPLICABLE','fixed_cost_normalized':1.0,'online_cost_normalized':ONLINE_RATIO,'expected_fail_closed_cost_before_amortization':expected,'calibration_cost_fixed_query_equivalents':n,'break_even_workload_queries':n/gain if gain>0 else 'NO_FINITE_BREAK_EVEN','scenario':'THEORETICAL_NORMALIZED_FAIL_CLOSED'})
F=pd.DataFrame(rows);F.to_csv(OUT/'certification_frontier.csv',index=False)
g=pd.read_csv(ROOT/'results/rcrs_signal/glove_threshold_calibration.csv');auto=[]
for i,r in g.reset_index(drop=True).iterrows():
 k=int(r.failures);n=int(r.n);u1=upper(k,n,ALPHA);u16=upper(k,n,ALPHA/16);c1=u1<=.05;c16=u16<=.05
 if r.stop_coverage==0 and c16:label='SAFE_BUT_ZERO_COVERAGE'
 elif c1 and not c16:label='MULTIPLICITY_LIMITED'
 elif k/n<=.05 and not c1:label='SAMPLE_POWER_LIMITED'
 elif k>0 or k/n>.05:label='POINTWISE_UNSAFE'
 else:label='NOT_ESTIMABLE'
 auto.append({'policy_id':f'glove_threshold_{i:02d}','threshold':r.threshold,'checkpoint_rule':'frozen full sequential policy with fixed fallback','n':n,'failures':k,'failure_rate':k/n,'uncorrected_cp_upper':u1,'bonferroni_cp_upper':u16,'certified_M1':c1,'certified_M16':c16,'early_stop_rate':r.stop_coverage,'calibration_mean_ndc':r.mean_ndc,'fixed_mean_ndc':r.fixed_mean_ndc,'gross_ndc_gain':r.gross_ndc_gain,'design_side_ndc_gain':'NOT_RECOVERABLE_PER_POLICY','design_eval_result':'ONLY_SELECTED_POLICY_RECORDED_SEPARATELY','per_build_result':'NOT_RECOVERABLE_PER_POLICY','classification':label})
A=pd.DataFrame(auto);A.to_csv(OUT/'glove_16_policy_autopsy.csv',index=False)
h=F[(F.M==16)&(F.delta==.05)].pivot(index='true_failure_rate',columns='n',values='P_cert');plt.figure(figsize=(7,4));plt.imshow(h,aspect='auto',origin='lower',vmin=0,vmax=1,cmap='viridis');plt.xticks(range(len(h.columns)),h.columns);plt.yticks(range(len(h.index)),h.index);plt.xlabel('n');plt.ylabel('true p');plt.colorbar(label='P(certified)');plt.title('Certification power, M=16, delta=0.05');plt.tight_layout();plt.savefig(FIG/'certification_power_heatmap.png',dpi=180);plt.savefig(FIG/'certification_power_heatmap.pdf');plt.close()
z=F[(F.n==256)&(F.delta==.05)].copy();
for m,x in z.groupby('M'):plt.plot(x.true_failure_rate,x.expected_fail_closed_cost_before_amortization,marker='o',label=f'M={m}')
plt.xlabel('true failure p');plt.ylabel('expected normalized fail-closed cost');plt.title('Certification-aware fail-closed cost (online/fixed=0.5)');plt.legend();plt.tight_layout();plt.savefig(FIG/'fail_closed_cost_frontier.png',dpi=180);plt.savefig(FIG/'fail_closed_cost_frontier.pdf');plt.close()
print({'frontier_rows':len(F),'autopsy':A.classification.value_counts().to_dict(),'min_failures':int(A.failures.min()),'max_failures':int(A.failures.max())})
