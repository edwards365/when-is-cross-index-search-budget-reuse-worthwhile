"""Future measurements at original lifecycle boundaries, never old-time replacements."""
import argparse,hashlib,importlib.util,json,os,platform,signal,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def pin(p,h):
    if sha(p)!=h:raise ValueError('Pinned identity: '+Path(p).name)
def load(p,name,h):
    pin(p,h);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
def dependency(req,cfg,package,name):
    folder=Path(req[package]);p=folder/name;pin(p,cfg['dependencies'][package+'/'+name]);return p

def role_stage(req,out,cfg,core):
    import copy
    protocol=dict(cfg['role_protocol']);roles_path=Path(req['old_roles']);exclusions_path=Path(req['old_exclusions']);candidate=Path(req['e1b_candidate'])
    for p,key in ((roles_path,'prior_roles_sha256'),(exclusions_path,'prior_base_exclusions_sha256'),(candidate,'prior_e1b_query_candidate_sha256')):pin(p,protocol[key])
    roles=json.loads(roles_path.read_bytes());exclusions=json.loads(exclusions_path.read_bytes())
    for row in roles['datasets']:
        # Explicit root bindings; source hash remains checked INSIDE the original timer.
        row['relative_path']=str(Path(req['raw_sources'][row['name']]).resolve(strict=True))
    protocol.update(new_measurement_only=True,original_role_source_sha256=cfg['source_files']['freeze_tcp_fresh_roles_v1.py'],source_bindings={r['name']:r['relative_path'] for r in roles['datasets']})
    config_path=out/'resolved_context.json';write(config_path,protocol);folder=out/'data';ops=out/'ops';folder.mkdir();ops.mkdir()
    result=core.role_firewall(out,config_path,protocol,roles_path,candidate,roles,exclusions,folder,ops)
    registry=json.loads(dependency(req,cfg,'portable_fresh_inputs','registry.json').read_text());pin(folder/'membership.npz',registry['expected_membership_sha256'])
    if result['status']!='PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME':raise ValueError('Role firewall failure')
    return {'measured_record':'ops/final.json','record_sha256':sha(ops/'final.json'),'wall_seconds':result['wall_seconds'],'membership_sha256':sha(folder/'membership.npz')}

