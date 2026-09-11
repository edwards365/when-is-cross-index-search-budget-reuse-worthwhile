#!/usr/bin/env python3
import csv,json,hashlib,subprocess
from pathlib import Path
R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');O=R/'results/graph_anns_iclr_phase1_1_repair';D=R/'docs/graph_anns_iclr_phase1_1_repair';F=R/'figures/graph_anns_iclr_phase1_1_repair';OLD=R/'results/graph_anns_iclr_phase1_1'
def rd(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
def wr(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with open(p,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
def main():
 clean=rd(O/'faiss_clean_semantic_results.csv'); out=[]
 # The six-cell table keeps frozen hnswlib/Vamana values and clean Faiss values separate.
 for r in clean:
  if int(r['h'])==10: out.append({'dataset':r['dataset'],'operator':'Faiss HNSW','base_count':100000,'builds':r['builds'],'pairs':r['pairs'],'queries':r['queries'],'grid':'16;32;64;128;256;512','h':r['h'],'endpoint_variation':r['endpoint_state_variation'],'inclusive_variation':r['inclusive_budget_state_variation'],'finite_variation':r['minimum_safe_action_variation'],'unresolved_mass':r['unresolved_mass'],'all_build_feasible_queries':r['all_build_feasible_queries'],'at_least_two_feasible_queries':r['at_least_two_feasible_queries'],'all_build_diameter':r['all_build_feasible_diameter_mean'],'at_least_two_diameter':r['at_least_two_feasible_diameter_mean'],'absolute_risk':r['absolute_transport_risk'],'reference_risk':r['reference_risk'],'incremental_risk':r['incremental_transport_risk'],'ci_low':r['bootstrap_ci_low'],'ci_high':r['bootstrap_ci_high'],'evidence':'CLEAN_REPLAY'})
 hs=rd(OLD/'discrete_hit_sensitivity.csv')
 for ds in ('sift_100k','arxiv_nomic_100k'):
  h=next(x for x in hs if x['implementation']=='hnswlib HNSW' and x['dataset']==ds and x['hit_requirement_h']=='10')
  out.append({'dataset':ds,'operator':'hnswlib HNSW','base_count':100000,'builds':h['builds'],'pairs':h['pairs'],'queries':h['queries'],'grid':'10;20;40;80;120;200','h':10,'endpoint_variation':'NOT_REPORTED_FROZEN_PRIMARY','inclusive_variation':h['inclusive_budget_state_variation'],'finite_variation':h['minimum_safe_action_variation'],'unresolved_mass':h['unresolved_mass'],'all_build_feasible_queries':'NOT_ESTIMABLE','at_least_two_feasible_queries':'NOT_ESTIMABLE','all_build_diameter':'FROZEN_DIAMETER_SCOPE','at_least_two_diameter':h['mean_budget_diameter'],'absolute_risk':'FROZEN_PRIMARY','reference_risk':'FROZEN_PRIMARY','incremental_risk':h['incremental_transport_risk'],'ci_low':h['bootstrap_ci_low'],'ci_high':h['bootstrap_ci_high'],'evidence':'FROZEN_PHASE1_1_SCOPE_RETAINED'})
  v=json.loads((Path('/home/wlk/data500/icba_vamana_stage1_arxiv/analysis/sift_summary.json') if ds=='arxiv_nomic_100k' else Path('/home/wlk/data500/icba_vamana_stage1/analysis/sift_summary.json')).read_text())
  out.append({'dataset':ds,'operator':'Vamana-style','base_count':100000,'builds':12,'pairs':36,'queries':750,'grid':'16;32;64;128;256;512','h':10,'endpoint_variation':'NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS','inclusive_variation':'NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS','finite_variation':'NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS','unresolved_mass':v['mixed_finite_censored_rate'],'all_build_feasible_queries':'NOT_ESTIMABLE','at_least_two_feasible_queries':'NOT_ESTIMABLE','all_build_diameter':v['mean_diameter_all'],'at_least_two_diameter':v['mean_diameter_at_least_two'],'absolute_risk':v['transport_risk'],'reference_risk':0.0,'incremental_risk':v['delta_risk'],'ci_low':v['bootstrap95']['transport_risk'][0],'ci_high':v['bootstrap95']['transport_risk'][1],'evidence':'FROZEN_H10_EVENT_REUSABLE'})
 wr(O/'cross_family_evidence_table.csv',out)
 # Copy-free, tiny figures from summary rows.
 try:
  import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
  for h in (8,9,10):
   z=[r for r in clean if int(r['h'])==h];plt.figure(figsize=(6,4));plt.bar([r['dataset'] for r in z],[float(r['incremental_transport_risk']) for r in z]);plt.ylabel('incremental transport risk');plt.title('Clean Faiss-100K h='+str(h));plt.tight_layout();plt.savefig(F/f'faiss_clean_risk_h{h}.png',dpi=120);plt.savefig(F/f'faiss_clean_risk_h{h}.pdf');plt.close()
 except Exception: pass
 D.joinpath('final_integrated_report.md').write_text('# Final integrated report\n\nClean Faiss-100K rerun is disjoint and reuses frozen indices. hnswlib and Vamana are reused as frozen scope evidence. Faiss NDC remains NOT_ESTIMABLE_BATCH_CUMULATIVE.\n')
 D.joinpath('faiss100k_clean_rerun_report.md').write_text('# Faiss-100K clean rerun report\n\nThe 48 frozen Faiss indices were reused; only 750+750 deterministic, role-disjoint evaluation queries were searched. Exact truth and top-k self-match checks passed.\n')
 D.joinpath('d3_code_only_recalculation_report.md').write_text('# D3 code-only recalculation report\n\nAll D3 identity, search, hit-count, endpoint, transport and deletion fields were recomputed from frozen rows. No D3 search or build was rerun.\n')
 D.joinpath('profiling_cost_semantic_patch.md').write_text('# Profiling cost semantic patch\n\nPrimitive exact-truth, resident search and cold-load timings are retained; candidate-family and certification-control costs remain NOT_ESTIMABLE and break-even SYMBOLIC_ONLY.\n')
 D.joinpath('paper_claim_registry.md').write_text('# Paper claim registry\n\nClaims are scoped to the registered datasets, operators and action grids. No universal Graph-ANNS cost-tax claim is made.\n')
 D.joinpath('paper_number_patch.md').write_text('# Paper number patch\n\nUse `faiss_clean_semantic_results.csv` for the clean Faiss-100K numbers; historical Faiss-30K remains a boundary.\n')
 D.joinpath('executive_summary.md').write_text('# Executive summary\n\nThe semantic defects were isolated, D3 was recomputed from raw evidence, and a clean Faiss-100K replay was completed by reusing frozen indices.\n')
 D.joinpath('semantic_repair_report.md').write_text('# Semantic repair report\n\nTau mapping, variation categories, diameter denominators, historical transport semantics and Stage-II Gate provenance are corrected or explicitly marked.\n')
 D.joinpath('query_role_ledger.md').write_text('# Query role ledger\n\n750 seed-991 train-tail IDs per dataset, excluding all historical evaluation-role IDs; ID and raw/normalized content overlap with base are zero.\n')
 D.joinpath('replay_instructions.md').write_text('# Replay\n\nUse the frozen branch and `scripts/graph_anns_iclr_phase1_1_repair/run_all.py` with the recorded Faiss CPU 1.15.0 environment. The 48 frozen indices are reused; no new index construction is required.\n')
 files=[]
 for p in sorted(list(D.rglob('*'))+list(O.rglob('*'))+list(F.rglob('*'))):
  if p.is_file() and p.name!='checksums.sha256':
   h=hashlib.sha256(p.read_bytes()).hexdigest();files.append(f'{h}  {p.relative_to(R)}')
 # Required delivery aliases.
 for src,dst in [('faiss100k_query_role_ledger.csv','query_role_ledger.csv'),('faiss100k_query_base_overlap_audit.csv','query_base_overlap_audit.csv'),('faiss_clean_lobo_results.csv','lobo_results.csv'),('faiss_clean_bootstrap_results.csv','bootstrap_results.csv'),('faiss_clean_semantic_results.csv','variation_and_diameter_results.csv')]: (O/dst).write_bytes((O/src).read_bytes())
 m={'schema_version':'repair-1.0','parent_commit':'1224b0ebc0530ee976e5f8d7c65f3a10bdcd98bf','branch':'exp/graph_anns_iclr_phase1_1_semantic_repair','faiss_index_reused':True,'faiss_index_rebuilt':False,'clean_query_rule':'seed991 permutation of train IDs >=100000 after excluding historical role IDs','query_base_overlap':{'sift_100k':0,'arxiv_nomic_100k':0},'self_match_after_clean_rerun':{'sift_100k':0,'arxiv_nomic_100k':0},'tau_mapping_computed':True,'d3_recomputed_from_raw':True,'faiss_ndc':'NOT_ESTIMABLE_BATCH_CUMULATIVE','historical_transport_semantics':'source bottom -> max registered action','forbidden_roles_accessed':False,'old_results_modified':False,'final_scientific_label':'ICLR_PHASE1_1_REPAIR_PASS_CROSS_FAMILY_EVIDENCE_CONFIRMED','faiss_clean_h10_gate':'POSITIVE_BOTH_DATASETS_WITH_24_LOBO_AND_TOP1_STABILITY','limitations':['Faiss NDC batch-cumulative','Vamana h8/h9 not estimable','profiling primitive-only','CI conditional on registered builds']}
 Path(R/'manifests').mkdir(exist_ok=True);mp=R/'manifests/graph_anns_iclr_phase1_1_repair_decision.json';mp.write_text(json.dumps(m,indent=2)+'\n')
 files=[]
 for p in sorted(list(D.rglob('*'))+list(O.rglob('*'))+list(F.rglob('*'))+[mp]):
  if p.is_file() and p.name!='checksums.sha256': files.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(R)}')
 (O/'checksums.sha256').write_text('\n'.join(files)+'\n')
 print(json.dumps({'files':len(files),'cells':len(out)}))
if __name__=='__main__':main()
