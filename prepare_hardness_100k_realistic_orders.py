#!/usr/bin/env python3
"""Freeze natural and cluster-block construction histories without query access."""
import hashlib, json, os
from pathlib import Path
import h5py, numpy as np, sklearn, yaml
from sklearn.cluster import MiniBatchKMeans

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT=ROOT/'results/hardness_portability_100k/realistic_orders'
SEED=20260915; STOP=10*1024**3

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def free():
 s=os.statvfs(ROOT);return s.f_bavail*s.f_frsize

if OUT.exists():raise RuntimeError('refusing to overwrite realistic orders')
if free()<STOP:raise RuntimeError('disk below 10 GiB stop line')
OUT.mkdir(parents=True)
cfg=yaml.safe_load((ROOT/'configs/gate_a/gate_a_100k.yaml').read_text());records=[]
for offset,key in enumerate(('sift_100k','glove100_100k','arxiv_nomic_100k')):
 d=cfg['datasets'][key]
 with h5py.File(MAIN/d['source'],'r') as f:base=np.asarray(f['train'][:100000],dtype=np.float32)
 if d['normalized']:base/=np.linalg.norm(base,axis=1,keepdims=True)
 natural=np.arange(100000,dtype=np.uint32)
 model=MiniBatchKMeans(n_clusters=100,random_state=SEED,batch_size=4096,n_init=1,max_iter=100,reassignment_ratio=0.0,compute_labels=True).fit(base)
 labels=model.labels_;rng=np.random.default_rng(SEED+offset);parts=[]
 for cluster in range(100):
  members=np.flatnonzero(labels==cluster).astype(np.uint32);parts.append(rng.permutation(members))
 block=np.concatenate(parts)
 if len(block)!=100000 or not np.array_equal(np.sort(block),natural):raise RuntimeError(key+' invalid order')
 npth=OUT/f'{key}_natural_source_order.npy';bpth=OUT/f'{key}_cluster_block_order.npy';lpth=OUT/f'{key}_cluster_labels.npy'
 np.save(npth,natural,allow_pickle=False);np.save(bpth,block,allow_pickle=False);np.save(lpth,labels.astype(np.uint16),allow_pickle=False)
 records.append({'dataset':key,'natural_definition':'ascending frozen train source member ID 0..99999','cluster_algorithm':'sklearn MiniBatchKMeans','sklearn_version':sklearn.__version__,'n_clusters':100,'cluster_seed':SEED,'batch_size':4096,'n_init':1,'max_iter':100,'reassignment_ratio':0.0,'cluster_order':'ascending learned cluster label','within_cluster_seed':SEED+offset,'uses_queries_or_truth':False,'natural_path':str(npth.relative_to(ROOT)),'natural_sha256':sha(npth),'cluster_block_path':str(bpth.relative_to(ROOT)),'cluster_block_sha256':sha(bpth),'cluster_labels_path':str(lpth.relative_to(ROOT)),'cluster_labels_sha256':sha(lpth),'cluster_size_min':int(np.bincount(labels,minlength=100).min()),'cluster_size_max':int(np.bincount(labels,minlength=100).max())})
manifest={'schema_version':1,'protocol':'Query Hardness Is Not Portable 100K','status':'FROZEN_BEFORE_REALISTIC_HISTORY_GRAPHS','core_gate_commit':'091bb1ee1a2e5495ef945c80b891dcfd503e1678','orders':['natural_source_order','cluster_block_order'],'records':records,'query_sealed_during_order_generation':True,'formal_test_accessed':False}
(ROOT/'manifests/hardness_portability_100k/realistic_history_preregistration.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'completed':[r['dataset'] for r in records]},indent=2))
