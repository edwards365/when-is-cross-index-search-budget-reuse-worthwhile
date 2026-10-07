"""Lock simple-baseline decisions before opening final evaluation arrays."""
import argparse, hashlib, importlib.util, json, os, platform, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def load(path,name,pin):
    if digest(path)!=pin:raise ValueError('Code identity')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def validate_array(a,role,cfg,np):
    n=cfg['role_counts'][role];g=len(cfg['build_ids']);k=len(cfg['action_grid'])
    if a['build_ids'].tolist()!=cfg['build_ids'] or a['action_grid'].tolist()!=cfg['action_grid']:raise ValueError('Build/grid order')
    if a['query_ids'].shape!=(n,) or len(set(map(int,a['query_ids'])))!=n:raise ValueError('Query identity')
    if a['hits'].shape!=(g,k,n) or a['ndc'].shape!=(g,k,n):raise ValueError('Response shape')
    if a['hits'].dtype.kind not in 'iu' or a['ndc'].dtype.kind not in 'iu':raise ValueError('Integer metrics required')
    if np.any(a['hits']<0) or np.any(a['hits']>10) or np.any(a['ndc']<=0):raise ValueError('Response range')

def decisions(selection,qualification,dataset,cfg,core,np):
    validate_array(selection,'target_selection',cfg,np);validate_array(qualification,'target_certification',cfg,np)
    if set(map(int,selection['query_ids']))&set(map(int,qualification['query_ids'])):raise ValueError('Selection/qualification overlap')
    rows=[]
    for t,build in enumerate(cfg['build_ids']):
        for method in cfg['methods']:
            if method=='endpoint2400':
                row=dict(decision='REFERENCE',candidate_action=2400,candidate_index=10,deployed_index=10,selection_n=0,certification_n=0)
            else:
                size=250 if method=='TG500' else 500
                row=core.simple_decision(selection['hits'][t],selection['ndc'][t],qualification['hits'][t],size,method)
            row.update(dataset=dataset,target=build,method=method,coverage=int(row['decision']!='UNDEPLOYABLE'));rows.append(row)
    return rows

def evaluate(arrays,rows,dataset,cfg,np):
    validate_array(arrays,'target_evaluation',cfg,np);result=[]
    wanted=[r for r in rows if r['dataset']==dataset]
    if len(wanted)!=len(cfg['build_ids'])*len(cfg['methods']):raise ValueError('Incomplete locked decisions')
    for row in wanted:
        t=cfg['build_ids'].index(row['target']);base={k:row[k] for k in ('dataset','target','method','decision','coverage')}
        if not row['coverage']:
            result.append(dict(base,raw_failures=None,raw_risk=None,mean_ndc=None,action=None));continue
        a=row['deployed_index']
        if not 0<=a<len(cfg['action_grid']):raise ValueError('Invalid deployment index')
        fail=arrays['hits'][t,a]<10
        result.append(dict(base,raw_failures=int(fail.sum()),raw_risk=float(fail.mean()),
            mean_ndc=float(arrays['ndc'][t,a].astype(float).mean()),action=cfg['action_grid'][a]))
    return result

