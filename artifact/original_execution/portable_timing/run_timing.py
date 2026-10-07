"""Opt-in fresh timing of one pinned graph after an explicitly pinned policy lock."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from timing import digest,pin,write_json,query_ids,reference,validate,save_arrays

HERE=Path(__file__).resolve().parent

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def dependencies(folder,names):
    for name,h in names.items():pin(folder/name,h)

def validated_native(folder,cfg):
    r=json.loads((folder/'completed.json').read_text())
    if (folder/'failure.json').exists() or r['status']!='PASS_NEW_NATIVE_TIMING_BUILD_AND_SYNTHETIC_CHECKS':raise ValueError('New native build check required')
    for field,file in [('config_sha256','config.json'),('build_entry_sha256','build_native.py'),('validator_sha256','timing.py')]:
        if r[field]!=digest(HERE/file):raise ValueError('Build/validator identity differs')
    pin(folder/'runtime',r['binaries']['runtime']);pin(HERE/'e1a_runtime_native.cpp',cfg['source_sha256'])
    return r

def validated_profile(folder,prefix,build,cfg):
    done=json.loads((folder/'completed.json').read_text());start=json.loads((folder/'start.json').read_text())
    if (folder/'failure.json').exists() or done['status']!='NEW_PROFILES_MATCH_ALL_FROZEN_CSVS' or (done['dataset'],done['role'])!=(prefix,'target_evaluation'):
        raise ValueError('New complete evaluation profile receipt required')
    if start['config_sha256']!=cfg['dependencies']['portable_profiles']['config.json']:
        raise ValueError('Profile config identity')
    rows={r['build']:r for r in done['profiles']}
    if len(rows)!=len(cfg['build_ids']) or set(rows)!=set(cfg['build_ids']):raise ValueError('Complete profile graph coverage required')
    for name,r in rows.items():
        expected=cfg['datasets'][prefix]['evaluation']['profiles'][name]
        if r['actual_exit_code']!=0 or r['csv_sha256']!=expected['sha256']:raise ValueError('Prior profile exit/identity')
    p=folder/(build+'.csv');frozen=cfg['datasets'][prefix]['evaluation']['profiles'][build]
    pin(p,frozen['sha256'],frozen['bytes']);return p

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input-adapter','policy-adapter','policy-lock','prepared','profiles','graphs','native-build','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--policy-lock-sha256',required=True)
    p.add_argument('--dataset',choices=('sift','arxiv'),required=True);p.add_argument('--build',required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True)
    p.add_argument('--authorize-new-timing',action='store_true');p.add_argument('--assert-isolated-host',action='store_true')
    a=p.parse_args()
    if not a.authorize_new_timing or not a.assert_isolated_host:p.error('Explicit new timing and externally arranged host-isolation acknowledgement required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux x86_64 Python3.11 without -O required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('Historical CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    cfg=json.loads((HERE/'config.json').read_text())
    if a.build not in cfg['build_ids']:raise ValueError('Unregistered graph')
    dependencies(a.policy_adapter,cfg['dependencies']['portable_policy'])
    # Lock validation deliberately precedes reads of evaluation profile/query contents.
    policy=load(a.policy_adapter/'run_policy.py','timing_policy_lock')
    pc=json.loads((a.policy_adapter/'config.json').read_text());expected=json.loads((a.policy_adapter/'expected_certification_rows.json').read_text())
    lock=policy.validated_lock(a.policy_lock,a.policy_lock_sha256,pc,expected)
    if any(r['decision']=='UNDEPLOYABLE' for r in lock['rows']):raise ValueError('Undeployable target has no substitute timing action')
    dependencies(a.input_adapter,cfg['dependencies']['portable_fresh_inputs'])
    adapter=load(a.input_adapter/'prepare_inputs.py','timing_resources')
    native=validated_native(a.native_build,cfg)
    import fcntl
    # All units using this build serialize under its existing receipt, without modifying it.
    lease=(a.native_build/'completed.json').open('rb');fcntl.flock(lease.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    row=cfg['datasets'][a.dataset];evaluation=row['evaluation']
    prep=json.loads((a.prepared/'completed.json').read_text())
    if (a.prepared/'failure.json').exists() or prep['status']!='NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED':raise ValueError('New prepared inputs required')
    qbin=a.prepared/'tcp_fresh_profiles_v1'/(a.dataset+'_target_evaluation')/'queries.qbin'
    pin(qbin,evaluation['qbin_sha256'],evaluation['qbin_bytes'])
    graph=a.graphs/(a.dataset+'_'+a.build+'.bin');gp=row['graphs'][a.build];pin(graph,gp['sha256'],gp['bytes'])
    csv=validated_profile(a.profiles,a.dataset,a.build,cfg)
    ids=query_ids(qbin);expected_topk=reference(csv,ids,cfg['action_grid'])
    plan=cfg['resource_plan']
    out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,
        {'graph':graph,'qbin':qbin,'profile':csv,'lock':a.policy_lock/'completed.json','binary':a.native_build/'runtime'},a.outstanding_growth_bytes)
    import resource
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),
                     (resource.RLIMIT_CPU,plan['cpu_seconds_whole_stage']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    seed_material=f"{row['name']}|{a.build}|{cfg['schedule_seed']}".encode('ascii')
    seed=int.from_bytes(hashlib.sha256(seed_material).digest()[:8],'big')
    out.mkdir(mode=0o700)
    write_json(out/'start.json',{'status':'NEW_SINGLE_GRAPH_TIMING_STARTED','dataset':a.dataset,'build':a.build,
        'config_sha256':digest(HERE/'config.json'),'entry_sha256':digest(Path(__file__)),'resources':snapshot,
        'prior_lock_sha256':a.policy_lock_sha256,'native_build_receipt_sha256':digest(a.native_build/'completed.json'),
        'profile_receipt_sha256':digest(a.profiles/'completed.json'),'graph_sha256':gp['sha256'],
        'qbin_sha256':evaluation['qbin_sha256'],'profile_csv_sha256':digest(csv),'schedule_seed':seed,
        'host_isolation':'Caller arranged; lease prevents concurrent timing through the same native build, not all unrelated host work',
        'historical_timing_replaced':False,'graph_load_and_validation_not_query_timing':True})
    started=time.monotonic_ns();timed=out/'timed.csv';timeout=False
    try:
        argv=[str((a.native_build/'runtime').resolve()),str(graph.resolve()),str(qbin.resolve()),row['metric'],
            ','.join(map(str,cfg['action_grid'])),str(row['base_count']),str(csv.resolve()),'1000',str(seed),'7',str(timed)]
        with (out/'native.stdout').open('xb') as stdout,(out/'native.stderr').open('xb') as stderr:
            child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
            try:code=child.wait(timeout=plan['wall_seconds_per_unit'])
            except subprocess.TimeoutExpired:
                timeout=True;child.kill();code=child.wait()
            except BaseException:
                child.kill();code=child.wait()
                write_json(out/'native_wait.json',{'actual_exit_code':code,'interrupted':True,'operational_process_elapsed_ns':time.monotonic_ns()-started})
                raise
        write_json(out/'native_wait.json',{'actual_exit_code':code,'wall_timeout':timeout,'operational_process_elapsed_ns':time.monotonic_ns()-started})
        if timeout or code:raise RuntimeError('Native timing failed; no retry or historical-output replacement')
        wall,cpu,audit=validate(timed,ids,cfg['action_grid'],expected_topk)
        target=out/(a.dataset+'_'+a.build+'.npz');save_arrays(target,ids,cfg['action_grid'],wall,cpu)
        if sum(x.stat().st_size for x in out.iterdir() if x.is_file())>plan['max_output_growth_bytes']:raise ValueError('Stage output-growth cap')
        masks=[next(s for s in f.read_text().splitlines() if s.startswith('Cpus_allowed_list:')).split(':')[1].strip() for f in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'2'}:raise ValueError('Final thread-affinity check')
        write_json(out/'completed.json',{'status':'NEW_TIMING_ROWS_VALIDATED','dataset':a.dataset,'build':a.build,
            'actual_exit_code':code,'audit':audit,'raw_csv_sha256':digest(timed),'array_sha256':digest(target),
            'array_bytes':target.stat().st_size,'thread_masks':masks,'schedule_seed':seed,
            'mean_endpoint_wall_ns':float(wall[:,-1,:].mean()),'median_endpoint_wall_ns':float(__import__('numpy').median(wall[:,-1,:])),
            'cpu_clock_boundary':'Zero/coarse process CPU cells allowed; wall_ns is the primary query measure',
            'aggregation':'Arithmetic mean over repetitions before selecting one action per query',
            'historical_time_or_binary_identity_claimed':False,'cold_cache_or_end_to_end_claimed':False})
    except BaseException as e:write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK_NO_RETRY','error':repr(e)});raise
    finally:lease.close()

if __name__=='__main__':main()
