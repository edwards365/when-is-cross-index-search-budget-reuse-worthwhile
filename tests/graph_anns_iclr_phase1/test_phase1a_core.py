#!/usr/bin/env python3
import csv
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'results/graph_anns_iclr_phase1'
s=list(csv.DictReader((p/'cross_family_semantic_table.csv').open()))
w=list(csv.DictReader((p/'workpoint_sensitivity.csv').open()))
u=list(csv.DictReader((p/'unresolved_mass.csv').open()))
t=list(csv.DictReader((p/'tail_cost_summary.csv').open()))
assert len(s)==6 and len(w)==18 and len(u)==6 and len(t)==6
assert {(x['implementation'],x['dataset']) for x in s}=={(x['implementation'],x['dataset']) for x in u}
expected={
 ('hnswlib HNSW','sift_100k'):.215734299517,
 ('hnswlib HNSW','arxiv_nomic_100k'):.17120531401,
 ('Faiss HNSW','sift_100k'):.193946859903,
 ('Faiss HNSW','arxiv_nomic_100k'):.168229468599,
 ('DiskANN3/Vamana-style','sift_100k'):.16862962963,
 ('DiskANN3/Vamana-style','arxiv_nomic_100k'):.113740740741}
for x in s:
 assert abs(float(x['incremental_transport_risk'])-expected[(x['implementation'],x['dataset'])])<1e-10
 assert int(x['queries'])==750 and int(x['pairs']) in (36,552)
 assert float(x['A1_category_variation'])>0 and float(x['jointly_feasible_violation'])>0
for x in w:
 assert float(x['incremental_transport_risk'])>0
 assert float(x['ci_low'])>0
 assert float(x['ci_high'])>float(x['ci_low'])
 assert x['tau'] in ('0.9','0.95','0.99')
assert all(float(x['target_unresolved_mass'])>=0 for x in u)
assert all(int(x['safe_pair_query_units'])>0 for x in t)
print('Phase1A core: 18 deterministic assertions passed')
