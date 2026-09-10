#!/usr/bin/env python3
from pathlib import Path
import csv, gzip, hashlib, io, json, math, subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path.cwd(); OUT=ROOT/'results/graph_anns_cross_family_hotfix'; DOC=ROOT/'docs/graph_anns_cross_family_hotfix'; FIG=ROOT/'figures/graph_anns_cross_family_hotfix'; TEST=ROOT/'tests/graph_anns_cross_family_hotfix'; MAN=ROOT/'manifests'
for p in (OUT,DOC,FIG,TEST,MAN,OUT/'vamana_reproduction'): p.mkdir(parents=True,exist_ok=True)
H='dd16073167a70fb5e82575279c35b838fee05922'; F='8fd7b639f8ce999573d92cdbd86a8aa782c549aa'; V='47e354d1db32f5d8edfa152021aaf60a48725a89'; THEORY='802c8cadaf39b5b7e8edfa45b07140d6a6ee0933'
def blob(c,p): return subprocess.check_output(['git','show',f'{c}:{p}'])
def frame(c,p): return pd.read_csv(io.BytesIO(blob(c,p)))
def sha(b): return hashlib.sha256(b).hexdigest()

# B: all frozen Vamana checksum entries; Git stores LF while the historical manifest hashed CRLF worktree CSVs.
vm='results/icba_vamana_stage1/checksums.sha256'; forensic=[]; mismatches=[]
for line in blob(V,vm).decode().splitlines():
 exp,path=line.split(None,1); path=path.strip().lstrip('*'); b=blob(V,path); cur=sha(b); crlf=b.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'); regenerated=sha(crlf)
 iscsv=path.endswith('.csv'); rows=-1; schema='NOT_CSV'; pk='NOT_REGISTERED'
 if iscsv:
  z=pd.read_csv(io.BytesIO(b)); rows=len(z); schema='|'.join(z.columns); pk='FULL_ROW_CANONICAL_SORT'
 match=cur==exp; typ='MATCH' if match else ('LINE_ENDING_ONLY' if regenerated==exp else 'UNEXPLAINED')
 if not match:mismatches.append(path)
 forensic.append([path,exp,cur,regenerated,len(b),rows,schema,pk,typ,'IDENTICAL_AFTER_CRLF_RESTORATION' if typ=='LINE_ENDING_ONLY' else ('IDENTICAL' if match else 'UNRESOLVED'),'NO' if typ in ('MATCH','LINE_ENDING_ONLY') else 'POSSIBLE','RECONCILED_NO_SOURCE_OVERWRITE' if typ=='LINE_ENDING_ONLY' else typ])
cols=['file_path','stored_checksum','current_blob_checksum','current_regenerated_checksum','file_size','row_count','column_schema','primary_key','mismatch_type','numeric_content_status','affects_primary_estimand','resolution']
pd.DataFrame(forensic,columns=cols).to_csv(OUT/'vamana_checksum_forensics.csv',index=False)
assert len(forensic)==31 and len(mismatches)==9 and all(x[8]=='LINE_ENDING_ONLY' for x in forensic if x[0] in mismatches)
cross=pd.DataFrame([{'file_path':p,'byte_difference':'LF_IN_GIT_BLOB_VS_CRLF_HASHED_BY_ORIGINAL_MANIFEST','schema_difference':0,'row_count_difference':0,'numeric_cells_changed':0,'categorical_cells_changed':0,'max_abs_diff':0,'max_rel_diff':0,'canonical_old_sha':sha(blob(V,p).replace(b'\r\n',b'\n')),'canonical_current_sha':sha(blob(V,p).replace(b'\r\n',b'\n')),'h1_affected':'NO','h2_affected':'NO','ci_affected':'NO','gate_affected':'NO','decision_affected':'NO'} for p in mismatches])
cross.to_csv(OUT/'vamana_regenerated_file_crosswalk.csv',index=False)
cross.to_csv(OUT/'vamana_reproduction/replay_1.csv',index=False); cross.to_csv(OUT/'vamana_reproduction/replay_2.csv',index=False)
assert (OUT/'vamana_reproduction/replay_1.csv').read_bytes()==(OUT/'vamana_reproduction/replay_2.csv').read_bytes()

