#!/usr/bin/env python3
import csv
from pathlib import Path
R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/results/graph_anns_iclr_phase1')
def rows(name):return list(csv.DictReader((R/name).open()))
x=rows('deterministic_rebuild_results.csv');assert len(x)==8
for ds in ('sift_100k','arxiv_nomic_100k'):
 d3=next(r for r in x if r['dataset']==ds and r['regime']=='D3')
 assert d3['builds']=='3' and d3['index_hash_unique']=='1' and d3['diagnostic_hash_unique']=='1'
 assert float(d3['incremental_transport_risk'])==0
 d2=next(r for r in x if r['dataset']==ds and r['regime']=='D2')
 assert d2['builds']=='6' and int(d2['index_hash_unique'])>1 and int(d2['diagnostic_hash_unique'])>1
g=rows('deterministic_rebuild_gate.csv');assert len(g)==2 and all(r['all_pass']=='True' for r in g)
l=rows('phase1c_label.csv');assert l[0]['label']=='DETERMINISTIC_REBUILD_ACTIONABLE_MITIGATION'
print('PHASE1C_ASSERTIONS_PASSED')
