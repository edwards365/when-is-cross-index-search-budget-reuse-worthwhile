#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');SEED=20261001
src=json.load(open(ROOT/'manifests/hardness_portability_100k/data_query_truth_manifest.json'));prev=json.load(open(ROOT/'manifests/rebuild_tax/validation_split.json'));pm={x['dataset']:x for x in prev['datasets']};records=[]
for off,x in enumerate(sorted(src['datasets'],key=lambda z:z['dataset'])):
 old=set(map(int,np.load(ROOT/x['source_ids_path']).tolist()));old.update(pm[x['dataset']]['calibration_source_ids']);old.update(pm[x['dataset']]['audit_source_ids'])
 pool=np.array([i for i in range(100000,int(x['train_count'])) if i not in old],dtype=np.int64);ids=np.random.default_rng(SEED+off).choice(pool,1000,replace=False);raw=ids.astype('<i8').tobytes()
 records.append({'dataset':x['dataset'],'source_path':x['source_path'],'source_sha256':x['source_sha256'],'source_member':'train','formal_test_member':'test (disjoint HDF5 member)','selection_seed':SEED+off,'eligible_rule':'train id >=100000 excluding frozen hardness-100K and rebuild-tax query source IDs','excluded_prior_count':len(old),'design_source_ids':ids[:250].tolist(),'confirm_source_ids':ids[250:].tolist(),'source_ids_le_i64_sha256':hashlib.sha256(raw).hexdigest(),'design_count':250,'confirm_count':750})
out={'schema_version':1,'status':'FROZEN_BEFORE_QUERY_VECTOR_READ_OR_ANY_G1_GRAPH','seed':SEED,'datasets':records,'sets_disjoint':True,'base_disjoint_by_source_id_range':True,'prior_query_ids_excluded':True,'formal_test_accessed':False,'validation_dev_accessed':False};p=ROOT/'manifests/cross_index_g1_query_membership.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'hashes':{r['dataset']:r['source_ids_le_i64_sha256'] for r in records}},indent=2))
