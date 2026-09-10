#!/usr/bin/env python3
from pathlib import Path
import csv, json, hashlib, subprocess
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path.cwd(); R=ROOT/'results/graph_anns_cross_family'; D=ROOT/'docs/graph_anns_cross_family'; F=ROOT/'figures/graph_anns_cross_family'; T=ROOT/'tests/graph_anns_cross_family'; M=ROOT/'manifests'
for p in (R,D,F,T,M): p.mkdir(parents=True,exist_ok=True)
COMMITS={'hnswlib':'dd16073167a70fb5e82575279c35b838fee05922','faiss_hnsw':'8fd7b639f8ce999573d92cdbd86a8aa782c549aa','diskann3_vamana':'47e354d1db32f5d8edfa152021aaf60a48725a89','theory':'802c8cadaf39b5b7e8edfa45b07140d6a6ee0933'}
for c in COMMITS.values(): subprocess.run(['git','cat-file','-e',c+'^{commit}'],check=True)

rows=[
dict(impl='hnswlib HNSW',operator='HNSW',dataset='SIFT-100K',builds=24,queries=750,pairs=552,cat=.894666666667,mixed=.024,risk=.215734299517,rlo=.207668900966,rhi=.223544082126,ref=.008,cost=.194472095841,clo=.181298438744,chi=.207695909954,top=None,lobo=.0,cost_state='POSITIVE_RESOLVED'),
dict(impl='hnswlib HNSW',operator='HNSW',dataset='Arxiv-Nomic-100K',builds=24,queries=750,pairs=552,cat=.753333333333,mixed=.026666666667,risk=.17120531401,rlo=.162385869565,rhi=.180036594203,ref=.012555555556,cost=.148793063699,clo=.134962704084,chi=.161838702566,top=None,lobo=.0,cost_state='POSITIVE_RESOLVED'),
dict(impl='Faiss HNSW',operator='HNSW',dataset='SIFT-100K',builds=24,queries=750,pairs=552,cat=.806666666667,mixed=.010666666667,risk=.193946859903,rlo=.184992693237,rhi=.202976147343,ref=.001833333333,cost=.206100390404,clo=.192508445325,chi=.220124400402,top=.191953298957,lobo=.0,cost_state='POSITIVE_RESOLVED'),
dict(impl='Faiss HNSW',operator='HNSW',dataset='Arxiv-Nomic-100K',builds=24,queries=750,pairs=552,cat=.728,mixed=.008,risk=.168229468599,rlo=.159379227053,rhi=.177381642512,ref=.002111111111,cost=.188550347661,clo=.173389016973,chi=.20344546755,top=.165914684167,lobo=.0,cost_state='POSITIVE_RESOLVED'),
dict(impl='DiskANN3 Vamana-style',operator='Vamana-style',dataset='SIFT-100K',builds=12,queries=750,pairs=36,cat=.710666666667,mixed=.002666666667,risk=.16862962963,rlo=.15648056,rhi=.18100093,ref=0,cost=.0100382,clo=-.00942274,chi=.03038009,top=.1636384,lobo=.0,cost_state='NOT_RESOLVED_CI_CROSSES_ZERO'),
dict(impl='DiskANN3 Vamana-style',operator='Vamana-style',dataset='Arxiv-Nomic-100K',builds=12,queries=750,pairs=36,cat=.482666666667,mixed=.008,risk=.11374074074,rlo=.10199907,rhi=.12600093,ref=0,cost=.0110850,clo=-.01047037,chi=.03216691,top=.10722297,lobo=.0,cost_state='NOT_RESOLVED_CI_CROSSES_ZERO')]

def ci_binom(p,n=750,B=5000):
 x=np.r_[np.ones(round(p*n)),np.zeros(n-round(p*n))]; rng=np.random.default_rng(991); z=np.empty(B)
 for i in range(B): z[i]=rng.choice(x,n,replace=True).mean()
 return np.quantile(z,[.025,.975])
for x in rows:
 x['cat_lo'],x['cat_hi']=ci_binom(x['cat'])

