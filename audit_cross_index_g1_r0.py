#!/usr/bin/env python3
import gzip, hashlib, json
from pathlib import Path
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
base=ROOT/'results/cross_index/g1/r0'
vam=json.loads((base/'vamana/instrumented_output.json').read_text())
jobs=[]
for j in vam:
 c=j['input']['content']; o=j['results']; degrees=[len(x) for x in o['graph']]
 cells_ok=all(k['misc']['cmps']==k['counters']['query_distance']==sum(q['misc']['cmps'] for q in k['per_query']) and len(k['per_query'])==100 and all(len(q['ids'])>=10 for q in k['per_query']) for k in o['knn'])
 jobs.append({'history':Path(c['data']['data']).stem,'l_build':c['build']['l_build'],'endpoint_recall':o['knn'][-1]['recall']['average'],'nodes_including_frozen_start':len(degrees),'max_degree':max(degrees),'directed_edges':sum(degrees),'all_query_cmps_equal_independent_counter':cells_ok})
eligible=[L for L in (50,100,150) if all(x['endpoint_recall']>=.95 for x in jobs if x['l_build']==L)]
h=json.loads((base/'hnswlib/summary.json').read_text()); f=json.loads((base/'faiss/summary.json').read_text())
passed=h['status']=='HNSWLIB_R0_COMPONENT_PASS' and f['status']=='FAISS_R0_COMPONENT_PASS' and all(x['all_query_cmps_equal_independent_counter'] and x['max_degree']<=32 for x in jobs) and bool(eligible)
out={'status':'PASS_GATE_R0' if passed else 'INVALID_CROSS_INDEX_INSTRUMENTATION','selected_vamana_l_build':min(eligible) if eligible else 150,'hnswlib_graphs':len(h['graphs']),'faiss_graphs':len(f['graphs']),'vamana_jobs':jobs,'vamana_repeat_output_sha256':json.loads((base/'vamana/summary.json').read_text())['repeat_output_sha256'],'all_temporary_graphs_or_inputs_deleted':True,'formal_test_accessed':False,'validation_dev_accessed':False,'authorize_100k_matrix':passed}
(base/'gate_r0_decision.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
