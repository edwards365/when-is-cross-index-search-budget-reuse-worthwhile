"""Explicit, receipt-bound S9-3/S9-4 preparation, native and decision stages."""
import argparse,csv,gzip,hashlib,importlib.util,json,os,platform,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
FIELDS=['dataset','build_id','query_role','query_position','ef_search','recall_at_10','failure','ndc','top10_sha256']

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def load(path,name,pin):
    if digest(path)!=pin:raise ValueError('Code identity: '+path.name)
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def core(name,cfg):return load(HERE/name,name.replace('.','_'),cfg['core_hashes'][name])

def receipt(folder,pin,status,cfg):
    if folder is None or not pin:raise ValueError('Explicit prior stage SHA required')
    p=folder/'completed.json'
    if (folder/'failure.json').exists() or digest(p)!=pin:raise ValueError('Failed/drifted parent')
    obj=json.loads(p.read_text())
    if obj['status']!=status or obj['config_sha256']!=digest(HERE/'config.json'):raise ValueError('Parent stage/config')
    for name,record in obj['files'].items():
        path=(folder/name).resolve()
        if not path.is_relative_to(folder.resolve()) or digest(path)!=record['sha256'] or path.stat().st_size!=record['bytes']:raise ValueError('Parent output identity')
    return obj

def validate_role_ids(ids,roles):
    allids=[]
    for role in roles:
        v=ids[role]
        if len(v)!=500 or len(set(v))!=500 or any(x<100000 for x in v):raise ValueError('500 distinct external training queries required')
        allids.extend(v)
    if len(set(allids))!=1500:raise ValueError('Query roles overlap')
    return allids

def normalized(base,queries,metric,np):
    if metric=='ip':
        tiny=np.finfo(np.float32).tiny
        base/=np.maximum(np.linalg.norm(base,axis=1,keepdims=True),tiny)
        queries/=np.maximum(np.linalg.norm(queries,axis=1,keepdims=True),tiny)
    return base,queries

def graph_pin(cfg,dataset,ordinal):
    if cfg['graphs'] is None:raise ValueError('Frozen registry not delivered')
    seed=cfg['seeds'][ordinal];name=f'{dataset}__s9p3_{ordinal:02d}__seed{seed}'
    return next(r for r in cfg['graphs'] if r['dataset']==dataset and r['build_id']==name)

def native(args,cfg):
    wrapper=load(args.truth_adapter/'run_truth.py','recovery_native_identity',cfg['truth_adapter_sha256'])
    path=args.truth_adapter/'native_lock.json'
    if digest(path)!=cfg['native_lock_sha256']:raise ValueError('Native wheel lock')
    faiss,np,h5py,identity=wrapper.native_environment(json.loads(path.read_text()))
    faiss.omp_set_num_threads(1)
    # The historical gate checked the AVX2 payload, not actual selected dispatch.
    if not any(v=='1324bc7385fd6b19c9205db64eab130fdd4e4996a447854448109fb1d63a5834' for v in json.loads(path.read_text())['installed_payload'].values()):raise ValueError('Registered AVX2 binary unavailable')
    return faiss,np,h5py,identity

def prepare(args,cfg,roles,out):
    import numpy as np,h5py
    spec=roles[args.family];name_order=spec['names'];ic=core('input_core.py',cfg)
    if args.family not in cfg['input_pins'] or cfg['graphs'] is None:raise ValueError('Frozen prepared-file/graph input pins missing')
    for ds,path in [('sift_100k',args.sift_hdf5),('arxiv_nomic_100k',args.arxiv_hdf5)]:
        if path is None or digest(path)!=spec['sources'][ds]['sha256']:raise ValueError('Original HDF5 identity')
        ids=validate_role_ids(spec['ids'][ds],name_order)
        with h5py.File(path,'r') as h:
            base=np.asarray(h['train'][:100000],dtype=np.float32);order=np.argsort(ids)
            sortedq=np.asarray(h['train'][np.asarray(ids)[order]],dtype=np.float32);queries=sortedq[np.argsort(order)]
        metric='l2' if ds=='sift_100k' else 'ip';base,queries=normalized(base,queries,metric,np)
        truth=ic.exact_top10(base,queries,metric)
        np.save(out/(ds+'.queries.npy'),queries);np.save(out/(ds+'.truth.npy'),truth)
        (out/(ds+'.external_ids.json')).write_text(json.dumps({'role_order':name_order,
            'role_offsets':{n:[i*500,(i+1)*500] for i,n in enumerate(name_order)},'external_ids':ids},indent=2)+'\n',encoding='utf-8')
        with (out/(ds+'.base.f32bin')).open('xb') as f:
            np.asarray(base.shape,dtype=np.int64).tofile(f);base.tofile(f)
        if digest(out/(ds+'.base.f32bin'))!=graph_pin(cfg,ds,0)['base_sha256']:raise ValueError('Base bits differ from original normalized/L2 input')
        for suffix in ('queries.npy','truth.npy','external_ids.json'):
            name=ds+'.'+suffix;pin=cfg['input_pins'][args.family][name]
            if digest(out/name)!=pin['sha256'] or (out/name).stat().st_size!=pin['bytes']:raise ValueError('Prepared input differs; no repinning')
    return {'status':'NEW_RECOVERY_INPUTS_FROZEN_MATCH','family':args.family,'train_only':True,'base_rows':[0,100000]}

