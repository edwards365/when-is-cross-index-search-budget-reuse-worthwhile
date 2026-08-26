#!/usr/bin/env python3
import csv,gzip,hashlib,json,os,tempfile
from pathlib import Path
import h5py,numpy as np
import sys
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k'); MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
sys.path.insert(0,str(ROOT/'.deps/cross_index_g1')); import faiss
EFS=[10,16,24,32,48,64,96,128,192,256,384,512]; STOP=10*1024**3
OUT=ROOT/'results/cross_index/g1/r0/faiss'; OUT.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def free(): s=os.statvfs(ROOT); return s.f_bavail*s.f_frsize
m=json.loads((ROOT/'manifests/cross_index_g1_query_membership.json').read_text()); rec=next(x for x in m['datasets'] if x['dataset']=='sift_100k')
with h5py.File(MAIN/rec['source_path'],'r') as f: base=np.asarray(f['train'][:10000],dtype=np.float32)
queries=np.load(ROOT/'results/cross_index/g1/query_inputs/sift_100k_queries.npy',allow_pickle=False)[:100]
truth=np.load(ROOT/'results/cross_index/g1/query_inputs/sift_100k_truth.npy',allow_pickle=False)[:100]
orders={'natural_source_order':np.arange(10000,dtype=np.int64),'random':np.random.default_rng(20260915).permutation(10000)}
rows=[]; graphs=[]
for history,order in orders.items():
 for seed in (43,59):
  if free()<STOP: raise RuntimeError('disk below stop line')
  index=faiss.IndexHNSWFlat(128,16,faiss.METRIC_L2); index.hnsw.efConstruction=100; index.hnsw.rng=faiss.RandomGenerator(seed); index.add(base[order])
  with tempfile.NamedTemporaryFile(dir=str(ROOT),suffix='.faiss',delete=False) as tf: p=Path(tf.name)
  try: faiss.write_index(index,str(p)); graph_hash=sha(p)
  finally: p.unlink(missing_ok=True)
  for ef in EFS:
   index.hnsw.efSearch=ef
   for qi,q in enumerate(queries):
    q=q.reshape(1,-1)
    faiss.cvar.hnsw_stats.reset(); d1,i1=index.search(q,10); n1=int(faiss.cvar.hnsw_stats.ndis)
    faiss.cvar.hnsw_stats.reset(); d2,i2=index.search(q,10); n2=int(faiss.cvar.hnsw_stats.ndis)
    if not (np.array_equal(i1,i2) and np.array_equal(d1,d2) and n1==n2): raise RuntimeError('instrumentation/determinism mismatch')
    labels=order[i1[0]]; recall=len(set(map(int,labels)) & set(map(int,truth[qi])))/10
    rows.append((history,seed,ef,qi,';'.join(map(str,labels)),recall,n1,graph_hash))
  graphs.append({'history':history,'seed':seed,'graph_sha256':graph_hash,'rows':1200,'labels_distances_repeat_exact':True,'ndc_repeat_exact':True,'temporary_graph_deleted':True})
with gzip.open(OUT/'rows.csv.gz','wt',newline='') as f:
 w=csv.writer(f);w.writerow(['history','seed','budget','query_id','labels','recall_at_10','exact_ndc','graph_sha256']);w.writerows(rows)
out={'status':'FAISS_R0_COMPONENT_PASS','faiss_version':faiss.__version__,'graphs':graphs,'rows':len(rows),'formal_test_accessed':False,'validation_dev_accessed':False}
(OUT/'summary.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
