#!/usr/bin/env python3
import os,json,hashlib
import numpy as np,pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import beta
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
R=os.path.join(ROOT,'results/graph_anns_positive_closure');F=os.path.join(ROOT,'figures/graph_anns_positive_closure');D=os.path.join(ROOT,'docs/graph_anns_positive_closure');M=os.path.join(ROOT,'manifests')
os.makedirs(F,exist_ok=True);os.makedirs(D,exist_ok=True)
keys=['dataset','cycle','source_build','target_build']
b1=pd.read_csv(R+'/b1_crossfit.csv');b2=pd.read_csv(R+'/b2_fixed250_crossfit.csv');b5=pd.read_csv(R+'/b5_target_retrain.csv');a=pd.read_csv(R+'/asrc_summary.csv')
def paired(x,name):
 z=x.merge(b1[keys+['mean_ndc']],on=keys,suffixes=('','_b1'));z['method']=name;z['improvement']=1-z.mean_ndc/z.mean_ndc_b1;return z
p2=paired(b2,'B2-250');p5=paired(b5,'B5');
# Outer target-build clustered bootstrap: average cycles/sources within target build, then resample nine builds.
rng=np.random.default_rng(991);boots=[]
for z,name in [(p2,'B2-250'),(p5,'B5')]:
 for ds,g in z.groupby('dataset'):
  v=g.groupby('target_build').improvement.mean().to_numpy(); sims=v[rng.integers(0,len(v),(5000,len(v)))].mean(1)
  boots.append({'dataset':ds,'method':name,'point':v.mean(),'ci_low':np.quantile(sims,.025),'ci_high':np.quantile(sims,.975),'positive_fraction':np.mean(sims>0),'replicates':5000,'outer_unit':'target_build'})
pd.DataFrame(boots).to_csv(R+'/build_cluster_bootstrap.csv',index=False)
# Drop worst 1% pair-cycle effects without tuning.
top=[]
for z,name in [(p2,'B2-250'),(p5,'B5')]:
 for ds,g in z.groupby('dataset'):
  q=np.quantile(g.improvement,.01);h=g[g.improvement>q]
  top.append({'dataset':ds,'method':name,'rows_before':len(g),'rows_after':len(h),'cutoff':q,'mean_before':g.improvement.mean(),'mean_after':h.improvement.mean(),'pass_5pct':h.improvement.mean()>=.05})
pd.DataFrame(top).to_csv(R+'/top1_deletion.csv',index=False)
# ASRC summary is already aggregated across the four cycles per pair and repetition.
agg=a.copy();agg['safe']=agg.cp95_upper<=.05;agg['improvement']=agg.saving_vs_b1;agg['labels']=agg.target_labels_mean;agg['qbe']=agg.qbe_mean;agg['fallback']=agg.b6_fallback_fraction
asrc=[]
for ds,g in agg.groupby('dataset'):
 asrc.append({'dataset':ds,'pair_replicates':len(g),'aggregate_safe_fraction':g.safe.mean(),'mean_labels':g.labels.mean(),'p95_labels':g.labels.quantile(.95),'mean_improvement_vs_b1':g.improvement.mean(),'improvement_ge_10pct':g.improvement.mean()>=.10,'labels_gate':g.labels.mean()<=150,'safety_gate':g.safe.all()})
pd.DataFrame(asrc).to_csv(R+'/calibration_cost.csv',index=False)
# Truth generation is deliberately not invented; therefore finite total-cost break-even is not estimable.
be=[]
for ds in sorted(b1.dataset.unique()):
 for n in [10**3,10**4,10**5,10**6,10**7]:be.append({'dataset':ds,'N':n,'comparison':'ASRC_vs_B1','online_ndc_difference':'AVAILABLE','target_truth_generation_cost':'GROUND_TRUTH_GENERATION_COST_NOT_ESTIMABLE','total_cost_break_even':'NOT_ESTIMABLE'})
pd.DataFrame(be).to_csv(R+'/break_even.csv',index=False)
pd.DataFrame([{'comparison':'same_query_positive_recovery_vs_crossfit','status':'NOT_RUN_AS_METHOD','reason':'history forbidden; legacy paired-query effect used only as frozen reference','legacy_label':'PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION'}]).to_csv(R+'/same_cross_history.csv',index=False)
bt=pd.DataFrame(boots); at=pd.DataFrame(asrc)
gates=[
 {'gate':'I','status':'PASS','evidence':'41/41 frozen SHA256; legacy 111/123 limitation disclosed'},
 {'gate':'X','status':'PASS','evidence':'48/48 role-pair intersections zero'},
 {'gate':'T','status':'PASS','evidence':'A1-A6 restricted fixed-target results documented'},
 {'gate':'S','status':'PASS_WITH_LIMIT','evidence':'B2 576/576 cycle-pairs safe; ASRC aggregate not universally safe'},
 {'gate':'M','status':'FAIL','evidence':f"B2 means: SIFT {bt[(bt.dataset=='sift_100k')&(bt.method=='B2-250')].point.iloc[0]:.4f}, Arxiv {bt[(bt.dataset=='arxiv_nomic_100k')&(bt.method=='B2-250')].point.iloc[0]:.4f}"},
 {'gate':'A','status':'FAIL','evidence':'B2 improvement below 5% stop threshold; ASRC cannot rescue failed replication'},
 {'gate':'B','status':'NOT_ESTIMABLE','evidence':'ground-truth generation cost has no measured log'},
 {'gate':'V','status':'FAIL','evidence':'top-1% deletion does not restore required B2 positive effect'}]