def build(args,cfg,out):
    parent=receipt(args.prepared,args.prepared_sha256,'NEW_RECOVERY_INPUTS_FROZEN_MATCH',cfg)
    if parent['family']!='3':raise ValueError('Build from S9-3 prepared base')
    pin=graph_pin(cfg,args.dataset,args.ordinal);faiss,np,_,identity=native(args,cfg)
    nc=core('native_core.py',cfg);nc.faiss=faiss;base=nc.load_f32bin(args.prepared/(args.dataset+'.base.f32bin'))
    perm=np.random.default_rng(pin['permutation_seed']).permutation(len(base)).astype(np.int64)
    if hashlib.sha256(perm.tobytes()).hexdigest()!=pin['permutation_sha256']:raise ValueError('Permutation identity')
    index=nc.build_index(base,perm);faiss.write_index(index,str(out/'index.faiss'))
    if digest(out/'index.faiss')!=pin['index_sha256'] or (out/'index.faiss').stat().st_size!=pin['index_bytes']:raise ValueError('Original graph mismatch; no alternate seed/retry')
    if faiss.read_index(str(out/'index.faiss')).ntotal!=100000:raise ValueError('Saved graph count')
    return {'status':'NEW_RECOVERY_GRAPH_FROZEN_MATCH','dataset':args.dataset,'build_id':pin['build_id'],'native':identity,
            'metric':'METRIC_L2','prepared_receipt_sha256':args.prepared_sha256}

