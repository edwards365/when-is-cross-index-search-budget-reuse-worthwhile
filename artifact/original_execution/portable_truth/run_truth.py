"""Explicit exact-truth regeneration, with pinned native payload and frozen output gates."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

HERE=Path(__file__).resolve().parent
ROLES=('source_design','target_selection','target_certification','target_evaluation')

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def load(path,name,expected):
    if digest(path)!=expected:raise ValueError('Code identity: '+path.name)
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def pinned_payload(site,lock):
    site=site.resolve(strict=True)
    for rel,expected in lock['installed_payload'].items():
        path=(site/rel).resolve(strict=True)
        if not path.is_relative_to(site) or digest(path)!=expected:
            raise ValueError('Native package payload mismatch: '+rel)
    return len(lock['installed_payload'])

def native_environment(lock):
    if platform.system()!='Linux' or platform.machine()!='x86_64' or list(sys.version_info[:2])!=[3,11]:
        raise ValueError('Pinned wheel requires Linux x86_64 / Python 3.11')
    if any(k in os.environ for k in ('FAISS_OPT_LEVEL','FAISS_DISABLE_CPU_FEATURES','LD_PRELOAD')):
        raise ValueError('Explicit dispatch/preload override not part of this entry')
    if any(n=='faiss' or n.startswith('faiss.') for n in sys.modules):raise ValueError('Faiss already imported')
    import importlib.metadata
    dist=importlib.metadata.distribution('faiss-cpu')
    if dist.version!=lock['distribution_version']:raise ValueError('Wrong wheel distribution')
    site=Path(dist.locate_file('')).resolve(strict=True)
    count=pinned_payload(site,lock)
    spec=importlib.util.find_spec('faiss')
    if spec is None or Path(spec.origin).resolve()!=(site/'faiss/__init__.py').resolve():
        raise ValueError('Shadowed Faiss module')
    import faiss
    import numpy as np
    import h5py
    if faiss.__version__!=lock['module_version'] or np.__version__!=lock['numpy_version'] or h5py.__version__!=lock['h5py_version']:
        raise ValueError('Library version mismatch')
    loaded=[]
    for name,module in tuple(sys.modules.items()):
        if name.startswith('faiss._swigfaiss'):
            p=Path(module.__file__).resolve(strict=True);rel=p.relative_to(site).as_posix()
            if rel not in lock['installed_payload'] or digest(p)!=lock['installed_payload'][rel]:raise ValueError('Unexpected native module')
            loaded.append({'file':rel,'sha256':digest(p)})
    if len(loaded)!=1:raise ValueError('Expected one selected native module')
    return faiss,np,h5py,{'payload_files_checked':count,'loaded_native':loaded,
                         'compile_options':faiss.get_compile_options(),
                         'historical_dispatch_attested':False}

def inputs(input_dir,adapter_dir,cfg):
    regpath=adapter_dir/'registry.json'
    if digest(regpath)!=cfg['input_registry_sha256']:raise ValueError('Input registry changed')
    reg=json.loads(regpath.read_text())
    adapter=load(adapter_dir/'prepare_inputs.py','truth_input_adapter',cfg['input_adapter_sha256'])
    start=json.loads((input_dir/'start.json').read_text())
    done=json.loads((input_dir/'completed.json').read_text())
    if (input_dir/'failure.json').exists():raise ValueError('Preparation failure retained')
    if start['status']!='NEW_INPUT_PREPARATION_STARTED' or done['status']!='NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED':
        raise ValueError('Not a completed new preparation receipt')
    if start['adapter_sha256']!=cfg['input_adapter_sha256'] or start['registry_sha256']!=cfg['input_registry_sha256']:
        raise ValueError('Preparation code/registry receipt mismatch')
    member=input_dir/'tcp_fresh_roles_v1/membership.npz'
    if digest(member)!=reg['expected_membership_sha256'] or done['membership_sha256']!=reg['expected_membership_sha256']:
        raise ValueError('Membership identity mismatch')
    core=adapter.load_core(reg);np=core.np
    partitions={}
    with np.load(member,allow_pickle=False) as arrays:
        expected_keys={p+'_'+r+'_ids' for p in reg['datasets'] for r in ROLES}|{p+'_base_exclusion_ids' for p in reg['datasets']}
        if set(arrays.files)!=expected_keys:raise ValueError('Unexpected membership keys')
        for p,row in reg['datasets'].items():
            new,allids,base=adapter.partition(reg,row,core)
            if done['datasets'][p]['base_count']!=len(base):raise ValueError('Receipt base count')
            for r in ROLES:
                if not np.array_equal(arrays[p+'_'+r+'_ids'],new[r]):raise ValueError('Role arrays differ')
                q=input_dir/'tcp_fresh_profiles_v1'/(p+'_'+r)/'queries.qbin'
                record=done['datasets'][p]['queries'][r]
                if digest(q)!=record['sha256'] or q.stat().st_size!=record['bytes']:raise ValueError('Query file drift')
                if r=='target_evaluation' and any(record[k]!=reg['evaluation_qbin_pins'][p][k] for k in ('bytes','sha256')):
                    raise ValueError('Evaluation input identity')
            if arrays[p+'_base_exclusion_ids'].tolist()!=row['expected_base_exclusions']:raise ValueError('Exclusions differ')
            partitions[p]=(new,allids,base)
    return adapter,reg,partitions

def check_truth(path,ids,base,metric,np):
    with np.load(path,allow_pickle=False) as a:
        if set(a.files)!={'query_ids','neighbor_raw_ids','scores'} or not np.array_equal(a['query_ids'],ids):raise ValueError('Truth query identity')
        top=a['neighbor_raw_ids'];scores=a['scores']
        if top.dtype!=np.int64 or scores.dtype!=np.float32 or top.shape!=(len(ids),10) or scores.shape!=top.shape:
            raise ValueError('Truth shape/dtype')
        if not np.all(np.isin(top,base)) or np.any(top==ids[:,None]):raise ValueError('Truth outside retained base')
        if np.any(np.diff(np.sort(top,axis=1),axis=1)==0) or not np.all(np.isfinite(scores)):raise ValueError('Truth duplicates/nonfinite')
        delta=np.diff(scores,axis=1)
        if (metric=='squared_l2' and np.any(delta < -1e-4)) or (metric=='inner_product' and np.any(delta>1e-4)):raise ValueError('Truth score order')

def score_reference(queries,neighbors,scores,metric,np):
    q=queries.astype(np.float64);b=neighbors.astype(np.float64)
    if metric=='squared_l2':
        diff=q[:,None,:]-b;reference=np.einsum('qkd,qkd->qk',diff,diff)
        scale=np.sum((np.abs(q[:,None,:])+np.abs(b))**2,axis=2)
    else:
        reference=np.sum(q[:,None,:]*b,axis=2)
        scale=np.sum(np.abs(q[:,None,:])*np.abs(b),axis=2)
    tolerance=128*np.finfo(np.float32).eps*scale+1e-3
    if not np.all(np.isfinite(reference)) or not np.all(np.isfinite(scores)) or np.any(np.abs(scores-reference)>tolerance):
        raise ValueError('Independent raw-vector public-score check')
    return {'max_abs_score_error':float(np.max(np.abs(scores-reference))),
            'max_allowed_tolerance':float(np.max(tolerance))}

def audit_scores(source,out,prefix,row,np,h5py,cfg):
    collector=load(HERE/'historical_collect.py','truth_vector_collector',cfg['collect_sha256'])
    loaded={};wanted=set()
    for role in ROLES:
        with np.load(out/(prefix+'_'+role+'.npz'),allow_pickle=False) as a:
            ids=a['query_ids'];top=a['neighbor_raw_ids'];scores=a['scores']
        loaded[role]=(ids,top,scores);wanted.update(map(int,ids));wanted.update(map(int,top.flat))
    with h5py.File(source,'r') as h:
        train=h['train']
        if list(train.shape)!=row['train_shape'] or str(train.dtype)!='float32':raise ValueError('Score audit source shape')
        ordered,vec=collector.collect_vectors(train,wanted)
    records={}
    for role,(ids,top,scores) in loaded.items():
        records[role]=score_reference(vec[np.searchsorted(ordered,ids)],vec[np.searchsorted(ordered,top)],scores,row['metric'],np)
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=('check-native','generate'))
    ap.add_argument('--input-adapter',type=Path);ap.add_argument('--prepared',type=Path)
    ap.add_argument('--dataset',choices=('sift','arxiv'));ap.add_argument('--source',type=Path)
    ap.add_argument('--output',type=Path);ap.add_argument('--outstanding-growth-bytes',type=int)
    ap.add_argument('--authorize-exact-truth',action='store_true');args=ap.parse_args()
    cfg=json.loads((HERE/'config.json').read_text())
    if digest(HERE/'native_lock.json')!=cfg['native_lock_sha256']:raise ValueError('Native lock changed')
    lock=json.loads((HERE/'native_lock.json').read_text())
    if args.command=='check-native':
        if any((args.input_adapter,args.prepared,args.dataset,args.source,args.output,args.outstanding_growth_bytes is not None,args.authorize_exact_truth)):
            ap.error('check-native takes no dataset or output')
        for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
        _,_,_,native=native_environment(lock)
        print(json.dumps({'status':'PASS_NATIVE_PAYLOAD_AND_IMPORT','native':native,'dataset_reads':0,'searches':0}));return
    if not all((args.input_adapter,args.prepared,args.dataset,args.source,args.output,args.outstanding_growth_bytes is not None,args.authorize_exact_truth)):
        ap.error('generate needs adapter, preparation, dataset, source, new output, outstanding budget and explicit opt-in')
    if sys.flags.optimize:raise ValueError('No optimized Python')
    plan=cfg['resource_plan']
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]=str(plan['faiss_threads'])
    adapter=load(args.input_adapter/'prepare_inputs.py','truth_resource_adapter',cfg['input_adapter_sha256'])
    resource_cfg={'python_minor':[3,11],'resource_plan':dict(plan,max_output_growth_bytes=plan['max_total_output_growth_bytes'])}
    out,snapshot=adapter.preflight(resource_cfg,args.output,{'raw':args.source,'receipt':args.prepared/'completed.json'},args.outstanding_growth_bytes)
    os.sched_setaffinity(0,set(plan['cpu_affinity']))
    import resource,signal,time
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),
                     (resource.RLIMIT_CPU,plan['cpu_seconds_per_dataset']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    faiss,np,h5py,native=native_environment(lock);faiss.omp_set_num_threads(plan['faiss_threads'])
    adapter,reg,parts=inputs(args.prepared,args.input_adapter,cfg)
    row=reg['datasets'][args.dataset];roles,allids,base=parts[args.dataset]
    core=load(HERE/'historical_truth.py','historical_truth',cfg['core_sha256'])
    out.mkdir(mode=0o700)
    adapter.write_json(out/'start.json',{'status':'NEW_TRUTH_STARTED','native':native,'resources':snapshot,
        'config_sha256':digest(HERE/'config.json'),'adapter_sha256':digest(Path(__file__)),
        'preparation_receipt_sha256':digest(args.prepared/'completed.json'),'dataset':args.dataset,
        'limits':{str(k):list(resource.getrlimit(k)) for k in (resource.RLIMIT_AS,resource.RLIMIT_FSIZE,resource.RLIMIT_CPU,resource.RLIMIT_CORE)},
        'not_historical_first_use':True})
    def timeout(signum,frame):raise TimeoutError('Truth wall limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds_per_dataset']);started=time.monotonic_ns()
    try:
        if digest(args.source)!=row['source_sha256']:raise ValueError('Original HDF5 SHA')
        n,dim=row['train_shape'];keep=np.zeros(n,dtype=bool);keep[base]=True
        result=core.acquire(args.source,n,dim,keep,base,roles,row['metric'],out,args.dataset,faiss,np,h5py)
        for role in ROLES:
            path=out/(args.dataset+'_'+role+'.npz')
            check_truth(path,roles[role],base,row['metric'],np)
            if digest(path)!=cfg['truth_sha256'][args.dataset][role]:raise ValueError('Frozen truth SHA differs; stop, no retry/repinning')
        score_checks=audit_scores(args.source,out,args.dataset,row,np,h5py,cfg)
        if sum(p.stat().st_size for p in out.iterdir() if p.is_file())>plan['max_total_output_growth_bytes']:raise ValueError('Output growth')
        masks=[next(s for s in p.read_text().splitlines() if s.startswith('Cpus_allowed_list:')).split(':')[1].strip() for p in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'4-19'}:raise ValueError('All-thread affinity mismatch')
        adapter.write_json(out/'completed.json',dict(result,status='NEW_EXACT_TRUTH_MATCHES_FROZEN_BYTES',dataset=args.dataset,
            source_sha256=row['source_sha256'],membership_sha256=reg['expected_membership_sha256'],thread_masks=masks,
            elapsed_ns=time.monotonic_ns()-started,ANN_runs=0,independent_score_checks=score_checks,
            global_top10_independently_recomputed=False,new_receipt_not_historical_audit=True))
    except BaseException as e:
        adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_PROFILES_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)

if __name__=='__main__':main()
