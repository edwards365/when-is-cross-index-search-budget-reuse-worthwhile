"""Role-safe exact input bridge; preserves legacy bundle pins without replacing them."""
import json,struct,shutil
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import run_native as entry
HERE=Path(__file__).resolve().parent
ROLES=('source_design','target_selection','target_certification','target_evaluation')

def context(c,dataset):
    spec=c['inputs'][dataset];row=next(x for x in json.loads((HERE/'roles.json').read_text())['datasets'] if x['name']==spec['dataset']);held=np.concatenate([np.asarray(row['roles'][r],dtype=np.int64) for r in ROLES]);excluded=np.asarray(spec['excluded_raw_ids'],dtype=np.int64)
    if len(held)!=2500 or len(np.unique(held))!=2500 or np.intersect1d(held,excluded).size:raise ValueError('Frozen role/base partitions')
    keep=np.ones(row['train_shape'][0],bool);keep[held]=False;keep[excluded]=False;ids=np.flatnonzero(keep).astype(np.int64)
    if len(ids)!=spec['base_rows']:raise ValueError('Frozen retained base count')
    return spec,row,held,excluded,keep,ids

def gate(a):
    if a.role=='source_design':return None
    if a.previous is None:raise ValueError('Preceding source/model/held-out stage required before accessing a new target role')
    raw=json.loads((a.previous/'completed.json').read_text());r=entry.check_prior(a.previous,raw['phase'])
    if r['dataset']!=a.dataset:raise ValueError('Preceding dataset')
    if a.role=='target_selection':ok=r['phase'] in ('source-search','darth-train')
    else:ok=r['phase'] in ('heldout-search','darth-heldout') and r['role']==('target_selection' if a.role=='target_certification' else 'target_certification')
    if not ok:raise ValueError('Preceding role/stage mismatch')
    return entry.sha(a.previous/'completed.json')

def write_qbin(path,ids,q):
    with path.open('xb') as f:
        f.write(b'E1AQ0001'+struct.pack('<QQ',len(ids),q.shape[1]))
        for i,v in zip(ids,q):f.write(struct.pack('<q',int(i))+np.asarray(v,dtype='<f4').tobytes())

def write_source_only(path,source,keep,raw_ids,qids,queries,neighbors,source_sha,h5py,chunk=4096):
    with h5py.File(source,'r') as src,h5py.File(path,'x',libver='latest') as dest:
        train=src['train'];dim=train.shape[1];target=dest.create_dataset('train',(len(raw_ids),dim),dtype='f4',chunks=(min(chunk,len(raw_ids)),dim));cursor=0
        for lo in range(0,len(keep),chunk):
            data=np.asarray(train[lo:lo+chunk][keep[lo:lo+chunk]],dtype=np.float32);target[cursor:cursor+len(data)]=data;cursor+=len(data)
        if cursor!=len(raw_ids):raise ValueError('Streamed raw base incomplete')
        dest.create_dataset('raw_ids',data=raw_ids,dtype='i8');dest.create_dataset('order_seed13_random',data=np.random.RandomState(13).permutation(len(raw_ids)).astype(np.uint64),dtype='u8')
        dest.create_dataset('source_design_query_ids',data=qids,dtype='i8');dest.create_dataset('source_design_queries',data=queries,dtype='f4');dest.create_dataset('source_design_truth',data=neighbors,dtype='i4')
        dest.attrs['source_sha256']=source_sha;dest.attrs['layout']='NEW_NATIVE_SOURCE_ONLY_V1';dest.attrs['forbidden_raw_hdf5_datasets_accessed']='[]';dest.flush()

def audit_source_only(path,source,keep,raw_ids,qids,queries,neighbors,source_sha,h5py,chunk=4096):
    # Re-read every serialized base vector; equality uses uint32, including -0.
    with h5py.File(path,'r') as b,h5py.File(source,'r') as src:
        if set(b)!={'train','raw_ids','order_seed13_random','source_design_query_ids','source_design_queries','source_design_truth'} or b.attrs['source_sha256']!=source_sha or b.attrs['layout']!='NEW_NATIVE_SOURCE_ONLY_V1':raise ValueError('New source-only schema/attributes')
        if b['train'].shape!=(len(raw_ids),src['train'].shape[1]) or b['train'].dtype!=np.dtype('float32'):raise ValueError('Base shape/dtype')
        np.testing.assert_array_equal(b['raw_ids'][:],raw_ids);np.testing.assert_array_equal(b['order_seed13_random'][:],np.random.RandomState(13).permutation(len(raw_ids)).astype(np.uint64))
        np.testing.assert_array_equal(b['source_design_query_ids'][:],qids);np.testing.assert_array_equal(b['source_design_queries'][:].view('<u4'),queries.view('<u4'));np.testing.assert_array_equal(b['source_design_truth'][:],neighbors.astype('<i4'))
        cursor=0
        for lo in range(0,len(keep),chunk):
            expected=np.asarray(src['train'][lo:lo+chunk][keep[lo:lo+chunk]],dtype=np.float32);actual=b['train'][cursor:cursor+len(expected)]
            if not np.isfinite(expected).all():raise ValueError('Nonfinite source')
            np.testing.assert_array_equal(actual.view('<u4'),expected.view('<u4'));cursor+=len(expected)
        if cursor!=len(raw_ids):raise ValueError('Audit base coverage')
    return {'all_base_vector_bits':'PASS','all_source_query_bits':'PASS','raw_ids_and_order':'PASS','source_truth_ids':'PASS','future_role_vectors_or_truth_in_bundle':False}

