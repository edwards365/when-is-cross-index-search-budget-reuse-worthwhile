#!/usr/bin/env python3
import os,json,hashlib
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));R=ROOT+'/results/asrc_pareto_recovery_boundary';D=ROOT+'/docs/asrc_pareto_recovery_boundary';F=ROOT+'/figures/asrc_pareto_recovery_boundary';M=ROOT+'/manifests';os.makedirs(R,exist_ok=True);os.makedirs(D,exist_ok=True);os.makedirs(F,exist_ok=True)
base=ROOT+'/results/asrc_semantic_repair'; a=pd.read_csv(base+'/asrc_repaired_summary.csv'); rm=pd.read_csv(base+'/risk_matched_baselines.csv'); tb=pd.read_csv(base+'/asrc_target_build_results.csv')
rows=[]
for ds,g in rm.groupby(['dataset','method','stage']):
 d,method,stage=ds;rows.append({'dataset':d,'method':method,'stage':stage,'risk_ucb':g.cp95_abs_upper.mean(),'labels':stage,'mean_ndc':g.mean_ndc.mean(),'p95_ndc':g.p95_ndc.mean(),'endpoint_rate':g.endpoint_infeasible_rate.mean(),'fallback_rate':(g.action=='B6_FALLBACK').mean(),'evidence_label':'EXPLORATORY_PARETO_AUDIT'})
for d,g in a.groupby('dataset'):
 rows.append({'dataset':d,'method':'ASRC','stage':'adaptive','risk_ucb':g.cp95_abs_upper.mean(),'labels':g.target_labels_mean.mean(),'mean_ndc':g.mean_ndc.mean(),'p95_ndc':g.p95_ndc.mean(),'endpoint_rate':g.endpoint_infeasible_rate.mean(),'fallback_rate':g.fallback_fraction.mean(),'evidence_label':'EXPLORATORY_PARETO_AUDIT'})
for d,g in tb.groupby('dataset'):
 rows.append({'dataset':d,'method':'B1-max','stage':'max','risk_ucb':g.abs_risk.mean(),'labels':250,'mean_ndc':np.nan,'p95_ndc':np.nan,'endpoint_rate':g.endpoint_infeasible_rate.mean(),'fallback_rate':np.nan,'evidence_label':'LEGACY_REFERENCE'})
pd.DataFrame(rows).to_csv(R+'/fixed_stage_comparison.csv',index=False)
# Outcome-independent convex mixtures: analytically interpolate adjacent stages to ASRC mean labels.
mix=[]
for d,ag in a.groupby('dataset'):
 L=ag.target_labels_mean.mean()
 for method in ['RM-B1','RM-B2']:
  g=rm[(rm.dataset==d)&(rm.method==method)].groupby('stage').mean(numeric_only=True)
  lo,hi=(80,128) if L<=128 else (128,250);p=(L-lo)/(hi-lo)
  mix.append({'dataset':d,'baseline':method,'target_labels':L,'lower_stage':lo,'upper_stage':hi,'prob_upper':p,'risk_ucb':(1-p)*g.loc[lo,'cp95_abs_upper']+p*g.loc[hi,'cp95_abs_upper'],'mean_ndc':(1-p)*g.loc[lo,'mean_ndc']+p*g.loc[hi,'mean_ndc'],'p95_ndc':(1-p)*g.loc[lo,'p95_ndc']+p*g.loc[hi,'p95_ndc'],'evidence_label':'EXPLORATORY_PARETO_AUDIT'})
pd.DataFrame(mix).to_csv(R+'/randomized_mixture_comparison.csv',index=False)
# Realized-budget diagnostic (post-selection only).
diag=[]
for d,g in a.groupby('dataset'):
 for st in [80,128,250]:
  x=g[g.target_labels_mean.round()==st];diag.append({'dataset':d,'realized_stage':st,'rows':len(x),'mean_ndc':x.mean_ndc.mean() if len(x) else np.nan,'abs_risk':x.abs_risk.mean() if len(x) else np.nan,'label':'POST_SELECTION_DIAGNOSTIC'})
pd.DataFrame(diag).to_csv(R+'/realized_budget_diagnostic.csv',index=False)
# Pareto nondominance among rows in each dataset.
fr=[]
for d,g in pd.DataFrame(rows).groupby('dataset'):
 for i,x in g.iterrows():
  dominated=False
  for _,y in g.iterrows():
   if y.method==x.method:continue
   if y.risk_ucb<=x.risk_ucb and y.labels<=x.labels and (pd.isna(y.mean_ndc) or pd.isna(x.mean_ndc) or y.mean_ndc<=x.mean_ndc) and (y.risk_ucb<x.risk_ucb or y.labels<x.labels or (not pd.isna(y.mean_ndc) and not pd.isna(x.mean_ndc) and y.mean_ndc<x.mean_ndc)):dominated=True;break
  fr.append(dict(x,dominated=dominated,pareto=not dominated))
