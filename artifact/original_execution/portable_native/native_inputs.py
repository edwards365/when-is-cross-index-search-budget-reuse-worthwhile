"""Native raw-bit preparation from hash-bound historical bundle/qbin and truth."""
import json,struct
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def write_fbin(path,blocks,n,d):
    count=0
    with path.open('xb') as f:
        f.write(struct.pack('<II',n,d))
        for b in blocks:
            if b.dtype!=np.dtype('float32') or b.ndim!=2 or b.shape[1]!=d or not np.isfinite(b).all():raise ValueError('Vector bits/shape')
            count+=len(b);f.write(np.asarray(b,dtype='<f4').tobytes())
    if count!=n:raise ValueError('Vector rows')
def native_distances(scores,metric):
    if scores.dtype!=np.dtype('float32') or not np.isfinite(scores).all():raise ValueError('Truth dtype/nonfinite')
    if metric=='inner_product':
        if np.any(scores[:,1:]>scores[:,:-1]):raise ValueError('IP truth order')
        return (scores.view('<u4')^np.uint32(0x80000000)).view('<f4')
    if np.any(scores<0) or np.any(scores[:,1:]<scores[:,:-1]):raise ValueError('L2 truth order')
    return scores
def prepare(a,c,out):
    import run_native as entry
    import h5py
    if np.__version__!='1.26.4' or h5py.__version__!='3.11.0':raise ValueError('Library versions')
    spec=c['inputs'][a.dataset];r=spec['roles'][a.role];core=entry.module('input_core')
    reg=next(x for x in json.loads((HERE/'roles.json').read_text())['datasets'] if x['name']==spec['dataset'])
    qids=np.asarray(reg['roles'][a.role],dtype=np.int64);n=len(qids);d=spec['dimension']
    if entry.sha(a.truth)!=r['truth_sha256']:raise ValueError('Truth pin')
    with np.load(a.truth,allow_pickle=False) as t:
        if not np.array_equal(t['query_ids'],qids):raise ValueError('Truth query ordering')
        neighbors=t['neighbor_raw_ids'];scores=t['scores']
    if neighbors.shape!=(n,10) or scores.shape!=(n,10) or any(len(set(row))!=10 for row in neighbors):raise ValueError('Truth rows')
    if a.role=='source_design':
        if a.bundle is None or entry.sha(a.bundle)!=spec['bundle_sha256']:raise ValueError('Pinned source bundle required')
        with h5py.File(a.bundle,'r') as h:
            if h.attrs['source_sha256']!=reg['source_sha256'] or h['train'].shape!=(spec['base_rows'],d):raise ValueError('Bundle binding')
            raw=h['raw_ids'][:];order=h['order_seed13_random'][:];queries=h['source_design_queries'][:]
            if not np.array_equal(h['source_design_query_ids'][:],qids) or not np.array_equal(h['source_design_truth'][:],neighbors):raise ValueError('Bundle query/truth')
            mapped=core.native_ids(raw,order,neighbors).astype('<u4')
            write_fbin(out/'base.fbin',core.ordered_blocks(h['train'],order),len(raw),d)
            raw=raw[order]
    else:
        if a.source_prepared is None or a.qbin is None:raise ValueError('Source preparation and frozen qbin required')
        prior=entry.check_prior(a.source_prepared,'prepare')
        if prior['role']!='source_design' or prior['dataset']!=a.dataset:raise ValueError('Source preparation identity')
        if entry.sha(a.qbin)!=r['qbin_sha256']:raise ValueError('Qbin pin')
        raw=np.fromfile(a.source_prepared/'base_raw_ids.bin',dtype='<i8');sort=np.argsort(raw)
        pos=np.searchsorted(raw[sort],neighbors)
        if np.any(pos>=len(raw)) or not np.array_equal(raw[sort][pos],neighbors):raise ValueError('Truth outside base')
        mapped=sort[pos].astype('<u4');queries=np.empty((n,d),dtype='<f4')
        with a.qbin.open('rb') as f:
            if f.read(8)!=b'E1AQ0001' or struct.unpack('<QQ',f.read(16))!=(n,d):raise ValueError('Qbin shape')
            for i,qid in enumerate(qids):
                if struct.unpack('<q',f.read(8))[0]!=qid:raise ValueError('Qbin raw ID')
                queries[i]=np.frombuffer(f.read(d*4),dtype='<f4')
            if f.read(1):raise ValueError('Qbin trailing bytes')
    if len(raw)!=spec['base_rows'] or len(set(raw.tolist()))!=len(raw) or any(np.intersect1d(raw,v).size for v in reg['roles'].values()):raise ValueError('Base/role separation')
    write_fbin(out/'queries.fbin',[queries],n,d);dist=native_distances(scores,spec['metric'])
    with (out/'truth.bin').open('xb') as f:f.write(struct.pack('<II',n,10)+mapped.tobytes()+dist.astype('<f4').tobytes())
    with (out/'base_raw_ids.bin').open('xb') as f:f.write(raw.astype('<i8').tobytes())
    with (out/'query_raw_ids.bin').open('xb') as f:f.write(qids.astype('<i8').tobytes())
    return {'dataset':a.dataset,'role':a.role,'base_rows':len(raw),'query_rows':n,'dimension':d,'metric':spec['metric'],'vector_transform':'NONE_FLOAT32_BITS_PRESERVED','base_ids_sha256':entry.sha(out/'base_raw_ids.bin'),'truth_input_sha256':r['truth_sha256']}