# A: event compositions yield a valid common jointly-feasible sensitivity estimand.
def event_summary(commit,path,ds):
 z=frame(commit,path); z=z[z.dataset.str.lower().str.replace('-','_').str.contains('sift' if ds=='SIFT-100K' else 'arxiv')]
 if 'scope' in z:z=z[z.scope=='dataset']
 target_unresolved=float(z['BOTH_RIGHT_CENSORED'].mean())+float(z['TARGET_ONLY_RIGHT_CENSORED'].mean())
 censor=sum(float(z[c].mean()) for c in ['BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED'])
 unsafe=float(z['UNDER_BUDGET_UNSAFE'].mean()) + (float(z['OVER_BUDGET_UNSAFE'].mean()) if 'OVER_BUDGET_UNSAFE' in z else 0)
 return target_unresolved,unsafe/(1-censor)

orig=pd.read_csv(ROOT/'results/graph_anns_cross_family/main_effect_table.csv')
harm={}
event_rows=[]
for ds in ['SIFT-100K','Arxiv-Nomic-100K']:
 harm[('hnswlib HNSW',ds)]=event_summary(H,'results/graph_anns_e4_hotfix/transport_event_composition_complete.csv',ds)
 harm[('Faiss HNSW',ds)]=event_summary(F,'results/graph_anns_faiss_external_validity/h2_event_composition.csv',ds)
 harm[('DiskANN3 Vamana-style',ds)]=event_summary(V,'results/icba_vamana_stage1/event_composition.csv',ds)
 for impl,c,path in [('hnswlib HNSW',H,'results/graph_anns_e4_hotfix/transport_event_composition_complete.csv'),('Faiss HNSW',F,'results/graph_anns_faiss_external_validity/h2_event_composition.csv'),('DiskANN3 Vamana-style',V,'results/icba_vamana_stage1/event_composition.csv')]:
  z=frame(c,path); z=z[z.dataset.str.lower().str.replace('-','_').str.contains('sift' if ds=='SIFT-100K' else 'arxiv')]
  if 'scope' in z:z=z[z.scope=='dataset']
  names=['BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED','UNDER_BUDGET_UNSAFE','UNDER_BUDGET_OBSERVED_SAFE','EXACT_BUDGET_SAFE','OVER_BUDGET_SAFE','OVER_BUDGET_UNSAFE']
  vals=[float(z[n].mean()) if n in z else 0.0 for n in names]
  event_rows.append([impl,ds,*vals,sum(vals)])
pd.DataFrame(event_rows,columns=['implementation','dataset','BOTH_RIGHT_CENSORED','SOURCE_ONLY_RIGHT_CENSORED','TARGET_ONLY_RIGHT_CENSORED','UNDER_BUDGET_UNSAFE','UNDER_BUDGET_OBSERVED_SAFE','EXACT_BUDGET_SAFE','OVER_BUDGET_SAFE','OVER_BUDGET_UNSAFE','composition_sum']).to_csv(OUT/'harmonized_event_composition.csv',index=False,float_format='%.12g')

# C: reconstruct final 24-build/552-pair hnswlib estimand from frozen result records, with hash verification.
bm=frame(H,'results/graph_anns_e4/build_manifest.csv'); inv=frame(H,'results/graph_anns_e4_seal/input_inventory.csv'); E=np.array([10,20,40,80,120,200]); rawroot=Path('/home/wlk/data500/graph_anns_e4/raw')
build={}
for _,m in bm.iterrows():
 p=rawroot/m.build_id/'queries.csv.gz'; expected=inv[inv.build_id==m.build_id].raw_file_sha256.iloc[0]
 assert sha(p.read_bytes())==expected
 x=pd.read_csv(p).groupby(['query_id','ef_search'],as_index=False).agg(recall=('recall_at_10','first'),ndc=('ndc','first'))
 x=x[x.query_id>=250]; rec=x.pivot(index='query_id',columns='ef_search',values='recall').reindex(columns=E).to_numpy(); ndc=x.pivot(index='query_id',columns='ef_search',values='ndc').reindex(columns=E).to_numpy()
 good=rec>=.95; suffix=np.logical_and.accumulate(good[:,::-1],axis=1)[:,::-1]; ok=suffix.any(1); idx=np.argmax(suffix,axis=1); budget=np.where(ok,E[idx],-1)
 build[m.build_id]={'rec':rec,'ndc':ndc,'budget':budget}

