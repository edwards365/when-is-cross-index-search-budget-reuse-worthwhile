"""Aggregate only typed new S9-3/S9-4 receipts, never replace saved paper results."""
import argparse,importlib.metadata,json,os,platform,signal,sys
from pathlib import Path
from types import SimpleNamespace
from run_recovery import HERE,digest,load,receipt,response_frame,core

def validate_runtime(frame,actions,dataset,build):
    import numpy as np
    keys=['dataset','target_build','query_position','repetition','ef_search']
    if set(frame.dataset)!={dataset} or set(frame.target_build)!={build}:raise ValueError('Timing context')
    expected={(q,r,a) for q in range(500) for r in range(7) for a in actions}
    if frame.duplicated(keys).any() or set(zip(frame.query_position,frame.repetition,frame.ef_search))!=expected:raise ValueError('Seven-repeat complete timing cube required')
    for col in ('wall_ns','cpu_ns','ndc'):
        if not np.isfinite(frame[col]).all() or (frame[col]<0).any():raise ValueError('Invalid timing/count value')
    if (frame.wall_ns<=0).any() or (frame.cpu_ns<=0).any():raise ValueError('Nonpositive timing')
    if frame.groupby(['query_position','ef_search']).top10_sha256.nunique().max()!=1:raise ValueError('Runtime top10 differs across repetitions')

def verify_response_hashes(runtime,response):
    keys=['dataset','target_build','query_position','ef_search']
    expected=response.rename(columns={'build_id':'target_build'})[keys+['top10_sha256']]
    observed=runtime[keys+['top10_sha256']].drop_duplicates()
    merged=observed.merge(expected,on=keys,how='left',indicator=True,suffixes=('_runtime','_response'),validate='one_to_one')
    if not merged['_merge'].eq('both').all() or not merged.top10_sha256_runtime.eq(merged.top10_sha256_response).all():raise ValueError('Runtime/native response top10 mismatch or missing cell')
    return len(merged)

