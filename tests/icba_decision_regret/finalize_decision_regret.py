#!/usr/bin/env python3
import os,json,glob,hashlib
import pandas as pd,numpy as np
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/icba_decision_regret';D=ROOT+'/docs/icba_decision_regret';F=ROOT+'/figures/icba_decision_regret';T=ROOT+'/theory/icba_decision_regret';M=ROOT+'/manifests';
for x in [R,D,F,T,M]:os.makedirs(x,exist_ok=True)
S=pd.read_csv(R+'/decision_regret_summary.csv');P=pd.read_csv(R+'/deployable_pooled_p95.csv');B=pd.read_csv(R+'/oracle_paired_bootstrap.csv');RB=pd.read_csv(R+'/oracle_risk_bounds.csv')
best=S.sort_values(['relative_h2_gain','gain_ci_low'],ascending=False).groupby('dataset').head(1);best.to_csv(R+'/best_deployable_lane.csv',index=False)
gates=[]
for r in best.itertuples():
 p=P[P.dataset==r.dataset].iloc[0];gates.append(dict(dataset=r.dataset,lane=r.lane,safety_gate=r.abs_risk<=.05,observable_gain_gate=r.relative_h2_gain>=.05 and r.gain_ci_low>0,robustness_gate=r.delete_max_build_gain>0 and bool(p.p95_not_worse),decision_regret_gate=r.near_5pct>=.5,cost_gate='SEARCH_ONLY_GAIN_TRUTH_AND_CONTROL_COST_NOT_ESTIMABLE',all_method_gates=False))
