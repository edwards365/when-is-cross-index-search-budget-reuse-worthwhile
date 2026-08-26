#!/usr/bin/env python3
import csv,hashlib,json,os,shutil,struct,subprocess,tempfile
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');BIN=MAIN/'build-r0/hnsw_gate_a_benchmark';OUT=ROOT/'results/cross_index/g1/r0/hnswlib';OUT.mkdir(parents=True,exist_ok=True)
EFS='10,16,24,32,48,64,96,128,192,256,384,512';STOP=10*1024**3
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mat(p,a,dt):
 a=np.asarray(a,dtype=dt,order='C');f=open(p,'wb');f.write(struct.pack('<QQ',*a.shape));a.tofile(f);f.close()
def ordfile(p,a):
 f=open(p,'wb');f.write(struct.pack('<Q',len(a)));np.asarray(a,dtype='<u4').tofile(f);f.close()
def free():s=os.statvfs(ROOT);return s.f_bavail*s.f_frsize
m=json.loads((ROOT/'manifests/cross_index_g1_query_membership.json').read_text());rec=next(x for x in m['datasets'] if x['dataset']=='sift_100k')
with h5py.File(MAIN/rec['source_path'],'r') as f:base=np.asarray(f['train'][:10000],dtype=np.float32)
q=np.load(ROOT/'results/cross_index/g1/query_inputs/sift_100k_queries.npy')[:100];truth=np.load(ROOT/'results/cross_index/g1/query_inputs/sift_100k_truth.npy')[:100]
orders={'natural_source_order':np.arange(10000,dtype=np.uint32),'random':np.random.default_rng(20260915).permutation(10000).astype(np.uint32)};graphs=[]
with tempfile.TemporaryDirectory(prefix='g1-r0-hnsw-',dir='/dev/shm') as td:
 td=Path(td);mat(td/'points.bin',base,np.float32);mat(td/'queries.bin',q,np.float32);mat(td/'truth.bin',truth,np.uint32)
 for hist,order in orders.items():
  ordfile(td/'order.bin',order)
  for seed in (43,59):
   if free()<STOP:raise RuntimeError('disk below stop line')
   run=f'hnswlib__{hist}__seed{seed}';raw=td/run;raw.mkdir();cmd=[str(BIN),str(td/'points.bin'),str(td/'order.bin'),str(td/'queries.bin'),str(td/'truth.bin'),'-','l2','16','100',str(seed),'sift_r0','original','-',EFS,'0','1','cross-index-g1-r0','cross-index-g1',run,str(raw)]
   subprocess.run(cmd,check=True,stdout=(raw/'stdout.log').open('w'),stderr=(raw/'stderr.log').open('w'))
   rows=list(csv.DictReader(open(raw/'queries.csv')))
   if len(rows)!=1200 or any(r['native_match']!='1' for r in rows):raise RuntimeError(run+' native mismatch')
   graphs.append({'history':hist,'seed':seed,'rows':len(rows),'graph_sha256':sha(raw/'edges.csv'),'index_sha256':sha(raw/'index.bin'),'native_instrumented_exact':True,'temporary_graph_deleted':True})
out={'status':'HNSWLIB_R0_COMPONENT_PASS','graphs':graphs,'rows':sum(x['rows'] for x in graphs),'formal_test_accessed':False,'validation_dev_accessed':False};(OUT/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
