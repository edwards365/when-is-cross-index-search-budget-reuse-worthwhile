"""Portable E2 cache stage. Check never measures; measure is explicit opt-in."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import struct
import sys
import zipfile

HERE = Path(__file__).resolve().parent
GIB = 1024**3


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20), b''): h.update(block)
    return h.hexdigest()


def pinned(root, item):
    rel = Path(item['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Input paths must be relative descendants')
    root = root.resolve(strict=True)
    path = (root/rel).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Input escaped selected root')
    if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
        raise ValueError('Input identity mismatch: '+item['path'])
    return path


def load_npz(np, path):
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members)>64 or len({m.filename for m in members})!=len(members):
            raise ValueError('Invalid array archive')
        if sum(m.file_size for m in members)>64*1024**2:
            raise ValueError('Array expansion exceeds stage input cap')
    with np.load(path,allow_pickle=False) as arrays:
        return {k:arrays[k].copy() for k in arrays.files}


def query_rows(np, path, count, dimension):
    blob = path.read_bytes()
    if len(blob)<24: raise ValueError('Truncated query header')
    magic,n,d = struct.unpack('<8sQQ',blob[:24])
    if magic!=b'E1AQ0001' or (n,d)!=(count,dimension) or len(blob)!=24+n*(8+4*d):
        raise ValueError('Query header/shape/EOF mismatch')
    ids=[];queries=[]
    for i in range(n):
        start=24+i*(8+4*d)
        ids.append(struct.unpack('<q',blob[start:start+8])[0])
        queries.append(blob[start+8:start+8+4*d])
    if len(set(ids))!=n or min(ids)<0 or len(set(queries))!=n:
        raise ValueError('Duplicate/negative query IDs or duplicate query bytes')
    if not all(np.isfinite(np.frombuffer(q,dtype='<f4')).all() for q in queries):
        raise ValueError('Nonfinite query')
    return ids,queries


def check_inputs(spec, root, np):
    member=load_npz(np,pinned(root,spec['membership']))
    checked=[]
    for prefix, case in spec['datasets'].items():
        paths={k:pinned(root,v) for k,v in case['files'].items()}
        ids,queries=query_rows(np,paths['queries'],spec['historical_query_count'],case['dimension'])
        truth=load_npz(np,paths['truth']);profile=load_npz(np,paths['profile'])
        n=len(ids)
        if not np.array_equal(member[prefix+'_target_evaluation_ids'],ids):
            raise ValueError('Membership/query order mismatch')
        if not np.array_equal(truth['query_ids'],ids) or not np.array_equal(profile['query_ids'],ids):
            raise ValueError('Truth/profile query order mismatch')
        for key in ('neighbor_raw_ids','scores'):
            if truth[key].shape!=(n,10): raise ValueError('Truth shape')
        if truth['neighbor_raw_ids'].dtype.kind not in 'iu' or truth['scores'].dtype.kind!='f':
            raise ValueError('Truth dtype')
        if not np.isfinite(truth['scores']).all() or (truth['neighbor_raw_ids']<0).any():
            raise ValueError('Invalid truth contents')
        if not all(len(set(row.tolist()))==10 for row in truth['neighbor_raw_ids']):
            raise ValueError('Duplicate neighbor IDs')
        if profile['hits'].shape!=(8,11,n) or profile['ndc'].shape!=(8,11,n) or profile['topk'].shape!=(8,11,n,10):
            raise ValueError('Profile shape')
        checked.append({'dataset':prefix,'queries':n,'dimension':case['dimension'],
                        'profile_payload_bytes':sum(profile[k].nbytes for k in ('hits','ndc','topk'))})
    return checked


def load_core(spec):
    path=HERE/'historical_cache.py'
    if digest(path)!=spec['core_sha256']: raise ValueError('Extracted core identity mismatch')
    module_spec=importlib.util.spec_from_file_location('historical_cache',path)
    module=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def bind_inputs(core,spec,root,np):
    core.np=np
    core.input_path=lambda conf,prefix,kind:pinned(root,conf['datasets'][prefix]['files'][kind])
    core.load_input=lambda conf,prefix,kind:load_npz(np,core.input_path(conf,prefix,kind))


def require_new_output(path, input_root):
    parent=path.parent.resolve(strict=True)
    target=parent/path.name
    if path.exists() or path.is_symlink() or not path.name or path.name in ('.','..'):
        raise ValueError('Output must be a new named directory; no retry/overwrite')
    inputs=input_root.resolve(strict=True)
    if target.is_relative_to(inputs) or inputs.is_relative_to(target):
        raise ValueError('Outputs must be separate from immutable inputs')
    return target


def measure(spec,root,out,growth):
    if sys.flags.optimize: raise ValueError('Python -O disables historical checks')
    if platform.system()!='Linux' or list(sys.version_info[:2])!=spec['python_minor']:
        raise ValueError('Measurement requires Linux / historical Python 3.11 minor')
    if growth<spec['resources']['all_output_growth_bytes'] or growth>128*GIB:
        raise ValueError('Declare total project outstanding growth, including this stage; cap 128 GiB')
    out=require_new_output(out,root)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='1'
    import resource
    import signal
    import time
    # CPU 4 and original process limits are unchanged. No ANN or model is imported.
    if 4 not in os.sched_getaffinity(0):
        raise ValueError('CPU 4 is outside the existing allowed affinity')
    os.sched_setaffinity(0,{4})
    core=load_core(spec);core.CAMPAIGN=out.parent
    conf=json.loads(json.dumps(spec));conf['resources']['project_growth_bytes']=growth
    fresh=core.fresh_resources(conf)
    for kind,cap in [(resource.RLIMIT_AS,spec['resources']['address_space_bytes']),
                     (resource.RLIMIT_FSIZE,spec['resources']['max_file_bytes']),
                     (resource.RLIMIT_CPU,spec['resources']['cpu_seconds']), (resource.RLIMIT_CORE,0)]:
        soft,hard=resource.getrlimit(kind)
        cap=min([cap]+[v for v in (soft,hard) if v>=0])
        resource.setrlimit(kind,(cap,cap))
    import numpy as np
    if np.__version__!=spec['numpy_version']: raise ValueError('Historical NumPy version mismatch')
    checked=check_inputs(spec,root,np)
    bind_inputs(core,spec,root,np)
    out.mkdir();records=out/'records';records.mkdir()
    core.write_json(out/'start.json',{'status':'NEW_MEASUREMENT_STARTED','inputs':checked,
        'core_sha256':spec['core_sha256'],'adapter_sha256':digest(Path(__file__)),
        'python':sys.version,'numpy':np.__version__,'platform':platform.system(),
        'affinity':sorted(os.sched_getaffinity(0)),'resources':fresh,
        'limits':{str(k):resource.getrlimit(k) for k in (resource.RLIMIT_AS,resource.RLIMIT_CPU,resource.RLIMIT_FSIZE,resource.RLIMIT_CORE)},
        'timing_identity':'New-host measurement, not the paper values or a replacement for historical evidence'})
    def expired(signum,frame): raise TimeoutError('Historical 1800s wall cap')
    signal.signal(signal.SIGALRM,expired);signal.alarm(spec['resources']['wall_seconds'])
    start=time.monotonic_ns()
    try:
        report=core.e2(conf,records)
        files={p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in records.iterdir() if p.is_file()}
        if sum(v['bytes'] for v in files.values())>spec['resources']['all_output_growth_bytes']:
            raise ValueError('Output growth cap exceeded')
        masks=[next(x for x in p.read_text().splitlines() if x.startswith('Cpus_allowed_list:')).split(':')[1].strip()
               for p in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'4'}: raise ValueError('Final all-thread affinity check failed')
        core.write_json(out/'completed.json',{'status':'NEW_CACHE_STAGE_COMPLETED','report':report,'files':files,
            'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'sampled_thread_masks':masks,'historical_results_replaced':False})
    except BaseException as exc:
        core.write_json(out/'failure.json',{'status':'FAILED_RETAIN_OUTPUT_NO_RETRY','error':repr(exc)})
        raise
    finally: signal.alarm(0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['check','measure'])
    parser.add_argument('--input-root',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--authorize-new-timing',action='store_true')
    parser.add_argument('--outstanding-growth-bytes',type=int)
    args=parser.parse_args()
    spec=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    if args.command=='check':
        if args.output or args.authorize_new_timing or args.outstanding_growth_bytes is not None:
            parser.error('check accepts input-root only and never measures or writes')
        import numpy as np
        load_core(spec)
        rows=check_inputs(spec,args.input_root,np)
        print(json.dumps({'status':'PASS_PINNED_CACHE_INPUT_SCHEMA','rows':rows,'timing_runs':0}))
    else:
        if not args.authorize_new_timing or args.output is None or args.outstanding_growth_bytes is None:
            parser.error('measure requires explicit timing opt-in, fresh output, and total outstanding growth')
        measure(spec,args.input_root,args.output,args.outstanding_growth_bytes)


if __name__=='__main__': main()
