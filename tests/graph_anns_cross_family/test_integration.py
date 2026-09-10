#!/usr/bin/env python3
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
