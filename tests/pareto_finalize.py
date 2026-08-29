#!/usr/bin/env python3
import os,json,hashlib
import pandas as pd,numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));R=ROOT+'/results/asrc_pareto_recovery_boundary';D=ROOT+'/docs/asrc_pareto_recovery_boundary';F=ROOT+'/figures/asrc_pareto_recovery_boundary';M=ROOT+'/manifests'
os.makedirs(D,exist_ok=True);os.makedirs(R,exist_ok=True)
h=pd.read_csv(R+'/recovery_headroom.csv');
active=[]; splits=[]
for ds in h.dataset.unique():
 for total in [80,128,250]:
  for sel,cert in [(0,total),(16,total-16),(32,total-32),(64,total-64),(32,total-32)]:
   if cert<=0:continue
   active.append({'dataset':ds,'lane':'UNIFORM_SELECTION_DESIGN','m_total':total,'selection_labels':sel,'certification_labels':cert,'selection_accuracy':'NOT_ESTIMABLE','certification_pass':'NOT_RUN_NO_NEW_TRUTH','total_labels':total,'mean_ndc':'NOT_ESTIMABLE','relative_gain':'NOT_ESTIMABLE','deployable_lane':'DESIGN_ONLY','oracle_lane':'NON_DEPLOYABLE_ACTIVE_SENTINEL_ORACLE','evidence_label':'EXPLORATORY_PARETO_AUDIT'})
   splits.append({'dataset':ds,'m_total':total,'selection_labels':sel,'certification_labels':cert,'selection_outcome_dependence':False,'certificate_set_independent':True,'risk_bound_zero_fail_cp95':1-0.05**(1/cert),'status':'DESIGN_ONLY_NOT_ESTIMABLE'})
pd.DataFrame(active).drop_duplicates().to_csv(R+'/active_sentinel_upper_bound.csv',index=False);pd.DataFrame(splits).drop_duplicates().to_csv(R+'/selection_certification_split.csv',index=False)
pd.DataFrame([{'gate':'P','status':'FAIL_INCREMENT','evidence':'ASRC lacks >=5% same-risk same-label improvement with positive cluster CI in both datasets'},{'gate':'H','status':'PASS_UPPER_BOUND_ONLY','evidence':'H3/H4 headroom 14.8% SIFT and 17.4% Arxiv; Oracle lanes non-deployable'},{'gate':'C','status':'SYMBOLIC_COST_ONLY','evidence':'truth cost not measured'},{'gate':'O','status':'FIXED_TARGET_DESIGN_ONLY','evidence':'no independent outer build'}]).to_csv(R+'/unified_gate_table.csv',mode='a',header=False,index=False)
docs={
'input_audit.md':'# Input audit\n\nParent 4362609 parses and its 45-item SHA256 passes. All Pareto inputs are frozen repair outputs. qfull/search NDC is a proxy, not exact truth-generation cost. ASRC internal 500 orderings share evaluation queries; they are not independent builds. Top-1 query deletion is NOT_ESTIMABLE from sealed outputs.\n',
'pareto_dominance_report.md':'# Pareto dominance report\n\nRisk UCB, mean/p95 NDC and labels are compared for B0, B1/B2 max, RM-B1/RM-B2 stages, randomized mixtures, ASRC and B5 proxy. ASRC is not granted an independent increment: its same-risk matched RM improvements fail the 10%/5% requirements and confidence lower-bound criteria. Any apparent B1-max advantage is not sufficient evidence.\n',
'positive_recovery_theory.md':'# Positive recovery theory\n\nT-PR1 separates alpha error certification from beta failure to identify. T-PR2 gives m=O((log(J/alpha)+log(J/beta))/gamma^2) by Hoeffding plus union bound. T-PR3 gives a Bernoulli KL lower bound; only PARTIAL_RATE_MATCH is justified unless all J, alpha and beta factors are matched. T-PR4 is a restricted finite-candidate proposition: adaptive allocation can beat fixed mixtures only when early sentinel outcomes contain environment information. T-PR5 models E~P_E and q~P(q|E); zero failures with alpha=.05 requires about59 independent builds, so nine builds cannot certify open-world meta-risk. T-PR6 gives symbolic total cost C_total=N*C_online+C_truth+C_selection+C_certificate+C_retraining; truth cost is NOT_ESTIMABLE. Classical CP, fixed-sequence, union bounds, KL and order-statistic facts are labeled as classical applications.\n',
'recovery_headroom_report.md':'# Recovery headroom report\n\nH3 environment-stage and H4 pair oracles expose 14.8% SIFT and 17.4% Arxiv mean-NDC headroom over the H2 fixed-mixture envelope. These are NON_DEPLOYABLE oracle upper bounds, not evidence of a deployable selector. Headroom is sufficient to justify design-level active-sentinel research, not independent confirmation.\n',
'method_derivation_recommendation.md':'# Method derivation recommendation\n\nRetain ASRC as exploratory and do not confirm it. The two-dataset oracle headroom supports a preregistered active-sentinel design with an independent random certification set, but selection accuracy and total truth cost are not estimable here. Any future method must first use genuinely unused queries and then new builds.\n',
'executive_brief.md':'# Executive brief\n\nPareto audit: ASRC has no proven independent Pareto advantage; environment-aware oracle headroom remains, so the method question is unresolved. Scope is fixed-target design only.\n',
'final_report.md':'# Final report\n\nFinal verdict: THEORY_BOUNDARY_STRENGTHENED_METHOD_UNRESOLVED. ASRC is retained as exploratory; H3/H4 headroom is quantified only as a non-deployable upper bound. Active-sentinel outputs are design-only, truth cost is symbolic, and no independent query or outer-build confirmation is authorized.\n'}
for n,s in docs.items():open(D+'/'+n,'w').write(s)
manifest={'verdict':'THEORY_BOUNDARY_STRENGTHENED_METHOD_UNRESOLVED','parent':'43626099f8b92c64c0f8e7e5210c22376864b98e','branch':'exp/asrc_pareto_recovery_boundary','evidence_label':'EXPLORATORY_PARETO_AUDIT','asrc_status':'EXPLORATORY_NO_INDEPENDENT_PARETO_ADVANTAGE','h3_headroom':{'sift':0.14792640454302797,'arxiv':0.17385043186905325},'active_sentinel_executed':True,'active_sentinel_status':'DESIGN_ONLY_NOT_ESTIMABLE','independent_confirmation_authorized':False,'new_method_derivation_authorized':'DESIGN_ONLY','truth_cost':'NOT_ESTIMABLE','scope':'FIXED_TARGET_DESIGN_ONLY','validation_dev_accessed':False,'formal_test_accessed':False}
json.dump(manifest,open(M+'/asrc_pareto_recovery_boundary_decision.json','w'),indent=2)
files=[]
for basep in [D,R,F,M+'/asrc_pareto_recovery_boundary_decision.json']:
 if os.path.isdir(basep):
  for dp,_,fs in os.walk(basep):
   for fn in fs:
    if fn=='checksums.sha256':continue
    p=os.path.join(dp,fn);files.append((os.path.relpath(p,ROOT),hashlib.sha256(open(p,'rb').read()).hexdigest()))
 else:files.append((os.path.relpath(basep,ROOT),hashlib.sha256(open(basep,'rb').read()).hexdigest()))
open(R+'/checksums.sha256','w').write(''.join(f'{h}  {p}\n' for p,h in sorted(files)));print('HASHES',len(files))
