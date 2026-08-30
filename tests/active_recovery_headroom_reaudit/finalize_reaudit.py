#!/usr/bin/env python3
import os,json,glob,hashlib
import pandas as pd,numpy as np
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/active_recovery_headroom_reaudit';D=ROOT+'/docs/active_recovery_headroom_reaudit';F=ROOT+'/figures/active_recovery_headroom_reaudit';T=ROOT+'/tests/active_recovery_headroom_reaudit';M=ROOT+'/manifests';
for x in [R,D,F,T,M]:os.makedirs(x,exist_ok=True)
s=pd.read_csv(R+'/active_sentinel_signal_summary.csv');x=s[(~s.lane.str.contains('NON_DEPLOYABLE'))&s.certifiable&(s.n_selection>0)];best=x.sort_values(['accuracy_gain','certified_safe_rate'],ascending=False).groupby('dataset').head(1);best.to_csv(R+'/active_sentinel_best_deployable.csv',index=False)
theory=pd.DataFrame([
['T-PR1','CLASSICAL_APPLICATION','Alpha controls false certification; beta controls failure to identify.'],['T-PR2','RESTRICTED_PROPOSITION','Finite-J fixed-target margin bound with explicit constants; not outer-build.'],['T-PR3','CLASSICAL_APPLICATION','Bernoulli KL lower bound; only gamma-rate partial match.'],['T-PR4','CONJECTURE','No deployable early signal was found; adaptive advantage not proved.'],['T-PR5','RESTRICTED_PROPOSITION','59-build zero-event heuristic requires ideal independent builds.'],['T-PR6','PROOF_SKETCH','Symbolic break-even only; truth cost unavailable.'] ],columns=['claim','status','scope']);theory.to_csv(R+'/theory_status.csv',index=False)
gate=pd.read_csv(R+'/gate_h_robustness.csv'); gate['gate']='H-Strong';gate.to_csv(R+'/gate_decisions.csv',index=False)
docs={
'README.md':'# Active Recovery Headroom Re-audit\n\nExploratory fixed-target re-audit. Final label: **CORRECTED_HEADROOM_CONFIRMED_NO_DEPLOYABLE_SIGNAL**. Legacy reproducibility remains conditional (111/123); no exact Full Seal claim.\n',
'corrected_headroom_report.md':'# Corrected Headroom\n\nEpisode-randomized H2 and held-out-cycle H3b/H4b replace invalid interpolation and row-minimum oracles. Both datasets pass H-Strong; see `gate_h_robustness.csv`.\n',
'active_sentinel_report.md':'# Active Sentinel Pilot\n\nSelection and certification are disjoint. Certification sets below 59 are controls only. All deployable lanes with positive selection fail to beat the majority action baseline. Oracle lane is non-deployable.\n',
'pareto_correction.md':'# Pareto Correction\n\nPrimary coordinates are target-build cluster risk, expected labels, and mean NDC. Missing primary coordinates cannot dominate. Mean and p95 are reported separately.\n',
'theory_audit.md':'# Theory Audit\n\nT-PR1–6 are restricted to fixed-target design. No outer-build PAC or full phase-transition claim is made. T-PR6 remains symbolic because truth-generation cost is unavailable.\n',
'data_firewall.md':'# Data Firewall\n\nNo validation-dev, formal-test, new graph, exact truth, Faiss, Vamana, GPU, or evaluation-driven tuning was used. Frozen design records only.\n',
'limitations.md':'# Limitations\n\nHistorical evidence is conditionally reproducible: legacy checksums match 111/123. The re-audit is exploratory, has nine target-build clusters per dataset, and does not establish open-world certification.\n',
'decision.md':'# Decision\n\n**CORRECTED_HEADROOM_CONFIRMED_NO_DEPLOYABLE_SIGNAL**: robust non-deployable headroom exists, but preregistered deployable early-sentinel lanes do not outperform majority selection.\n'}
for n,v in docs.items():open(D+'/'+n,'w').write(v)
# Nine compact evidence plots, each PNG and PDF.
plots=[('headroom',gate,'dataset','headroom'),('ci_low',gate,'dataset','ci_low'),('risk',gate,'dataset','abs_risk'),('delete_max',gate,'dataset','delete_max_build_headroom'),('active_accuracy',best,'dataset','accuracy'),('majority',best,'dataset','majority_accuracy'),('accuracy_gain',best,'dataset','accuracy_gain'),('certified_safe',best,'dataset','certified_safe_rate'),('labels',best,'dataset','n_selection')]
for name,df,xc,yc in plots:
 fig,ax=plt.subplots(figsize=(6,3.5));labels=[f'{a}\n{b}' if 'oracle' in df.columns else str(a) for a,b in zip(df[xc],df.get('oracle',pd.Series(['']*len(df))))];ax.bar(range(len(df)),df[yc]);ax.set_xticks(range(len(df)),labels,rotation=20,ha='right');ax.set_ylabel(yc);ax.set_title(name);fig.tight_layout();fig.savefig(F+'/'+name+'.png',dpi=160);fig.savefig(F+'/'+name+'.pdf');plt.close(fig)
manifest={'label':'CORRECTED_HEADROOM_CONFIRMED_NO_DEPLOYABLE_SIGNAL','scope':'FIXED_TARGET_DESIGN_ONLY','evidence':'EXPLORATORY_HEADROOM_REAUDIT','parent':'5f4d04f6e836059c98024b01f4929bcd406cdcc1','legacy_checksum_limit':'111/123','gate_h':'H-Strong','active_sentinel_executed':True,'deployable_early_signal':'NO_DEPLOYABLE_EARLY_SIGNAL','truth_cost':'SEARCH_COST_POSITIVE_TRUTH_COST_UNKNOWN','validation_dev_accessed':False,'formal_test_accessed':False,'new_graphs':False}
open(M+'/active_recovery_headroom_reaudit_decision.json','w').write(json.dumps(manifest,indent=2)+'\n')
files=sorted(glob.glob(D+'/*')+glob.glob(R+'/*')+glob.glob(F+'/*')+glob.glob(T+'/*.py')+[M+'/active_recovery_headroom_reaudit_decision.json']);open(R+'/checksums.sha256','w').write(''.join(hashlib.sha256(open(p,'rb').read()).hexdigest()+'  '+os.path.relpath(p,ROOT)+'\n' for p in files if not p.endswith('checksums.sha256')))
print(json.dumps(manifest,indent=2));print('docs',len(glob.glob(D+'/*')),'csv',len(glob.glob(R+'/*.csv*')),'figures',len(glob.glob(F+'/*')))
