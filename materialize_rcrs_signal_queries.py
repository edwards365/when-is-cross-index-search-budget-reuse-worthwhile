#!/usr/bin/env python3
import hashlib,json,struct
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');m=json.load(open(ROOT/'manifests/rcrs_signal_query_split.json'));src=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/data/raw/glove-100-angular.hdf5')
ids=np.array(sum([m['splits'][k] for k in ['rcrs_design_queries','rcrs_calibration_queries','rcrs_design_eval_queries']],[]),dtype=int)
with h5py.File(src,'r') as f:
 base=f['train'][:100000].astype('float32')
 order=np.argsort(ids)
 sorted_q=f['train'][ids[order]].astype('float32')
 q=np.empty_like(sorted_q);q[order]=sorted_q
base/=np.linalg.norm(base,axis=1,keepdims=True)
q/=np.linalg.norm(q,axis=1,keepdims=True)
truth=np.empty((len(q),10),dtype='uint32')
for a in range(0,len(q),32):
 score=q[a:a+32]@base.T;part=np.argpartition(-score,9,axis=1)[:,:10]
 for i in range(len(part)):truth[a+i]=part[i,np.argsort(-score[i,part[i]])]
def wb(path,x):
 with open(path,'wb') as f:f.write(struct.pack('II',*x.shape));f.write(x.tobytes())
wb('/tmp/rcrs_glove_queries.f32bin',q);wb('/tmp/rcrs_glove_truth.u32bin',truth)
qh=hashlib.sha256(q.tobytes()).hexdigest();th=hashlib.sha256(truth.tobytes()).hexdigest();m.update({'vectors_read':True,'query_content_sha256':qh,'truth_content_sha256':th,'truth_method':'exact inner product against L2-normalized frozen train[0:100000]','preprocessing':'L2-normalize base and queries exactly as frozen Gate A ingest','query_count':len(q),'truth_k':10,'materializer':'materialize_rcrs_signal_queries.py','validation_dev_accessed':False,'formal_test_accessed':False})
(ROOT/'manifests/rcrs_signal_query_split.json').write_text(json.dumps(m,indent=2)+'\n');print(qh,th)
