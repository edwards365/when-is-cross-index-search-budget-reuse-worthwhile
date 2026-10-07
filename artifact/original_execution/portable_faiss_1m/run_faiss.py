"""Distinct E3 Faiss1.8 AVX2 fixed-member chain; no old output path or rerun."""
import argparse,hashlib,importlib.util,json,os,platform,signal,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
ROLES={'source':'source_design','selection':'target_selection','certify':'target_certification','evaluate':'target_evaluation'}
PANELS={'source':'source_design_panel_audit.json','selection':'target_selection_panel_audit.json','certify':'target_certification_panel_audit.json','evaluate':'target_evaluation_panel_audit.json'}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def pin(p,h):
    if sha(p)!=h:raise ValueError('Pinned identity '+Path(p).name)
def load(p,name,h):
    pin(p,h);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,allow_nan=False);f.write('\n')
def key(row):return row['dataset']+'_'+row.get('target_build_id',row.get('build_id',f"seed{row.get('seed')}_"+str(row.get('history'))))
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def expected(cfg,phase):return {key(r):r for r in cfg['records'][PANELS[phase]]['rows']}
def unitkey(req,cfg):return cfg['datasets'][req['dataset']]['name']+f"_seed{req['seed']}_"+req['history']
def native(req,cfg):
    folder=Path(req['transfer_adapter']);sys.path.insert(0,str(folder))
    for n in ('run_phase.py','run_transfer.py','config.json'):pin(folder/n,cfg['dependencies']['portable_transfer_1m/'+n])
    helper=load(folder/'run_phase.py','faiss1m_native_dispatch',cfg['dependencies']['portable_transfer_1m/run_phase.py']);tc=json.loads((folder/'config.json').read_text())
    # Same pinned wheel, explicit AVX2 dispatch as this distinct E3 protocol.
    return helper.native_truth(Path(req['truth_adapter']),tc,'e1b')
def members(row,np):
    held=np.concatenate([np.asarray(v,dtype='i8') for v in row['roles'].values()]);excluded=np.asarray(row['excluded_index_row_ids'],dtype='i8')
    if len(held)!=2500 or np.unique(held).size!=2500 or np.intersect1d(held,excluded).size:raise ValueError('Role exclusions')
    keep=np.ones(row['train_shape'][0],dtype=bool);keep[held]=False;keep[excluded]=False;raw=np.flatnonzero(keep).astype('i8')
    if len(raw)!=row['effective_base_count']:raise ValueError('Base count')
    return raw
def verify_array(path,cfg,phase,name):
    import numpy as np
    pin(path,expected(cfg,phase)[name]['array_sha256'])
    with np.load(path,allow_pickle=False) as a:
        hits=np.asarray(a['hits']);top=np.asarray(a['topk']);z=hits<10
        if not np.array_equal(z,a['z_rec']) or not np.array_equal(z[-1],a['z_censor']) or not np.array_equal(z|z[-1][None,:],a['z_abs']):raise ValueError('Event arrays')
        if np.any(np.diff(np.sort(top,axis=-1),axis=-1)==0):raise ValueError('Duplicate IDs')
        return {k:a[k].copy() for k in a.files}
def panel(path,cfg,phase):
    folder=Path(path);d=json.loads((folder/'completed.json').read_text())
    if (folder/'failure.json').exists() or d['status']!='NEW_FAISS1M_PANEL_LOCKED' or d['phase']!=phase or d['config_sha256']!=sha(HERE/'config.json') or set(d['units'])!=set(expected(cfg,phase)):raise ValueError('Complete predecessor phase required')
    for name,r in d['units'].items():
        unit=Path(r['directory']);pin(unit/'completed.json',r['receipt_sha256']);verify_array(unit/'response.npz',cfg,phase,name)
    if phase=='selection' and canonical(d['policy'])!=cfg['policy_reference_sha256']['selection']:raise ValueError('Frozen selection policy identity')
    if phase=='certify':
        ordered=sorted(d['policy']['decisions'],key=lambda r:(r['dataset'],r['target_build_id'],str(r['source_build_id']),r['arm']))
        if canonical(ordered)!=cfg['policy_reference_sha256']['certify']:raise ValueError('Frozen certification policy identity')
    return d
