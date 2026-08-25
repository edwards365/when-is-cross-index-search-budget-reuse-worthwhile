import hashlib, json, struct, subprocess, time
from pathlib import Path
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt')
DATA=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/results/gb_mpcc')
BIN=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/build-r0/hnsw_gate_a_benchmark')
OUT=ROOT/'results/index_conditionality/ocgt_v2/raw'; OUT.mkdir(parents=True,exist_ok=True)
EFS='10,16,24,32,48,64,96,128,192,256,384,512'
spec=json.loads((DATA/'r0_inputs/manifest.json').read_text())['inputs']
qman=json.loads((DATA/'e0/search_inputs/manifest.json').read_text())['datasets']
def readmat(p):
    with open(p,'rb') as f:
        n,d=struct.unpack('<QQ',f.read(16)); return np.fromfile(f,np.float32,n*d).reshape(n,d)
def readraw(p,n,d):
    return np.memmap(p,dtype=np.float32,mode='r',shape=(n,d))
def readtruth(p):
    with open(p,'rb') as f:
        n,k=struct.unpack('<QQ',f.read(16)); return np.fromfile(f,np.uint32,n*k).reshape(n,k)
def writeorder(p,a):
        with open(p,'wb') as f: f.write(struct.pack('<Q',len(a))); np.asarray(a,np.uint32).tofile(f)
def writepoints(p,x):
    if p.exists(): return
    with open(p,'wb') as f:
        f.write(struct.pack('<QQ',len(x),x.shape[1])); np.asarray(x,dtype=np.float32).tofile(f)
def lid_order(x,cache):
    if cache.exists(): return np.load(cache)
    n=len(x); kth=np.full((n,100),np.inf,np.float32)
    xt=x.astype(np.float32)
    for s in range(0,n,256):
        b=xt[s:s+256]; d=((b*b).sum(1)[:,None]+(xt*xt).sum(1)[None,:]-2*b@xt.T)
        d[np.arange(len(b)),np.arange(s,min(s+256,n))]=np.inf
        kth[s:s+len(b)]=np.partition(d,99,axis=1)[:,:100]
    r=kth[:,-1][:,None]; dist=kth
    lid= -100.0/np.log((dist/(r+1e-30)).clip(1e-30)).sum(1)
    order=np.lexsort((np.arange(n),lid)); np.save(cache,order); return order
for rec,qrec in zip(spec,qman):
    ds=rec['dataset']; x=readraw(DATA/'r0_inputs'/Path(rec['path']).name,rec['points'],rec['dimensions']); q=readmat(DATA/'e0/search_inputs'/Path(qrec['queries']).name); t=readtruth(DATA/'e0/search_inputs'/Path(qrec['truth']).name); pointfile=ROOT/'results/index_conditionality/ocgt_v2'/(ds+'.points.f32bin'); writepoints(pointfile,x)
    metric='ip' if rec['normalized'] else 'l2'; cache=ROOT/'results/index_conditionality/ocgt_v2'/f'{ds}_lid.npy'
    orders={'random':np.random.default_rng(101).permutation(len(x)), 'lid_ascending':lid_order(x,cache), 'lid_descending':lid_order(x,cache)[::-1]}
    for seed in (7,17,29):
      for name,order in orders.items():
        run=f'{ds}__seed{seed}__{name}'; out=OUT/run
        if (out/'queries.csv').exists(): continue
        out.mkdir(parents=True,exist_ok=True); op=ROOT/'results/index_conditionality/ocgt_v2'/f'{run}.order'; writeorder(op,order)
        cmd=[str(BIN),str(pointfile),str(op),str(DATA/'e0/search_inputs'/Path(qrec['queries']).name),str(DATA/'e0/search_inputs'/Path(qrec['truth']).name),'-',metric,'16','100',str(seed),ds,'original','-',EFS,'0','1','f479c9b1e944dbc2a3e5c5a8f77f3854fa9ee7f4','ocgt-v2',run,str(out)]
        print('START',run,flush=True); subprocess.run(cmd,check=True); print('DONE',run,flush=True)
        op.unlink(missing_ok=True); idx=out/'index.bin'; idx.unlink(missing_ok=True)
