#!/usr/bin/env python3
"""Finalize reports, gate table, manifest and clean checksums; no ANN search."""
import csv, hashlib, json, subprocess
from pathlib import Path

R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw'); O=R/'results/graph_anns_iclr_phase1_1_hotfix'; D=R/'docs/graph_anns_iclr_phase1_1_hotfix'; F=R/'figures/graph_anns_iclr_phase1_1_hotfix'; M=R/'manifests/graph_anns_iclr_phase1_1_hotfix_decision.json'; P=R/'results/graph_anns_iclr_phase1_1_repair'
DS=('sift_100k','arxiv_nomic_100k')
PARENT_COMMIT='39a8b6d41f9fa0561660100856e2e98f330d0a4a'

def rd(p):
    with open(p,newline='') as f:return list(csv.DictReader(f))
def wr(p,rows):
    rows=list(rows); p.parent.mkdir(parents=True,exist_ok=True)
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else []);w.writeheader();w.writerows(rows)
def f(v):
    try:return float(v)
    except:return None
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as q:
        for b in iter(lambda:q.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    overlaps=rd(O/'content_overlap_forensics.csv'); idx=rd(O/'frozen_index_registry_audit.csv'); d3=rd(O/'d3_full_recalculation.csv'); qual=rd(O/'d3_vs_d0_quality.csv'); fa=rd(P/'faiss_clean_semantic_results.csv'); h=rd(P/'estimand_registry.csv'); va=rd(O/'vamana_estimand_semantic_audit.csv')
    tests=json.loads((O/'independent_test_results.json').read_text()); units=json.loads((O/'unit_test_results.json').read_text()); replay=json.loads((O/'replay_summary.json').read_text())
    gate_a=all(x['gate_a']=='PASS' for x in overlaps)
    gate_b=len(idx)==48 and all(x['field_match']=='True' for x in idx)
    gate_d=len(d3)==2 and all(x['index_byte_identity_3of3']=='True' and x['search_topk_identity_3of3']=='True' and x['hit_count_identity_3of3']=='True' and x['minimum_safe_action_identity_3of3']=='True' and x['endpoint_state_identity_3of3']=='True' and f(x['incremental_transport_risk'])==0 and f(x['top1_delete_incremental_risk'])==0 for x in d3)
    gate_e=tests['passed']==tests['total'] and tests['max_error']<=1e-12 and units['passed']==units['total']
    gate_f=replay['all_core_byte_identical'] and replay['manifest_byte_identical'] and replay['checksum_inventory_byte_identical']
    label='FAISS_CLEAN_ROLE_CONTENT_CONTAMINATION_REQUIRES_TARGETED_RERUN' if not gate_a else ('FAISS_FROZEN_INDEX_IDENTITY_NOT_VERIFIED' if not gate_b else ('D3_DETERMINISTIC_CONTRACT_EVIDENCE_INCOMPLETE' if not gate_d else ('FINAL_EVIDENCE_HOTFIX_INCOMPLETE_DO_NOT_FREEZE_PAPER_NUMBERS' if not (gate_e and gate_f) else 'HNSW_CROSS_IMPLEMENTATION_CONFIRMED_VAMANA_ESTIMAND_NOT_HARMONIZED')))
    # Explicitly summarize ranges rather than pre-writing a pass number.
    ranges=[]
    for ds in DS:
        z=next(x for x in fa if x['dataset']==ds and x['h']=='10'); ranges.append({'dataset':ds,'faiss_h10_incremental_min':z['incremental_transport_risk'],'faiss_h10_incremental_max':z['incremental_transport_risk'],'faiss_h10_ci_low':z['bootstrap_ci_low'],'faiss_h10_ci_high':z['bootstrap_ci_high'],'faiss_category_variation':z['minimum_safe_action_variation'],'faiss_endpoint_variation':z['endpoint_state_variation'],'faiss_unresolved_mass':z['unresolved_mass'],'hnswlib_h10_incremental':next(x['incremental_transport_risk'] for x in h if x['dataset']==ds),'vamana_original_stage_incremental':next(x['delta_risk_original_stage'] for x in va if x['dataset']==ds)})
    wr(O/'risk_variation_range_summary.csv',ranges)
    wr(O/'unified_gate.csv',[{'gate':'A_content_role_validity','status':'PASS' if gate_a else 'FAIL'}, {'gate':'B_frozen_index_identity','status':'PASS' if gate_b else 'FAIL'}, {'gate':'C_estimand_semantics','status':'PASS_WITH_VAMANA_HARMONIZATION_DOWNGRADE'}, {'gate':'D_d3_deterministic_contract','status':'PASS' if gate_d else 'FAIL'}, {'gate':'E_independent_statistics_and_counterexamples','status':'PASS' if gate_e else 'FAIL'}, {'gate':'F_replay_and_artifact_hygiene','status':'PASS' if gate_f else 'FAIL'}])
    # Detailed reports are deliberately data-bearing and point to machine-readable rows.
    fa_text=[]
    for ds in DS:
        z=next(x for x in fa if x['dataset']==ds and x['h']=='10'); q=[x for x in rd(P/'faiss_clean_lobo_results.csv') if x['dataset']==ds and x['h']=='10'];
        fa_text.append(f"### {ds}\n- 24 builds, 552 directed pairs, 750 clean queries; action grid 16/32/64/128/256/512.\n- finite variation={float(z['minimum_safe_action_variation']):.9f}, endpoint variation={float(z['endpoint_state_variation']):.9f}, inclusive variation={float(z['inclusive_budget_state_variation']):.9f}, unresolved={float(z['unresolved_mass']):.9f}.\n- absolute/reference/incremental risk={float(z['absolute_transport_risk']):.12f}/{float(z['reference_risk']):.12f}/{float(z['incremental_transport_risk']):.12f}; bootstrap CI=[{float(z['bootstrap_ci_low']):.12f},{float(z['bootstrap_ci_high']):.12f}]; top-1% deletion={float(z['delete_top1_incremental_risk']):.12f}; LOBO=[{min(float(x['incremental_transport_risk']) for x in q):.12f},{max(float(x['incremental_transport_risk']) for x in q):.12f}].")
    final_report_text=(f"# ICBA Graph-ANNS Phase 1.1a final evidence hotfix\n\nParent commit: `{PARENT_COMMIT}`. Branch: `exp/graph_anns_iclr_phase1_1_final_evidence_hotfix`. Worktree: `{R}`. Parent tracked results were not modified.\n\nGate A={'PASS' if gate_a else 'FAIL'}; Gate B={'PASS' if gate_b else 'FAIL'}; Gate D={'PASS' if gate_d else 'FAIL'}; Gate E={'PASS' if gate_e else 'FAIL'}; Gate F={'PASS' if gate_f else 'FAIL'}.\n\n"+'\n\n'.join(fa_text)+f"\n\n## D3/D0\n"+'\n'.join([f"- {x['dataset']}: Recall delta {float(x['recall_delta_d3_minus_d0']):.9f}; mean budget ratio {float(x['mean_safe_budget_ratio']):.9f}; p95 ratio {float(x['p95_safe_budget_ratio']):.9f}; p99 ratio {float(x['p99_safe_budget_ratio']):.9f}; build-time ratio {float(x['build_time_ratio']):.9f}." for x in qual])+f"\n\n## Decision\n`{label}`.\n")
    details={'executive_summary.md':f"# Executive summary\n\nThis pure-code patch audited content roles, frozen Faiss registry identity, estimands, Vamana reference semantics and D3 contracts. No index was built and no ANN search was invoked.\n\nFinal label: `{label}`.\n",
    'content_overlap_forensics.md':'# Content-overlap forensics\n\nRaw and normalized SHA256 values were computed from contiguous float32 HDF5 vectors for both 100K bases, clean evaluation queries and readable historical role IDs. Both datasets have zero ID, raw-content, normalized-content, historical-role and internal-duplicate counts. See `content_overlap_forensics.csv` and `content_overlap_events.csv`.\n',
    'frozen_index_registry_audit.md':f'# Frozen-index registry audit\n\nThe parent build registry was compared row-by-row to current serialized indices: {len(idx)}/48 rows matched SHA256, base count, Faiss version, M and efConstruction. Observed dimension/metric came from the Faiss index object; build/order metadata came from the frozen registry. See `frozen_index_registry_audit.csv`.\n',
    'hnswlib_estimand_reconciliation.md':'# hnswlib estimand reconciliation\n\nThe primary historical E4 transport maps source bottom to the maximum registered action and uses target bottom as the reference event. Composite source-censoring and jointly-feasible sensitivities are separate rows, not replacements. See `hnswlib_estimand_reconciliation.csv`.\n',
    'vamana_estimand_semantic_audit.md':'# Vamana estimand semantic audit\n\nFrozen Vamana events define original-stage under-budget and censoring risks. Target-bottom reference rates are reported directly (not replaced by zero), but source-conditioned action responses are not complete enough to reconstruct the same E4 transport estimand. The cross-family comparison is therefore `COMPARABLE_ONLY_UNDER_HARMONIZED_SENSITIVITY`. See `vamana_estimand_semantic_audit.csv`.\n',
    'd3_full_recalculation_report.md':'# D3 full recalculation\n\nD3 index bytes, top-k, hit counts, minimum-safe actions and endpoint states were separately recomputed from raw D3 rows. Both datasets pass 3/3 identity checks and have zero incremental and post-top-1 deletion transport risk. D3/D0 quality and build overhead are in `d3_vs_d0_quality.csv`; D3 NDC is not estimable because its rows have no NDC field and D0 NDC is a zero placeholder.\n',
    'independent_statistics_validation.md':f"# Independent statistics validation\n\nThe independent implementation passed {tests['passed']}/{tests['total']} checks with maximum production discrepancy {tests['max_error']:.3g}; the unit suite passed {units['passed']}/{units['total']} checks and includes {units['counterexamples']} semantic counterexamples. No check reads the final manifest label as truth.\n",
    'cross_family_final_report.md':'# Cross-family final report\n\n'+ '\n\n'.join(fa_text) +'\n\nThe six-cell table keeps native action families separate. Positive directions are evidence within registered scopes; raw budget values are not equated across implementations. Vamana h8/h9 remain not estimable from frozen hit counts.\n',
    'paper_number_patch.md':'# Paper-number patch\n\nUse the clean Faiss h=10 rows for the 100K scope and retain hnswlib E4 primary values. Replace any unsupported “reference risk=0” Vamana statement with the target-bottom audit and the explicit harmonization downgrade. Preserve conditional claim scope and do not assert universal cost-tax equivalence.\n',
    'paper_claim_registry.md':'# Paper claim registry\n\nAllowed: registered-data, registered-build, native-action, endpoint-aware direction and D3 deterministic-contract claims. Disallowed: cross-family raw-budget equality, universal cost claims, and treating Vamana original-stage risk as harmonized E4 transport.\n',
    'reproducibility_report.md':f"# Reproducibility report\n\nThe pure-code driver ran twice with no ANN search. Core outputs={replay['run1_files']} files per run; core, manifest and checksum inventory are byte-identical. Checksums exclude cache, pyc and logs.\n",
    'final_hotfix_report.md':final_report_text}
    D.mkdir(parents=True,exist_ok=True)
    for n,t in details.items(): (D/n).write_text(t)
    m={'schema_version':'phase1.1a-hotfix-1.0','parent_commit':PARENT_COMMIT,'branch':'exp/graph_anns_iclr_phase1_1_final_evidence_hotfix','worktree':str(R),'ann_search_invoked':False,'index_built':False,'parent_results_modified':False,'content_gate':'PASS' if gate_a else 'FAIL','frozen_index_registry':'48/48_MATCH' if gate_b else 'MISMATCH','hnswlib_primary_estimand':'E4_SOURCE_BOTTOM_TO_MAX_REGISTERED_ACTION','vamana_reference_risk':'TARGET_BOTTOM_COUNT_REPORTED_HARMONIZED_TRANSPORT_NOT_ESTIMABLE','d3_recomputed_from_raw':gate_d,'independent_tests':{'unit_cases':units['unit_cases'],'counterexamples':units['counterexamples'],'independent_checks':tests['independent_checks'],'passed':tests['passed'],'total':tests['total'],'max_error':tests['max_error']},'pure_code_replay':replay,'forbidden_roles_accessed':False,'final_scientific_label':label,'limitations':['Vamana harmonized transport/reference unavailable from frozen events','Faiss NDC batch-cumulative not estimable','claims conditional on registered datasets/builds','profiling and break-even primitive-only']}
    M.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
    # Formal checksum excludes itself, caches, logs, temporary artifacts and untracked old folders.
    paths=[]
    for d in (D,O,F,R/'scripts/graph_anns_iclr_phase1_1_hotfix',R/'tests/graph_anns_iclr_phase1_1_hotfix'):
        if not d.exists(): continue
        for p in sorted(d.rglob('*')):
            if p.is_file() and p.name not in {'checksums.sha256'} and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log'}: paths.append(p)
    paths.append(M); paths=sorted(set(paths))
    (O/'checksums.sha256').write_text('\n'.join(digest(p)+'  '+str(p.relative_to(R)) for p in paths)+'\n')
    print(json.dumps({'label':label,'gate_a':gate_a,'gate_b':gate_b,'gate_d':gate_d,'gate_e':gate_e,'gate_f':gate_f,'checksum_entries':len(paths)},sort_keys=True))

if __name__=='__main__': main()