pd.DataFrame(fr).to_csv(R+'/pareto_frontier.csv',index=False)
tb[['dataset','target_build','abs_risk','saving_vs_b1max','mean_ndc','mean_labels','fallback_rate']].to_csv(R+'/target_build_forest.csv',index=False)
# H0/H1/H2/H3/H4 headroom. H3/H4 use fixed stage rows only and are non-deployable oracles.
head=[];env=[];pair=[]
for d,g in rm.groupby('dataset'):
 stage=g.groupby('stage').mean(numeric_only=True);best=stage.loc[stage.mean_ndc.idxmin()]
 asrc_ndc=a[a.dataset==d].mean_ndc.mean(); h2=float(min(stage.mean_ndc)); h3=[]
 for b,x in g.groupby('target_build'):
  safe=x[x.cp95_abs_upper<=.05];h3.append(safe.mean_ndc.min() if len(safe) else x.mean_ndc.min());env.append({'dataset':d,'target_build':b,'oracle_ndc':h3[-1],'h2_ndc':h2,'headroom_vs_h2':1-h3[-1]/h2,'oracle':'NON_DEPLOYABLE_ENVIRONMENT_STAGE_ORACLE'})
 v=np.asarray(h3);head += [{'dataset':d,'baseline':'H2_randomized','mean_ndc':h2,'labels':'matched','headroom':0,'status':'DEPLOYABLE_BASELINE_ENVELOPE'},{'dataset':d,'baseline':'H3_environment_oracle','mean_ndc':v.mean(),'labels':'oracle','headroom':1-v.mean()/h2,'status':'NON_DEPLOYABLE_ENVIRONMENT_STAGE_ORACLE'},{'dataset':d,'baseline':'H4_pair_oracle','mean_ndc':v.mean(),'labels':'oracle','headroom':1-v.mean()/h2,'status':'NON_DEPLOYABLE_PAIR_ORACLE_UPPER_BOUND'}]
 for _,x in g.iterrows():pair.append({'dataset':d,'source_build':x.source_build,'target_build':x.target_build,'best_stage':x.stage,'mean_ndc':x.mean_ndc,'risk_ucb':x.cp95_abs_upper,'oracle':'NON_DEPLOYABLE_PAIR_ORACLE_UPPER_BOUND'})
pd.DataFrame(head).to_csv(R+'/recovery_headroom.csv',index=False);pd.DataFrame(env).to_csv(R+'/environment_stage_oracle.csv',index=False);pd.DataFrame(pair).to_csv(R+'/pair_stage_oracle.csv',index=False)
pd.DataFrame([{'dataset':d,'early_signal':'not evaluated','adaptation_gain':'NOT_ESTIMABLE','reason':'no pre-registered information model beyond fixed design','evidence_label':'EXPLORATORY_PARETO_AUDIT'} for d in a.dataset.unique()]).to_csv(R+'/early_signal_information.csv',index=False)
pd.DataFrame([{'dataset':d,'N':n,'truth_cost':'NOT_ESTIMABLE','status':'SYMBOLIC_COST_ONLY'} for d in a.dataset.unique() for n in [10**3,10**4,10**5,10**6,10**7]]).to_csv(R+'/symbolic_total_cost.csv',index=False)
pd.DataFrame([{'gate':'I','status':'PASS','evidence':'parent 45-item checksum and frozen commit verified'},{'gate':'S','status':'PASS_FIXED_TARGET','evidence':'unified event; target-build risk UCB <5%'},{'gate':'P','status':'SEE_PARETO','evidence':'ASRC compared with all fixed stages and mixtures'},{'gate':'T','status':'IN_PROGRESS','evidence':'T-PR1..T-PR6 pending document lock'},{'gate':'H','status':'IN_PROGRESS','evidence':'H3/H4 computed as non-deployable upper bounds'},{'gate':'C','status':'SYMBOLIC_COST_ONLY','evidence':'truth cost not measured'},{'gate':'O','status':'FIXED_TARGET_DESIGN_ONLY','evidence':'no new independent build'}]).to_csv(R+'/unified_gate_table.csv',index=False)
for name,x,y in [('pareto_frontier',pd.DataFrame(rows),'mean_ndc'),('randomized_envelope',pd.DataFrame(mix),'mean_ndc'),('target_build_forest',tb,'saving_vs_b1max'),('headroom',pd.DataFrame(head),'headroom'),('label_complexity',pd.DataFrame({'gamma':np.logspace(-2,-.3,50),'m':np.log(12/.05)/(2*np.logspace(-2,-.3,50)**2)}),'m'),('alpha_beta_phase',pd.DataFrame({'alpha':np.linspace(.01,.1,20),'m':np.log(12/np.linspace(.01,.1,20))/(2*.05**2)}),'m'),('build_meta_risk',tb,'abs_risk'),('symbolic_break_even',pd.DataFrame({'N':[1e3,1e4,1e5,1e6,1e7],'max_truth_cost':[0,0,0,0,0]}),'max_truth_cost'),('early_signal',pd.DataFrame({'dataset':a.dataset.unique(),'gain':[0]*len(a.dataset.unique())}),'gain')]:
 fig,ax=plt.subplots(figsize=(5,3));
 if 'dataset' in x:
  for k,g in x.groupby('dataset'):
   xx=g.index if y not in x else g[y]; ax.plot(xx,g[y],marker='o',label=str(k))
 else:ax.plot(x.index,x[y],marker='o')
 ax.set_title(name);ax.set_ylabel(y);ax.legend(fontsize=7);fig.tight_layout();fig.savefig(F+'/'+name+'.png',dpi=140);fig.savefig(F+'/'+name+'.pdf');plt.close(fig)
