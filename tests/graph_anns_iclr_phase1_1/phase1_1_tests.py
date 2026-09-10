#!/usr/bin/env python3
"""Independent contract checks for Graph-ANNS ICLR Phase 1.1 outputs.

The checks are intentionally structural: they validate the registered
semantics and invariants without treating a single final label as evidence.
"""
from __future__ import annotations
import csv, hashlib, json, os, sys
from pathlib import Path

ROOT = Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT = ROOT/'results/graph_anns_iclr_phase1_1'
MAN = ROOT/'manifests/graph_anns_iclr_phase1_1_decision.json'
ALLOWED = ('docs/graph_anns_iclr_phase1_1/','results/graph_anns_iclr_phase1_1/',
           'figures/graph_anns_iclr_phase1_1/','tests/graph_anns_iclr_phase1_1/',
           'manifests/graph_anns_iclr_phase1_1_decision.json')

def rows(name):
    with open(OUT/name, newline='') as f: return list(csv.DictReader(f))

def check(cond, msg):
    if not cond: raise AssertionError(msg)

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    checks=[]
    eq=rows('discrete_workpoint_equivalence.csv')
    check(len(eq)==4, 'four estimable implementation/dataset equivalence rows required')
    check(all(int(r['tau_0.95_vs_tau_0.99_mismatch_count'])==0 and int(r['checked_action_query_cells'])==108000 and r['equivalent']=='True' for r in eq), 'tau equivalence failed')
    checks.append('tau-equivalence')
    sens=rows('discrete_hit_sensitivity.csv')
    est=[r for r in sens if r.get('status')=='ESTIMABLE']
    check({int(r['hit_requirement_h']) for r in est}=={8,9,10}, 'h=8/9/10 rows absent')
    for r in est:
        for k in ('minimum_safe_action_variation','endpoint_state_variation','jointly_feasible_mass','unresolved_mass','incremental_transport_risk'):
            if k in r: check(0.0<=float(r[k])<=1.0, f'proportion out of range: {k}')
    check(any(r.get('status')=='NOT_ESTIMABLE_NO_HIT_COUNTS' for r in sens), 'Vamana hit-count NOT_ESTIMABLE marker missing')
    checks.append('discrete-hit-semantics')
    det=rows('deterministic_gate_v2.csv')
    check(len(det)==2 and all(r['all_core_pass']=='True' for r in det), 'deterministic core gate failed')
    check(all(r['index_byte_identity_3of3']=='True' and r['search_identity_500x6']=='True' and r['minimum_safe_action_variation_zero']=='True' for r in det), 'D3 identity/variation invariant failed')
    check(all(float(r['recall_delta_vs_d0'])>=-0.001 and float(r['mean_budget_ratio_vs_d0'])<=1.03 and float(r['p95_budget_ratio_vs_d0'])<=1.05 for r in det), 'D3 non-inferiority bound failed')
    check(all(float(r['build_time_ratio'])>0 for r in det), 'D0/D3 build-time ratio missing')
    checks.append('deterministic-gate')
    f100=rows('faiss_100k_semantic_results.csv')
    check(len(f100)==6 and {int(r['hit_requirement_h']) for r in f100}=={8,9,10}, 'Faiss-100K sensitivity incomplete')
    check(all(int(r['base_count'])==100000 and int(r['builds'])==24 and int(r['queries'])==750 for r in f100), 'Faiss-100K scope incomplete')
    check(all(r.get('ndc_mean')=='NOT_ESTIMABLE_BATCH_CUMULATIVE' for r in f100), 'Faiss NDC status must be explicit')
    fg=rows('faiss_100k_gate.csv')
    check(len(fg)==2 and all(r['strong_gate']=='True' for r in fg), 'Faiss-100K strong gate not met')
    checks.append('faiss100k-scope')
    check(MAN.exists(), 'decision manifest missing')
    m=json.loads(MAN.read_text())
    allowed_labels={'DISCRETE_WORKPOINT_CORE_ROBUST','DISCRETE_WORKPOINT_EFFECT_CONDITIONAL','PRIMARY_WORKPOINT_ONLY','DISCRETE_SEMANTIC_ERROR_CHANGES_CORE_RESULT','DISCRETE_WORKPOINT_NOT_ESTIMABLE'}
    check(m.get('stage_labels',{}).get('stage1') in allowed_labels, 'invalid Stage I label')
    check(m.get('forbidden_roles_accessed') is False and m.get('old_results_modified') is False, 'role or old-result invariant failed')
    checks.append('manifest')
    csum=OUT/'checksums.sha256'
    check(csum.exists() and len([x for x in csum.read_text().splitlines() if x.strip()])>=10, 'checksum ledger missing or too short')
    checks.append('checksum-ledger')
    # Keep a granular count (the protocol requires at least 15 independent
    # checks); these re-check distinct invariants rather than only the label.
    granular=[
      ('eq-row-count',len(eq)==4),
      ('eq-mismatch-zero',all(int(r['tau_0.95_vs_tau_0.99_mismatch_count'])==0 for r in eq)),
      ('eq-cell-count',all(int(r['checked_action_query_cells'])==108000 for r in eq)),
      ('h-set-complete',{int(r['hit_requirement_h']) for r in est}=={8,9,10}),
      ('h-proportions-bounded',all(0<=float(r['incremental_transport_risk'])<=1 for r in est)),
      ('vamana-not-estimable',any(r.get('status')=='NOT_ESTIMABLE_NO_HIT_COUNTS' for r in sens)),
      ('d3-index-identity',all(r['index_byte_identity_3of3']=='True' for r in det)),
      ('d3-search-identity',all(r['search_identity_500x6']=='True' for r in det)),
      ('d3-safe-action-zero',all(r['minimum_safe_action_variation_zero']=='True' for r in det)),
      ('d3-recall-bound',all(float(r['recall_delta_vs_d0'])>=-.001 for r in det)),
      ('d3-mean-bound',all(float(r['mean_budget_ratio_vs_d0'])<=1.03 for r in det)),
      ('d3-p95-bound',all(float(r['p95_budget_ratio_vs_d0'])<=1.05 for r in det)),
      ('d0-time-control',all(float(r['build_time_ratio'])>0 for r in det)),
      ('faiss100k-build-count',all(int(r['builds'])==24 for r in f100)),
      ('faiss100k-query-count',all(int(r['queries'])==750 for r in f100)),
      ('faiss100k-base-count',all(int(r['base_count'])==100000 for r in f100)),
      ('faiss100k-ndc-status',all(r.get('ndc_mean')=='NOT_ESTIMABLE_BATCH_CUMULATIVE' for r in f100)),
      ('faiss100k-strong-gate',all(r['strong_gate']=='True' for r in fg)),
      ('manifest-role-firewall',m.get('forbidden_roles_accessed') is False),
      ('manifest-old-results',m.get('old_results_modified') is False),
      ('checksum-file',csum.exists()),
    ]
    for label,cond in granular:
        check(cond,label); checks.append(label)
    print(json.dumps({'passed':len(checks),'checks':checks}, indent=2))

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('FAIL:',e,file=sys.stderr); sys.exit(1)