def predecessor(req,cfg):
    previous={'source':None,'selection':'source','certify':'selection','evaluate':'certify'}[req['phase']]
    return None if previous is None else panel(req['prior_panel'],cfg,previous)

def generate_truth(req,out,cfg,core):
    # Own 48-record gate, before importing native code or opening held-out data.
    prior=predecessor(req,cfg)
    folder=Path(req['transfer_adapter']);sys.path.insert(0,str(folder))
    for name in ('config.json','run_phase.py','run_transfer.py','historical_core.py'):
        pin(folder/name,cfg['dependencies']['portable_transfer_1m/'+name])
    helper=load(folder/'run_phase.py','faiss1m_truth_helpers',cfg['dependencies']['portable_transfer_1m/run_phase.py'])
    tc=json.loads((folder/'config.json').read_text())
    truthcore=load(folder/'historical_core.py','faiss1m_exact_truth_core',cfg['dependencies']['portable_transfer_1m/historical_core.py'])
    # Exact truth retains E1a native dispatch and timing/search blocks, not E3 ANN dispatch.
    faiss,np,h5py,proof=helper.native_truth(Path(req['truth_adapter']),tc,'e1a')
    row=cfg['datasets'][req['dataset']];phase=req['phase'];ids=np.asarray(row['roles'][ROLES[phase]],dtype='i8')
    base=members(row,np);held=set(int(v) for values in row['roles'].values() for v in values);excluded=set(map(int,row['excluded_index_row_ids']))
    source=Path(req['source']);pin(source,row['source_sha256']);metric='l2' if req['dataset']=='sift' else 'ip'
    common=(row,metric,len(base),ids,held,excluded,source,faiss,h5py)
    if phase=='source':
        protocol={'metric':'squared_l2' if metric=='l2' else 'inner_product_on_original_normalized_float32','source_design_query_count':500}
        arrays=truthcore.truth_e1a_source(row,protocol,len(base),held,excluded,source,8192,faiss,h5py)
    elif phase=='selection':
        arrays=truthcore.truth_e1a_selection(row,{row['name']:{'metric':metric,'base_count':len(base)}},SimpleNamespace(dataset=row['name']),ids,held,excluded,source,faiss,h5py)
    else:arrays=getattr(truthcore,'truth_e1a_'+phase)(*common)
    dest=out/'truth.npz'
    with dest.open('xb') as f:(np.savez if phase=='source' else np.savez_compressed)(f,**arrays)
    pin(dest,cfg['truth_pins'][req['dataset']+'_'+ROLES[phase]])
    return {'status':'NEW_FAISS1M_TRUTH_MATCHES_FROZEN_BYTES','phase':phase,'truth_sha256':sha(dest),'native':proof,'prior_panel_receipt_sha256':None if prior is None else sha(Path(req['prior_panel'])/'completed.json'),'historical_timing_identity_claimed':False}
def actions(prior,phase,dataset,bid,grid):
    if phase in ('source','selection'):return grid
    pol=prior['policy'];required={4096}
    if phase=='certify':
        rows=[r for r in pol['directed_pair_actions'] if r['dataset']==dataset and r['target_build_id']==bid];g=[r for r in pol['target_global_actions'] if r['dataset']==dataset and r['target_build_id']==bid]
        if len(rows)!=23 or len(g)!=1:raise ValueError('Selection action cardinality')
        required.add(int(g[0]['candidate_efSearch']))
        for r in rows:required.update(int(r[n]['candidate_efSearch']) for n in ('source_reuse','one_rung','selected_ladder'))
    else:
        rows=[r for r in pol['decisions'] if r['dataset']==dataset and r['target_build_id']==bid]
        if len(rows)!=71:raise ValueError('Certification decision cardinality')
        required.update(int(r['candidate_efSearch']) for r in rows);required.update(int(r['execute_efSearch']) for r in rows if r['execute_efSearch'] is not None)
    if not required<=set(grid):raise ValueError('Action outside grid')
    return sorted(required)
