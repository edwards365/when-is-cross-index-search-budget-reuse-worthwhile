#!/usr/bin/env python3
import os,json,hashlib
import numpy as np,pandas as pd
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));R=ROOT+'/results/asrc_semantic_repair';D=ROOT+'/docs/asrc_semantic_repair';F=ROOT+'/figures/asrc_semantic_repair';M=ROOT+'/manifests';os.makedirs(F,exist_ok=True)
a=pd.read_csv(R+'/asrc_repaired_summary.csv');rm=pd.read_csv(R+'/risk_matched_baselines.csv');cal=pd.read_csv(R+'/calibration_size_effect.csv');reuse=pd.read_csv(R+'/query_reuse_effect.csv');tb=pd.read_csv(R+'/asrc_target_build_results.csv')
# Event audit table.
pd.DataFrame([
 {'channel':'evaluation','original_event':'underbudget OR censoring','repaired_event':'shared Z_abs','status':'VERIFIED'},
 {'channel':'ASRC sentinel','original_event':'underbudget only','repaired_event':'shared Z_abs','status':'MISMATCH_REPAIRED'},
 {'channel':'B1 terminal','original_event':'underbudget only','repaired_event':'shared Z_abs','status':'MISMATCH_REPAIRED'},
 {'channel':'mechanism diagnostic','original_event':'not explicit','repaired_event':'shared Z_rec','status':'ADDED'}]).to_csv(R+'/event_consistency_audit.csv',index=False)
# Risk-matched adaptive comparison uses closest preregistered stage to mean labels (128).
cmp=[]
for ds,g in a.groupby('dataset'):
 am=g.mean_ndc.mean()
 for method in ['RM-B1','RM-B2']:
  base=rm[(rm.dataset==ds)&(rm.method==method)&(rm.stage==128)].mean_ndc.mean();cmp.append({'dataset':ds,'baseline':method,'stage':128,'asrc_mean_ndc':am,'baseline_mean_ndc':base,'asrc_improvement':1-am/base,'comparison':'CLOSEST_PREREGISTERED_STAGE','evidence_label':'EXPLORATORY_REPAIR'})
cmpdf=pd.DataFrame(cmp);cmpdf.to_csv(R+'/risk_matched_comparison.csv',index=False)
# Symbolic break-even thresholds, with unknown truth cost retained symbolically.
be=[]
for _,x in cmpdf.iterrows():
 delta=x.baseline_mean_ndc-x.asrc_mean_ndc
 for n in [10**3,10**4,10**5,10**6,10**7]:be.append({'dataset':x.dataset,'baseline':x.baseline,'N':n,'online_ndc_margin':delta,'max_total_fixed_overhead_ndc':n*delta if delta>0 else 0,'truth_cost':'NOT_ESTIMABLE','status':'SYMBOLIC_BREAK_EVEN_ONLY' if delta>0 else 'NO_FINITE_BREAK_EVEN'})
pd.DataFrame(be).to_csv(R+'/symbolic_break_even.csv',index=False)
# LOTO sensitivity; top-1 query deletion cannot be reconstructed without forbidden new query-level repeat cache.
loto=[]
for ds,g in tb.groupby('dataset'):
 for omit in g.target_build:
  h=g[g.target_build!=omit];loto.append({'dataset':ds,'omitted_target_build':omit,'abs_risk':h.abs_risk.mean(),'saving_vs_b1max':h.saving_vs_b1max.mean(),'status':'LOTO'})
pd.DataFrame(loto).to_csv(R+'/leave_one_target_build_out.csv',index=False)
gates=[
 {'gate':'0','status':'PASS','evidence':'frozen inputs readable; 6a8cbcf hashes passed; no sealed access'},
 {'gate':'E','status':'PASS_REPAIRED','evidence':'one shared Z_abs/Z_rec; synthetic tests pass; old CSV unchanged'},
 {'gate':'C','status':'NOT_IDENTIFIABLE','evidence':'reuse explains <50%; calibration-size pattern nonmonotone; legacy 750 is descriptive'},
 {'gate':'S','status':'PASS_FIXED_TARGET','evidence':'target-build bootstrap upper absolute risk <.05 on both datasets; top-1 query sensitivity NOT_ESTIMABLE'},
 {'gate':'M','status':'FAIL','evidence':'closest-stage RM-B1/RM-B2 increments fail 10%/5% jointly across datasets'},
 {'gate':'B','status':'SYMBOLIC_BREAK_EVEN_ONLY','evidence':'truth generation timing absent'},
 {'gate':'O','status':'FIXED_TARGET_ONLY_NOT_OPEN_WORLD_CERTIFIED','evidence':'no new outer build'}]