def run(req,out,cfg,ac):
    import pandas as pd
    family=req['family'];lockdir=Path(req['lock']['directory']);locksha=req['lock']['completed_sha256']
    lock=receipt(lockdir,locksha,'NEW_RECOVERY_DECISIONS_LOCKED',cfg)
    edir=Path(req['evaluation']['directory']);ev=receipt(edir,req['evaluation']['completed_sha256'],'NEW_RECOVERY_EVALUATION_COMPLETE',cfg)
    if lock['family']!=family or ev['family']!=family or ev['lock_sha256']!=locksha:raise ValueError('Family/evaluation/lock mismatch')
    roles=json.loads((HERE/'roles.json').read_text());role=roles[family]['names'][2]
    responses,links=response_frame(SimpleNamespace(family=family,response_manifest=Path(req['response_manifest'])),cfg,roles,[role])
    if sorted(links)!=sorted(ev['response_receipts']):raise ValueError('Evaluation response provenance differs')
    decisions=pd.read_csv(lockdir/'decisions.csv');cells=pd.read_csv(edir/'evaluation_cells.csv')
    if family=='4':
        expanded=pd.read_csv(edir/'decisions_with_oracle.csv')
        # The nondeployable oracle is evaluated, never timed as a deployable arm.
        pd.testing.assert_frame_equal(expanded[~expanded.arm.eq('O1_EVALUATION_ORACLE')].reset_index(drop=True),decisions.reset_index(drop=True),check_dtype=False)
        decisions=expanded
    dc=core('decision'+family+'_core.py',cfg)
    reconstructed=(dc.attach_evaluation if family=='3' else dc.evaluation_cells)(decisions,responses)
    pd.testing.assert_frame_equal(cells.reset_index(drop=True),reconstructed.reset_index(drop=True),check_dtype=False,rtol=1e-12,atol=1e-12)
    timings=req['timings'];wanted={(r['dataset'],r['build_id']) for r in cfg['graphs']};seen=set();frames=[]
    if len(timings)!=16:raise ValueError('All16 new timing units required')
    for item in timings:
        folder=Path(item['directory']);r=receipt(folder,item['completed_sha256'],'NEW_RECOVERY_TIMING_COMPLETE',cfg);key=(r['dataset'],r['build_id'])
        if r['family']!=family or r['lock_sha256']!=locksha or key not in wanted or key in seen:raise ValueError('Timing detached/duplicate/unregistered')
        if not r['runtime_is_new_measurement'] or not r['exclusive_host_assertion']:raise ValueError('New isolated timing required')
        selected=decisions[(decisions.dataset==key[0])&(decisions.target_build==key[1])]
        if family=='4':selected=selected[selected.deployable.astype(str).str.lower().eq('true')]
        col='deployed_action' if family=='3' else 'executed_action';actions=sorted(set(map(int,selected[col].dropna())).union({512}))
        if actions!=r['actions']:raise ValueError('Timing actions differ from lock')
        f=pd.read_csv(folder/'runtime.csv');validate_runtime(f,actions,*key)
        if len(f)!=r['rows']:raise ValueError('Timing row count')
        seen.add(key);frames.append(f)
    if seen!=wanted:raise ValueError('Incomplete build panel')
    runtime=pd.concat(frames,ignore_index=True);checked=verify_response_hashes(runtime,responses)
    quality=load(HERE/f'analysis{family}_quality_core.py','new_quality',ac['cores'][f'analysis{family}_quality_core.py'])
    timing=load(HERE/f'analysis{family}_runtime_core.py','new_runtime',ac['cores'][f'analysis{family}_runtime_core.py'])
    safety=quality.summarize(decisions,cells)
    qualityname='primary_summary.json' if family=='3' else 'arm_ndc_summary.json'
    (out/qualityname).write_text(json.dumps(safety,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    timing.analyze(runtime,decisions,safety,out,checked)
    return {'status':'NEW_RECOVERY_ANALYSIS_COMPLETE','family':family,'new_results_not_saved_paper':True,'historical_values_compared_or_replaced':False,'runtime_repetitions':7,'bootstrap_repetitions':5000,'bootstrap_seed':991,'lock_sha256':locksha,'evaluation_receipt_sha256':req['evaluation']['completed_sha256'],'timing_receipt_sha256s':[r['completed_sha256'] for r in timings],'runtime_response_top10_checked_cells':checked}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--authorize-new-analysis',action='store_true');a=p.parse_args()
    if not a.authorize_new_analysis or a.output.exists():raise ValueError('Explicit new exclusive analysis required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11):raise ValueError('Linux Python3.11 required')
    os.sched_setaffinity(0,{2})
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    for name,version in [('numpy','1.26.4'),('scipy','1.13.1'),('pandas','2.2.2')]:
        if importlib.metadata.version(name)!=version:raise ValueError('Pinned analysis dependency '+name)
    ac=json.loads((HERE/'analysis_config.json').read_text());cfg=json.loads((HERE/'config.json').read_text())
    if digest(HERE/'config.json')!=ac['recovery_config_sha256'] or digest(HERE/'run_recovery.py')!=ac['recovery_entry_sha256']:raise ValueError('Producer binding drift')
    req=json.loads(a.request.read_text())
    if req['family'] not in ('3','4'):raise ValueError('Family')
    import resource
    for key,cap in [(resource.RLIMIT_AS,4*1024**3),(resource.RLIMIT_FSIZE,512*1024**2),(resource.RLIMIT_CPU,3600),(resource.RLIMIT_CORE,0)]:
        old=resource.getrlimit(key);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(key,(cap,cap))
    def timeout(s,f):raise TimeoutError('New analysis wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(7200);a.output.mkdir(mode=0o700)
    try:
        result=run(req,a.output,cfg,ac)
        result.update(config_sha256=digest(HERE/'analysis_config.json'),request_sha256=digest(a.request),files={f.name:{'sha256':digest(f),'bytes':f.stat().st_size} for f in a.output.iterdir() if f.is_file()})
        if sum(x['bytes'] for x in result['files'].values())>512*1024**2:raise ValueError('Aggregate output cap')
        (a.output/'completed.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    except BaseException as e:(a.output/'failure.json').write_text(json.dumps({'status':'FAILED_NEW_ANALYSIS','error':repr(e)})+'\n',encoding='utf-8');raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
