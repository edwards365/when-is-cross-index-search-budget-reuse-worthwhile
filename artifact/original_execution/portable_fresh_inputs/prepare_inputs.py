"""Fresh-query role/base/query preparation; never imports Faiss or runs ANN."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import struct
import sys

HERE=Path(__file__).resolve().parent
ROLES=('source_design','target_selection','target_certification','target_evaluation')
GIB=1024**3


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()


def load_core(cfg):
    path=HERE/'historical_roles.py'
    if digest(path)!=cfg['core_sha256']:raise ValueError('Historical core identity mismatch')
    spec=importlib.util.spec_from_file_location('historical_roles',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def partition(cfg,row,core):
    np=core.np;n=row['train_shape'][0];counts=cfg['role_counts'];total=sum(counts.values())
    all_roles={}
    for label,key in [('old','old_roles'),('e1b','e1b_roles')]:
        for role in ROLES:
            ids=row[key][role]
            if len(ids)!=counts[role] or ids!=sorted(set(ids)):
                raise ValueError('Prior role length/order/duplicate')
            for i in ids:
                if not isinstance(i,int) or i<0 or i>=n or i in all_roles:
                    raise ValueError('Prior role range/overlap')
                all_roles[i]=label+'_'+role
    old_ex=row['old_base_exclusions']
    if old_ex!=sorted(set(old_ex)) or any(i<0 or i>=n or i in all_roles for i in old_ex):
        raise ValueError('Prior exclusion range/overlap')
    unavailable=set(all_roles)|set(old_ex)
    available=np.asarray(sorted(set(range(n))-unavailable),dtype=np.int64)
    new=core.fresh_ids(row['dataset'],cfg['seed'],available,counts)
    for role in ROLES:
        if new[role].tolist()!=row['expected_fresh_roles'][role]:
            raise ValueError('Regenerated role differs from frozen IDs')
        for i in new[role]:
            i=int(i)
            if i in all_roles:raise ValueError('Fresh role overlap')
            all_roles[i]='new_'+role
    if len(all_roles)!=3*total:raise ValueError('All-role count')
    ex=row['expected_base_exclusions']
    if ex!=sorted(set(ex)) or any(i<0 or i>=n or i in all_roles for i in ex):
        raise ValueError('Frozen exclusion range/overlap')
    if not set(old_ex).issubset(ex):raise ValueError('Prior exclusions not retained')
    keep=np.ones(n,dtype=bool)
    keep[np.asarray(sorted(all_roles),dtype=np.int64)]=False
    keep[np.asarray(ex,dtype=np.int64)]=False
    base=np.flatnonzero(keep).astype(np.int64)
    if len(base)!=row['expected_base_count']:raise ValueError('Frozen base count mismatch')
    return new,all_roles,base


def train_only(handle,shape):
    train=handle['train']
    if list(train.shape)!=shape or str(train.dtype)!='float32':
        raise ValueError('Train shape/dtype mismatch')
    return train


def scan_and_check(train,row,all_roles,core):
    np=core.np
    duplicates,counterparts=core.scan_content(train,np.asarray(sorted(all_roles),dtype=np.int64),all_roles)
    if duplicates:raise ValueError('Query-query content collision; no replacement permitted')
    excluded=sorted({int(x[1]) for x in counterparts}|set(row['old_base_exclusions']))
    if excluded!=row['expected_base_exclusions']:
        raise ValueError('Full content scan differs from frozen exclusions')
    return np.asarray(excluded,dtype=np.int64)


def write_queries(train,ids,path,np):
    # Encoding matches run_tcp_fresh_profiles_v1.py; no normalization or dtype promotion.
    vectors=np.ascontiguousarray(train[ids.tolist()],dtype=np.float32)
    with path.open('xb') as stream:
        stream.write(b'E1AQ0001')
        stream.write(struct.pack('<QQ',len(ids),vectors.shape[1]))
        for raw_id,vector in zip(ids,vectors):
            stream.write(struct.pack('<q',int(raw_id)))
            stream.write(vector.astype('<f4',copy=False).tobytes())
        stream.flush();os.fsync(stream.fileno())
    return {'sha256':digest(path),'bytes':path.stat().st_size,'count':len(ids)}


def preflight(cfg,output,sources,growth):
    if platform.system()!='Linux' or list(sys.version_info[:2])!=cfg['python_minor'] or sys.flags.optimize:
        raise ValueError('Preparation requires Linux / Python 3.11, without -O')
    plan=cfg['resource_plan']
    if output.exists() or output.is_symlink():raise FileExistsError('Exclusive output exists')
    parent=output.parent.resolve(strict=True);out=parent/output.name
    if output.name in ('','..','.') or any(p.resolve(strict=True).is_relative_to(out) for p in sources.values()):
        raise ValueError('Output conflicts with inputs')
    if not plan['max_output_growth_bytes']<=growth<=plan['remaining_project_growth_limit_bytes']:
        raise ValueError('Invalid total outstanding growth; include this stage')
    import time
    mem={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if ':' in s}
    rss=0;unreadable=0
    for p in Path('/proc').glob('[0-9]*/status'):
        try:
            rss+=sum(int(s.split()[1])*1024 for s in p.read_text().splitlines() if s.startswith('VmRSS:'))
        except (OSError,ValueError):unreadable+=1
    stat=lambda:list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    first=stat();time.sleep(.2);diff=[b-a for a,b in zip(first,stat())]
    iowait=diff[4]/sum(diff) if sum(diff)>0 else None
    v=os.statvfs(parent);free=v.f_bavail*v.f_frsize
    if mem['MemAvailable']<160*GIB or mem['MemAvailable']-plan['expected_rss_bytes']<80*GIB:
        raise OSError('RAM availability floor')
    if rss+64*GIB>.6*mem['MemTotal']:raise OSError('Machine RSS/reserve gate')
    if free-growth<plan['minimum_projected_disk_free_bytes']:raise OSError('Projected disk floor')
    if iowait is None or iowait>=.15:raise OSError('I/O wait gate')
    cpus=set(plan['cpu_affinity'])
    if not cpus.issubset(os.sched_getaffinity(0)):raise OSError('Unavailable historical CPU affinity')
    return out,{'available_ram_bytes':mem['MemAvailable'],'observed_machine_rss_bytes':rss,
                'unreadable_proc_status':unreadable,'disk_free_bytes':free,'declared_outstanding_growth':growth,
                'iowait':iowait,'snapshot_not_continuous_quota':True}


def write_json(path,data):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def prepare(cfg,sources,output,growth):
    out,snapshot=preflight(cfg,output,sources,growth)
    plan=cfg['resource_plan']
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    os.sched_setaffinity(0,set(plan['cpu_affinity']))
    import resource
    import signal
    import time
    for kind,cap in [(resource.RLIMIT_AS,plan['address_space_bytes']),
                     (resource.RLIMIT_FSIZE,plan['file_size_bytes']),
                     (resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)]:
        old=resource.getrlimit(kind);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    import h5py
    core=load_core(cfg);np=core.np
    if np.__version__!=cfg['numpy_version'] or h5py.__version__!=cfg['h5py_version']:
        raise ValueError('Pinned NumPy/h5py versions required')
    out.mkdir(mode=0o700)
    write_json(out/'start.json',{'status':'NEW_INPUT_PREPARATION_STARTED','resources':snapshot,
        'adapter_sha256':digest(Path(__file__)),'registry_sha256':digest(HERE/'registry.json'),
        'python':sys.version,'numpy':np.__version__,'h5py':h5py.__version__,
        'affinity':sorted(os.sched_getaffinity(0)),'forbidden_hdf5_keys':cfg['forbidden_hdf5_keys'],
        'not_historical_first_use':True})
    def timeout(signum,frame):raise TimeoutError('Frozen wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    arrays={};records={};started=time.monotonic_ns()
    try:
        for prefix,row in cfg['datasets'].items():
            source=sources[prefix]
            if digest(source)!=row['source_sha256']:raise ValueError('Raw HDF5 SHA mismatch')
            new,all_roles,base=partition(cfg,row,core)
            with h5py.File(source,'r') as handle:
                train=train_only(handle,row['train_shape'])
                excluded=scan_and_check(train,row,all_roles,core)
                for role in ROLES:arrays[prefix+'_'+role+'_ids']=new[role]
                arrays[prefix+'_base_exclusion_ids']=excluded
                roles={}
                for role in ROLES:
                    folder=out/'tcp_fresh_profiles_v1'/(prefix+'_'+role);folder.mkdir(parents=True)
                    roles[role]=write_queries(train,new[role],folder/'queries.qbin',np)
                    if role=='target_evaluation':
                        expected=cfg['evaluation_qbin_pins'][prefix]
                        if any(roles[role][k]!=expected[k] for k in ('bytes','sha256')):
                            raise ValueError('Evaluation qbin differs from frozen bytes')
            records[prefix]={'base_count':len(base),'base_raw_id_order_sha256':hashlib.sha256(base.astype('<i8').tobytes()).hexdigest(),
                             'exclusions':len(excluded),'all_query_count':len(all_roles),'queries':roles}
        folder=out/'tcp_fresh_roles_v1';folder.mkdir()
        path=folder/'membership.npz'
        with path.open('xb') as f:np.savez_compressed(f,**arrays);f.flush();os.fsync(f.fileno())
        if digest(path)!=cfg['expected_membership_sha256']:
            raise ValueError('Membership serialization differs; no automatic repinning')
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>plan['max_output_growth_bytes']:
            raise ValueError('Output growth cap')
        masks=[next(s for s in p.read_text().splitlines() if s.startswith('Cpus_allowed_list:')).split(':')[1].strip()
               for p in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'2'}:raise ValueError('Final all-thread affinity check')
        write_json(out/'completed.json',{'status':'NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED','datasets':records,
            'membership_sha256':digest(path),'elapsed_ns':time.monotonic_ns()-started,'thread_masks':masks,
            'truth_generated':False,'ANN_runs':0,'historical_results_replaced':False})
    except BaseException as exc:
        write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK_NO_RETRY','error':repr(exc)});raise
    finally:signal.alarm(0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check-registry','prepare'])
    parser.add_argument('--sift',type=Path);parser.add_argument('--arxiv',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--authorize-input-preparation',action='store_true')
    parser.add_argument('--outstanding-growth-bytes',type=int)
    args=parser.parse_args();cfg=json.loads((HERE/'registry.json').read_text(encoding='utf-8'))
    if args.command=='check-registry':
        if any((args.sift,args.arxiv,args.output,args.authorize_input_preparation,args.outstanding_growth_bytes is not None)):
            parser.error('check-registry reads packaged registry only')
        core=load_core(cfg)
        if core.np.__version__!=cfg['numpy_version']:raise ValueError('NumPy version mismatch')
        rows=[]
        for prefix,row in cfg['datasets'].items():
            new,all_roles,base=partition(cfg,row,core)
            rows.append({'dataset':prefix,'fresh_queries':sum(map(len,new.values())),'all_queries':len(all_roles),
                         'base_count':len(base),'excluded_content_rows':len(row['expected_base_exclusions'])})
        print(json.dumps({'status':'PASS_FROZEN_ID_RECONSTRUCTION','datasets':rows,'HDF5_reads':0,'ANN_runs':0}))
    else:
        if not all((args.sift,args.arxiv,args.output,args.authorize_input_preparation,args.outstanding_growth_bytes is not None)):
            parser.error('prepare requires both raw inputs, new output, explicit preparation opt-in and total outstanding growth')
        prepare(cfg,{'sift':args.sift,'arxiv':args.arxiv},args.output,args.outstanding_growth_bytes)


if __name__=='__main__':main()
