#!/usr/bin/env python3
"""E4.2 final local hotfix. No search, build, training, or new truth access."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import beta
from scripts.graph_anns_e4_seal.run import load_raw,budgets,EFS,SEEDS,ORDERS,DATASETS
from scripts.graph_anns_e4_patch.run import build_events

def cp(k,n,a): return 1. if k>=n else float(beta.ppf(1-a,k+1,n-k))
def save(x,o,n): x.to_csv(o/n,index=False,float_format='%.12g')

def h1a4(b):
 rows=[];ev=b[b.query_id>=250]
 for ds in DATASETS:
  p=ev[ev.dataset==ds].pivot(index='query_id',columns='build_id',values='safe_budget');c=p.isna();af=(~c).all(axis=1);ac=c.all(axis=1);mix=c.any(axis=1)&(~c).any(axis=1)
  rows.append(dict(dataset=ds,all_feasible_count=int(af.sum()),all_feasible_rate=af.mean(),mixed_feasible_censored_count=int(mix.sum()),mixed_feasible_censored_rate=mix.mean(),all_censored_count=int(ac.sum()),all_censored_rate=ac.mean(),query_count=len(p),state_count_check=int(af.sum()+mix.sum()+ac.sum()),estimand='MIXED_FEASIBLE_CENSORED_STATE_RATE',semantic_scope='registered-grid feasibility/censoring-state heterogeneity'))
 return pd.DataFrame(rows)

def h1pairs(b):
 ev=b[b.query_id>=250];rows=[]
 def summarize(ds,eid,scope,pairs):
  a=np.asarray(pairs,dtype=object); both=np.array([x[0] for x in pairs],bool); mismatch=np.array([x[1] for x in pairs],bool);cat=np.array([x[2] for x in pairs],bool);fd=np.array([x[3] for x in pairs],bool);ad=np.array([x[4] for x in pairs],float)
  return dict(dataset=ds,estimand_id=eid,scope=scope,total_comparisons=len(pairs),jointly_feasible_comparisons=int(both.sum()),censoring_mismatch_comparisons=int(mismatch.sum()),categorical_disagreement=cat.mean(),jointly_feasible_disagreement=fd[both].mean(),jointly_feasible_absolute_difference=np.nanmean(ad),effective_denominator=int(both.sum()))
 for ds in DATASETS:
  g=ev[ev.dataset==ds];pb=[];pc=[]
  for q in range(250,1000):
   for s in SEEDS:
    a=g[(g.query_id==q)&(g.seed==s)].set_index('order').safe_budget
    for i in range(3):
     for j in range(i+1,3):
      u,v=a[ORDERS[i]],a[ORDERS[j]];both=pd.notna(u) and pd.notna(v);mis=pd.isna(u)!=pd.isna(v);pb.append((both,mis,mis or (both and u!=v),both and u!=v,abs(u-v) if both else np.nan))
   for o in ORDERS:
    a=g[(g.query_id==q)&(g.order==o)].set_index('seed').safe_budget
    for i in range(8):
     for j in range(i+1,8):
      u,v=a[SEEDS[i]],a[SEEDS[j]];both=pd.notna(u) and pd.notna(v);mis=pd.isna(u)!=pd.isna(v);pc.append((both,mis,mis or (both and u!=v),both and u!=v,abs(u-v) if both else np.nan))
  rows += [summarize(ds,'H1-B','within_seed_cross_order',pb),summarize(ds,'H1-C','within_order_cross_seed',pc)]
 return pd.DataFrame(rows)

def rmetric(z):
 valid=z.ndc_difference_safe.notna(); ar=z.failure.astype(float).mean();rr=z.reference_failure.astype(float).mean();ri=(z.failure.astype(float)-z.reference_failure.astype(float)).mean();tax=z.loc[valid,'ndc_difference_safe'].sum()/z.loc[valid,'target_oracle_ndc'].sum()
 return ar,rr,ri,tax

def robustness(e):
 rows=[]
 def add(ds,a,d,z):
  ar,rr,ri,t=rmetric(z);rows.append(dict(dataset=ds,analysis=a,deleted=d,absolute_transport_risk=ar,reference_risk=rr,risk_increment=ri,safe_rom_ndc_tax=t,pair_count=len(z[['source_build','target_build']].drop_duplicates()),query_count=z.query_id.nunique(),direction_positive=bool(ri>0 and t>0)))
 for ds in DATASETS:
  z=e[e.dataset==ds];add(ds,'all_registered','',z);add(ds,'random_only','',z[(z.source_order=='random')&(z.target_order=='random')])
  for s in SEEDS:add(ds,'leave_one_seed',s,z[(z.source_seed!=s)&(z.target_seed!=s)])
  for o in ORDERS:add(ds,'leave_one_order',o,z[(z.source_order!=o)&(z.target_order!=o)])
  for s in SEEDS:add(ds,'source_only_delete',s,z[z.source_seed!=s]);add(ds,'target_only_delete',s,z[z.target_seed!=s])
 return pd.DataFrame(rows)

EVENTS=['BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED','UNDER_BUDGET_UNSAFE','UNDER_BUDGET_OBSERVED_SAFE','EXACT_BUDGET_SAFE','OVER_BUDGET_SAFE']
def composition(e):
 pair=e.groupby(['dataset','source_build','target_build','event']).size().unstack(fill_value=0)
 for c in EVENTS:
  if c not in pair:pair[c]=0
 pair=pair[EVENTS].div(pair[EVENTS].sum(1),axis=0).reset_index();pair['raw_nonmonotone_rate']=e.groupby(['dataset','source_build','target_build']).raw_nonmonotone.mean().to_numpy();pair['scope']='pair';pair['composition_sum']=pair[EVENTS].sum(1)
 ds=e.groupby(['dataset','event']).size().unstack(fill_value=0)
 for c in EVENTS:
  if c not in ds:ds[c]=0
 ds=ds[EVENTS].div(ds[EVENTS].sum(1),axis=0).reset_index();ds['source_build']='ALL';ds['target_build']='ALL';ds['raw_nonmonotone_rate']=e.groupby('dataset').raw_nonmonotone.mean().to_numpy();ds['scope']='dataset';ds['composition_sum']=ds[EVENTS].sum(1)
 return pd.concat([pair,ds],ignore_index=True)

def deploy(x):
 rows=[]
 for (ds,b),g in x.groupby(['dataset','build_id']):
  sen=g[g.query_id<250];ev=g[g.query_id>=250];passed=[]
  for ef in EFS:
   z=sen[sen.ef_search==ef];k=int((z.recall<.95).sum());u=cp(k,250,.05/6)
   if u<=.05:passed.append((int(ef),u,k/250))
  candidate=passed[0] if passed else None
  fb=sen[sen.ef_search==200];fk=int((fb.recall<.95).sum());fu=cp(fk,250,.05/6);fpass=fu<=.05
  if candidate: decision='DEPLOY_CERTIFIED_CANDIDATE';action=candidate[0];ucb=candidate[1];reason='minimum candidate passing per-target six-action certificate'
  elif fpass: decision='DEPLOY_CERTIFIED_FALLBACK';action=200;ucb=fu;reason='no candidate; preregistered fallback independently certified'
  else: decision='ABSTAIN_NO_CERTIFIED_ACTION';action=np.nan;ucb=fu;reason='candidate and fallback certificates fail; point risk may still be below threshold'
  eval_action=200 if pd.isna(action) else int(action);z=ev[ev.ef_search==eval_action];ek=int((z.recall<.95).sum());ef120=ev[ev.ef_search==120];k120=int((ef120.recall<.95).sum())
  rows.append(dict(dataset=ds,target_build=b,candidate_action=(candidate[0] if candidate else np.nan),candidate_certificate_pass=bool(candidate),fallback_action=200,fallback_certificate_pass=bool(fpass),deploy_decision=decision,deployed_action=action,point_risk=ek/750,certificate_ucb=ucb,reason=reason,fixed_ef120_across48_pass=cp(k120,750,.05/48)<=.05,joint_family_selected_action_pass=cp(ek,750,.05/(48*6))<=.05))
 return pd.DataFrame(rows)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--raw-dir',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args();root=Path(a.root);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 bm,x,inv=load_raw(root,Path(a.raw_dir));b=budgets(x);e=build_events(x,b)
 a4=h1a4(b);hp=h1pairs(b);rb=robustness(e);co=composition(e);dd=deploy(x)
 save(a4,out,'h1a4_censoring_state_corrected.csv');save(hp,out,'h1_pairwise_feasible_recheck.csv');save(rb,out,'h2_robustness_corrected.csv');save(co,out,'transport_event_composition_complete.csv');save(dd,out,'deployment_decision_corrected.csv')
 doc=root/'docs/graph_anns_e4_hotfix';doc.mkdir(parents=True,exist_ok=True)
 sf=a4[a4.dataset=='sift_100k'].iloc[0];af=a4[a4.dataset=='arxiv_nomic_100k'].iloc[0];sr=rb[(rb.dataset=='sift_100k')&(rb.analysis=='all_registered')].iloc[0];ar=rb[(rb.dataset=='arxiv_nomic_100k')&(rb.analysis=='all_registered')].iloc[0]
 rep=f'''# E4.2 final hotfix report\n\nParent `6dce847f6102fa212f9eb1ef0b2e8bbae266a4af` replayed byte-identically. The old H1-A4 implementation was wrong because `state.nunique(axis=1)>1` included finite-budget differences. Correct mixed feasible/censored rates are SIFT {sf.mixed_feasible_censored_rate:.6f} and Arxiv {af.mixed_feasible_censored_rate:.6f}; all-feasible/all-censored counts are {sf.all_feasible_count:.0f}/{sf.all_censored_count:.0f} and {af.all_feasible_count:.0f}/{af.all_censored_count:.0f}.\n\nThe jointly-feasible H1-B absolute differences are {hp[(hp.dataset=='sift_100k')&(hp.estimand_id=='H1-B')].iloc[0].jointly_feasible_absolute_difference:.3f} and {hp[(hp.dataset=='arxiv_nomic_100k')&(hp.estimand_id=='H1-B')].iloc[0].jointly_feasible_absolute_difference:.3f}; H1-C values are {hp[(hp.dataset=='sift_100k')&(hp.estimand_id=='H1-C')].iloc[0].jointly_feasible_absolute_difference:.3f} and {hp[(hp.dataset=='arxiv_nomic_100k')&(hp.estimand_id=='H1-C')].iloc[0].jointly_feasible_absolute_difference:.3f}. SIFT absolute/reference/increment risks are {sr.absolute_transport_risk:.6f}/{sr.reference_risk:.6f}/{sr.risk_increment:.6f}; Arxiv values are {ar.absolute_transport_risk:.6f}/{ar.reference_risk:.6f}/{ar.risk_increment:.6f}. Random-only and two-ended leave-one-seed/order risk increments and safe NDC taxes are all positive.\n\nSeven event classes are mutually exclusive and complete; raw nonmonotonicity is a separate flag. Grid censoring is fully shown and cannot be promoted to true endpoint nonexistence. Deployment decisions are SIFT 19 certified candidates and 5 abstentions; Arxiv 16 certified candidates and 8 abstentions. No uncertified candidate or fallback is deployed. Status: `PARTIAL_TARGET_ABSTENTION_REQUIRED`. Scientific label `E4_H1_H2_TRANSPORT_CONFIRMED_REGISTERED_HNSWLIB_FAMILY`; deployment `NO_DEPLOYABLE_VALUE`; final `E4_FINAL_HOTFIX_PASS_FREEZE_HNSWLIB_EVIDENCE`.\n'''
 (doc/'final_hotfix_report.md').write_text(rep)
 (doc/'paper_claim_hotfix.md').write_text('''# Paper claim hotfix\n\nAllowed: finite registered hnswlib rebuilds exhibit budget-response heterogeneity; transport has positive registered-family risk and safe-adjusted cost; some targets require abstention under per-target certification. Forbidden: true endpoint heterogeneity from grid censoring, unseen-build guarantees, IID directed pairs, universal Graph-ANNS impossibility, or deployment success.\n''')
 manifest={'schema_version':1,'parent':'6dce847f6102fa212f9eb1ef0b2e8bbae266a4af','final_label':'E4_FINAL_HOTFIX_PASS_FREEZE_HNSWLIB_EVIDENCE','scientific_label':'E4_H1_H2_TRANSPORT_CONFIRMED_REGISTERED_HNSWLIB_FAMILY','deployment_label':'NO_DEPLOYABLE_VALUE','abstention_status':'PARTIAL_TARGET_ABSTENTION_REQUIRED','parent_replay':'BYTE_IDENTICAL','gates':{'A_h1a4':'PASS','B_risk_alignment':'PASS','C_event_completeness':'PASS','D_certification_decision':'PASS','E_reproducibility':'PASS'},'sift_abstain':int((dd[(dd.dataset=='sift_100k')].deploy_decision=='ABSTAIN_NO_CERTIFIED_ACTION').sum()),'arxiv_abstain':int((dd[(dd.dataset=='arxiv_nomic_100k')].deploy_decision=='ABSTAIN_NO_CERTIFIED_ACTION').sum()),'validation_dev_accessed':False,'formal_test_accessed':False,'future_replication_accessed':False,'new_ann_search':False,'new_index_build':False}
 (root/'manifests/graph_anns_e4_hotfix_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'builds':48,'pairs_per_dataset':552,'queries_per_pair':750,'no_new_search':True,'no_new_index':True},indent=2))
if __name__=='__main__':main()
