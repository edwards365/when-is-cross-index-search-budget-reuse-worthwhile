#!/usr/bin/env python3
import csv
import gzip
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/icba_theory_elevation/z1_field_audit.csv'
headers={}
for impl in ('hnswlib','faiss','vamana'):
    p=next((ROOT/'results/cross_index/g1/main'/impl).glob('*.csv.gz'))
    with gzip.open(p,'rt',newline='') as f: headers[impl]=set(next(csv.reader(f)))

specs=[
 ('exact_ndc','per_query_budget','runtime distance counter','low','integer counter','DEPLOYABLE_EXISTING'),
 ('returned_top10_ids','per_query_budget','native result IDs','low','ordered result identities','DEPLOYABLE_EXISTING'),
 ('returned_top10_distances','per_query_budget','native result distances','low','distance vector','DEPLOYABLE_EXISTING'),
 ('kth_result_distance','derived_per_query_budget','returned_top10_distances','low','distance scale tail','DEPLOYABLE_EXISTING'),
 ('first_second_distance_gap','derived_per_query_budget','returned_top10_distances','low','local distance gap','DEPLOYABLE_EXISTING'),
 ('query_latency_ns','per_query_budget','runtime clock','low','wall-clock proxy','DEPLOYABLE_EXISTING'),
 ('entry_point','per_query_budget','index runtime metadata','none','entry node identifier','DEPLOYABLE_EXISTING'),
 ('max_level','per_query_budget','index metadata','none','hierarchy depth','DEPLOYABLE_EXISTING'),
 ('visited_expansions','per_query_budget','search instrumentation','medium','expanded-node count','DEPLOYABLE_REQUIRES_INSTRUMENTATION'),
 ('frontier_size','per_checkpoint','search instrumentation','medium','frontier cardinality','DEPLOYABLE_REQUIRES_INSTRUMENTATION'),
 ('candidate_queue_size','per_checkpoint','search instrumentation','medium','candidate heap occupancy','DEPLOYABLE_REQUIRES_INSTRUMENTATION'),
 ('top_candidate_heap','per_checkpoint','search instrumentation','medium','top-candidate state','DEPLOYABLE_REQUIRES_INSTRUMENTATION'),
 ('checkpoint_churn','derived_per_checkpoint','repeated returned IDs','low','result-set turnover','DEPLOYABLE_EXISTING'),
 ('returned_neighbor_stability','derived_per_checkpoint','returned_top10_ids','low','set/rank stability','DEPLOYABLE_EXISTING'),
 ('fixed_probe_marginal_work','derived_per_checkpoint','exact_ndc','low','incremental distance computations','DEPLOYABLE_EXISTING'),
 ('recall_at_10','per_query_budget','exact target truth','high','quality label','LABEL_DEPENDENT'),
 ('stable_sufficient_budget','derived_per_query','complete labeled source curve','high','source action oracle','SOURCE_ORACLE'),
]
rows=[]
for field,gran,source,cost,semantic,default in specs:
 for impl in ('hnswlib','faiss','vamana'):
  base=field in headers[impl]
  if field in ('kth_result_distance','first_second_distance_gap'):
   base='returned_top10_distances' in headers[impl]
  elif field in ('checkpoint_churn','returned_neighbor_stability'):
   base='returned_top10_ids' in headers[impl]
  elif field=='fixed_probe_marginal_work': base='exact_ndc' in headers[impl]
  if default in ('LABEL_DEPENDENT','SOURCE_ORACLE'): status=default
  elif base: status='DEPLOYABLE_EXISTING'
  elif default=='DEPLOYABLE_REQUIRES_INSTRUMENTATION': status=default
  else: status='NOT_AVAILABLE'
  rows.append({'field':field,'implementation':impl,'dataset':'SIFT/Arxiv/GloVe frozen schema',
   'available_per_query':gran.startswith('per_query') or 'derived_per_query' in gran,
   'available_per_budget':'budget' in gran or 'checkpoint' in gran,
   'requires_ground_truth':status in ('LABEL_DEPENDENT','SOURCE_ORACLE'),
   'available_online':status in ('DEPLOYABLE_EXISTING','DEPLOYABLE_REQUIRES_INSTRUMENTATION'),
   'instrumentation_cost':cost,'storage_cost':'low_to_medium','semantic_equivalent_across_implementations':field in ('exact_ndc','returned_top10_ids','fixed_probe_marginal_work','returned_neighbor_stability'),
   'current_provenance':source,'status':status})
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
assert any(r['implementation']=='hnswlib' and r['field']=='returned_top10_distances' and r['status']=='DEPLOYABLE_EXISTING' for r in rows)
assert all(r['status']=='NOT_AVAILABLE' for r in rows if r['field']=='returned_top10_distances' and r['implementation'] in ('faiss','vamana'))
print({'rows':len(rows),'hnswlib_existing':sum(r['implementation']=='hnswlib' and r['status']=='DEPLOYABLE_EXISTING' for r in rows)})
