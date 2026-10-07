"""One fixed role on all eight pinned saved graphs; never builds a benchmark graph."""
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
from native_entry import validate_csv

HERE=Path(__file__).resolve().parent
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def pinned(path,expected):
    if digest(path)!=expected:raise ValueError('Pinned identity differs: '+path.name)
def load(path,name,expected):
    pinned(path,expected);s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def validate_build(folder,cfg):
    r=json.loads((folder/'completed.json').read_text())
    if (folder/'failure.json').exists() or r['status']!='PASS_NEW_BUILD_AND_SYNTHETIC_NATIVE_CHECKS' or r['config_sha256']!=digest(HERE/'config.json'):
        raise ValueError('Native build/synthetic receipt missing or wrong')
    if r['entry_sha256']!=digest(HERE/'native_entry.py') or r['synthetic_fixture_sha256']!=digest(HERE/'tiny_fixture.cpp'):
        raise ValueError('Build adapter changed after synthetic check')
    for n in ('replay500','replay1000'):pinned(folder/n,r['binaries'][n])
    return r

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('input-adapter','truth-adapter','prepared','truth','graphs','native-build','output'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--dataset',choices=('sift','arxiv'),required=True)
    ap.add_argument('--role',choices=('source_design','target_selection','target_certification','target_evaluation'),required=True)
    ap.add_argument('--outstanding-growth-bytes',type=int,required=True)
    ap.add_argument('--authorize-native-profiles',action='store_true');a=ap.parse_args()
    if not a.authorize_native_profiles:ap.error('Explicit original-profile opt-in required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux/Python3.11 without -O required')
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    if 2 not in os.sched_getaffinity(0):raise ValueError('Historical CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    cfg=json.loads((HERE/'config.json').read_text());row=cfg['datasets'][a.dataset];role=row['roles'][a.role]
    truth=load(a.truth_adapter/'run_truth.py','profiles_truth_adapter',cfg['truth_adapter_sha256'])
    pinned(a.truth_adapter/'config.json',cfg['truth_config_sha256']);tc=json.loads((a.truth_adapter/'config.json').read_text())
    adapter,registry,parts=truth.inputs(a.prepared,a.input_adapter,tc)
    build=validate_build(a.native_build,cfg)
    done=json.loads((a.truth/'completed.json').read_text());start=json.loads((a.truth/'start.json').read_text())
    if (a.truth/'failure.json').exists() or done['status']!='NEW_EXACT_TRUTH_MATCHES_FROZEN_BYTES' or done['dataset']!=a.dataset:
        raise ValueError('Truth completion/identity')
    if start['config_sha256']!=cfg['truth_config_sha256'] or start['adapter_sha256']!=cfg['truth_adapter_sha256']:
        raise ValueError('Truth implementation identity')
    if set(done['independent_score_checks'])!=set(row['roles']):raise ValueError('Independent score checks missing')
    if start['preparation_receipt_sha256']!=digest(a.prepared/'completed.json'):raise ValueError('Truth prepared-input identity')
    if done['membership_sha256']!=registry['expected_membership_sha256'] or done['source_sha256']!=registry['datasets'][a.dataset]['source_sha256']:
        raise ValueError('Truth source/base identity')
    for r,pin in row['roles'].items():pinned(a.truth/(a.dataset+'_'+r+'.npz'),pin['truth_sha256'])
    ids,allids,base=parts[a.dataset];qbin=a.prepared/'tcp_fresh_profiles_v1'/(a.dataset+'_'+a.role)/'queries.qbin'
    pinned(qbin,role['qbin_sha256'])
    if qbin.stat().st_size!=role['qbin_bytes'] or len(ids[a.role])!=role['count']:raise ValueError('Role input count/size')
    graphs={name:a.graphs/(a.dataset+'_'+name+'.bin') for name in cfg['build_ids']}
    # Original serialized graph identities remain mandatory, even for rebuilt inputs.
    for name,path in graphs.items():
        pinned(path,row['graphs'][name]['sha256'])
        if path.stat().st_size!=row['graphs'][name]['bytes']:raise ValueError('Graph size')
    plan=cfg['resource_plan'];resource_cfg={'python_minor':[3,11],'resource_plan':dict(plan,max_output_growth_bytes=plan['max_total_output_growth_bytes'])}
    out,snapshot=adapter.preflight(resource_cfg,a.output,dict(graphs,qbin=qbin,truth=a.truth/'completed.json'),a.outstanding_growth_bytes)
    os.sched_setaffinity(0,set(plan['cpu_affinity']))
    import resource,signal
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),
                     (resource.RLIMIT_CPU,plan['cpu_seconds_per_role']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700)
    adapter.write_json(out/'start.json',{'status':'NEW_PROFILES_STARTED','dataset':a.dataset,'role':a.role,
        'resources':snapshot,'config_sha256':digest(HERE/'config.json'),'adapter_sha256':digest(Path(__file__)),
        'native_build_receipt_sha256':digest(a.native_build/'completed.json'),'truth_receipt_sha256':digest(a.truth/'completed.json'),
        'not_historical_prospective_run':True,'query_export_cost_not_remeasured':True})
    results=[];began=time.monotonic_ns();binary=a.native_build/('replay1000' if role['count']==1000 else 'replay500')
    try:
        for name in cfg['build_ids']:
            csv=out/(name+'.csv');argv=[str(binary.resolve()),str(graphs[name].resolve()),str(qbin.resolve()),row['metric'],
                ','.join(map(str,cfg['action_grid'])),str(role['count']),str(row['base_count']),str(csv)]
            t=time.monotonic_ns()
            # One child, no background workers or descendants. run() waits/kills on timeout.
            with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:
                proc=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=plan['wall_seconds_per_graph'],check=False)
            receipt={'build':name,'actual_exit_code':proc.returncode,'operational_elapsed_ns':time.monotonic_ns()-t,
                     'binary_sha256':digest(binary),'graph_sha256':row['graphs'][name]['sha256']}
            adapter.write_json(out/(name+'.json'),receipt)
            if proc.returncode:raise RuntimeError('Native profile failure; stop all dependent work')
            count=validate_csv(csv,ids[a.role],cfg['action_grid'],base)
            if csv.stat().st_size!=role['profiles'][name]['bytes']:raise ValueError('Frozen CSV size differs')
            pinned(csv,role['profiles'][name]['sha256']);results.append(dict(receipt,csv_sha256=digest(csv),rows=count))
            if sum(p.stat().st_size for p in out.iterdir())>plan['max_total_output_growth_bytes']:raise ValueError('Output growth')
        masks=[next(s for s in p.read_text().splitlines() if s.startswith('Cpus_allowed_list:')).split(':')[1].strip() for p in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'2'}:raise ValueError('Final all-thread affinity')
        adapter.write_json(out/'completed.json',{'status':'NEW_PROFILES_MATCH_ALL_FROZEN_CSVS','dataset':a.dataset,'role':a.role,'thread_masks':masks,
            'profiles':results,'elapsed_ns':time.monotonic_ns()-began,'not_new_formal_timing':True,
            'original_binary_bitwise_identity':digest(binary) in cfg['historical_binaries'].values()})
    except BaseException as e:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK_NO_RETRY','error':repr(e)});raise
if __name__=='__main__':main()