def profile(args,cfg,roles,out):
    prep=receipt(args.prepared,args.prepared_sha256,'NEW_RECOVERY_INPUTS_FROZEN_MATCH',cfg)
    graph=receipt(args.graph,args.graph_sha256,'NEW_RECOVERY_GRAPH_FROZEN_MATCH',cfg)
    if prep['family']!=args.family or graph['dataset']!=args.dataset or args.role not in roles[args.family]['names']:raise ValueError('Role/family/dataset')
    faiss,np,_,identity=native(args,cfg);nc=core('native_core.py',cfg);nc.faiss=faiss
    i=roles[args.family]['names'].index(args.role);sl=slice(i*500,(i+1)*500)
    queries=np.load(args.prepared/(args.dataset+'.queries.npy'),allow_pickle=False)[sl]
    truth=np.load(args.prepared/(args.dataset+'.truth.npy'),allow_pickle=False)[sl]
    nc.ROLE_OFFSETS={args.role:(0,500)};nc.GRID=cfg['grid']
    index=faiss.read_index(str(args.graph/'index.faiss'))
    with (out/'responses.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();nc.evaluate_unit(index,queries,truth,args.dataset,graph['build_id'],w)
    return {'status':'NEW_RECOVERY_ROLE_PROFILE_COMPLETE','family':args.family,'dataset':args.dataset,'build_id':graph['build_id'],
            'role':args.role,'rows':3000,'prepared_receipt_sha256':args.prepared_sha256,'graph_receipt_sha256':args.graph_sha256,
            'native':identity,'counter':'Faiss HNSW n3 diagnostic; not independently exact distance count'}

def response_frame(args,cfg,roles,wanted):
    import pandas as pd
    manifest=json.loads(args.response_manifest.read_text());frames=[];seen=set();links=[]
    if len(manifest)!=16*len(wanted):raise ValueError('Need all 16 builds for declared roles')
    for row in manifest:
        folder=Path(row['directory']);r=receipt(folder,row['completed_sha256'],'NEW_RECOVERY_ROLE_PROFILE_COMPLETE',cfg)
        key=(r['dataset'],r['build_id'],r['role'])
        if r['family']!=args.family or r['role'] not in wanted or key in seen:raise ValueError('Unexpected/duplicate role profile')
        allowed=[p['build_id'] for p in cfg['graphs'] if p['dataset']==r['dataset']]
        if r['build_id'] not in allowed:raise ValueError('Unknown build')
        seen.add(key);f=pd.read_csv(folder/'responses.csv')
        expected={(a,q) for a in cfg['grid'] for q in range(500)}
        if len(f)!=3000 or set(zip(f.ef_search,f.query_position))!=expected:raise ValueError('Incomplete response grid')
        if set(f.dataset)!={r['dataset']} or set(f.build_id)!={r['build_id']} or set(f.query_role)!={r['role']}:raise ValueError('Response context')
        if not f.failure.isin([0,1]).all() or not (f.failure==(f.recall_at_10<.95).astype(int)).all():raise ValueError('Failure event')
        frames.append(f);links.append(row['completed_sha256'])
    return pd.concat(frames,ignore_index=True),links

def lock(args,cfg,roles,out):
    names=roles[args.family]['names'];response,links=response_frame(args,cfg,roles,names[:2])
    if args.family=='3':
        dc=core('decision3_core.py',cfg);decisions=dc.make_decisions(response,cfg['grid'],.05)
        import pandas as pd
        expected=HERE/'expected_source_decisions.csv'
        if digest(expected)!=cfg['expected_source_decisions_sha256']:raise ValueError('Frozen source decisions')
        pd.testing.assert_frame_equal(decisions.reset_index(drop=True),pd.read_csv(expected),check_dtype=False,check_exact=False,rtol=0,atol=1e-12)
    else:
        prior=receipt(args.source_lock,args.source_lock_sha256,'NEW_RECOVERY_DECISIONS_LOCKED',cfg)
        if prior['family']!='3':raise ValueError('S9-3 source decisions required')
        dc=core('decision4_lock_core.py',cfg);decisions=dc.make_decisions(response,dc.source_policy_map(args.source_lock/'decisions.csv'))
    decisions.to_csv(out/'decisions.csv',index=False)
    return {'status':'NEW_RECOVERY_DECISIONS_LOCKED','family':args.family,'response_receipts':links,
        'decision_rows':len(decisions),'evaluation_read':False,'source_lock_sha256':args.source_lock_sha256,
        'oracle_deferred_until_evaluation':args.family=='4'}

def evaluate(args,cfg,roles,out):
    import pandas as pd
    prior=receipt(args.lock,args.lock_sha256,'NEW_RECOVERY_DECISIONS_LOCKED',cfg)
    if prior['family']!=args.family:raise ValueError('Lock family')
    response,links=response_frame(args,cfg,roles,[roles[args.family]['names'][2]])
    decisions=pd.read_csv(args.lock/'decisions.csv')
    if args.family=='3':cells=core('decision3_core.py',cfg).attach_evaluation(decisions,response)
    else:
        # Oracle is post-hoc and never enters the locked deployable decision set.
        oracle=[]
        for row in decisions[decisions.arm.eq('B0_ENDPOINT_512')].to_dict('records'):
            e=response[(response.dataset==row['dataset'])&(response.build_id==row['target_build'])]
            action=next((a for a in cfg['grid'] if e[e.ef_search.eq(a)].failure.mean()<=.05),512)
            row.update(arm='O1_EVALUATION_ORACLE',deployable=False,proposed_action=action,executed_action=action,
                decision='DIAGNOSTIC_NO_CERTIFICATE',certification_queries=0,candidate_cert_ucb=float('nan'),endpoint_cert_ucb=float('nan'))
            oracle.append(row)
        decisions=pd.concat([decisions,pd.DataFrame(oracle)],ignore_index=True)
        decisions.to_csv(out/'decisions_with_oracle.csv',index=False)
        cells=core('decision4_core.py',cfg).evaluation_cells(decisions,response)
    cells.to_csv(out/'evaluation_cells.csv',index=False)
    return {'status':'NEW_RECOVERY_EVALUATION_COMPLETE','family':args.family,'lock_sha256':args.lock_sha256,
            'response_receipts':links,'rows':len(cells),'bootstrap_recomputed':False}

def timing(args,cfg,roles,preregs,out):
    import pandas as pd
    lockrec=receipt(args.lock,args.lock_sha256,'NEW_RECOVERY_DECISIONS_LOCKED',cfg)
    prep=receipt(args.prepared,args.prepared_sha256,'NEW_RECOVERY_INPUTS_FROZEN_MATCH',cfg)
    graph=receipt(args.graph,args.graph_sha256,'NEW_RECOVERY_GRAPH_FROZEN_MATCH',cfg)
    if prep['family']!=args.family or lockrec['family']!=args.family or graph['dataset']!=args.dataset:raise ValueError('Timing parent context')
    if not args.exclusive_timing:raise ValueError('Explicit exclusive timing assurance required')
    faiss,np,_,identity=native(args,cfg);nc=core('native_core.py',cfg);nc.faiss=faiss
    records=pd.read_csv(args.lock/'decisions.csv');target=records[(records.dataset==args.dataset)&(records.target_build==graph['build_id'])]
    if args.family=='4':target=target[target.deployable.astype(str).str.lower().eq('true')]
    col='deployed_action' if args.family=='3' else 'executed_action';actions=sorted(set(map(int,target[col].dropna())).union({512}))
    queries=np.load(args.prepared/(args.dataset+'.queries.npy'),allow_pickle=False)[1000:1500]
    index=faiss.read_index(str(args.graph/'index.faiss'));g=nc.core(index)
    for action in actions:g.hnsw.efSearch=action;index.search(queries[:50],10)
    pin=next(x for x in cfg['graphs'] if x['build_id']==graph['build_id']);rng=np.random.default_rng(991+pin['permutation_seed'])
    fields=['dataset','target_build','query_position','repetition','ef_search','wall_ns','cpu_ns','ndc','top10_sha256']
    with (out/'runtime.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for rep in range(7):
            for q in rng.permutation(len(queries)):
                for action in rng.permutation(actions):
                    g.hnsw.efSearch=int(action);faiss.cvar.hnsw_stats.reset();cpu=time.process_time_ns();wall=time.monotonic_ns()
                    _,found=index.search(queries[q:q+1],10);wall=time.monotonic_ns()-wall;cpu=time.process_time_ns()-cpu
                    w.writerow(dict(dataset=args.dataset,target_build=graph['build_id'],query_position=int(q),repetition=rep,ef_search=int(action),
                        wall_ns=wall,cpu_ns=cpu,ndc=int(faiss.cvar.hnsw_stats.n3),top10_sha256=hashlib.sha256(found.astype(np.int64).tobytes()).hexdigest()))
    return {'status':'NEW_RECOVERY_TIMING_COMPLETE','family':args.family,'dataset':args.dataset,'build_id':graph['build_id'],
        'actions':actions,'rows':500*7*len(actions),'lock_sha256':args.lock_sha256,'native':identity,
        'historical_timings_replaced':False,'exclusive_host_assertion':True,'runtime_is_new_measurement':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['prepare','build','profile','lock','evaluate','timing']);p.add_argument('--family',choices=['3','4'],required=True)
    for name in ('input-adapter','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('truth-adapter','prepared','graph','lock','source-lock','response-manifest','sift-hdf5','arxiv-hdf5'):p.add_argument('--'+name,type=Path)
    for name in ('prepared','graph','lock','source-lock'):p.add_argument('--'+name+'-sha256')
    p.add_argument('--dataset',choices=['sift_100k','arxiv_nomic_100k']);p.add_argument('--ordinal',type=int,choices=range(8));p.add_argument('--role')
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-stage',action='store_true');p.add_argument('--exclusive-timing',action='store_true');args=p.parse_args()
    if not args.authorize_new_stage:p.error('Explicit new-stage opt-in required')
    if args.stage=='build' and args.family!='3':p.error('S9-4 reuses the S9-3 graph; no independent rebuild')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 without -O required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    cfg=json.loads((HERE/'config.json').read_text())
    for name,key in [('roles.json','roles_sha256'),('preregistrations.json','preregistrations_sha256')]:
        if digest(HERE/name)!=cfg[key]:raise ValueError('Registered configuration drift')
    roles=json.loads((HERE/'roles.json').read_text());preregs=json.loads((HERE/'preregistrations.json').read_text())
    adapter=load(args.input_adapter/'prepare_inputs.py','recovery_resource',cfg['input_adapter_sha256'])
    out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':cfg['resource_plan']},args.output,{},args.outstanding_growth_bytes)
    import resource,signal
    plan=cfg['resource_plan']
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);adapter.write_json(out/'start.json',{'stage':args.stage,'family':args.family,'resources':snapshot,
        'config_sha256':digest(HERE/'config.json'),'adapter_sha256':digest(Path(__file__))})
    def timeout(signum,frame):raise TimeoutError('Recovery stage wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        import numpy,scipy,pandas,h5py
        if (numpy.__version__,scipy.__version__,pandas.__version__,h5py.__version__)!=('1.26.4','1.13.1','2.2.2','3.11.0'):raise ValueError('Pinned dependencies')
        if args.stage=='prepare':result=prepare(args,cfg,roles,out)
        elif args.stage=='build':result=build(args,cfg,out)
        elif args.stage=='profile':result=profile(args,cfg,roles,out)
        elif args.stage=='lock':result=lock(args,cfg,roles,out)
        elif args.stage=='evaluate':result=evaluate(args,cfg,roles,out)
        else:result=timing(args,cfg,roles,preregs,out)
        result.update(config_sha256=digest(HERE/'config.json'),files={f.name:{'sha256':digest(f),'bytes':f.stat().st_size}
            for f in out.iterdir() if f.is_file() and f.name!='start.json'})
        adapter.write_json(out/'completed.json',result)
    except BaseException as exc:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK','error':repr(exc)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