def run(a,c,out):
    import h5py
    if h5py.__version__!='3.11.0' or np.__version__!='1.26.4':raise ValueError('Input serialization dependencies')
    if a.phase=='input-role':previous=gate(a)
    spec,row,held,excluded,keep,rawids=context(c,a.dataset)
    if entry.sha(a.hdf5)!=row['source_sha256']:raise ValueError('Raw train HDF5 SHA')
    if a.phase=='input-role':
        ids=np.asarray(row['roles'][a.role],dtype=np.int64);order=np.argsort(ids)
        with h5py.File(a.hdf5,'r') as f:
            if list(f['train'].shape)!=row['train_shape'] or str(f['train'].dtype)!='float32':raise ValueError('Raw train metadata')
            queries=np.ascontiguousarray(np.asarray(f['train'][ids[order]],dtype=np.float32)[np.argsort(order)])
        write_qbin(out/'queries.qbin',ids,queries)
        if entry.sha(out/'queries.qbin')!=spec['roles'][a.role]['qbin_sha256']:raise ValueError('Frozen query bytes differ')
        if a.truth is not None:
            if entry.sha(a.truth)!=spec['roles'][a.role]['truth_sha256']:raise ValueError('Frozen supplied truth')
            shutil.copyfile(a.truth,out/'truth.npz');origin='HASH_BOUND_EXISTING_TRUTH'
        else:
            faiss=entry.module('refresh_phases').native();core=entry.module('native_truth_core');metric='l2' if a.dataset=='sift' else 'ip';base=len(rawids);heldset=set(map(int,held));ex=set(map(int,excluded))
            if a.role=='source_design':arrays=core.truth_e1a_source(row,{'metric':'squared_l2' if metric=='l2' else 'inner_product_on_original_normalized_float32','source_design_query_count':500},base,heldset,ex,a.hdf5,8192,faiss,h5py)
            elif a.role=='target_selection':arrays=core.truth_e1a_selection(row,{row['name']:{'metric':metric,'base_count':base}},SimpleNamespace(dataset=row['name']),ids,heldset,ex,a.hdf5,faiss,h5py)
            else:arrays=getattr(core,'truth_e1a_'+('certify' if a.role=='target_certification' else 'evaluate'))(row,metric,base,ids,heldset,ex,a.hdf5,faiss,h5py)
            with (out/'truth.npz').open('xb') as f:(np.savez if a.role=='source_design' else np.savez_compressed)(f,**arrays)
            origin='NEW_EXACT_TRUTH_UNCHANGED_ORIGINAL_ROLE_BLOCK'
        if entry.sha(out/'truth.npz')!=spec['roles'][a.role]['truth_sha256']:raise ValueError('Frozen truth serialization differs; stop, do not repin')
        return {'dataset':a.dataset,'role':a.role,'source_sha256':row['source_sha256'],'truth_origin':origin,'prior_receipt_sha256':previous,'query_truth_frozen_sha':'PASS','forbidden_hdf5_members_accessed':[]}
    prior=entry.check_prior(a.prior,'input-role')
    if prior['dataset']!=a.dataset or prior['role']!='source_design':raise ValueError('Source-only input role required')
    qids=np.asarray(row['roles']['source_design'],dtype=np.int64)
    with h5py.File(a.hdf5,'r') as f:queries=np.ascontiguousarray(f['train'][qids],dtype=np.float32)
    with np.load(a.prior/'truth.npz',allow_pickle=False) as t:
        np.testing.assert_array_equal(t['query_ids'],qids);neighbors=t['neighbor_raw_ids'].copy()
    path=out/'bundle.hdf5';chunk=8192 if a.dataset=='sift' else 4096
    write_source_only(path,a.hdf5,keep,rawids,qids,queries,neighbors,row['source_sha256'],h5py,chunk)
    audit=audit_source_only(path,a.hdf5,keep,rawids,qids,queries,neighbors,row['source_sha256'],h5py,chunk)
    return {'dataset':a.dataset,'layout':'NEW_NATIVE_SOURCE_ONLY_V1','container_sha256':entry.sha(path),'historical_container_sha256':spec['bundle_sha256'],'historical_container_identity_claimed':False,'source_sha256':row['source_sha256'],'source_input_receipt_sha256':entry.sha(a.prior/'completed.json'),'audit':audit,'reason':'Role-safe new layout and independently checked complete scientific contents; HDF5 container metadata may vary, original legacy SHA is not replaced'}
