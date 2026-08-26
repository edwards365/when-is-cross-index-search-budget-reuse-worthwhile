#!/usr/bin/env python3
import hashlib, json, os, struct, subprocess, tempfile
from pathlib import Path
import h5py, numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
MAIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
BIN=Path('/tmp/g1-rust/target/release/integration-test')
OUT=ROOT/'results/cross_index/g1/r0/vamana'; OUT.mkdir(parents=True,exist_ok=True)
EFS=[10,16,24,32,48,64,96,128,192,256,384,512]; STOP=10*1024**3
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fbin(path,a):
 a=np.asarray(a,order='C');
 with open(path,'wb') as f: f.write(struct.pack('<II',*a.shape)); a.tofile(f)
def free(): s=os.statvfs(ROOT); return s.f_bavail*s.f_frsize
m=json.loads((ROOT/'manifests/cross_index_g1_query_membership.json').read_text())
r=next(x for x in m['datasets'] if x['dataset']=='sift_100k')
with h5py.File(MAIN/r['source_path'],'r') as f: base=np.asarray(f['train'][:10000],dtype=np.float32)
queries=np.load(ROOT/'results/cross_index/g1/query_inputs/sift_100k_queries.npy')[:100]
dist=(queries*queries).sum(1)[:,None]+(base*base).sum(1)[None,:]-2.0*(queries@base.T)
truth=np.argsort(dist,axis=1,kind='stable')[:,:10].astype(np.uint32)
orders={'natural_source_order':np.arange(10000,dtype=np.int64),'random':np.random.default_rng(20260915).permutation(10000)}
records=[]
with tempfile.TemporaryDirectory(prefix='g1-vamana-r0-',dir='/dev/shm') as td:
 td=Path(td); fbin(td/'queries.fbin',queries)
 jobs=[]
 for history,order in orders.items():
  inverse=np.empty(10000,dtype=np.uint32); inverse[order]=np.arange(10000,dtype=np.uint32)
  fbin(td/f'{history}.fbin',base[order]); fbin(td/f'{history}.gtbin',inverse[truth])
  for lbuild in (50,100,150):
   jobs.append({'type':'integration-test','content':{'build':{'alpha':1.2,'l_build':lbuild,'max_degree':32,'pruned_degree':32},'data':{'data':f'{history}.fbin','data_type':'f32','groundtruth':f'{history}.gtbin','metric':'l2','queries':'queries.fbin','preprocess':[]},'layer':{'FullPrecision':{'data_type':'f32'}},'search':{'knn':[{'beam_width':None,'knn':10,'search_l':x} for x in EFS]}}})
 spec={'search_directories':[str(td)],'output_directory':None,'jobs':jobs}; (td/'input.json').write_text(json.dumps(spec))
 if free()<STOP: raise RuntimeError('disk below stop line')
 hashes=[]
 for rep in (1,2):
  out=td/f'out{rep}.json'; subprocess.run([str(BIN),'run','--input-file',str(td/'input.json'),'--output-file',str(out)],check=True,stdout=(td/f'run{rep}.log').open('w'),stderr=(td/f'run{rep}.err').open('w')); hashes.append(sha(out))
 if hashes[0]!=hashes[1]: raise RuntimeError('Vamana repeated output mismatch')
 evidence=json.loads((td/'out1.json').read_text()); (OUT/'instrumented_output.json').write_text(json.dumps(evidence,indent=2)+'\n')
 summary={'status':'VAMANA_R0_EXECUTION_REPEAT_PASS_PENDING_GRAPH_STRUCTURE_AUDIT','jobs':6,'logical_graphs':12,'query_budget_cells':7200,'repeat_output_sha256':hashes[0],'native_cmps_used':True,'seed_control':'implementation_has_no_rng_parameter; seed43/59 are exact deterministic repeats','temporary_inputs_deleted':True,'formal_test_accessed':False,'validation_dev_accessed':False}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary,indent=2))