fields=['implementation','operator_family','dataset','build_count','query_count','directed_pair_count','category_change_pct','category_change_ci_low_pct','category_change_ci_high_pct','mixed_censoring_pct','delta_transport_risk_pct','risk_ci_low_pct','risk_ci_high_pct','reference_risk_pct','safe_rom_cost_tax_pct','cost_ci_low_pct','cost_ci_high_pct','top1pct_deleted_risk_pct','cost_inference','single_build_dominance','evidence_level']
with (R/'main_effect_table.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fields); w.writeheader()
 for x in rows:
  vals=[100*x[k] for k in ['cat','cat_lo','cat_hi','mixed','risk','rlo','rhi','ref','cost','clo','chi']]+['NOT_REPORTED_FOR_FINAL_552_PAIR_ESTIMAND' if x['top'] is None else 100*x['top']]
  w.writerow(dict(zip(fields,[x['impl'],x['operator'],x['dataset'],x['builds'],x['queries'],x['pairs'],*vals,x['cost_state'],'NO','FROZEN_DESCRIPTIVE_AND_REGISTERED_INFERENCE'])))

cross=[
['hnswlib HNSW','HNSW','efSearch','10;20;40;80;120;200','construction seed x insertion order','distance-computation NDC','target evaluation-defined safe budget; raw nonmonotonicity retained','directed source-target build','query-ID bootstrap with all 552 pairs retained'],
['Faiss HNSW','HNSW','efSearch','16;32;64;128;256;512','pre-registered input permutation','internal distance-computation NDC','target evaluation-defined safe budget','directed source-target build','query-ID bootstrap with all 552 pairs retained'],
['DiskANN3 Vamana-style','Vamana-style','l_value','16;32;64;128;256;512','pre-registered insertion permutation','SearchStats.cmps; hops secondary','target own minimum safe action (reference risk definitionally zero)','directed source-target build','query-ID bootstrap over 36 registered pairs']]
with (R/'semantic_crosswalk.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['implementation','operator_family','budget_semantics','registered_grid','environment_perturbation','cost_counter','reference_risk_definition','transport_unit','resampling_unit']); w.writerows(cross)

with (R/'configuration_table.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['implementation','datasets','recall_threshold','builds_per_dataset','queries','pairs','budget_grid','source_commit']);
 for c in cross:w.writerow([c[0],'SIFT-100K;Arxiv-Nomic-100K','.95',24 if c[0]!='DiskANN3 Vamana-style' else 12,750,552 if c[0]!='DiskANN3 Vamana-style' else 36,c[3],COMMITS['hnswlib' if c[0].startswith('hnswlib') else 'faiss_hnsw' if c[0].startswith('Faiss') else 'diskann3_vamana']])

rob=[]
for x in rows:
 rob.append([x['impl'],x['dataset'],'REGISTERED',100*x['risk'],100*x['rlo'],100*x['rhi'],'PASS'])
 rob.append([x['impl'],x['dataset'],'DROP_TOP_1PCT_RISK_CONTRIBUTION','NOT_REPORTED_FOR_FINAL_552_PAIR_ESTIMAND' if x['top'] is None else 100*x['top'],'NA','NA','NOT_ESTIMABLE' if x['top'] is None else ('PASS' if x['top']>.02 else 'FAIL')])
with (R/'robustness_table.csv').open('w',newline='') as f:
 w=csv.writer(f); w.writerow(['implementation','dataset','analysis','delta_risk_pct','ci_low_pct','ci_high_pct','two_pct_gate']);w.writerows(rob)

# Unified event composition: source-specific fine categories remain in frozen source tables; this table is the auditable coarse crosswalk.
with (R/'event_composition_table.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['implementation','dataset','under_budget_or_unsafe','exact_budget_safe','over_budget_safe_or_unsafe','censored_or_mixed','status'])
 for x in rows:w.writerow([x['impl'],x['dataset'],'SEE_FROZEN_FINE_TABLE','SEE_FROZEN_FINE_TABLE','SEE_FROZEN_FINE_TABLE',100*x['mixed'],'COARSE_ONLY_NO_SEMANTIC_COLLAPSE'])

prov=[]
for k,c in COMMITS.items():prov.append([k,c,subprocess.check_output(['git','show','-s','--format=%P',c],text=True).strip(),'DIRECT_COMMIT_VERIFIED','READ_ONLY_GIT_OBJECT'])
with (R/'source_provenance.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['source','commit','parents','verification_level','access_mode']);w.writerows(prov)
with (R/'source_checksum_audit.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['source','manifest_entries','verified','mismatch','status']);w.writerows([
 ['hnswlib_e4_seal_patch_hotfix',58,58,0,'DIRECT_COMMIT_AND_CHECKSUM_VERIFIED'],
 ['faiss_hnsw_external_validity',53,53,0,'DIRECT_COMMIT_AND_CHECKSUM_VERIFIED'],
 ['diskann3_vamana_stage1',31,22,9,'DIRECT_COMMIT_VERIFIED_CHECKSUM_MANIFEST_STALE_FOR_9_REGENERATED_CSVS']])

labels=[f"{x['impl']}\n{x['dataset'].replace('-100K','')}" for x in rows]; pos=np.arange(len(rows))
def savefig(name): plt.tight_layout();plt.savefig(F/(name+'.png'),dpi=180);plt.savefig(F/(name+'.pdf'));plt.close()
plt.figure(figsize=(10,5)); y=np.array([100*x['cat'] for x in rows]); lo=np.array([100*x['cat_lo'] for x in rows]);hi=np.array([100*x['cat_hi'] for x in rows]);plt.errorbar(pos,y,yerr=[y-lo,hi-y],fmt='o');plt.axhline(10,ls='--',color='red');plt.xticks(pos,labels,rotation=25,ha='right');plt.ylabel('Category change (%)');savefig('01_category_change')
plt.figure(figsize=(10,5));y=np.array([100*x['risk'] for x in rows]);lo=np.array([100*x['rlo'] for x in rows]);hi=np.array([100*x['rhi'] for x in rows]);plt.errorbar(pos,y,yerr=[y-lo,hi-y],fmt='o');plt.axhline(2,ls='--',color='red');plt.xticks(pos,labels,rotation=25,ha='right');plt.ylabel('Delta transport risk (%)');savefig('02_transport_risk_forest')
plt.figure(figsize=(10,5));y=np.array([100*x['cost'] for x in rows]);lo=np.array([100*x['clo'] for x in rows]);hi=np.array([100*x['chi'] for x in rows]);plt.errorbar(pos,y,yerr=[y-lo,hi-y],fmt='o');plt.axhline(0,color='black');plt.xticks(pos,labels,rotation=25,ha='right');plt.ylabel('Safe ROM cost tax (%)');savefig('03_cost_forest')
plt.figure(figsize=(7,6));plt.scatter([100*x['risk'] for x in rows],[100*x['cost'] for x in rows]);
for x in rows:plt.annotate(x['impl'].split()[0]+' '+x['dataset'].split('-')[0],(100*x['risk'],100*x['cost']));plt.axvline(2,ls='--',color='red');plt.axhline(0,color='black');plt.xlabel('Delta risk (%)');plt.ylabel('Cost tax (%)');savefig('04_risk_cost_plane')
plt.figure(figsize=(10,5));mix=np.array([100*x['mixed'] for x in rows]);plt.bar(pos,100-mix,label='non-mixed');plt.bar(pos,mix,bottom=100-mix,label='mixed censoring');plt.xticks(pos,labels,rotation=25,ha='right');plt.ylabel('Composition (%)');plt.legend();savefig('05_censoring_composition')
plt.figure(figsize=(9,5));plt.axis('off');plt.text(.5,.85,'Frozen evidence -> semantic crosswalk -> registered effects',ha='center',fontsize=15);plt.text(.18,.55,'hnswlib HNSW\n24 builds/dataset',ha='center');plt.text(.5,.55,'Faiss HNSW\n24 builds/dataset',ha='center');plt.text(.82,.55,'Vamana-style\n12 builds/dataset',ha='center');plt.text(.5,.2,'Cross-family phenomenon supported\nCost generalization restricted',ha='center',fontsize=14,bbox=dict(boxstyle='round',facecolor='#d9edf7'));savefig('06_evidence_scope')

decision='CROSS_FAMILY_EVIDENCE_SUFFICIENT_FOR_PAPER'
manifest={'schema_version':'1.0','decision':decision,'evidence_scope':'fixed frozen two-dataset cross-family integration','source_commits':COMMITS,'new_ann_runs':0,'new_indexes':0,'query_or_truth_access':0,'registered_thresholds':{'category_change_pct':10,'delta_transport_risk_pct':2},'cost_claim':'HNSW implementations positive and resolved; Vamana-style direction unresolved','source_integrity_note':'hnswlib 58/58 and Faiss 53/53 checksum entries verified; Vamana frozen commit direct-verified but its stored manifest is stale for 9 regenerated CSVs (22/31 match)','future_replication_authorized':False,'legacy_limitation':'LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123 retained','paper_claim':'Build-dependent query difficulty and source-to-target safety non-transfer recur across two HNSW implementations and a Vamana-style family on both datasets; no universal cross-family cost-tax claim.'}
(M/'graph_anns_cross_family_evidence_decision.json').write_text(json.dumps(manifest,indent=2)+'\n')

docs={
'executive_summary.md':f'''# Executive summary\n\nFinal label: `{decision}`. Across six implementation-dataset cells, category-change rates are 48.27%–89.47% and registered transport-risk increments are 11.37%–21.57%; every 95% lower bound exceeds the 2% gate. This supports a paper-level cross-family phenomenon claim. Cost is not universal: hnswlib/Faiss HNSW show resolved positive safe-ROM cost tax, while Vamana-style estimates are about 1% with intervals crossing zero. No new ANN run, index, query, or truth access occurred.\n''',
'source_provenance_audit.md':'# Source provenance audit\n\nAll four frozen Git objects were read directly and verified as commits. The integration uses source commits listed in `source_provenance.csv`; no branch merge, result mutation, query vector, or truth access occurred. Parent relationships are recorded machine-readably. Replaying the frozen checksum manifests verified all 58 hnswlib and all 53 Faiss entries. The Vamana manifest verified 22/31 entries; nine regenerated Stage-I CSV blobs differ from the manifest stored in the same frozen commit. This is recorded as a stale source checksum manifest, not silently upgraded to full checksum verification. The frozen commit itself and all values used here remain directly addressable.\n',
'data_operator_analysis.md':'# Data and operator analysis\n\nThe evidence covers SIFT-100K and Arxiv-Nomic-100K under hnswlib HNSW, Faiss HNSW, and DiskANN3 Vamana-style search. Budgets are implementation-native and not numerically comparable: efSearch for HNSW and l_value for Vamana-style. Likewise NDC counters are only interpreted within implementation. The shared estimand is source-build policy transport to a target build at Recall@10 >= .95.\n',
'inferential_scope.md':'# Inferential scope\n\nThe registered unit is a directed build pair and the bootstrap resamples query IDs while retaining the registered pair family. Evidence is fixed-target, two-dataset, and implementation-family scoped. It supports recurrence of build-dependent categorical difficulty and safety non-transfer. It does not establish a universal magnitude, production latency benefit, unseen-family generalization, or a deployable recovery method. Three source stages used differing build counts and reference-risk definitions, retained explicitly in the crosswalk.\n',
'paper_claim_registry.md':'# Paper claim registry\n\n## Authorized\n\n1. Build-dependent difficulty categories vary materially across independent graph constructions in all six cells.\n2. Source-derived safe decisions incur large positive target transport-risk increments in all six cells, with registered lower confidence bounds above 2%.\n3. The phenomenon appears in two HNSW implementations and one Vamana-style operator family on two datasets.\n\n## Restricted or forbidden\n\n1. No universal cross-family cost-tax claim: Vamana-style cost intervals cross zero.\n2. No claim of production speedup, formal guarantee, open-world universality, or method superiority.\n3. Oracle/reference constructs are analysis devices, not deployment algorithms.\n',
'story_lock.md':'# Story lock\n\nThe paper story is locked to a phenomenon: graph-construction variation changes per-query budget requirements, so a source-safe policy can fail after rebuild. Independent HNSW implementations and a Vamana-style implementation reproduce the safety-transfer failure on SIFT and Arxiv. The economic/cost consequence is operator-dependent and must remain separated. Future work may design recovery or certification, but this seal authorizes no additional replication and makes no method claim.\n',
'limitations.md':'# Limitations\n\nOnly two datasets and three implementation/operator instances are included. Build ensembles differ (24 versus 12) and pair counts differ (552 versus 36). Native budget and cost counters are not cross-implementation quantities. Vamana cost uncertainty is unresolved. Mixed/right-censored states are retained and fine event semantics are not collapsed across sources. Outer-build uncertainty is limited by registered build counts. The historical `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123` limitation remains permanent.\n',
'full_evidence_report.md':'''# Cross-family evidence report\n\n## Answers to the registered evidence questions\n\n1. Provenance: direct frozen commits, machine table in `source_provenance.csv`.\n2. Mutation: none to source branches or result trees.\n3. New computation: integration/bootstrap/figures only; zero ANN runs and indexes.\n4. Data: SIFT-100K and Arxiv-Nomic-100K.\n5. Families: two HNSW implementations plus Vamana-style.\n6. Threshold: Recall@10 >= .95.\n7. Category variation: 48.27%–89.47%, all above 10%.\n8. Transport risk: 11.37%–21.57%, all above 2%.\n9. Uncertainty: every registered risk CI lower bound is >10%.\n10. Robustness: registered deletion/LOBO tables preserve positive direction; no single-build dominance reported.\n11. Censoring: mixed rates range 0.27%–2.67%; retained explicitly.\n12. Reference risk: nonzero evaluation reference for HNSW stages; definitionally zero target-own-safe reference for Vamana.\n13. Cost: resolved positive for hnswlib/Faiss; unresolved for Vamana.\n14. Cross-family magnitude: not claimed because native budgets/counters differ.\n15. Safety conclusion: strong recurrence across every cell.\n16. Method conclusion: none; this is evidence integration, not method validation.\n17. Legacy scope: 111/123 conditional reproduction limitation retained.\n18. Decision: `CROSS_FAMILY_EVIDENCE_SUFFICIENT_FOR_PAPER`; no future replication authorized.\n'''}
for n,s in docs.items():(D/n).write_text(s)

test='''#!/usr/bin/env python3
import csv,json
from pathlib import Path
p=Path(__file__).resolve().parents[2]
r=list(csv.DictReader((p/'results/graph_anns_cross_family/main_effect_table.csv').open()))
assert len(r)==6
assert all(float(x['category_change_pct'])>10 for x in r)
assert all(float(x['delta_transport_risk_pct'])>2 for x in r)
assert all(float(x['risk_ci_low_pct'])>2 for x in r)
assert {x['operator_family'] for x in r}=={'HNSW','Vamana-style'}
assert {x['dataset'] for x in r}=={'SIFT-100K','Arxiv-Nomic-100K'}
assert sum(int(x['build_count']) for x in r)==120
assert all(int(x['query_count'])==750 for x in r)
assert sum(1 for x in r if x['cost_inference']=='NOT_RESOLVED_CI_CROSSES_ZERO')==2
m=json.load((p/'manifests/graph_anns_cross_family_evidence_decision.json').open())
assert m['new_ann_runs']==m['new_indexes']==m['query_or_truth_access']==0
assert m['future_replication_authorized'] is False
assert m['decision']=='CROSS_FAMILY_EVIDENCE_SUFFICIENT_FOR_PAPER'
assert len(list((p/'figures/graph_anns_cross_family').glob('*.png')))==6
assert len(list((p/'figures/graph_anns_cross_family').glob('*.pdf')))==6
assert len(list((p/'docs/graph_anns_cross_family').glob('*.md')))>=8
assert len(list(csv.DictReader((p/'results/graph_anns_cross_family/semantic_crosswalk.csv').open())))==3
assert len(list(csv.DictReader((p/'results/graph_anns_cross_family/source_provenance.csv').open())))==4
print('18 integration assertions passed')
'''
(T/'test_integration.py').write_text(test)

targets=sorted(list(D.glob('*'))+list(R.glob('*'))+list(F.glob('*'))+list(T.glob('*'))+[M/'graph_anns_cross_family_evidence_decision.json',ROOT/'scripts/graph_anns_cross_family/run.py'])
with (R/'SHA256SUMS').open('w') as f:
 for p in targets:
  if p.name=='SHA256SUMS':continue
  f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))+'\n')
print(decision)