def profile_stage(req,out,cfg,core):
    import numpy as np
    prefix=req['dataset'];role=req['role'];row=cfg['profile_datasets'][prefix]
    if role not in row['roles']:raise ValueError('Unregistered role')
    input_path=dependency(req,cfg,'portable_fresh_inputs','prepare_inputs.py');truth_path=dependency(req,cfg,'portable_truth','run_truth.py');truth_cfg_path=dependency(req,cfg,'portable_truth','config.json')
    truth=load(truth_path,'operational_truth',cfg['dependencies']['portable_truth/run_truth.py']);tc=json.loads(truth_cfg_path.read_text())
    _,registry,parts=truth.inputs(Path(req['prepared']),input_path.parent,tc)
    raw=registry['datasets'][prefix];source=Path(req['source']);pin(source,raw['source_sha256'])
    tdir=Path(req['truth']);td=json.loads((tdir/'completed.json').read_text());ts=json.loads((tdir/'start.json').read_text())
    if (tdir/'failure.json').exists() or td['status']!='NEW_EXACT_TRUTH_MATCHES_FROZEN_BYTES' or td['dataset']!=prefix or set(td['independent_score_checks'])!=set(row['roles']):raise ValueError('New independently checked truth required')
    if ts['preparation_receipt_sha256']!=sha(Path(req['prepared'])/'completed.json'):raise ValueError('Truth/preparation mismatch')
    tr=tdir/(prefix+'_'+role+'.npz');pin(tr,row['roles'][role]['truth_sha256']);ids=parts[prefix][0][role]
    with np.load(tr,allow_pickle=False) as a:
        if not np.array_equal(ids,a['query_ids']) or a['neighbor_raw_ids'].shape!=(len(ids),10):raise ValueError('Truth role identity')
    profiles=dependency(req,cfg,'portable_profiles','config.json').parent;dependency(req,cfg,'portable_profiles','native_entry.py');pc=json.loads((profiles/'config.json').read_text())
    for file,h in pc['files'].items():pin(profiles/file,h)
    build=Path(req['native_build']);bd=json.loads((build/'completed.json').read_text())
    if (build/'failure.json').exists() or bd['status']!='PASS_NEW_BUILD_AND_SYNTHETIC_NATIVE_CHECKS' or bd['config_sha256']!=sha(profiles/'config.json') or bd['entry_sha256']!=sha(profiles/'native_entry.py'):raise ValueError('New profile-native build required')
    binary=build/('replay1000' if len(ids)==1000 else 'replay500');pin(binary,bd['binaries'][binary.name])
    graph_specs={};bindings=out/'bindings';bindings.mkdir()
    if set(req['graphs'])!=set(cfg['build_ids']):raise ValueError('All eight graph bindings required')
    for bid in cfg['build_ids']:
        supplied=req['graphs'][bid];receipt=Path(supplied['receipt']);d=json.loads(receipt.read_text());index=Path(supplied['index']).resolve(strict=True);expected=row['graphs'][bid]
        if (receipt.parent/'failure.json').exists() or d['status']!='NEW_GRAPH_MATCHES_FROZEN_BYTES' or d['index_sha256']!=expected['sha256'] or d['index_bytes']!=expected['bytes']:raise ValueError('New graph receipt does not bind frozen index')
        # Do not hash/read graph contents here: the original timed loop does that.
        bound=bindings/(bid+'.json');write(bound,{'status':'BUILT_NO_QUERY_OUTCOME_ACCESSED','effective_base_count':row['base_count'],'index_path':str(index),'index_sha256':expected['sha256'],'new_receipt_binding_sha256':sha(receipt),'historical_receipt_claimed':False})
        graph_specs[bid]={'receipt_path':str(bound.resolve()),'receipt_sha256':sha(bound)}
    context={'action_grid':cfg['action_grid'],'source':str(source.resolve()),'native_binary_sha256':sha(binary),'new_measurement_only':True};config_path=out/'resolved_context.json';write(config_path,context)
    folder=out/'data';ops=out/'ops';folder.mkdir();ops.mkdir();policy={'build_ids':cfg['build_ids']};spec={'graphs':graph_specs,'base_count':row['base_count']}
    record={'schema_version':'icde2027-tcp-fresh-native-profiles-v1','status':'RUNNING','dataset':row['name'],'role':role,'query_count':len(ids),'config_sha256':sha(config_path),'role_receipt_sha256':sha(Path(req['prepared'])/'completed.json'),'truth_sha256':sha(tr),'binary_sha256':sha(binary),'cpu_affinity':sorted(os.sched_getaffinity(0)),'profiles':[]}
    result=core.profiles(source,ids,{'train_shape':raw['train_shape']},folder,ops,record,policy,spec,context,{'wall_seconds_per_graph':3600},binary,row['metric'],out,SimpleNamespace(dataset=row['name'],role=role),subprocess)
    if result['status']!='NATIVE_PROFILES_COMPLETE_AUDIT_PENDING' or len(result['profiles'])!=8:raise ValueError('Incomplete measured profile stage')
    # Frozen CSV checks occur AFTER the complete original whole-unit timer.
    for unit in result['profiles']:
        expected=row['roles'][role]['profiles'][unit['build']]
        pin(Path(unit['csv_path']),expected['sha256'])
        if Path(unit['csv_path']).stat().st_size!=expected['bytes']:raise ValueError('CSV size')
    qbin=folder/'queries.qbin';pin(qbin,row['roles'][role]['qbin_sha256'])
    return {'measured_record':'ops/final.json','record_sha256':sha(ops/'final.json'),'whole_unit_ns':result['whole_unit_ns'],'query_read_ns':result['query_read_ns'],'query_export_fsync_ns':result['query_export_fsync_ns'],'independent_full_array_audit_still_required':True}