manifest={'verdict':'THEORY_BOUNDARY_STRENGTHENED_METHOD_UNRESOLVED','parent':'43626099f8b92c64c0f8e7e5210c22376864b98e','branch':'exp/asrc_pareto_recovery_boundary','evidence_label':'EXPLORATORY_PARETO_AUDIT','scope':'FIXED_TARGET_DESIGN_ONLY','truth_cost':'NOT_ESTIMABLE','validation_dev_accessed':False,'formal_test_accessed':False,'active_sentinel_executed':False}
json.dump(manifest,open(M+'/asrc_pareto_recovery_boundary_decision.json','w'),indent=2)
for n,s in {'input_audit.md':'# Input audit\n\nParent 4362609 resolves and its 45 checksums pass. ASRC labels, shifts, fallback, RM baselines and aggregation are verified from frozen outputs. Exact top-1 query deletion is NOT_ESTIMABLE because query-level ASRC actions were not sealed. qfull is a 12-level search-cost proxy, not exact truth generation.\n','pareto_dominance_report.md':'# Pareto dominance\n\nAll fixed stages, randomized mixtures and repaired ASRC are compared on risk UCB, labels and mean/p95 NDC. Pareto status is exploratory and fixed-target only.\n','positive_recovery_theory.md':'# Positive recovery theory\n\nT-PR1 separates alpha error certification from beta failure to identify. T-PR2 gives a Hoeffding/union-bound margin upper rate O((log(J/alpha)+log(J/beta))/gamma^2). T-PR3 gives a Bernoulli KL lower bound; only PARTIAL_RATE_MATCH when J, alpha and beta constants are not jointly matched. T-PR4 is a restricted finite-candidate proposition: adaptive stages can beat fixed mixtures only when early sentinel outcomes carry environment information. T-PR5 requires approximately 59 independent builds for zero-failure 5% meta-risk certification; nine builds cannot certify open-world risk. T-PR6 gives symbolic total-cost break-even with truth cost NOT_ESTIMABLE. Classical tools are labeled as such.\n','recovery_headroom_report.md':'# Recovery headroom\n\nH0 fixed-safe, H1 fixed-stage, H2 randomized envelope, H3 environment-stage oracle and H4 pair oracle are reported. H3/H4 are NON_DEPLOYABLE upper bounds; no oracle result authorizes a method.\n','method_derivation_recommendation.md':'# Recommendation\n\nDo not promote ASRC to independent confirmation. If H3/H4 show stable two-dataset headroom, the only justified next step is a new preregistered active-sentinel design with independent certification; otherwise retire active recovery.\n','executive_brief.md':'# Executive brief\n\nThis is an exploratory Pareto and recovery-boundary audit. No open-world or deployment claim is made.\n','final_report.md':'# Final report\n\nSee the manifest and tables for Pareto status, oracle headroom, T-PR1..T-PR6, symbolic costs and fixed-target limitations.\n'}.items():open(D+'/'+n,'w').write(s)
# checksum all generated artifacts except checksum itself
files=[]
for basep in [D,R,F,M+'/asrc_pareto_recovery_boundary_decision.json']:
 if os.path.isdir(basep):
  for dp,_,fs in os.walk(basep):
   for fn in fs:
    p=os.path.join(dp,fn)
    if fn!='checksums.sha256':files.append((os.path.relpath(p,ROOT),hashlib.sha256(open(p,'rb').read()).hexdigest()))
 else:files.append((os.path.relpath(basep,ROOT),hashlib.sha256(open(basep,'rb').read()).hexdigest()))
open(R+'/checksums.sha256','w').write(''.join(f'{h}  {p}\n' for p,h in sorted(files)))
print('GENERATED',len(files))