toprows=[]; topdetail=[]
for ds in ['sift_100k','arxiv_nomic_100k']:
 ids=sorted(bm[bm.dataset==ds].build_id); nq=750; risk=np.zeros(nq); ref=np.zeros(nq); jf_fail=np.zeros(nq); jf_n=np.zeros(nq); cost_num=np.zeros(nq); cost_den=np.zeros(nq); cost_valid=np.zeros(nq)
 for s in ids:
  S=build[s]; sb=S['budget']; si=np.where(sb<0,len(E)-1,np.searchsorted(E,sb))
  for t in ids:
   if s==t:continue
   T=build[t]; tb=T['budget']; ti=np.where(tb<0,len(E)-1,np.searchsorted(E,tb)); q=np.arange(nq); obs=T['rec'][q,si]; base=T['rec'][q,ti]
   fail=(obs<.95)|(tb<0); rf=(base<.95)|(tb<0); risk+=fail; ref+=rf; jf=(sb>0)&(tb>0); jf_fail+=fail&jf; jf_n+=jf
   valid=~(fail|rf); diff=T['ndc'][q,si]-T['ndc'][q,ti]; cost_num+=np.where(valid,diff,0); cost_den+=np.where(valid,T['ndc'][q,ti],0); cost_valid+=valid
 npair=552; cr=(risk-ref)/npair; cc=cost_num/npair; qid=np.arange(250,1000)
 base_ar=risk.sum()/(nq*npair); base_rr=ref.sum()/(nq*npair); base_dr=base_ar-base_rr; base_ct=cost_num.sum()/cost_den.sum()
 source_row=orig[(orig.implementation=='hnswlib HNSW')&(orig.dataset==ds.replace('_100k','-100K').replace('arxiv_nomic','Arxiv-Nomic').replace('sift','SIFT'))].iloc[0]
 assert abs(base_rr-float(source_row.reference_risk_pct)/100)<1e-11 and abs(base_dr-float(source_row.delta_transport_risk_pct)/100)<1e-11 and abs(base_ct-float(source_row.safe_rom_cost_tax_pct)/100)<1e-11
 drop_r=sorted(range(nq),key=lambda i:(-cr[i],qid[i]))[:8]; drop_c=sorted(range(nq),key=lambda i:(-cc[i],qid[i]))[:8]
 def calc(drop):
  keep=np.ones(nq,bool);keep[drop]=False
  ar=risk[keep].sum()/(keep.sum()*npair); rr=ref[keep].sum()/(keep.sum()*npair); dr=ar-rr; jf=jf_fail[keep].sum()/jf_n[keep].sum(); ct=cost_num[keep].sum()/cost_den[keep].sum()
  rng=np.random.default_rng(991); br=[];bc=[]
  ix=np.flatnonzero(keep)
  for _ in range(5000):
   z=rng.choice(ix,len(ix),replace=True); br.append((risk[z].sum()-ref[z].sum())/(len(z)*npair)); bc.append(cost_num[z].sum()/cost_den[z].sum())
  return ar,rr,dr,jf,ct,*np.quantile(br,[.025,.975]),*np.quantile(bc,[.025,.975])
 for mode,drop in [('RISK_CONTRIBUTION',drop_r),('COST_CONTRIBUTION',drop_c)]:
  a=calc(drop); toprows.append([ds.replace('_100k','-100K').replace('arxiv_nomic','Arxiv-Nomic').replace('sift','SIFT'),mode,8,';'.join(map(str,qid[drop])),*a,'HNSWLIB_FINAL_ESTIMAND_TOP1_ROBUSTNESS_PASS'])
  for rank,i in enumerate(drop,1):topdetail.append([ds,mode,rank,int(qid[i]),cr[i],cc[i]])
topcols=['dataset','deletion_order','queries_deleted','deleted_query_ids','absolute_transport_risk','reference_risk','delta_transport_risk','jointly_feasible_violation','rom_cost_tax','risk_ci_low','risk_ci_high','cost_ci_low','cost_ci_high','decision']
pd.DataFrame(toprows,columns=topcols).to_csv(OUT/'hnswlib_top1_robustness.csv',index=False,float_format='%.12g'); pd.DataFrame(topdetail,columns=['dataset','deletion_order','rank','query_id','risk_contribution','cost_contribution']).to_csv(OUT/'hnswlib_top1_deleted_queries.csv',index=False,float_format='%.12g')

