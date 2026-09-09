from __future__ import annotations
import hashlib,json,struct,subprocess,time
from pathlib import Path
import h5py,numpy as np
ROOT=Path('/home/wlk/data500/icba_vamana_stage1_arxiv'); ROOT.mkdir(parents=True,exist_ok=True)
BASEP=Path('/home/wlk/data500/graph_anns_e4/inputs/arxiv_nomic_100k/base.f32bin')
H5P=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/data/raw/arxiv-nomic-768-normalized.hdf5')
BIN=Path('/home/wlk/data500/icba_vamana_preflight/target/release/diskann-benchmark')
GRID=[16,32,64,128,256,512]; SEEDS=[1103,1207,1301,1409,1511,1601,2101,2203,2309,2411,2503,2609]
def read64(p):
 with p.open('rb') as f:n,d=struct.unpack('<QQ',f.read(16))
 return np.memmap(p,dtype='<f4',mode='r',offset=16,shape=(n,d))
def wf(p,a):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('wb') as f:f.write(struct.pack('<II',*a.shape));a.astype('<f4',copy=False).tofile(f)
def wt(p,ids):
 with p.open('wb') as f:f.write(struct.pack('<II',len(ids),10));ids.astype('<u4').tofile(f);np.zeros_like(ids,dtype='<f4').tofile(f)
base=read64(BASEP); assert base.shape==(100000,768)
rng=np.random.default_rng(991); pool=rng.choice(np.arange(100000,1344643),3000,replace=False)
names=('vamana_design','vamana_evaluation','vamana_runtime','vamana_future_replication'); roles={n:np.sort(pool[i*750:(i+1)*750]) for i,n in enumerate(names)}
manifest={n:{'count':750,'ids_sha256':hashlib.sha256(('\n'.join(map(str,v))+'\n').encode()).hexdigest(),'access_state':'IDS_ONLY' if n in ('vamana_runtime','vamana_future_replication') else 'READ'} for n,v in roles.items()}
(ROOT/'query_roles.json').write_text(json.dumps(manifest,indent=2)+'\n'); (ROOT/'query_role_ids.json').write_text(json.dumps({k:v.tolist() for k,v in roles.items()},indent=2)+'\n')
with h5py.File(H5P,'r') as h:
 # Only train is read; the sealed HDF5 test dataset is never dereferenced.
 q=h['train'][roles['vamana_evaluation']]
 # The registered base is a frozen train subsample; ensure new train queries do not equal any base vector.
 base_hashes={hashlib.sha256(np.asarray(v,dtype='<f4').tobytes()).digest() for v in base}
 assert all(hashlib.sha256(np.asarray(v,dtype='<f4').tobytes()).digest() not in base_hashes for v in q)
wf(ROOT/'evaluation_queries.fbin',q)
# normalized vectors: exact neighbors maximize dot product
ext=np.empty((750,10),np.uint32)
for lo in range(0,750,25):
 score=q[lo:lo+25]@np.asarray(base).T; ix=np.argpartition(score,-10,axis=1)[:,-10:]
 order=np.argsort(-np.take_along_axis(score,ix,axis=1),axis=1); ext[lo:lo+len(ix)]=np.take_along_axis(ix,order,axis=1)
for i,seed in enumerate(SEEDS,1):
 bid=f'V{i:02d}'; out=ROOT/'builds'/bid; data=ROOT/'data'/bid; out.mkdir(parents=True,exist_ok=True);data.mkdir(parents=True,exist_ok=True)
 rng=np.random.default_rng(seed);perm=rng.permutation(len(base));inv=np.empty_like(perm);inv[perm]=np.arange(len(perm))
 wf(data/'base.fbin',np.asarray(base[perm]));wf(data/'queries.fbin',q);wt(data/'truth.bin',inv[ext]);np.save(data/'internal_to_external.npy',perm);np.save(data/'external_to_internal.npy',inv)
 cfg={'search_directories':[str(data)],'output_directory':str(out),'jobs':[{'type':'graph-index-build','content':{'source':{'index-source':'Build','data_type':'float32','data':'base.fbin','distance':'cosine_normalized','max_degree':32,'l_build':64,'alpha':1.2,'backedge_ratio':1.0,'num_threads':1,'start_point_strategy':'medoid','num_insert_attempts':1,'saturate_inserts':False,'multi_insert':{'batch_size':1,'batch_parallelism':1,'intra_batch_candidates':'none'},'save_path':'index'},'search_phase':{'search-type':'topk','queries':'queries.fbin','groundtruth':'truth.bin','reps':1,'num_threads':[1],'runs':[{'search_n':10,'search_l':GRID,'recall_k':10}]}}}]}
 cp=ROOT/'configs'/f'{bid}.json';cp.parent.mkdir(exist_ok=True);cp.write_text(json.dumps(cfg,indent=2)+'\n')
 if not (out/'run_report.json').exists():
  print('START',bid,flush=True);t=time.time();subprocess.run([str(BIN),'--quiet','run','--input-file',str(cp),'--output-file',str(out/'run_report.json')],check=True);print('DONE',bid,time.time()-t,flush=True)
 rr=np.random.default_rng(seed+991).integers(0,len(perm),10000);assert np.all(perm[inv[rr]]==rr) and np.all(inv[perm[rr]]==rr)
print('STAGE1_ARXIV_RAW_COMPLETE',flush=True)