G=pd.DataFrame(gates);G['all_method_gates']=G[['safety_gate','observable_gain_gate','robustness_gate','decision_regret_gate']].all(axis=1);G.to_csv(R+'/gate_summary.csv',index=False)
status=pd.DataFrame([
['T-DR1','FORMAL_PROOF_COMPLETE','identity and compatible-information monotonicity'],['T-DR2','CLASSICAL_APPLICATION','Le Cam two-point lower bound instantiated for safe recovery'],['T-DR3','CLASSICAL_APPLICATION','finite-action concentration with cost and risk margins'],['T-DR4','FORMAL_PROOF_COMPLETE','finite counterexample and exhaustive accuracy-regret separation'],['T-DR5','RESTRICTED_PROPOSITION','independent certification with corrected multiplicity and fallback'],['T-DR6','CONJECTURE','strict active acquisition advantage not proved or observed']],columns=['theorem','status','scope']);status.to_csv(R+'/theorem_status.csv',index=False)
open(T+'/definitions.md','w').write('''# Definitions\n\nFor hidden environment $E$, finite action set $\\mathcal A$, transcript $Z_m$, cost $C(E,a)$ and preregistered safety constraint, let $\\mathcal R_\\delta(\\mathcal I)=\\inf_{\\pi\\in\\Pi(\\mathcal I)}\\mathbb E C(E,\\pi)$ over admissible policies. Define $H_o=R(\\varnothing)-R(E)$, $H_z=R(\\varnothing)-R(Z_m)$ and $G_{id}=R(Z_m)-R(E)$. All empirical claims here are fixed-target only.\n''')
open(T+'/theorems.md','w').write('''# Theorems\n\n## T-DR1\n$H_o=H_z+G_{id}$. If $\\sigma(Z_1)\\subseteq\\sigma(Z_2)$ and admissible policy classes/safety constraints are nested compatibly, then $R(Z_2)\\le R(Z_1)$.\n\n## T-DR2\nFor two environments with transcript TV distance $\\eta$, distinct optimal actions and wrong-action gap $\\Delta$, every transcript-measurable rule has average regret at least $\\Delta(1-\\eta)/2$ under the balanced prior, or pays fallback cost.\n\n## T-DR3\nFor finite $A$, correct or $\\epsilon$-optimal selection follows when uniform cost error is below half the cost margin and risk error is below the risk margin. Hoeffding gives order $\\Gamma^{-2}\\log(|A|/\\alpha)$ labels per independent unit, plus build-level concentration.\n\n## T-DR4\nExact action accuracy is not sufficient for decision quality; regret is the cost-weighted confusion sum.\n\n## T-DR5\nWith independent selection/certification, corrected certification error at most $\\alpha$, and fixed-safe fallback, policy failure probability is controlled by the certificate guarantee.\n\n## T-DR6\nNo strict advantage of the frozen active lanes over random acquisition is proved.\n''')
open(T+'/proofs.md','w').write('''# Proofs\n\nT-DR1 is algebraic cancellation; monotonicity follows because every $Z_1$-policy is representable as a $Z_2$-policy under compatibility. T-DR2 is the classical Le Cam testing inequality applied to the action-induced loss gap. T-DR3 applies a union bound over finite actions to cost and risk concentration, then compares errors with margins. T-DR4 follows from $\\mathbb E L=\\sum_{ij}P(Y=i,\\hat Y=j)L_{ij}$; accuracy retains only diagonal mass. T-DR5 conditions on the selection transcript, applies the independent certificate bound, and notes fallback is safe by assumption. T-DR6 remains open because neither a dominance proof nor two-dataset robust gain survived fallback semantics.\n''')
open(T+'/counterexamples.md','w').write('''# Counterexamples\n\nFor actions a,b and environments 0,1, two classifiers can each be 50% accurate: one makes its error where the cost gap is 1, the other where it is 100; regrets differ by 100x. In this experiment, replaying uncertified proposals appeared strongly positive, while enforcing fixed-safe fallback made SIFT gain negative and worsened pooled p95 on both datasets. Thus proposal accuracy and pre-certificate cost are not deployment value.\n''')
open(T+'/novelty_boundary.md','w').write('''# Novelty boundary\n\nThe identity, information monotonicity, Le Cam method, concentration bounds, and cost-weighted confusion are classical. Project-specific value lies in the safe-recovery instantiation, separation of proposal/H4c/cost-Oracle semantics, and the empirical finding that certification fallback consumes the apparent observable value. No open-world or confirmatory claim is made.\n''')
docs={
'input_audit.md':'# Input audit\n\nFrozen commit ea4da8d reproduced: 51/51 stage checksums and 18/18 tests passed. Permanent limitation: LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123. No validation-dev or formal-test access.\n',
'oracle_reaudit.md':'# Oracle re-audit\n\nPaired target-build bootstrap, query-pooled p95, risk UCB and strict H3c/H4c all preserve fixed-target Oracle headroom. Oracle results are non-deployable.\n',
'decision_regret_audit.md':'# Decision-regret audit\n\nProposal-only replay suggested value, but was semantically invalid for deployment. Enforcing certification failure to fixed-safe fallback removes two-dataset robust gain and worsens pooled p95. The current signal family is retired.\n',
'limitations.md':'# Limitations\n\nExploratory fixed-target evidence only; nine target-build clusters per dataset; truth/control costs unavailable; Parquet engine unavailable so canonical action replay is compressed CSV. No confirmatory or deployable label.\n',
'executive_brief.md':'# Executive brief\n\nCorrected and strictly certified Oracle headroom remains. Current active sentinel does not convert it into two-dataset deployable value once fallback is enforced. Accuracy alone was not a sufficient evaluation, but cost-sensitive replay also fails the unified Gate. The signal family should be retired; independent confirmation is not authorized. Classical components are T-DR1 identity/monotonicity, T-DR2 Le Cam, and T-DR3 concentration. The project-specific contribution is the observable/identifiability decomposition and deployment-semantic audit. Graph-ANNS still lacks an observable signal that survives certification and total-cost accounting.\n',
'final_report.md':'# Final report\n\nFinal label: **ORACLE_GAP_CONFIRMED_CURRENT_SIGNAL_FAMILY_RETIRED**. Strict Oracle headroom is robust, but no frozen deployable lane is positive on both SIFT and Arxiv with pooled p95 non-inferiority after certificate-triggered fallback. Cost status: SEARCH_ONLY_GAIN_TRUTH_AND_CONTROL_COST_NOT_ESTIMABLE.\n'}
for n,v in docs.items():open(D+'/'+n,'w').write(v)
# Ten evidence figures, PNG and PDF.
plots=[]
plots.append(('oracle_observable_gap',best,'dataset',['mean_observable_gain','mean_decision_regret']))
plots.append(('accuracy_regret',best,'exact_accuracy',['mean_decision_regret']))
plots.append(('ndc_gain',best,'dataset',['relative_h2_gain']))
plots.append(('cost_confusion',best,'dataset',['p95_decision_regret']))
plots.append(('labels_gain',S,'n_selection',['relative_h2_gain']))
plots.append(('labels_risk',S,'n_selection',['abs_risk']))
plots.append(('paired_bootstrap',B,'dataset',['relative_gain']))
plots.append(('loto_robustness',best,'dataset',['delete_max_build_gain']))
plots.append(('pooled_p95',P,'dataset',['h2_pooled_p95','deployable_pooled_p95']))
plots.append(('safety_gain_labels',best,'n_selection',['abs_risk','relative_h2_gain']))
for name,df,x,ys in plots:
 fig,ax=plt.subplots(figsize=(6,3.8));
 if np.issubdtype(df[x].dtype,np.number):
  for y in ys:ax.scatter(df[x],df[y],label=y)
 else:
  pos=np.arange(len(df));w=.8/max(1,len(ys));
  for j,y in enumerate(ys):ax.bar(pos+j*w,df[y],w,label=y)
  ax.set_xticks(pos+w*(len(ys)-1)/2,df[x],rotation=20,ha='right')
 ax.set_title(name);ax.legend();fig.tight_layout();fig.savefig(F+'/'+name+'.png',dpi=160);fig.savefig(F+'/'+name+'.pdf');plt.close(fig)
manifest={'label':'ORACLE_GAP_CONFIRMED_CURRENT_SIGNAL_FAMILY_RETIRED','evidence_level':'EXPLORATORY_FIXED_TARGET_DECISION_AUDIT','parent':'ea4da8d4d981383bee00a1245ec450bfeddf2c4a','legacy_limit':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123','frozen_inputs_reproduced':True,'strict_oracle_headroom':True,'current_signal_family_retired':True,'independent_confirmation_authorized':False,'cost_status':'SEARCH_ONLY_GAIN_TRUTH_AND_CONTROL_COST_NOT_ESTIMABLE','parquet_status':'PARQUET_ENGINE_NOT_AVAILABLE','validation_dev_accessed':False,'formal_test_accessed':False,'new_graphs':False}
open(M+'/icba_decision_regret_decision.json','w').write(json.dumps(manifest,indent=2)+'\n')
print(G.to_string(index=False));print(json.dumps(manifest,indent=2))