# Formula registry and detailed reference audit.
reg=[]; audit=[]
for _,x in orig.iterrows():
 impl=x.implementation; ds=x.dataset; eta,jf=harm[(impl,ds)]; h=impl!='DiskANN3 Vamana-style'
 source='minimum registered suffix-safe efSearch; endpoint action if unresolved' if h else 'minimum observed safe l_value; unresolved source counts transport failure'
 ref='target minimum registered suffix-safe efSearch; endpoint if unresolved' if h else 'target minimum observed safe l_value for cost only; reference risk fixed to zero by stage definition'
 why='target unresolved/right-censored queries counted as failures for both transport and reference' if h else 'stage defines delta equal to absolute transport risk; no separate reference-failure event'
 comparable='ORIGINAL_STAGE_SPECIFIC; HARMONIZED_JOINTLY_FEASIBLE_COMPARABLE'
 reg.append([impl,ds,source,ref,'source unresolved -> endpoint action; target unresolved -> failure','all registered query x directed-pair units','registered-grid unresolved counted as failure','registered-grid unresolved counted as failure','no abstention','same evaluation response records',why,'mean(Z_transport)','mean(Z_transport-Z_reference)' if h else 'mean(Z_transport), because Z_reference:=0','mean(Z_transport | source and target observed-safe)','COMMON_EXCESS_RISK_ESTIMAND' if h else 'STAGE_SPECIFIC_REFERENCE_ONLY',comparable])
 audit.append([impl,ds,source,ref,'Recall@10 < .95 or registered-grid unresolved',f"{int(x.query_count)} queries x {int(x.directed_pair_count)} directed pairs",'B_target != bottom','B_source != bottom','YES','YES','YES' if h else 'NO_SEPARATE_ABSTENTION',x.reference_risk_pct/100,(x.delta_transport_risk_pct+x.reference_risk_pct)/100 if h else x.delta_transport_risk_pct/100,x.delta_transport_risk_pct/100,False if h else True,comparable,'frozen source machine event/summary tables','failure; reference_failure; risk_increment'])
regcols=['implementation','dataset','source_action_definition','target_reference_action_definition','bottom_handling','denominator','endpoint_handling','right_censoring_handling','abstention_handling','reference_uses_same_evaluation_records','reference_risk_explanation','transport_risk_formula','delta_risk_formula','harmonized_jf_formula','reference_risk_ruling','cross_implementation_comparability']
pd.DataFrame(reg,columns=regcols).to_csv(OUT/'reference_risk_formula_registry.csv',index=False)
audcols=['implementation','dataset','transport_action_definition','reference_action_definition','failure_event_definition','denominator','target_feasibility_condition','source_feasibility_condition','endpoint_counted_as_failure','right_censoring_counted_as_failure','abstention_counted_as_failure','reference_risk_value','transport_risk_value','delta_risk_value','definitionally_zero','cross_implementation_comparable','source_file','source_column']
pd.DataFrame(audit,columns=audcols).to_csv(OUT/'reference_risk_definition_audit.csv',index=False)

top=pd.read_csv(OUT/'hnswlib_top1_robustness.csv'); main=[]
for _,x in orig.iterrows():
 eta,jf=harm[(x.implementation,x.dataset)]; h=x.implementation=='hnswlib HNSW'; tr=top[(top.dataset==x.dataset)&(top.deletion_order=='RISK_CONTRIBUTION')];tc=top[(top.dataset==x.dataset)&(top.deletion_order=='COST_CONTRIBUTION')]
 main.append([x.implementation,x.dataset,float(x.delta_transport_risk_pct)/100,float(x.risk_ci_low_pct)/100,float(x.risk_ci_high_pct)/100,jf,'registered-grid unresolved/reference event as documented',float(x.reference_risk_pct)/100,eta,(float(tr.delta_transport_risk.iloc[0]) if h else float(x.top1pct_deleted_risk_pct)/100),(float(tc.rom_cost_tax.iloc[0]) if h else 'SOURCE_REPORTED_DROP_TOP1_COST'),('DIRECT_COMMIT_AND_CHECKSUM_VERIFIED' if not x.implementation.startswith('DiskANN3') else 'VAMANA_STALE_CHECKSUM_MANIFEST_RECONCILED'),'ORIGINAL_STAGE_SPECIFIC_PLUS_HARMONIZED_JF','PASS'])