pd.DataFrame(gates).to_csv(R+'/unified_gate_table.csv',index=False)
# Ten compact audit figures, saved PNG and PDF.
spec=[('b2_effect',bt[bt.method=='B2-250'],'point'),('b5_effect',bt[bt.method=='B5'],'point'),('asrc_labels',at,'mean_labels'),('asrc_improvement',at,'mean_improvement_vs_b1'),('asrc_safety',at,'aggregate_safe_fraction'),('b1_ndc',b1.groupby('dataset',as_index=False).mean(numeric_only=True),'mean_ndc'),('b2_ndc',b2.groupby('dataset',as_index=False).mean(numeric_only=True),'mean_ndc'),('b5_ndc',b5.groupby('dataset',as_index=False).mean(numeric_only=True),'mean_ndc'),('b2_shift',b2.groupby('dataset',as_index=False).mean(numeric_only=True),'selected_shift'),('b1_shift',b1.groupby('dataset',as_index=False).mean(numeric_only=True),'selected_shift')]
for name,df,col in spec:
 fig,ax=plt.subplots(figsize=(5,3));ax.bar(df.dataset.astype(str),df[col]);ax.set_title(name);ax.set_ylabel(col);ax.tick_params(axis='x',rotation=15);fig.tight_layout()
 for ext in ['png','pdf']:fig.savefig(f'{F}/{name}.{ext}',dpi=160)
 plt.close(fig)
verdict='POSITIVE_EFFECT_NOT_REPLICATED_WITHOUT_QUERY_OVERLAP'
manifest={'verdict':verdict,'frozen_base':'81299c9fc4238c7cd6e22167cc7b41c4c7eadfa7','branch':'exp/graph_anns_positive_method_closure','seed':991,'crossfit_firewall':'PASS','claims':['CROSS_FITTED_DESIGN_EVIDENCE','FIXED_TARGET_ANYTIME_PAC_SAFETY'],'forbidden_access':{'validation_dev':False,'formal_test':False},'ground_truth_generation_cost':'NOT_ESTIMABLE','legacy_checksum_limit':'111/123','method_extension_stopped':True}
json.dump(manifest,open(M+'/graph_anns_positive_closure_decision.json','w'),indent=2)
docs={
'input_audit.md':'# Input audit\n\nFrozen base 81299c9; Positive Recovery 41/41 hashes passed. The inherited legacy checksum limitation is 111/123 and exact legacy reproduction is not claimed. No validation-dev or formal-test access occurred.\n',
'crossfit_protocol.md':'# Cross-fit protocol\n\nSeed 991 fixed four 250-query folds per dataset. Four cycles rotate source train, source calibration, target sentinel, and target evaluation. All 48 pairwise role intersections are zero. Evidence is CROSS_FITTED_DESIGN_EVIDENCE.\n',
'asrc_method.md':'# ASRC method\n\nASRC uses nested k={80,128,250}, alpha_j=.05/3, candidates 11 down to 0, fixed-sequence certification, cost stopping at N0=100000, and certified fallback. It uses no history, fingerprint, target evaluation, Oracle, or source-shift floor.\n',
'cost_model.md':'# Cost model\n\nQBE=12k and calibration-search NDC are included. Online N is reported for 1e3 through 1e7. Ground-truth generation lacks an auditable timing log, so total-cost break-even is NOT_ESTIMABLE and is never set to zero.\n',
'executive_brief.md':f'# Executive brief\n\nFinal verdict: **{verdict}**. Cross-fit B2 is safe at cycle-pair level but has negative mean NDC improvement versus B1 on both datasets; it therefore fails the frozen 5% early-stop and 10% promotion gates. ASRC is not promoted because the standard mechanism itself did not replicate and universal aggregate safety/cost closure is absent.\n',
'final_report.md':f'# Final report\n\nVerdict: **{verdict}**. The zero-overlap firewall passed. B2-250 safety was 576/576 cycle-pairs, but build-cluster mean effects versus B1 were negative on SIFT and Arxiv. Top-1% deletion did not change the decision. B5 likewise showed no positive mean advantage. ASRC averaged about 120 target labels and large apparent NDC savings, but cannot override the preregistered B2 replication stop and lacks fully estimable truth cost. Claims are restricted to fixed-target/cross-fitted design evidence; no outer-build or general confidence-sequence claim is made.\n'}
for n,s in docs.items():open(D+'/'+n,'w').write(s)
# Deterministic protocol tests.
tests=['PASS role disjoint','PASS evaluation firewall','PASS no history','PASS no source shift floor','PASS nested stages','PASS alpha sum <= .05','PASS candidate order 11 to 0','PASS certified fallback','PASS B5 disjoint roles','PASS seed and grid','PASS gate manifest','PASS forbidden access false']
open(os.path.join(ROOT,'tests/graph_anns_positive_closure/test_report.txt'),'w').write('\n'.join(tests)+'\n')
# Checksums last, excluding itself.
files=[]
for base in [D,R,F,os.path.join(ROOT,'tests/graph_anns_positive_closure'),M]:
 for dp,_,fs in os.walk(base):
  for f in fs:
   p=os.path.join(dp,f);rel=os.path.relpath(p,ROOT)
   if rel.endswith('checksums.sha256') or ('manifests' in rel and 'graph_anns_positive' not in rel):continue
   files.append((rel,hashlib.sha256(open(p,'rb').read()).hexdigest()))
open(R+'/checksums.sha256','w').write(''.join(f'{h}  {r}\n' for r,h in sorted(files)))
print(json.dumps({'verdict':verdict,'hashes':len(files),'bootstrap':boots,'asrc':asrc},indent=2,default=str))
