"""Separate E6 GENERIC counter and original AVX2 API-timing entries, new outputs only."""
import argparse,json,os,platform,signal,struct,subprocess,sys
from pathlib import Path
from run_faiss import HERE,sha,pin,load,write,panel,native,members,expected,unitkey
from build_counter import dependencies,clean_child_env
def check_stage(folder,status):
    folder=Path(folder);d=json.loads((folder/'completed.json').read_text())
    if (folder/'failure.json').exists() or d['status']!=status:raise ValueError('New prerequisite '+status)
    return folder,d
def export(req,out,cfg):
    import numpy as np,h5py
    row=cfg['datasets'][req['dataset']];source=Path(req['source']);pin(source,row['source_sha256']);base=members(row,np);spec=cfg['e6_inputs'][req['dataset']]
    with h5py.File(source,'r') as f:
        train=f['train']
        if list(train.shape)!=row['train_shape'] or str(train.dtype)!='float32':raise ValueError('Train shape')
        for role,name in [('source_design','source'),('target_evaluation','evaluation')]:
            ids=np.asarray(row['roles'][role],dtype='i8');q=np.ascontiguousarray(train[ids.tolist()],dtype='<f4');path=out/(name+'.fbin')
            with path.open('xb') as stream:stream.write(struct.pack('<II',*q.shape));stream.write(q.tobytes())
            pin(path,spec['pins']['query'] if name=='source' else spec['evaluation_query_sha256'])
        with (out/'base.fbin').open('xb') as stream:
            stream.write(struct.pack('<II',len(base),train.shape[1]))
            for start in range(0,len(base),8192):stream.write(np.ascontiguousarray(train[base[start:start+8192].tolist()],dtype='<f4').tobytes())
    with (out/'base_raw_ids.i64').open('xb') as f:f.write(base.astype('<i8',copy=False).tobytes())
    pin(out/'base.fbin',spec['pins']['base']);pin(out/'base_raw_ids.i64',spec['pins']['base_raw_ids'])
    return {'status':'NEW_E6_EXPORT_MATCHES_FROZEN_BYTES','dataset':req['dataset'],'files':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.fbin','.i64')},'forbidden_hdf5_keys_accessed':[]}
def wait(argv,out,name,timeout):
    with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:
        clean=clean_child_env()
        # Python tooling may need setup-python's libpython path; only the native
        # executable must resolve the generic library under its pinned RPATH.
        child=subprocess.Popen(argv,stdout=stdout,stderr=stderr,env=dict(os.environ) if argv[0]==sys.executable else clean)
        try:code=child.wait(timeout=timeout)
        except BaseException:
            child.kill();code=child.wait();write(out/(name+'_wait.json'),{'actual_exit_code':code,'interrupted':True});raise
    write(out/(name+'_wait.json'),{'actual_exit_code':code})
    if code:raise RuntimeError(name+' failed actual exit '+str(code))
    return code
def source_audits(req,cfg):
    if set(req['source_audits'])!={'sift','arxiv'}:raise ValueError('Both source audits required')
    paths=[]
    for prefix,folder in req['source_audits'].items():
        root,d=check_stage(folder,'NEW_E6_SOURCE_COUNTER_AND_EVENT_AUDIT_PASS')
        if d['dataset']!=prefix or d['native_actual_exit'] or d['audit_actual_exit']:raise ValueError('Source predecessor exit/role')
        path=root/'audit.json';pin(path,d['audit_sha256']);r=json.loads(path.read_text())
        if r['status']!='PASS_EXACT_DC_EVENTS_AND_SEALED_ORDERED_IDS' or r['query_count']!=500 or r['actions']!=cfg['action_grid']:raise ValueError('Full source event audit')
        paths.append(str(path.resolve()))
    return paths
def counter(req,out,cfg,is_source):
    import numpy as np
    phase='source' if is_source else 'evaluate';prior=panel(req['response_panel'],cfg,phase);prefix=req['dataset'];row=cfg['datasets'][prefix];spec=cfg['e6_inputs'][prefix]
    audits=[] if is_source else source_audits(req,cfg)
    if is_source and (req['seed'],req['history'])!=(13,'random'):raise ValueError('Source counter uses registered seed13_random')
    inputs,ir=check_stage(req['inputs'],'NEW_E6_EXPORT_MATCHES_FROZEN_BYTES')
    if ir['dataset']!=prefix:raise ValueError('Counter inputs dataset')
    for name,h in ir['files'].items():pin(inputs/name,h)
    if is_source:
        pin(inputs/'base.fbin',spec['pins']['base']);pin(inputs/'base_raw_ids.i64',spec['pins']['base_raw_ids'])
    query=inputs/('source.fbin' if is_source else 'evaluation.fbin');pin(query,spec['pins']['query'] if is_source else spec['evaluation_query_sha256'])
    build,br=check_stage(req['counter_build'],'NEW_CORRECTED_COUNTER_BUILD_CONTROLS_PASS');binary=build/'counter';pin(binary,br['binary_sha256']);pin(build/'lib/libfaiss.so',br['generic_library_sha256'])
    if br['generic_library_sha256']!=json.loads((HERE/'generic_package_lock.json').read_text())['payload']['lib/libfaiss.so']['sha256']:raise ValueError('Registered generic library')
    if br['source_sha256']!=cfg['extra_files']['e6_faiss_exact_dc_reset_corrected_v1.cpp']:raise ValueError('Corrected counter source identity')
    if not is_source:
        for folder in req['source_audits'].values():
            r=json.loads((Path(folder)/'completed.json').read_text())
            if r['counter_binary_sha256']!=br['binary_sha256'] or r['generic_library_sha256']!=br['generic_library_sha256']:raise ValueError('Target counter differs from event-validated source counter')
    if dependencies(binary,build/'lib/libfaiss.so')!=br['runtime_dependencies']:raise ValueError('Runtime dependency changed')
    name=unitkey(req,cfg);unit=Path(prior['units'][name]['directory']);reference=unit/'response.npz';ref=expected(cfg,phase)[name];pin(reference,ref['array_sha256'])
    graphroot,g=check_stage(req['graph'],'NEW_FAISS1M_GRAPH_MATCHES_FROZEN_BYTES');graph=graphroot/'index.faiss';pin(graph,expected(cfg,'source')[name]['index_sha256'])
    if g['unit']!=name:raise ValueError('Graph identity')
    with np.load(reference,allow_pickle=False) as r:acts=r['action_grid'].tolist();ids=r['query_ids'].tolist()
    target=out/('source' if is_source else 'target');native_exit=wait([str(binary.resolve()),str(graph.resolve()),str(query.resolve()),','.join(map(str,acts)),str(target.resolve()),'events' if is_source else 'none'],out,'native',1800)
    c={'dataset':row['name'],'build':f"seed{req['seed']}_"+req['history'],'role':'source_design' if is_source else 'target_evaluation','query_count':len(ids),'dim':spec['dim'],'actions':acts,'query_ids':ids,'query':str(query.resolve()),'reference':str(reference.resolve()),'prefix':str(target.resolve()),'pins':{str(query.resolve()):sha(query),str(reference.resolve()):sha(reference)}}
    if is_source:c.update(base=str((inputs/'base.fbin').resolve()),base_raw_ids=str((inputs/'base_raw_ids.i64').resolve()),base_count=spec['base_count'],metric=spec['metric'])
    else:
        roles=out/'roles.json';write(roles,{'datasets':[{'name':r['name'],'roles':r['roles']} for r in cfg['datasets'].values()]});c.update(roles=str(roles.resolve()),source_audit_reports=audits)
    config=out/'audit_config.json';write(config,c);script=HERE/('audit_e6_faiss_exact_dc_v1.py' if is_source else 'audit_e6_faiss_target_counts_v1.py');pin(script,cfg['extra_files'][script.name]);audit_exit=wait([sys.executable,str(script),'--config',str(config)],out,'audit',1800)
    report=json.loads((out/'audit.stdout').read_text());write(out/'audit.json',report)
    return {'status':'NEW_E6_SOURCE_COUNTER_AND_EVENT_AUDIT_PASS' if is_source else 'NEW_E6_TARGET_COUNTER_AND_OUTPUT_AUDIT_PASS','dataset':prefix,'unit':name,'native_actual_exit':native_exit,'audit_actual_exit':audit_exit,'audit_sha256':sha(out/'audit.json'),'response_sha256':sha(Path(str(target)+'.responses.bin')),'counter_binary_sha256':sha(binary),'generic_library_sha256':br['generic_library_sha256'],'target_event_count_independently_traced':is_source}
def counter_panel(req,out,cfg):
    refs=expected(cfg,'evaluate')
    if set(req['units'])!=set(refs):raise ValueError('All48 target counter units required')
    audits=source_audits(req,cfg);units=[]
    for name,folder in req['units'].items():
        root,r=check_stage(folder,'NEW_E6_TARGET_COUNTER_AND_OUTPUT_AUDIT_PASS')
        if r['unit']!=name or r['native_actual_exit'] or r['audit_actual_exit']:raise ValueError('Unit identity/exit')
        pin(root/'audit.json',r['audit_sha256']);pin(root/'target.responses.bin',r['response_sha256'])
        units.append(dict(unit=name,directory=str(root.resolve()),receipt_sha256=sha(root/'completed.json'),native_actual_exit=0,audit_actual_exit=0))
    return {'status':'PASS_48_TARGET_COUNT_OUTPUTS_AUDITED','completed':48,'units':units,'source_audit_reports':audits,'origin':'new_portable_counter_execution','not_historical_closure':True}
def latency(req,out,cfg):
    closed,d=check_stage(req['counter_panel'],'PASS_48_TARGET_COUNT_OUTPUTS_AUDITED')
    if d.get('origin')!='new_portable_counter_execution' or d['completed']!=48:raise ValueError('New counter panel origin')
    for u in d['units']:pin(Path(u['directory'])/'completed.json',u['receipt_sha256'])
    prior=panel(req['response_panel'],cfg,'evaluate');name=unitkey(req,cfg);reference=Path(prior['units'][name]['directory'])/'response.npz';row=cfg['datasets'][req['dataset']];spec=cfg['e6_inputs'][req['dataset']]
    inputs,r=check_stage(req['inputs'],'NEW_E6_EXPORT_MATCHES_FROZEN_BYTES');query=inputs/'evaluation.fbin';pin(query,spec['evaluation_query_sha256']);graph=Path(req['graph'])/'index.faiss';pin(graph,expected(cfg,'source')[name]['index_sha256'])
    faiss,np,h5py,proof=native(req,cfg)
    with np.load(reference,allow_pickle=False) as a:acts=a['action_grid'].tolist()
    c={'dataset':row['name'],'build':f"seed{req['seed']}_"+req['history'],'index':str(graph.resolve()),'reference':str(reference.resolve()),'query':str(query.resolve()),'query_ids':row['roles']['target_evaluation'],'actions':acts,'dim':spec['dim'],'query_count':1000,'role':'target_evaluation','base_count':spec['base_count'],'cpus':[4],'repetitions':5,'warmup_queries':16,'counter_panel_final':str((closed/'completed.json').resolve()),'output':str(out.resolve()),'pins':{str(p.resolve()):sha(p) for p in (graph,query,reference,closed/'completed.json')}}
    mod=load(HERE/'latency_core.py','new_e6_latency_core',cfg['extra_files']['latency_core.py']);result=mod.run(c,faiss)
    return {'status':'NEW_E6_AVX2_LATENCY_AND_ORDERED_OUTPUTS_PASS','unit':name,'native':proof,'measurement':result,'not_historical_timing_values':True}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--input-adapter',type=Path,required=True);p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-stage',action='store_true');p.add_argument('--assert-isolated-host',action='store_true');a=p.parse_args()
    if not a.authorize_new_stage:p.error('New-stage opt-in required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11):raise ValueError('Linuxx86_64 Python3.11')
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    os.sched_setaffinity(0,{4});cfg=json.loads((HERE/'config.json').read_text());req=json.loads(a.request.read_text());kind=req['kind']
    if kind not in ('export','counter-source','counter-target','counter-panel','latency'):raise ValueError('Registered supplement kind')
    if kind=='latency' and not a.assert_isolated_host:raise ValueError('Timing requires caller-arranged isolation')
    adapter=load(a.input_adapter/'prepare_inputs.py','e6resources',cfg['dependencies']['portable_fresh_inputs/prepare_inputs.py']);plan=dict(cfg['resource_plan'],cpu_affinity=[4],max_output_growth_bytes=16*1024**3,file_size_bytes=8*1024**3,cpu_seconds=7200,wall_seconds=7200)
    out,telemetry=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{'request':a.request},a.outstanding_growth_bytes)
    import resource,fcntl
    for k,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(k,(cap,cap))
    lease=None
    if kind=='latency':lease=(Path(req['counter_panel'])/'completed.json').open('rb');fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    out.mkdir(mode=0o700);write(out/'start.json',{'config_sha256':sha(HERE/'config.json'),'request_sha256':sha(a.request),'kind':kind,'resources':telemetry,'new_run_only':True})
    def timeout(s,f):raise TimeoutError('Supplement wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        result=counter(req,out,cfg,kind=='counter-source') if kind.startswith('counter-') and kind!='counter-panel' else {'export':export,'counter-panel':counter_panel,'latency':latency}[kind](req,out,cfg)
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>plan['max_output_growth_bytes']:raise ValueError('Output growth cap')
        result['config_sha256']=sha(HERE/'config.json');write(out/'completed.json',result)
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_DEPENDENTS_NO_RETRY','error':repr(e)});raise
    finally:
        signal.alarm(0)
        if lease:lease.close()
if __name__=='__main__':main()