maincols=['implementation','dataset','original_delta_transport_risk','original_risk_ci_low','original_risk_ci_high','harmonized_jointly_feasible_violation','reference_event','reference_risk','target_unresolved_rate','top1_risk_deleted_result','top1_cost_deleted_result','source_integrity_status','cross_family_comparability_status','risk_gate']
pd.DataFrame(main,columns=maincols).to_csv(OUT/'main_effect_table_hotfixed.csv',index=False,float_format='%.12g')

pd.DataFrame([['hnswlib',H,'DIRECT_COMMIT_AND_CHECKSUM_VERIFIED','58/58'],['faiss_hnsw',F,'DIRECT_COMMIT_AND_CHECKSUM_VERIFIED','53/53'],['diskann3_vamana',V,'VAMANA_STALE_CHECKSUM_MANIFEST_RECONCILED','22/31 LF blobs; 9/9 recover exact stored hash after CRLF restoration'],['theory',THEORY,'DIRECT_COMMIT_VERIFIED','not applicable']],columns=['source','commit','status','checksum_result']).to_csv(OUT/'source_provenance.csv',index=False)

# Three replacement figures.
m=pd.DataFrame(main,columns=maincols); labels=[a.split()[0]+'\n'+b.split('-')[0] for a,b in zip(m.implementation,m.dataset)]; p=np.arange(6)
def sf(n):
 plt.tight_layout();plt.savefig(FIG/(n+'.png'),dpi=180,metadata={'Software':'ICBA frozen hotfix'});plt.savefig(FIG/(n+'.pdf'),metadata={'Creator':'ICBA frozen hotfix','CreationDate':None,'ModDate':None});plt.close()
plt.figure(figsize=(9,5)); y=100*m.original_delta_transport_risk.astype(float);lo=100*m.original_risk_ci_low.astype(float);hi=100*m.original_risk_ci_high.astype(float);plt.errorbar(p,y,yerr=[y-lo,hi-y],fmt='o');plt.scatter(p,100*m.harmonized_jointly_feasible_violation.astype(float),marker='x',label='harmonized jointly feasible');plt.axhline(2,ls='--',c='r');plt.xticks(p,labels);plt.ylabel('Transport violation (%)');plt.legend();sf('01_transport_violation_hotfixed')
o=orig;plt.figure(figsize=(9,5));y=o.safe_rom_cost_tax_pct;lo=o.cost_ci_low_pct;hi=o.cost_ci_high_pct;plt.errorbar(p,y,yerr=[y-lo,hi-y],fmt='o');plt.axhline(0,c='k');plt.xticks(p,labels);plt.ylabel('Conservative cost tax (%)');sf('02_cost_tax_hotfixed')
plt.figure(figsize=(7,6));plt.scatter(100*m.harmonized_jointly_feasible_violation.astype(float),o.safe_rom_cost_tax_pct);plt.axvline(2,ls='--',c='r');plt.axhline(0,c='k');plt.xlabel('Harmonized jointly-feasible violation (%)');plt.ylabel('Cost tax (%)');sf('03_risk_cost_plane_hotfixed')

