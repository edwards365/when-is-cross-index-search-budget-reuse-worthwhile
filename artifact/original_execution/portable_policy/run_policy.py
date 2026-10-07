"""New certify/evaluate receipts with frozen rules; no ANN, fitting or tuning."""
import argparse, hashlib, importlib.util, json, math, os, platform, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def load(p,name,pin):
    if digest(p)!=pin: raise ValueError('Code identity')
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def same_rows(actual,expected):
    if len(actual)!=len(expected): raise ValueError('Row count')
    for a,b in zip(actual,expected):
        if set(a)!=set(b): raise ValueError('Row fields')
        for k,v in b.items():
            if isinstance(v,float):
                if not isinstance(a[k],(int,float)) or not math.isfinite(a[k]) or abs(a[k]-v)>1e-12: raise ValueError('Numeric row mismatch: '+k)
            elif a[k]!=v: raise ValueError('Discrete row mismatch: '+k)
def validated_lock(folder,expected_sha,cfg,expected_rows):
    if (folder/'failure.json').exists(): raise ValueError('Failed lock stage')
    path=folder/'completed.json'
    if not expected_sha or digest(path)!=expected_sha: raise ValueError('Explicit lock SHA mismatch')
    lock=json.loads(path.read_text())
    if lock['status']!='NEW_QUALIFICATION_LOCKED_BEFORE_EVALUATION_READ' or lock['config_sha256']!=digest(HERE/'config.json'):
        raise ValueError('Lock status/config')
    same_rows(lock['rows'],expected_rows)
    return lock
def role_inputs(roots,role,cfg):
    audit={'rows':[]};receipts={}
    for prefix,folder in roots.items():
        done=folder/'completed.json';record=json.loads(done.read_text());name=prefix+'_'+role;path=folder/(name+'.npz');pin=cfg['expected_arrays'][name]
        if (folder/'failure.json').exists() or record['status']!='NEW_ARRAY_MATCHES_FROZEN_BYTES': raise ValueError('New array stage required')
        if (record['dataset'],record['role'])!=(prefix,role) or record['sha256']!=pin['sha256'] or record['bytes']!=pin['bytes']: raise ValueError('Array receipt role/identity')
        if path.stat().st_size!=pin['bytes'] or digest(path)!=pin['sha256']: raise ValueError('Frozen array identity')
        audit['rows'].append({'dataset':cfg['datasets'][prefix],'role':role,'array_path':str(path.resolve()),'array_sha256':pin['sha256']})
        receipts[prefix]={'receipt_sha256':digest(done),'array_sha256':pin['sha256']}
    return audit,receipts
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('certify','evaluate'))
    for n in ('sift-array-root','arxiv-array-root','input-adapter','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--lock',type=Path);p.add_argument('--lock-sha256');p.add_argument('--outstanding-growth-bytes',type=int,required=True)
    p.add_argument('--authorize-policy-stage',action='store_true');a=p.parse_args()
    if not a.authorize_policy_stage:p.error('Explicit new policy stage opt-in required')
    if a.phase=='certify' and (a.lock or a.lock_sha256):p.error('Certification does not accept an evaluation/lock input')
    if a.phase=='evaluate' and not (a.lock and a.lock_sha256):p.error('Evaluation requires already locked receipt and its SHA')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 without -O required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    cfg=json.loads((HERE/'config.json').read_text());expected_path=HERE/'expected_certification_rows.json'
    if digest(expected_path)!=cfg['expected_rows_sha256'] or digest(HERE/'policy.json')!=cfg['policy_sha256']:raise ValueError('Frozen policy/reference identity')
    expected=json.loads(expected_path.read_text());policy=json.loads((HERE/'policy.json').read_text())
    # Validate the lock BEFORE opening either evaluation array or its receipt.
    lock=validated_lock(a.lock,a.lock_sha256,cfg,expected) if a.phase=='evaluate' else None
    adapter=load(a.input_adapter/'prepare_inputs.py','policy_resources',cfg['input_adapter_sha256'])
    roots={'sift':a.sift_array_root,'arxiv':a.arxiv_array_root}
    out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':cfg['resource_plan']},a.output,
        {k:v/'completed.json' for k,v in roots.items()},a.outstanding_growth_bytes)
    import resource,signal,time
    plan=cfg['resource_plan']
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);adapter.write_json(out/'start.json',{'phase':a.phase,'config_sha256':digest(HERE/'config.json'),'adapter_sha256':digest(Path(__file__)),
        'resources':snapshot,'prior_lock_sha256':a.lock_sha256,'historical_auditor_rerun':False})
    def timeout(signum,frame):raise TimeoutError('Policy stage wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        import numpy as np,scipy
        if np.__version__!=cfg['numpy'] or scipy.__version__!=cfg['scipy']:raise ValueError('Pinned analysis libraries')
        core=load(HERE/'historical_policy.py','new_policy_core',cfg['core_sha256'])
        role='target_certification' if a.phase=='certify' else 'target_evaluation'
        audit,receipts=role_inputs(roots,role,cfg)
        started=time.monotonic_ns()
        if a.phase=='certify':
            rows=core.certify(audit,policy);same_rows(rows,expected)
            status='NEW_QUALIFICATION_LOCKED_BEFORE_EVALUATION_READ'
        else:
            if any(r['decision']=='UNDEPLOYABLE' for r in lock['rows']):raise ValueError('No endpoint proxy allowed for undeployable targets')
            rows=core.evaluate(audit,policy,lock);status='NEW_LOCKED_POLICY_EVALUATION_COMPLETE'
        adapter.write_json(out/'completed.json',{'status':status,'config_sha256':digest(HERE/'config.json'),'rows':rows,
            'new_input_receipts':receipts,'prior_lock_sha256':a.lock_sha256,'new_compute_elapsed_ns':time.monotonic_ns()-started,
            'historical_timing_replaced':False,'global_or_future_query_guarantee':False,
            'evaluation_failure_event':'candidate-or-endpoint union for TCP, endpoint for ENDPOINT; not generally raw candidate failure'})
    except BaseException as e:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
