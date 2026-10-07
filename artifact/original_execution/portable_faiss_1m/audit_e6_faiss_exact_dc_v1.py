"""Independent event counts, original-vector distances and sealed ordered-ID audit."""
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np

EVENT=np.dtype([('ef','<i4'),('q','<i4'),('kind','<i4'),('raw','<i8'),('dist','<f4')])
RESPONSE=np.dtype([('ef','<i4'),('q','<i4'),('scalar','<u8'),('batch','<u8'),('count','<u8'),('ids','<i8',(10,)),('dist','<f4',(10,))])
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def load(path,magic,dtype,n,dim):
    p=Path(path)
    with p.open('rb') as f:
        if f.read(12)!=magic+struct.pack('<II',n,dim):raise ValueError('header')
    if (p.stat().st_size-12)%dtype.itemsize:raise ValueError('partial record')
    return np.memmap(p,mode='r',offset=12,dtype=dtype)
def run(c):
    for p,h in c['pins'].items():
        if sha(p)!=h:raise ValueError('pin differs '+p)
    n,dim=c['query_count'],c['dim'];prefix=c['prefix'];actions=c['actions']
    r=load(prefix+'.responses.bin',b'E6RS',RESPONSE,n,dim)
    e=load(prefix+'.events.bin',b'E6EV',EVENT,n,dim)
    if len(r)!=n*len(actions):raise ValueError('response count')
    queries=np.memmap(c['query'],mode='r',dtype='<f4',offset=8,shape=(n,dim))
    base=np.memmap(c['base'],mode='r',dtype='<f4',offset=8,shape=(c['base_count'],dim))
    raw=np.memmap(c['base_raw_ids'],mode='r',dtype='<i8')
    if len(raw)!=c['base_count'] or len(np.unique(raw))!=len(raw):raise ValueError('raw mapping')
    order=np.argsort(raw);ordered=raw[order]
    with np.load(c['reference'],allow_pickle=False) as frozen:
        if not np.array_equal(frozen['query_ids'],c['query_ids']):raise ValueError('role/query order')
        refs={int(a):frozen['topk'][i] for i,a in enumerate(frozen['action_grid'])}
    if not set(actions)<=refs.keys():raise ValueError('reference actions')
    counts=[];pos=0;max_error=0.;max_ratio=0.
    for j,row in enumerate(r):
        a=actions[j//n];q=j%n
        if (int(row['ef']),int(row['q']))!=(a,q):raise ValueError('response order')
        if not np.array_equal(row['ids'],refs[a][q]):raise ValueError('sealed top10 mismatch')
        if len(np.unique(row['ids']))!=10 or not np.all(np.isfinite(row['dist'])):raise ValueError('returned values')
        count=int(row['count']);scalar=int(row['scalar']);batch=int(row['batch'])
        if count!=scalar+4*batch or count<=0 or pos+count>len(e):raise ValueError('declared count')
        # The independent audit counts actual serialized event rows, not native totals.
        part=e[pos:pos+count];pos+=count
        if np.any(part['ef']!=a) or np.any(part['q']!=q):raise ValueError('event attribution')
        if int(np.sum(part['kind']==1))!=scalar or int(np.sum(part['kind']==4))!=4*batch:raise ValueError('scalar/batch independent count')
        if np.any((part['kind']!=1)&(part['kind']!=4)):raise ValueError('kind')
        # Check each batch is exactly four consecutive events; no partial or double expansion.
        bmask=part['kind']==4;lo=0
        while lo<len(part):
            if bmask[lo]:
                if lo+4>len(part) or not np.all(bmask[lo:lo+4]):raise ValueError('batch boundaries')
                lo+=4
            else:lo+=1
        for lo in range(0,count,4096):
            chunk=part[lo:lo+4096];ix=np.searchsorted(ordered,chunk['raw'])
            if np.any(ix>=len(raw)) or not np.array_equal(ordered[ix],chunk['raw']):raise ValueError('event raw IDs')
            vectors=base[order[ix]].astype(np.float64);query=queries[q].astype(np.float64)
            if c['metric']=='L2':
                terms=(vectors-query)**2
            elif c['metric']=='IP':terms=vectors*query
            else:raise ValueError('metric')
            reference=np.sum(terms,axis=1);bound=64*np.finfo(np.float32).eps*np.sum(np.abs(terms),axis=1)+1e-6
            error=np.abs(reference-chunk['dist'].astype(np.float64))
            if np.any(~np.isfinite(chunk['dist'])) or np.any(error>bound):raise ValueError('event original-vector distance')
            max_error=max(max_error,float(error.max()));max_ratio=max(max_ratio,float((error/bound).max()))
        counts.append(count)
    if pos!=len(e):raise ValueError('extra unassigned event/EOF')
    return dict(status='PASS_EXACT_DC_EVENTS_AND_SEALED_ORDERED_IDS',query_count=n,actions=actions,
                counts_by_action=np.asarray(counts,dtype=np.uint64).reshape(-1,n).tolist(),
                event_count=len(e),max_distance_error=max_error,max_bound_ratio=max_ratio,
                response_sha=sha(prefix+'.responses.bin'),event_sha=sha(prefix+'.events.bin'),
                source_equivalence_only=True,not_original_wheel_counter=True,not_latency=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);a=ap.parse_args()
    print(json.dumps(run(json.loads(a.config.read_text())),allow_nan=False),flush=True)