pd.DataFrame(gates).to_csv(R+'/unified_gate_table.csv',index=False)
verdict='B2_EFFECT_JOINTLY_CONFOUNDED_ASRC_REMAINS_EXPLORATORY'
docs={
'causal_attribution_report.md':'# Causal attribution report\n\nMatched n={80,128,250} paired/disjoint comparisons keep evaluation, build pair, grid and seed fixed. At n=250, paired-minus-disjoint explains only 3.19 percentage points on SIFT and 4.11 on Arxiv, below the 50% “mainly” threshold. Calibration-size trends are nonmonotone. The legacy ~750 paired result changes both size and reuse and is descriptive only. Attribution: **B2_EFFECT_NOT_EXPLAINED / ATTRIBUTION_NOT_IDENTIFIABLE**; in the allowed main taxonomy this is jointly confounded.\n',
'executive_brief.md':f'# Executive brief\n\nFinal label: **{verdict}**. A real censoring mismatch was repaired, but it is too small to explain the original signal. Repaired ASRC meets fixed-target safety and label-count criteria yet fails incremental value against risk-matched baselines. No deployment or independent confirmation is authorized.\n',
'final_report.md':f'# Final report\n\nFinal decision: **{verdict}**. The original preregistered decision remains historical. Unified-event ASRC has target-build mean absolute risk about 1.1%, labels 117.50 (Arxiv) and 130.55 (SIFT), and savings versus B1-max 38.56% and 33.45%. Against closest-stage RM-B1/RM-B2, however, Arxiv is negative and SIFT is below the 10%/5% joint gate. Endpoint infeasibility is zero on Arxiv and 0.0444% on SIFT, so the semantic mismatch does not explain the main discrepancy. Truth cost is not measured; break-even is symbolic. Scope is fixed-target only.\n',
'independent_confirmation_preregistration.md':'# Independent confirmation preregistration\n\nNot authorized under the current Gate M result. If reconsidered, a genuinely unused training-side query set is required (`NEW_INDEPENDENT_QUERY_SET_REQUIRED`), hashed before experiments, with a shared risk event, measured truth/certificate/control time, query confirmation before outer-build confirmation, and no validation-dev/formal-test access.\n'}
for n,s in docs.items():open(D+'/'+n,'w').write(s)
# Eight compact figures, PNG and PDF.
plots=[]
for mode in ['paired','disjoint']:
 x=cal[cal['mode']==mode];plots.append((f'calibration_size_{mode}',x,'n_cal','point'))
plots += [('query_reuse',reuse,'n_cal','paired_minus_disjoint'),('risk_ndc_frontier',rm,'mean_ndc','abs_risk'),('labels_ndc',a,'target_labels_mean','mean_ndc'),('endpoint_decomposition',a.groupby('dataset',as_index=False).mean(numeric_only=True),'dataset','endpoint_infeasible_rate'),('target_build_forest',tb,'abs_risk','saving_vs_b1max'),('symbolic_break_even',pd.DataFrame(be),'N','max_total_fixed_overhead_ndc')]
for name,x,xc,yc in plots:
 fig,ax=plt.subplots(figsize=(5,3))
 for ds,g in x.groupby('dataset') if 'dataset' in x else [('all',x)]:ax.plot(g[xc].astype(str) if xc=='dataset' else g[xc],g[yc],marker='o',linestyle='none' if name in ['risk_ndc_frontier','labels_ndc','target_build_forest'] else '-',label=str(ds))
 ax.set_title(name);ax.set_xlabel(xc);ax.set_ylabel(yc);ax.legend(fontsize=7);fig.tight_layout()
 for ext in ['png','pdf']:fig.savefig(f'{F}/{name}.{ext}',dpi=150)
 plt.close(fig)
manifest={'verdict':verdict,'parent':'6a8cbcf7cf9f8f2f6734b05132e13d0f21e476bb','branch':'exp/asrc_semantic_repair','input_reproduction':'CONDITIONAL_41_OF_41_NEW_STAGE_HASHES; LEGACY_111_OF_123_LIMIT','event_mismatch':True,'repair_effect':'small on SIFT; none on Arxiv endpoint censoring','attribution':'B2_EFFECT_JOINTLY_CONFOUNDED','independent_confirmation_authorized':False,'new_server_required':False,'validation_dev_accessed':False,'formal_test_accessed':False,'scope':'FIXED_TARGET_ONLY_NOT_OPEN_WORLD_CERTIFIED','truth_cost':'NOT_ESTIMABLE','gates':gates}
json.dump(manifest,open(M+'/asrc_semantic_repair_decision.json','w'),indent=2)
print(json.dumps(manifest,indent=2))
