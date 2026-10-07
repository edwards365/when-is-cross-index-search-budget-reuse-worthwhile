"""Audit timed-profile CSVs into ordinary new arrays, without forging profile receipts."""
import argparse,json,os,platform,signal,sys
from pathlib import Path
from measure_operational import sha,pin,load,write,HERE
ARRAY_CODE='d4eac9aad46e92ca62334fdf61604d06e8d90497432747f568ccab8d82129ab5'
ARRAY_CONFIG='83c3eb8829acbbdbae0979f32c0a307f3dbf04ae94f21e6231d9a0e89380cb36'

def validate_receipts(folder,dataset,role,truth,prepared,pc):
    done=json.loads((folder/'completed.json').read_text());start=json.loads((folder/'start.json').read_text())
    if (folder/'failure.json').exists() or done['status']!='NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE' or done['kind']!='profiles':raise ValueError('Successful timed profile phase required')
    if start['config_sha256']!=sha(HERE/'operational_config.json'):raise ValueError('Operational config identity')
    final=folder/'ops/final.json';pin(final,done['measured']['record_sha256']);r=json.loads(final.read_text())
    if r['status']!='NATIVE_PROFILES_COMPLETE_AUDIT_PENDING' or (r['dataset'],r['role'])!=(pc['datasets'][dataset]['name'],role):raise ValueError('Timed role identity')
    if r['role_receipt_sha256']!=sha(prepared/'completed.json'):raise ValueError('Preparation identity')
    spec=pc['datasets'][dataset]['roles'][role];pin(truth/(dataset+'_'+role+'.npz'),spec['truth_sha256'])
    if r['truth_sha256']!=spec['truth_sha256']:raise ValueError('Timed truth identity')
    if [x['build'] for x in r['profiles']]!=pc['build_ids'] or any(x['actual_exit_code']!=0 for x in r['profiles']):raise ValueError('Full ordered native waits')
    for bid in pc['build_ids']:
        f=folder/'data'/(bid+'.csv');p=spec['profiles'][bid];pin(f,p['sha256'])
        if f.stat().st_size!=p['bytes']:raise ValueError('CSV size')
    pin(folder/'data/queries.qbin',spec['qbin_sha256'])
    return r

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('profiles','prepared','truth','input-adapter','truth-adapter','profile-adapter','array-adapter','output'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--dataset',choices=['sift','arxiv'],required=True);p.add_argument('--role',choices=['source_design','target_selection','target_certification','target_evaluation'],required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-materialization',action='store_true');a=p.parse_args()
    if not a.authorize_materialization:p.error('Explicit new output opt-in required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 required')
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    os.sched_setaffinity(0,{2});pin(a.array_adapter/'config.json',ARRAY_CONFIG);arrays=load(a.array_adapter/'materialize.py','operational_arrays',ARRAY_CODE)
    cfg=json.loads((a.array_adapter/'config.json').read_text());pin(a.profile_adapter/'config.json',cfg['profile_config_sha256']);pin(a.truth_adapter/'config.json',cfg['truth_config_sha256'])
    pc=json.loads((a.profile_adapter/'config.json').read_text());tc=json.loads((a.truth_adapter/'config.json').read_text());truth=load(a.truth_adapter/'run_truth.py','operational_array_truth',cfg['truth_adapter_sha256'])
    adapter,registry,parts=truth.inputs(a.prepared,a.input_adapter,tc);validate_receipts(a.profiles,a.dataset,a.role,a.truth,a.prepared,pc)
    import numpy as np,resource
    if np.__version__!='1.26.4':raise ValueError('NumPy version')
    ids=parts[a.dataset][0][a.role];base=parts[a.dataset][2]
    with np.load(a.truth/(a.dataset+'_'+a.role+'.npz'),allow_pickle=False) as f:
        if not np.array_equal(f['query_ids'],ids):raise ValueError('Truth role order')
        top=f['neighbor_raw_ids'].copy()
    plan=cfg['resource_plan'];out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{'profiles':a.profiles/'completed.json'},a.outstanding_growth_bytes)
    for k,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(k,(cap,cap))
    out.mkdir(mode=0o700);write(out/'start.json',{'status':'NEW_ARRAY_FROM_OPERATIONAL_PROFILES','profile_receipt_sha256':sha(a.profiles/'completed.json'),'resources':snapshot})
    def timeout(s,f):raise TimeoutError('Array wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        values=arrays.arrays_from_csv(a.profiles/'data',ids,pc['action_grid'],pc['build_ids'],top,base,np);name=a.dataset+'_'+a.role;path=out/(name+'.npz');arrays.write_array(path,values,np)
        expected=cfg['expected_arrays'][name];pin(path,expected['sha256'])
        if path.stat().st_size!=expected['bytes']:raise ValueError('Array size')
        write(out/'completed.json',{'status':'NEW_ARRAY_MATCHES_FROZEN_BYTES','dataset':a.dataset,'role':a.role,'sha256':sha(path),'bytes':path.stat().st_size,'cells':int(values['hits'].size),'ANN_runs':0,'native_count_independently_recomputed':False,'historical_audit_rerun':False,'profile_origin':'new_original_operational_boundary','profile_receipt_sha256':sha(a.profiles/'completed.json')})
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_DEPENDENTS_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
