"""Reconstruct fixed-format arrays from a complete new role response; no ANN or statistics."""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

HERE=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def load(p,name,pin):
    if digest(p)!=pin:raise ValueError('Adapter identity')
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def arrays_from_csv(folder,ids,grid,builds,true_topk,base,np):
    if true_topk.shape!=(len(ids),10) or len(set(map(int,ids)))!=len(ids):raise ValueError('Truth/query shape')
    allowed=set(map(int,base));shape=(len(builds),len(grid),len(ids))
    if not np.all(np.isin(true_topk,base)) or np.any(np.diff(np.sort(true_topk,axis=1),axis=1)==0):raise ValueError('Truth base/duplicates')
    hits=np.full(shape,-1,dtype=np.int16);ndc=np.zeros(shape,dtype=np.uint64);topk=np.empty((*shape,10),dtype=np.int64)
    for b,name in enumerate(builds):
        count=0
        with (folder/(name+'.csv')).open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=['query_id','ef','ndc','topk']:raise ValueError('CSV schema')
            for item in reader:
                a,q=divmod(count,len(ids))
                if a>=len(grid):raise ValueError('Extra rows')
                if int(item['query_id'])!=int(ids[q]) or int(item['ef'])!=grid[a]:raise ValueError('Query/action order')
                n=int(item['ndc']);found=list(map(int,item['topk'].split(';')))
                if not 0<n<=np.iinfo(np.uint64).max or len(found)!=10 or len(set(found))!=10:raise ValueError('Counter/top-k')
                if not set(found)<=allowed or int(ids[q]) in found:raise ValueError('Ineligible returned ID')
                ndc[b,a,q]=n;topk[b,a,q]=found;hits[b,a,q]=len(set(found)&set(map(int,true_topk[q])));count+=1
        if count!=len(grid)*len(ids):raise ValueError('Incomplete role/grid')
    return {'query_ids':ids,'action_grid':np.asarray(grid,dtype=np.int32),'build_ids':np.asarray(builds),
            'hits':hits,'ndc':ndc,'topk':topk}
def write_array(path,arrays,np):
    with path.open('xb') as f:np.savez_compressed(f,**arrays);f.flush();os.fsync(f.fileno())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('profile-adapter','truth-adapter','input-adapter','prepared','truth','profiles','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--dataset',choices=('sift','arxiv'),required=True)
    p.add_argument('--role',choices=('source_design','target_selection','target_certification','target_evaluation'),required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-materialization',action='store_true');a=p.parse_args()
    if not a.authorize_materialization:p.error('Explicit array materialization required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux/Python3.11 required for frozen NPZ encoding')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    cfg=json.loads((HERE/'config.json').read_text())
    for path,key in ((a.profile_adapter/'config.json','profile_config_sha256'),(a.truth_adapter/'config.json','truth_config_sha256')):
        if digest(path)!=cfg[key]:raise ValueError('Config identity')
    pc=json.loads((a.profile_adapter/'config.json').read_text());tc=json.loads((a.truth_adapter/'config.json').read_text())
    truth=load(a.truth_adapter/'run_truth.py','array_truth_adapter',cfg['truth_adapter_sha256'])
    adapter,reg,parts=truth.inputs(a.prepared,a.input_adapter,tc)
    import numpy as np
    if np.__version__!='1.26.4':raise ValueError('NumPy1.26.4 required')
    ids=parts[a.dataset][0][a.role];base=parts[a.dataset][2];row=pc['datasets'][a.dataset];spec=row['roles'][a.role]
    start=json.loads((a.profiles/'start.json').read_text());done=json.loads((a.profiles/'completed.json').read_text())
    if (a.profiles/'failure.json').exists() or done['status']!='NEW_PROFILES_MATCH_ALL_FROZEN_CSVS' or (done['dataset'],done['role'])!=(a.dataset,a.role):raise ValueError('Incomplete/new role receipt')
    if start['config_sha256']!=cfg['profile_config_sha256'] or start['adapter_sha256']!=cfg['profile_adapter_sha256']:raise ValueError('Role adapter receipt')
    if start['truth_receipt_sha256']!=digest(a.truth/'completed.json'):raise ValueError('Truth receipt link')
    if [v['build'] for v in done['profiles']]!=pc['build_ids'] or any(v['actual_exit_code']!=0 for v in done['profiles']):raise ValueError('Full native waits')
    for build in pc['build_ids']:
        path=a.profiles/(build+'.csv');pin=spec['profiles'][build]
        if digest(path)!=pin['sha256'] or path.stat().st_size!=pin['bytes']:raise ValueError('Frozen CSV identity')
    path=a.truth/(a.dataset+'_'+a.role+'.npz')
    if digest(path)!=spec['truth_sha256']:raise ValueError('Frozen truth identity')
    with np.load(path,allow_pickle=False) as t:
        if not np.array_equal(t['query_ids'],ids):raise ValueError('Truth role IDs')
        top=t['neighbor_raw_ids']
    out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':cfg['resource_plan']},a.output,{'profile':a.profiles/'completed.json','truth':path},a.outstanding_growth_bytes)
    import resource,signal
    plan=cfg['resource_plan']
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);adapter.write_json(out/'start.json',{'status':'NEW_ARRAY_MATERIALIZATION','resources':snapshot,'profile_receipt_sha256':digest(a.profiles/'completed.json')})
    def timeout(signum,frame):raise TimeoutError('Array stage wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        arrays=arrays_from_csv(a.profiles,ids,pc['action_grid'],pc['build_ids'],top,base,np)
        name=a.dataset+'_'+a.role;path=out/(name+'.npz');write_array(path,arrays,np);pin=cfg['expected_arrays'][name]
        if digest(path)!=pin['sha256'] or path.stat().st_size!=pin['bytes']:raise ValueError('Frozen NPZ bytes differ; no repinning/retry')
        adapter.write_json(out/'completed.json',{'status':'NEW_ARRAY_MATCHES_FROZEN_BYTES','dataset':a.dataset,'role':a.role,
            'sha256':digest(path),'bytes':path.stat().st_size,'cells':int(arrays['hits'].size),'ANN_runs':0,
            'native_count_independently_recomputed':False,'historical_audit_rerun':False})
    except BaseException as e:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