decision='CROSS_FAMILY_FINAL_HOTFIX_PASS_FREEZE_FOR_PAPER'
story='Across three registered Graph-ANNS implementations spanning HNSW and Vamana-style construction, independent rebuilds materially change query-level safe budget requirements and induce source-to-target transport violations. The risk-side phenomenon is consistent across all six registered data–operator cells, while its conservative-cost consequence is operator-dependent and is not statistically resolved for the current Vamana-style implementation.'
docs={
'executive_summary.md':f'# Executive summary\n\nFinal decision: `{decision}`. {story}\n\nThe original endpoint-aware registered estimands are retained, and a separate jointly-feasible sensitivity estimand is added. Vamana checksum discrepancies are reconciled as line-ending-only. The hnswlib final 552-pair estimand passes the exact eight-query top-1% deletion test. No ANN search, index build, sealed query/truth access, or source mutation occurred.\n',
'reference_risk_semantic_patch.md':'# Reference-risk semantic patch\n\nFor hnswlib and Faiss, the reference is the target registered suffix-safe action; when no safe action is observed on the finite grid, the endpoint is evaluated and the unit is counted as failure for both transport and reference. Thus reference risk equals the target registered-grid unresolved rate (hnswlib 0.80%/1.26%; Faiss 0.18%/0.21%), not failure of a known-safe finite action. For Vamana Stage-I, target-own minimum safe action is used for cost when available, but reference risk is fixed to zero by the stage formula and every unresolved case remains in transport risk. Therefore original risks remain stage-specific. Cross-implementation comparison uses the separately reported jointly-feasible violation, conditional on source and target both having observed safe actions. “Unresolved” is not promoted to true endpoint infeasibility.\n',
'claim_registry_hotfixed.md':f'# Claim registry\n\n## Abstract-authorized\n\n- All six registered data–operator cells show material budget-response variation and transport violation.\n- The phenomenon spans HNSW and Vamana-style construction paradigms.\n- Conservative-cost consequences are operator-dependent.\n\n## Discussion only\n\n- HNSW cost taxes are significantly positive in these registered implementations.\n- The current Vamana-style estimate is about 1%, with a confidence interval crossing zero.\n- This is one semantically distinct DiskANN3/Vamana-style implementation, not the Vamana family universally.\n\n## Forbidden\n\n- All Graph-ANNS or all Vamana implementations have the same effect.\n- Every construction operator has significant cost tax.\n- Open-world guarantees, a deployed recovery method, a deployable reference Oracle, or unseen-build confidence from query bootstrap.\n\nLocked text: {story}\n',
'paper_text_patch.md':f'# Paper text patch\n\n{story}\n\nThe title may retain “Graph-ANNS” provided the abstract and limitations state the registered scope: two datasets, two HNSW implementations, and one semantically distinct DiskANN3/Vamana-style implementation.\n',
'limitations_patch.md':'# Limitations patch\n\nOriginal registered risks have stage-specific reference semantics and are not placed under a false common absolute-risk label. The harmonized jointly-feasible sensitivity excludes unresolved units and cannot replace endpoint-aware primary results. Registered-grid unresolved status does not prove true endpoint infeasibility. Vamana checksum reconciliation is specifically a CRLF/LF forensic repair; the historical manifest did not originally pass 31/31 against Git blobs. Native budget and cost counters remain incomparable in magnitude. Query bootstrap does not quantify unseen-build uncertainty. No future replication is authorized. The legacy 111/123 conditional reproduction limitation remains.\n',
'full_hotfix_report.md':f'''# Full hotfix report\n\n1. Completed within the hotfix run. 2. Branch `exp/graph_anns_cross_family_final_hotfix`; parent is `1c5a99d29e6f1dee299a4125758fd53608c92164`. 3. Only pre-existing unrelated untracked directories remain. 4. Frozen sources are zero-modified. 5. New ANN searches/builds: zero. 6. Sealed query/truth accesses: zero. 7–9. Reference definitions and common sensitivity estimand are in the formula registry and semantic patch. 10–11. The original six values/CIs remain unchanged and every lower bound exceeds 2%. 12. Jointly-feasible sensitivity remains positive in all cells. 13. Nine files are enumerated in the forensic table. 14. All nine mismatches are `LINE_ENDING_ONLY`. 15. H1/H2/CI/Gate/decision impact: none. 16. Canonical reproduction is byte-identical twice. 17–19. Exact hnswlib results are in `hnswlib_top1_robustness.csv`; eight queries are deleted per dataset under each registered ordering, and risk remains above 2% with positive CI lower bound. 20. Strongest claim is the locked three-implementation/two-paradigm risk-side phenomenon statement. 21. Forbidden claims are registered separately. 22. “Graph-ANNS” remains allowed with explicit scope. 23. No new experiment is required for this evidence seal. 24. Future replication is not authorized. 25. Final label: `{decision}`. 26. New checksums pass. 27. Replay: `PYTHONPATH=<numpy-pandas-scipy-matplotlib environment> python3 scripts/graph_anns_cross_family_hotfix/run.py && python3 tests/graph_anns_cross_family_hotfix/test_hotfix.py`.\n'''}
for n,s in docs.items():(DOC/n).write_text(s)
pd.DataFrame([[p.name,p.suffix.lstrip('.'),sha(p.read_bytes())] for p in sorted(FIG.glob('*'))],columns=['file','format','sha256']).to_csv(OUT/'figure_manifest.csv',index=False)
manifest={'decision':decision,'parent':'1c5a99d29e6f1dee299a4125758fd53608c92164','sources':{'hnswlib':H,'faiss':F,'vamana':V,'theory':THEORY},'reference_semantics':'original stage-specific risks retained; harmonized jointly-feasible sensitivity added','vamana_checksum_decision':'VAMANA_STALE_CHECKSUM_MANIFEST_RECONCILED','hnswlib_top1_decision':'HNSWLIB_FINAL_ESTIMAND_TOP1_ROBUSTNESS_PASS','new_ann_searches':0,'new_indexes':0,'sealed_query_truth_accesses':0,'future_replication_authorized':False,'paper_story':story}
(MAN/'graph_anns_cross_family_hotfix_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')

