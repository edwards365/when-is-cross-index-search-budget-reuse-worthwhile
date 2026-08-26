#!/usr/bin/env python3
"""Freeze validation source IDs without reading query-vector members."""
import hashlib,json
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k'); SEED=20260926; N=2000
src=json.load(open(ROOT/'manifests/hardness_portability_100k/data_query_truth_manifest.json'))
records=[]
for offset,x in enumerate(sorted(src['datasets'],key=lambda z:z['dataset'])):
    old=set(map(int,np.load(ROOT/x['source_ids_path']).tolist()))
    eligible=np.array([i for i in range(100000,int(x['train_count'])) if i not in old],dtype=np.int64)
    rng=np.random.default_rng(SEED+offset); ids=rng.choice(eligible,size=N,replace=False)
    raw=ids.astype('<i8').tobytes(); digest=hashlib.sha256(raw).hexdigest()
    records.append({'dataset':x['dataset'],'source_path':x['source_path'],'source_sha256':x['source_sha256'],'source_member':'train','formal_test_member':'test (disjoint HDF5 member)','selection_seed':SEED+offset,'eligible_rule':'train source id >=100000 excluding all frozen 100K scale-dev source IDs','query_count':N,'calibration_count':1000,'audit_count':1000,'calibration_source_ids':ids[:1000].tolist(),'audit_source_ids':ids[1000:].tolist(),'source_ids_le_i64_sha256':digest})
out={'schema_version':1,'status':'FROZEN_BEFORE_VALIDATION_MEMBER_READ','protocol':'Adaptive ANN Has a Rebuild Tax / Gate C','generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'datasets':records,'graph_seeds':[43,59,71],'histories':['random','natural_source_order','cluster_block_order'],'M':16,'ef_construction':100,'k':10,'ef_grid':[10,16,24,32,48,64,96,128,192,256,384,512],'sentinel_n':[32,64,128,256,512,1000],'delta':[.05,.01,.005,.001],'sentinel_rule':'first n identifiers in frozen calibration_source_ids order','source_target_pairs':'all ordered pairs among 9 frozen graph configurations within each dataset','recall_noninferiority':-.001,'gate_c':{'under_budget_rate':'not above preregistered delta confidence allowance','aggregate_recall_delta_min':-.001,'datasets_with_headroom_retention_gt_20pct':2,'net_ndc_improvement_min_at_N_ge_1e5':.01,'p95_ndc_nonworse':True,'realistic_history_direction_consistent':True,'not_single_seed_dominated':True},'bootstrap':{'unit':'query','replicates':5000,'seed':991},'raw_schema':'dataset,seed,history,query_id,ef,recall_at_10,exact_ndc,native_match,graph_hash','validation_members_read':False,'formal_test_accessed':False}
p=ROOT/'manifests/rebuild_tax';p.mkdir(parents=True,exist_ok=True);(p/'validation_split.json').write_text(json.dumps(out,indent=2)+'\n');(p/'calibration_preregistration.json').write_text(json.dumps({k:v for k,v in out.items() if k!='datasets'}|{'dataset_member_hashes':[{'dataset':r['dataset'],'source_ids_le_i64_sha256':r['source_ids_le_i64_sha256'],'query_count':r['query_count']} for r in records]},indent=2)+'\n')
print(json.dumps({'status':out['status'],'datasets':[(r['dataset'],r['query_count'],r['source_ids_le_i64_sha256']) for r in records]},indent=2))