def decision_stage(req,out,cfg,core):
    role='target_certification';audit={'rows':[]}
    if set(req['arrays'])!={'sift','arxiv'}:raise ValueError('Both datasets required')
    for prefix,root in req['arrays'].items():
        folder=Path(root);d=json.loads((folder/'completed.json').read_text());expected=cfg['expected_arrays'][prefix+'_'+role];path=folder/(prefix+'_'+role+'.npz')
        if (folder/'failure.json').exists() or d['status']!='NEW_ARRAY_MATCHES_FROZEN_BYTES' or (d['dataset'],d['role'])!=(prefix,role) or d['sha256']!=expected['sha256'] or d['bytes']!=expected['bytes']:raise ValueError('New audited qualification array required')
        # Hash/read/decompress of arrays stays INSIDE original decision timer.
        audit['rows'].append({'dataset':cfg['profile_datasets'][prefix]['name'],'role':role,'array_path':str(path.resolve()),'array_sha256':expected['sha256']})
    auditpath=out/'bound_profile_audit.json';write(auditpath,audit);context={'phase':'certify','new_measurement_only':True,'profile_audit_sha256':sha(auditpath)};configpath=out/'resolved_context.json';write(configpath,context);ops=out/'ops';ops.mkdir()
    policy=cfg['policy'];result=core.certification(ops,SimpleNamespace(phase='certify'),policy,audit,policy['action_grid'],policy['build_ids'],configpath,auditpath,context)
    folder=Path(req['portable_policy']);expected=folder/'expected_certification_rows.json';pin(expected,cfg['expected_decision_rows_sha256'])
    rows=json.loads(expected.read_text())
    if len(rows)!=len(result['rows']):raise ValueError('Qualification row count')
    for a,b in zip(result['rows'],rows):
        if a.keys()!=b.keys():raise ValueError('Qualification row fields')
        for k,v in b.items():
            if isinstance(v,float):
                if abs(a[k]-v)>1e-12:raise ValueError('Qualification numeric drift')
            elif a[k]!=v:raise ValueError('Qualification decision drift')
    return {'measured_record':'ops/certification_decision_lock.json','record_sha256':sha(ops/'certification_decision_lock.json'),'decision_compute_ns_including_audited_array_read':result['decision_compute_ns_including_audited_array_read'],'evaluation_arrays_read':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-operational-measurement',action='store_true');a=p.parse_args()
    if not a.authorize_new_operational_measurement:p.error('New measurement opt-in required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux x86_64 Python3.11 required')
    req=json.loads(a.request.read_text());cfg=json.loads((HERE/'operational_config.json').read_text());kind=req['kind']
    if kind not in ('roles','profiles','decision'):raise ValueError('Registered operational measurement kind')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2});resourcepath=dependency(req,cfg,'portable_fresh_inputs','prepare_inputs.py');adapter=load(resourcepath,'operational_resources',cfg['dependencies']['portable_fresh_inputs/prepare_inputs.py'])
    plan=dict(cfg['resource_plan']);out,telemetry=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{'request':a.request},a.outstanding_growth_bytes)
    import resource,numpy as np,h5py,scipy
    if (np.__version__,h5py.__version__,scipy.__version__)!=('1.26.4','3.11.0','1.13.1'):raise ValueError('Scientific library versions')
    for k,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(k,(cap,cap))
    core=load(HERE/'operational_core.py','operational_measurement_core',cfg['core_sha256']);out.mkdir(mode=0o700);write(out/'start.json',{'status':'NEW_OPERATIONAL_MEASUREMENT_STARTED','kind':kind,'core_sha256':cfg['core_sha256'],'config_sha256':sha(HERE/'operational_config.json'),'request_sha256':sha(a.request),'telemetry':telemetry,'old_ledger_replaced':False})
    def timeout(s,f):raise TimeoutError('Operational stage wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        measured={'roles':role_stage,'profiles':profile_stage,'decision':decision_stage}[kind](req,out,cfg,core)
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>plan['max_output_growth_bytes']:raise ValueError('Aggregate output bound')
        write(out/'completed.json',dict(status='NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE',kind=kind,measured=measured,new_values_not_historical_measurements=True,formal_benchmark=False,original_e8='NOT_ESTIMABLE_UNCHANGED'))
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_DEPENDENTS_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)

if __name__=='__main__':main()