def graph(req,out,cfg,core):
    faiss,np,h5py,proof=native(req,cfg);row=cfg['datasets'][req['dataset']];source=Path(req['source']);pin(source,row['source_sha256']);raw=members(row,np);name=unitkey(req,cfg);ref=expected(cfg,'source')[name]
    with h5py.File(source,'r') as f:
        train=f['train']
        if list(train.shape)!=row['train_shape'] or str(train.dtype)!='float32':raise ValueError('Raw train shape')
        vectors=np.ascontiguousarray(train[:],dtype=np.float32)
    faiss.omp_set_num_threads(1);path=out/'index.faiss';result=core.build(vectors,raw,SimpleNamespace(history=req['history'],seed=req['seed'],dataset=row['name']),path,name,faiss)
    pin(path,ref['index_sha256'])
    if path.stat().st_size!=ref['index_bytes']:raise ValueError('Index size')
    return {'status':'NEW_FAISS1M_GRAPH_MATCHES_FROZEN_BYTES','unit':name,'sha256':sha(path),'bytes':path.stat().st_size,'base_count':result['base_count'],'native':proof,'new_operational_build_seconds':result['build_seconds'],'not_historical_time':True}
def response(req,out,cfg,core):
    prior=predecessor(req,cfg) # Locked predecessor before requested role access.
    faiss,np,h5py,proof=native(req,cfg);row=cfg['datasets'][req['dataset']];role=ROLES[req['phase']];ids=np.asarray(row['roles'][role],dtype='i8');base=members(row,np);source=Path(req['source']);pin(source,row['source_sha256'])
    name=unitkey(req,cfg);bid=f"seed{req['seed']}_"+req['history'];gd=Path(req['graph']);g=json.loads((gd/'completed.json').read_text());ref=expected(cfg,'source')[name]
    if (gd/'failure.json').exists() or g['status']!='NEW_FAISS1M_GRAPH_MATCHES_FROZEN_BYTES' or g['unit']!=name:raise ValueError('New graph predecessor')
    index=gd/'index.faiss';pin(index,ref['index_sha256']);truth=Path(req['truth']);pin(truth,cfg['truth_pins'][req['dataset']+'_'+role])
    with np.load(truth,allow_pickle=False) as t:
        if not np.array_equal(t['query_ids'],ids):raise ValueError('Truth query order')
        neighbors=t['neighbor_raw_ids'].copy()
    acts=actions(prior,req['phase'],row['name'],bid,cfg['action_grid']);protocol={'source_design':{'native_efSearch_grid':cfg['action_grid']},'native_search':{'action_grid':cfg['action_grid']}}
    faiss.omp_set_num_threads(1);path=out/'response.npz';summary=getattr(core,'response_'+req['phase'])(ids,source,index,{'effective_base_count':len(base)},protocol,path,neighbors,acts,name,faiss,h5py)
    arrays=verify_array(path,cfg,req['phase'],name)
    if not np.all(np.isin(arrays['topk'],base)):raise ValueError('Returned ID outside base')
    independently=np.asarray([[len(set(found)&set(truthrow)) for found,truthrow in zip(a,neighbors)] for a in arrays['topk']],dtype='u1')
    if not np.array_equal(independently,arrays['hits']):raise ValueError('Independent recall mismatch')
    return {'status':'NEW_FAISS1M_RESPONSE_MATCHES_FROZEN_BYTES','unit':name,'phase':req['phase'],'sha256':sha(path),'summary':summary,'native':proof,'prior_panel_receipt_sha256':None if prior is None else sha(Path(req['prior_panel'])/'completed.json')}
