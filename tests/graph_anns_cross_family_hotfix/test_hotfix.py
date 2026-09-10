#!/usr/bin/env python3
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