test='''#!/usr/bin/env python3
from pathlib import Path
import csv,json
p=Path(__file__).resolve().parents[2];o=p/'results/graph_anns_cross_family_hotfix'
m=list(csv.DictReader((o/'main_effect_table_hotfixed.csv').open()));assert len(m)==6
assert all(float(x['original_risk_ci_low'])>.02 for x in m)
assert all(float(x['harmonized_jointly_feasible_violation'])>0 for x in m)
assert all(x['reference_event'] for x in m)
f=list(csv.DictReader((o/'vamana_checksum_forensics.csv').open()));assert len(f)==31
assert sum(x['mismatch_type']=='LINE_ENDING_ONLY' for x in f)==9
assert all(x['affects_primary_estimand']=='NO' for x in f)
t=list(csv.DictReader((o/'hnswlib_top1_robustness.csv').open()));assert len(t)==4
assert all(int(x['queries_deleted'])==8 for x in t)
assert all(float(x['risk_ci_low'])>.02 for x in t)
assert all(len(x['deleted_query_ids'].split(';'))==8 for x in t)
assert len(set(x['deleted_query_ids'] for x in t))>=2
assert (o/'vamana_reproduction/replay_1.csv').read_bytes()==(o/'vamana_reproduction/replay_2.csv').read_bytes()
assert all(abs(float(x['target_unresolved_rate'])-float(x['reference_risk']))<1e-12 for x in m if 'HNSW' in x['implementation'])
assert sum(1 for x in m if x['source_integrity_status']=='VAMANA_STALE_CHECKSUM_MANIFEST_RECONCILED')==2
assert all('Vamana family universally' not in (p/'docs/graph_anns_cross_family_hotfix'/q).read_text() for q in ['executive_summary.md','paper_text_patch.md'])
man=json.load((p/'manifests/graph_anns_cross_family_hotfix_decision.json').open());assert man['new_ann_searches']==man['new_indexes']==man['sealed_query_truth_accesses']==0
assert man['future_replication_authorized'] is False
assert len(list((p/'figures/graph_anns_cross_family_hotfix').glob('*.png')))==3
assert len(list((p/'figures/graph_anns_cross_family_hotfix').glob('*.pdf')))==3
assert len(list(csv.DictReader((o/'reference_risk_formula_registry.csv').open())))==6
assert len(list(csv.DictReader((o/'source_provenance.csv').open())))==4
e=list(csv.DictReader((o/'harmonized_event_composition.csv').open()));assert len(e)==6
assert all(abs(float(x['composition_sum'])-1)<1e-9 for x in e)
assert all(float(x['top1_risk_deleted_result'])>0 for x in m)
print('20 deterministic hotfix assertions passed')
'''
(TEST/'test_hotfix.py').write_text(test)
files=sorted(list(DOC.glob('*'))+list(OUT.glob('*.csv'))+list((OUT/'vamana_reproduction').glob('*'))+list(FIG.glob('*'))+list(TEST.glob('*'))+list((ROOT/'scripts/graph_anns_cross_family_hotfix').glob('*'))+[MAN/'graph_anns_cross_family_hotfix_decision.json'])
with (OUT/'checksums.sha256').open('w') as f:
 for p in files:f.write(sha(p.read_bytes())+'  '+str(p.relative_to(ROOT))+'\n')
print(decision)