def lock_panel(req,out,cfg,core):
    phase=req['phase'];prior=predecessor(req,cfg);refs=expected(cfg,phase)
    if set(req['units'])!=set(refs) or len(refs)!=48:raise ValueError('All48 registered units required')
    units={};values={}
    for name,p in req['units'].items():
        folder=Path(p);d=json.loads((folder/'completed.json').read_text())
        if (folder/'failure.json').exists() or d['status']!='NEW_FAISS1M_RESPONSE_MATCHES_FROZEN_BYTES' or d['unit']!=name or d['phase']!=phase or d['config_sha256']!=sha(HERE/'config.json'):raise ValueError('New unit receipt')
        if prior is not None and d['prior_panel_receipt_sha256']!=sha(Path(req['prior_panel'])/'completed.json'):raise ValueError('Unit detached from preceding phase')
        values[name]=verify_array(folder/'response.npz',cfg,phase,name);units[name]={'directory':str(folder.resolve()),'receipt_sha256':sha(folder/'completed.json'),'summary':d['summary']}
    policy={}
    if phase=='source':
        for name,r in refs.items():
            a=values[name];u=[core.source_cp_upper(int(f),500,.05/9) for f in a['z_abs'].sum(axis=1)];passed=[j for j,v in enumerate(u) if v<=.05];chosen=None if not passed else int(a['action_grid'][passed[0]])
            if chosen!=r['selected_source_action'] or chosen!=units[name]['summary']['selected_source_action']:raise ValueError('Source selection differs')
    elif phase=='selection':
        policy={'directed_pair_actions':[],'target_global_actions':[]}
        for row in cfg['datasets'].values():
            responses={b:{'z_abs':values[row['name']+'_'+b]['z_abs'],'array_sha':refs[row['name']+'_'+b]['array_sha256']} for b in cfg['build_ids']}
            result=core.select_dataset(row['name'],responses,cfg['records'][PANELS['source']]['rows'])
            for k in policy:policy[k].extend(result[k])
        if canonical(policy)!=cfg['policy_reference_sha256']['selection']:raise ValueError('Selection lock differs')
    elif phase=='certify':
        rows=[]
        for row in cfg['datasets'].values():
            responses={b:({int(g):z for g,z in zip(values[row['name']+'_'+b]['action_grid'],values[row['name']+'_'+b]['z_abs'])},refs[row['name']+'_'+b]['array_sha256']) for b in cfg['build_ids']}
            rows.extend(core.certify_dataset(row['name'],responses,prior['policy']))
        ordered=sorted(rows,key=lambda r:(r['dataset'],r['target_build_id'],str(r['source_build_id']),r['arm']))
        if canonical(ordered)!=cfg['policy_reference_sha256']['certify']:raise ValueError('Certification decisions differ')
        policy={'decisions':rows}
    return {'status':'NEW_FAISS1M_PANEL_LOCKED','phase':phase,'units':units,'policy':policy,'all_registered_records_preserved':True,'independent_builds_claimed':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--input-adapter',type=Path,required=True);p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-stage',action='store_true');a=p.parse_args()
    if not a.authorize_new_stage:p.error('New-stage opt-in required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linuxx86_64 Python3.11')
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    cfg=json.loads((HERE/'config.json').read_text());req=json.loads(a.request.read_text());kind=req['kind']
    if kind not in ('graph','truth','response','panel'):raise ValueError('Registered stage kind')
    cpus=set(range(4,20)) if kind=='truth' else {2};threads=16 if kind=='truth' else 1
    if not cpus<=os.sched_getaffinity(0):raise ValueError('Declared affinity unavailable')
    os.sched_setaffinity(0,cpus)
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]=str(threads)
    core=load(HERE/'historical_core.py','faiss1m_core',cfg['core_sha256']);adapter=load(a.input_adapter/'prepare_inputs.py','faiss1m_resources',cfg['dependencies']['portable_fresh_inputs/prepare_inputs.py'])
    plan=dict(cfg['resource_plan'])
    plan.update(cpu_affinity=sorted(cpus),library_threads=threads)
    if kind!='graph':plan.update(max_output_growth_bytes=512*1024**2,file_size_bytes=256*1024**2)
    out,telemetry=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{'request':a.request},a.outstanding_growth_bytes)
    import resource
    for k,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(k,(cap,cap))
    out.mkdir(mode=0o700);write(out/'start.json',{'config_sha256':sha(HERE/'config.json'),'request_sha256':sha(a.request),'resources':telemetry,'not_original_experiment_rerun':True})
    def timeout(s,f):raise TimeoutError('Stage wall bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        result={'graph':graph,'truth':generate_truth,'response':response,'panel':lock_panel}[kind](req,out,cfg,core)
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>plan['max_output_growth_bytes']:raise ValueError('Aggregate output bound')
        result['config_sha256']=sha(HERE/'config.json');write(out/'completed.json',result)
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_DEPENDENTS_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
