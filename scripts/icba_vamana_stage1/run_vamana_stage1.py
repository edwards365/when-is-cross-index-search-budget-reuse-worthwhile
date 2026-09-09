from __future__ import annotations
import hashlib, json, os, struct, subprocess, sys, time
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/data500/icba_vamana_stage1')
E4=Path('/home/wlk/data500/graph_anns_e4/inputs/sift_100k')
SRC=Path('/home/wlk/data500/icba_vamana_preflight/source/DiskANN-8fb4d42e6a8bff0cff4db976a55c5fb99faaf475/test_data/sift/siftsmall_learn.bin')
BIN=Path('/home/wlk/data500/icba_vamana_preflight/target/release/diskann-benchmark')
GRID=[16,32,64,128,256,512]
SEEDS=[1103,1207,1301,1409,1511,1601,2101,2203,2309,2411,2503,2609]

def read_fbin(p):
    size=p.stat().st_size
    with p.open('rb') as f:
        raw=f.read(16); n32,d32=struct.unpack('<II',raw[:8]); n64,d64=struct.unpack('<QQ',raw)
    if 8+4*n32*d32==size: n,d,off=n32,d32,8
    elif 16+4*n64*d64==size: n,d,off=n64,d64,16
    else: raise ValueError(f'unsupported vector header: {p}')
    return np.memmap(p,dtype='<f4',mode='r',offset=off,shape=(n,d))
def write_fbin(p,a):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('wb') as f: f.write(struct.pack('<II',*a.shape)); a.astype('<f4',copy=False).tofile(f)
def write_truth(p,ids,dists):
    with p.open('wb') as f:
        f.write(struct.pack('<II',*ids.shape)); ids.astype('<u4').tofile(f); dists.astype('<f4').tofile(f)
def shab(b): return hashlib.sha256(b).hexdigest()

ROOT.mkdir(parents=True,exist_ok=True)
base=read_fbin(E4/'base.f32bin')
learn=read_fbin(SRC)
assert base.shape==(100000,128) and learn.shape[1]==128 and learn.shape[0]>=3000
rng=np.random.default_rng(991); role_ids=rng.choice(learn.shape[0],size=3000,replace=False)
roles={k:role_ids[i*750:(i+1)*750] for i,k in enumerate(('vamana_design','vamana_evaluation','vamana_runtime','vamana_future_replication'))}
role_manifest={}
for k,ids in roles.items():
    bb=('\n'.join(map(str,ids.tolist()))+'\n').encode()
    role_manifest[k]={'count':750,'ids_sha256':shab(bb),'access_state':'IDS_ONLY' if k in ('vamana_runtime','vamana_future_replication') else 'READ'}
(ROOT/'query_roles.json').write_text(json.dumps(role_manifest,indent=2)+'\n')
(ROOT/'query_role_ids.json').write_text(json.dumps({k:v.tolist() for k,v in roles.items()},indent=2)+'\n')

q=np.asarray(learn[roles['vamana_evaluation']])
write_fbin(ROOT/'evaluation_queries.fbin',q)
# Exact top-10 external IDs, computed in query blocks to bound memory.
qnorm=(q*q).sum(1); bnorm=np.asarray((base*base).sum(1)); ext=np.empty((len(q),10),np.uint32); dst=np.empty((len(q),10),np.float32)
for lo in range(0,len(q),50):
    qq=q[lo:lo+50]; d=qnorm[lo:lo+50,None]+bnorm[None,:]-2.0*(qq@np.asarray(base).T)
    ix=np.argpartition(d,9,axis=1)[:,:10]
    order=np.argsort(np.take_along_axis(d,ix,axis=1),axis=1)
    ext[lo:lo+len(qq)]=np.take_along_axis(ix,order,axis=1)
    dst[lo:lo+len(qq)]=np.take_along_axis(d,np.take_along_axis(ix,order,axis=1),axis=1)

for i,seed in enumerate(SEEDS,1):
    bid=f'V{i:02d}'; out=ROOT/'builds'/bid; data=ROOT/'data'/bid; out.mkdir(parents=True,exist_ok=True); data.mkdir(parents=True,exist_ok=True)
    r=np.random.default_rng(seed); perm=r.permutation(base.shape[0]); inv=np.empty_like(perm); inv[perm]=np.arange(len(perm))
    write_fbin(data/'base.fbin',np.asarray(base[perm])); write_fbin(data/'queries.fbin',q)
    write_truth(data/'truth.bin',inv[ext],dst)
    np.save(data/'internal_to_external.npy',perm); np.save(data/'external_to_internal.npy',inv)
    cfg={'search_directories':[str(data)],'output_directory':str(out),'jobs':[{'type':'graph-index-build','content':{
      'source':{'index-source':'Build','data_type':'float32','data':'base.fbin','distance':'squared_l2','max_degree':32,'l_build':64,'alpha':1.2,'backedge_ratio':1.0,'num_threads':1,'start_point_strategy':'medoid','num_insert_attempts':1,'saturate_inserts':False,'multi_insert':{'batch_size':1,'batch_parallelism':1,'intra_batch_candidates':'none'},'save_path':'index'},
      'search_phase':{'search-type':'topk','queries':'queries.fbin','groundtruth':'truth.bin','reps':1,'num_threads':[1],'runs':[{'search_n':10,'search_l':GRID,'recall_k':10}]}}}]}
    cp=ROOT/'configs'/f'{bid}.json'; cp.parent.mkdir(exist_ok=True); cp.write_text(json.dumps(cfg,indent=2)+'\n')
    if not (out/'run_report.json').exists():
        print(f'START {bid} seed={seed}',flush=True); t=time.time()
        subprocess.run([str(BIN),'--quiet','run','--input-file',str(cp),'--output-file',str(out/'run_report.json')],check=True)
        print(f'DONE {bid} seconds={time.time()-t:.3f}',flush=True)
    # mapping audit after materialization
    rr=np.random.default_rng(seed+991).integers(0,len(perm),10000)
    assert np.all(perm[inv[rr]]==rr) and np.all(inv[perm[rr]]==rr)
print('STAGE1_SIFT_RAW_COMPLETE',flush=True)
