#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');SRC=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
paths=sorted(SRC.glob('results/**/glove*source_ids.npy'));used=set(range(100000));provenance=[]
for p in paths:
 a=np.load(p).astype(int).ravel();used.update(a.tolist());provenance.append({'path':str(p),'count':len(a),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
rng=np.random.default_rng(20261020);eligible=np.array(sorted(set(range(100000,1183514))-used));chosen=rng.choice(eligible,768,replace=False)
splits={'rcrs_design_queries':chosen[:256].tolist(),'rcrs_calibration_queries':chosen[256:512].tolist(),'rcrs_design_eval_queries':chosen[512:].tolist()}
payload=json.dumps(splits,sort_keys=True,separators=(',',':')).encode();m={'schema_version':1,'status':'FROZEN_BEFORE_QUERY_VECTOR_READ','dataset':'glove100_100k','source':'data/raw/glove-100-angular.hdf5','source_member':'train','base_ids':'0:99999','seed':20261020,'counts':{k:len(v) for k,v in splits.items()},'splits':splits,'split_sha256':hashlib.sha256(payload).hexdigest(),'excluded_prior_sources':provenance,'overlap_between_splits':0,'overlap_with_base':0,'overlap_with_prior_queries':0,'validation_dev_accessed':False,'formal_test_accessed':False,'vectors_read':False}
(ROOT/'manifests/rcrs_signal_query_split.json').write_text(json.dumps(m,indent=2)+'\n')
print(m['split_sha256'],len(used))