def validated_lock(folder,pin,cfg,expected,helper):
    if not folder or not pin:raise ValueError('Previously locked receipt required')
    path=folder/'completed.json'
    if (folder/'failure.json').exists() or digest(path)!=pin:raise ValueError('Lock identity/failure')
    obj=json.loads(path.read_text(encoding='utf-8'))
    if obj['status']!='NEW_BASELINES_LOCKED_BEFORE_EVALUATION_READ' or obj['config_sha256']!=digest(HERE/'config.json'):raise ValueError('Lock stage/config')
    helper.same_rows(obj['rows'],expected)
    return obj

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('lock','evaluate'))
    for name in ('input-adapter','policy-adapter','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('sift-selection','arxiv-selection','sift-qualification','arxiv-qualification','sift-evaluation','arxiv-evaluation','lock'):p.add_argument('--'+name,type=Path)
    p.add_argument('--lock-sha256');p.add_argument('--outstanding-growth-bytes',type=int,required=True)
    p.add_argument('--authorize-baseline-stage',action='store_true');args=p.parse_args()
    if not args.authorize_baseline_stage:p.error('Explicit new baseline stage opt-in required')
    if args.phase=='lock':
        if any((args.sift_evaluation,args.arxiv_evaluation,args.lock,args.lock_sha256)):p.error('Lock cannot accept evaluation inputs')
        if not all((args.sift_selection,args.arxiv_selection,args.sift_qualification,args.arxiv_qualification)):p.error('Both selection and qualification role roots required')
    else:
        if any((args.sift_selection,args.arxiv_selection,args.sift_qualification,args.arxiv_qualification)):p.error('Evaluation cannot change calibration')
        if not all((args.sift_evaluation,args.arxiv_evaluation,args.lock,args.lock_sha256)):p.error('Evaluation needs prior lock SHA and both evaluation roots')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 without -O required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    cfg=json.loads((HERE/'config.json').read_text());reference=HERE/'expected_decisions.json'
    if digest(reference)!=cfg['expected_decisions_sha256']:raise ValueError('Expected decisions identity')
    expected=json.loads(reference.read_text());helper=load(args.policy_adapter/'run_policy.py','baseline_receipts',cfg['policy_adapter_sha256'])
    lock=validated_lock(args.lock,args.lock_sha256,cfg,expected,helper) if args.phase=='evaluate' else None
    adapter=load(args.input_adapter/'prepare_inputs.py','baseline_resources',cfg['input_adapter_sha256'])
    roots=({'target_selection':{'sift':args.sift_selection,'arxiv':args.arxiv_selection},'target_certification':{'sift':args.sift_qualification,'arxiv':args.arxiv_qualification}}
        if args.phase=='lock' else {'target_evaluation':{'sift':args.sift_evaluation,'arxiv':args.arxiv_evaluation}})
    inputs={r+'_'+ds:folder/'completed.json' for r,items in roots.items() for ds,folder in items.items()}
    out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':cfg['resource_plan']},args.output,inputs,args.outstanding_growth_bytes)
    import resource,signal,time
    plan=cfg['resource_plan']
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);adapter.write_json(out/'start.json',{'phase':args.phase,'config_sha256':digest(HERE/'config.json'),
        'adapter_sha256':digest(Path(__file__)),'resources':snapshot,'prior_lock_sha256':args.lock_sha256})
    def timeout(signum,frame):raise TimeoutError('Baseline wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        import numpy as np,scipy
        if np.__version__!=cfg['numpy'] or scipy.__version__!=cfg['scipy']:raise ValueError('Pinned analysis libraries')
        core=load(HERE/'historical_baselines.py','baseline_arithmetic',cfg['core_sha256']);loaded={};receipts={}
        for role,items in roots.items():
            audit,links=helper.role_inputs(items,role,cfg);receipts[role]=links
            for item in audit['rows']:
                with np.load(item['array_path'],allow_pickle=False) as z:loaded[item['dataset'],role]={k:z[k] for k in z.files}
        started=time.monotonic_ns();rows=[]
        for dataset in cfg['datasets'].values():
            if args.phase=='lock':rows.extend(decisions(loaded[dataset,'target_selection'],loaded[dataset,'target_certification'],dataset,cfg,core,np))
            else:rows.extend(evaluate(loaded[dataset,'target_evaluation'],lock['rows'],dataset,cfg,np))
        if args.phase=='lock':helper.same_rows(rows,expected)
        adapter.write_json(out/'completed.json',{'status':'NEW_BASELINES_LOCKED_BEFORE_EVALUATION_READ' if args.phase=='lock' else 'NEW_LOCKED_BASELINES_EVALUATION_COMPLETE',
            'config_sha256':digest(HERE/'config.json'),'rows':rows,'new_input_receipts':receipts,'prior_lock_sha256':args.lock_sha256,
            'new_compute_elapsed_ns':time.monotonic_ns()-started,'failure_event':'raw recall-threshold failure (hits < 10)',
            'historical_design':'retrospective paired comparison','new_prospective_study':False,'ANN_runs':0,
            'timing_or_confidence_intervals_recomputed':False,'historical_results_replaced':False})
    except BaseException as exc:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK','error':repr(exc)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
