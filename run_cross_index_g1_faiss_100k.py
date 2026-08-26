#!/usr/bin/env python3
import csv,gzip,hashlib,json,os,tempfile,time,sys
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
sys.path.insert(0,str(ROOT/'.deps/cross_index_g1'));import faiss
OUT=ROOT/'results/cross_index/g1/main/faiss';OUT.mkdir(parents=True,exist_ok=True)
EFS=[10,16,24,32,48,64,96,128,192,256,384,512];STOP=10*1024**3
NORM={'sift_100k':False,'glove100_100k':True,'arxiv_nomic_100k':True}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def free():s=os.statvfs(ROOT);return s.f_bavail*s.f_frsize
m=json.loads((ROOT/'manifests/cross_index_g1_query_membership.json').read_text());recs={r['dataset']:r for r in m['datasets']};results=[]
for ds in NORM:
 with h5py.File(MAIN/recs[ds]['source_path'],'r') as f:base=np.asarray(f['train'][:100000],dtype=np.float32)
 if NORM[ds]:base/=np.linalg.norm(base,axis=1,keepdims=True)
 q=np.load(ROOT/f'results/cross_index/g1/query_inputs/{ds}_queries.npy');truth=np.load(ROOT/f'results/cross_index/g1/query_inputs/{ds}_truth.npy')
 order_root=ROOT/'results/hardness_portability_100k/realistic_orders';orders={'random':np.random.default_rng(20260915).permutation(100000),'natural_source_order':np.arange(100000),'cluster_block_order':np.load(order_root/f'{ds}_cluster_block_order.npy')}
 for seed in (43,59,71):
  for history,order in orders.items():
   run=f'{ds}__seed{seed}__{history}';gz=OUT/f'{run}.csv.gz';mp=OUT/f'{run}.metadata.json'
   if gz.exists() and mp.exists():results.append(json.loads(mp.read_text()));continue
   if free()<STOP:raise RuntimeError('disk below 10 GiB stop line')
   metric=faiss.METRIC_INNER_PRODUCT if NORM[ds] else faiss.METRIC_L2;idx=faiss.IndexHNSWFlat(base.shape[1],16,metric);idx.hnsw.efConstruction=100;idx.hnsw.rng=faiss.RandomGenerator(seed);t=time.time();idx.add(base[order]);build=time.time()-t
   with tempfile.NamedTemporaryFile(dir='/dev/shm',suffix='.faiss',delete=False) as f:p=Path(f.name)
   try:faiss.write_index(idx,str(p));gh=sha(p)
   finally:p.unlink(missing_ok=True)
   rows=0
   with gzip.open(gz,'wt',newline='') as f:
    w=csv.writer(f);w.writerow(['dataset','index','history','seed','query_id','query_split','budget','returned_top10_ids','recall_at_10','exact_ndc','graph_hash'])
    for ef in EFS:
     idx.hnsw.efSearch=ef
     for qi,x in enumerate(q):
      faiss.cvar.hnsw_stats.reset();_,ids=idx.search(x.reshape(1,-1),10);ndc=int(faiss.cvar.hnsw_stats.ndis);labels=order[ids[0]];recall=len(set(map(int,labels))&set(map(int,truth[qi])))/10;w.writerow([ds,'faiss',history,seed,qi,'design' if qi<250 else 'confirm',ef,';'.join(map(str,labels)),recall,ndc,gh]);rows+=1
   rec={'dataset':ds,'history':history,'seed':seed,'rows':rows,'graph_hash':gh,'build_seconds':build,'temporary_index_deleted':True,'formal_test_accessed':False,'validation_dev_accessed':False};mp.write_text(json.dumps(rec,indent=2)+'\n');results.append(rec)
(OUT/'runs.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'graphs':len(results),'rows':sum(x['rows'] for x in results),'passed':len(results)==27},indent=2))
