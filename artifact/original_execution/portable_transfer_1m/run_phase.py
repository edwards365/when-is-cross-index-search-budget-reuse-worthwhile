"""New, explicitly requested truth/response/panel stages; never infer sealed paths."""
import argparse,importlib.metadata,importlib.util,json,os,platform,signal,struct,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from run_transfer import HERE,sha,pin,load,e1a_members

ROLES={'source':'source_design','selection':'target_selection','certify':'target_certification','evaluate':'target_evaluation'}

def write(p,x):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def done(folder,status,cfg):
    folder=Path(folder).resolve(strict=True)
    if (folder/'failure.json').exists():raise ValueError('Failed predecessor')
    d=json.loads((folder/'completed.json').read_text())
    if d['status']!=status or d.get('config_sha256')!=sha(HERE/'config.json'):raise ValueError('Predecessor status/config')
    return folder,d

def panel(folder,family,phase,cfg):
    folder,d=done(folder,'NEW_TRANSFER_PANEL_LOCKED',cfg)
    if (d['family'],d['phase'])!=(family,phase) or set(d['units'])!=set(cfg[family+'_response_pins'][phase]) or len(d['units'])!=16:raise ValueError('Wrong panel phase/cardinality')
    for key,row in d['units'].items():
        prior=Path(row['directory']);pin(prior/'completed.json',row['receipt_sha256']);pin(prior/'response.npz',cfg[family+'_response_pins'][phase][key]['sha256'])
        check_summary(prior/'response.npz',family,phase,row['summary'])
    if family=='e1a' and phase in ('selection','certify'):
        ref=cfg['historical_policy_references']['actions' if phase=='selection' else 'decisions']
        if phase=='selection' and d['policy']!=ref:raise ValueError('Locked selection policy drift')
        if phase=='certify':
            canon=lambda x:sorted(x['decisions'],key=lambda r:(r['dataset'],r['target_build_id'],str(r['source_build_id']),r['arm']))
            if canon(d['policy'])!=canon(ref):raise ValueError('Locked certification policy drift')
    return d

def check_summary(path,family,phase,summary):
    import numpy as np
    from scipy.stats import beta
    cp=lambda f,n,delta:1.0 if f==n else float(beta.ppf(1-delta,f+1,n-f))
    with np.load(path,allow_pickle=False) as a:
        if phase=='source':
            grid=a['action_grid'];z=a['z_abs'];ucbs=[cp(int(f),500,.05/11) for f in z.sum(axis=1)];accepted=[i for i,u in enumerate(ucbs) if u<=.05]
            selected=None if not accepted else int(grid[accepted[0]])
            if selected!=summary['selected_source_action'] or ucbs!=summary['cp_ucb']:raise ValueError('Source decision detached from response')
        if family=='e1b' and phase=='certify':
            u=[cp(int(a[k].sum()),500,.025) for k in ('z_abs_candidate','z_abs_endpoint')]
            decision='execute_candidate' if u[0]<=.05 and u[1]<=.05 else 'endpoint_fallback' if u[1]<=.05 else 'abstain'
            if decision!=summary['decision'] or u!=summary['cp_ucb'] or int(a['action_ef'][0])!=summary['selected_source_action']:raise ValueError('Certification decision detached from response')

def earlier(req,cfg):
    phase=req['phase'];family=req['family']
    # Lock gates execute before opening requested raw/query/truth inputs.
    previous={'source':None,'selection':'source','certify':'selection' if family=='e1a' else 'source','evaluate':'certify'}[phase]
    return None if previous is None else panel(req['prior_panel'],family,previous,cfg)

def identities(req,cfg,np):
    row=cfg['datasets'][req['dataset']];role=ROLES[req['phase']]
    if req['family']=='e1a':
        held,excluded,members=e1a_members(row,np);ids=np.asarray(row['roles'][role],dtype=np.int64)
    else:
        folder=Path(req['memberships']);m=json.loads((folder/'completed.json').read_text())
        if (folder/'failure.json').exists() or m['status']!='NEW_E1B_MEMBERSHIPS_MATCH_FROZEN_BYTES':raise ValueError('Membership predecessor')
        pin(folder/'candidate_ids.npz',cfg['e1b_candidate_sha256']);pin(folder/'final_membership_ids.npz',cfg['e1b_membership_sha256'])
        with np.load(folder/'candidate_ids.npz',allow_pickle=False) as a:ids=a[req['dataset']+'_'+role+'_ids'].copy()
        with np.load(folder/'final_membership_ids.npz',allow_pickle=False) as a:members=a[req['dataset']+'_'+req.get('state','initial')+'_member_ids'].copy()
        held=excluded=None
    if len(ids)!=(1000 if req['phase']=='evaluate' else 500) or np.unique(ids).size!=len(ids) or np.intersect1d(ids,members).size:raise ValueError('Query/member identity')
    return row,ids,members,held,excluded

def graph(req,cfg,state=None):
    family=req['family'];key=cfg['datasets'][req['dataset']]['name']+f"_seed{req['seed']}_"+req['history']
    path=Path(req['graphs'][state or 'fixed'])
    if family=='e1a':r=next(r for r in cfg['e1a_graphs'] if r['dataset']+f"_seed{r['seed']}_"+r['history']==key);count=r['serialized_count']
    else:r=cfg['e1b_graphs'][key][state];count=r['reload_count']
    pin(path,r['index_sha256'])
    if path.stat().st_size!=r['index_bytes']:raise ValueError('Graph size')
    return path,count,key

def truth_input(path,req,cfg,ids,np,state=None):
    key=req['dataset']+('_'+state if req['family']=='e1b' else '')+'_'+ROLES[req['phase']]
    pin(Path(path),cfg[req['family']+'_truth_pins'][key])
    with np.load(path,allow_pickle=False) as a:
        if not np.array_equal(a['query_ids'],ids) or a['neighbor_raw_ids'].shape!=(len(ids),10):raise ValueError('Truth role identity')
        return a['neighbor_raw_ids'].copy()

def native_truth(folder,cfg,family):
    helper=load(folder/'run_truth.py','transfer_truth_payload',cfg['dependencies']['truth_adapter']);pin(folder/'native_lock.json',cfg['dependencies']['truth_native_lock']);lock=json.loads((folder/'native_lock.json').read_text())
    if family=='e1a':return helper.native_environment(lock)
    if any(k in os.environ for k in ('FAISS_OPT_LEVEL','FAISS_DISABLE_CPU_FEATURES','LD_PRELOAD')) or 'faiss' in sys.modules:raise ValueError('No prior Faiss dispatch override/import')
    dist=importlib.metadata.distribution('faiss-cpu');site=Path(dist.locate_file('')).resolve(strict=True)
    if dist.version!=lock['distribution_version']:raise ValueError('Faiss distribution')
    count=helper.pinned_payload(site,lock)
    spec=importlib.util.find_spec('faiss')
    if Path(spec.origin).resolve()!=site/'faiss/__init__.py':raise ValueError('Shadowed Faiss')
    os.environ['FAISS_OPT_LEVEL']='AVX2'
    import faiss,numpy as np,h5py
    if faiss.get_compile_options().strip()!='OPTIMIZE AVX2' or faiss.__version__!=lock['module_version']:raise ValueError('E1b requires AVX2')
    if np.__version__!=lock['numpy_version'] or h5py.__version__!=lock['h5py_version']:raise ValueError('Truth libraries')
    native=Path(sys.modules['faiss._swigfaiss_avx2'].__file__).resolve();rel=native.relative_to(site).as_posix();pin(native,lock['installed_payload'][rel])
    return faiss,np,h5py,{'payload_files_checked':count,'dispatch':'AVX2','native_sha256':sha(native),'historical_runtime_retroactively_attested':False}

def generate_truth(req,out,cfg,core):
    earlier(req,cfg)
    faiss,np,h5py,native=native_truth(Path(req['truth_adapter']),cfg,req['family'])
    row,ids,members,held,excluded=identities(req,cfg,np);source=Path(req['source']);pin(source,row['source_sha256'])
    family=req['family'];phase=req['phase'];metric='l2' if req['dataset']=='sift' else 'ip'
    if family=='e1a':
        common=(row,metric,len(members),ids,set(map(int,held)),set(map(int,excluded)),source,faiss,h5py)
        if phase=='source':
            config={'metric':'squared_l2' if metric=='l2' else 'inner_product_on_original_normalized_float32','source_design_query_count':500}
            arrays=core.truth_e1a_source(row,config,len(members),set(map(int,held)),set(map(int,excluded)),source,8192,faiss,h5py)
        elif phase=='selection':arrays=core.truth_e1a_selection(row,{row['name']:{'metric':metric,'base_count':len(members)}},SimpleNamespace(dataset=row['name']),ids,set(map(int,held)),set(map(int,excluded)),source,faiss,h5py)
        else:arrays=getattr(core,'truth_e1a_'+phase)(*common)
    else:
        if phase=='selection':raise ValueError('E1b target_selection is never accessed')
        if phase=='certify' and req['state']!='refreshed':raise ValueError('Certification only refreshed membership')
        if phase=='source':arrays=core.truth_e1b_source(row,metric,len(members),ids,members,source,faiss,h5py)
        else:arrays=getattr(core,'truth_e1b_'+phase)(row,{'metric':metric,'member_count':len(members)},ids,members,source,faiss,h5py)
    dest=out/'truth.npz'
    with dest.open('xb') as f:(np.savez if family=='e1a' and phase=='source' else np.savez_compressed)(f,**arrays)
    key=req['dataset']+('_'+req['state'] if family=='e1b' else '')+'_'+ROLES[phase];pin(dest,cfg[family+'_truth_pins'][key])
    return {'status':'NEW_TRANSFER_TRUTH_MATCHES_FROZEN_BYTES','truth_sha256':sha(dest),'native':native,'historical_timing_identity_claimed':False}

def python_native(req,cfg):
    folder=Path(req['graph_adapter']);pin(folder/'config.json',cfg['dependencies']['graph_config']);helper=load(folder/'build_graph.py','transfer_search_native',cfg['dependencies']['graph_adapter'])
    return helper.installed_source(json.loads((folder/'config.json').read_text()))

def query_binary(path,source,ids,np,h5py):
    order=np.argsort(ids)
    with h5py.File(source,'r') as f:q=np.ascontiguousarray(np.asarray(f['train'][ids[order]],dtype=np.float32)[np.argsort(order)])
    with path.open('xb') as f:
        f.write(b'E1AQ0001'+struct.pack('<QQ',len(ids),q.shape[1]))
        for i,v in zip(ids,q):f.write(struct.pack('<q',int(i))+v.astype('<f4',copy=False).tobytes())

class CheckedProcess:
    def __init__(self,out):self.out=out;self.waits=[]
    def run(self,command,**kw):
        # Synchronous wait is real; caps/affinity inherited from this bounded stage.
        result=subprocess.run(command,timeout=600,capture_output=True,text=True)
        self.waits.append(result.returncode)
        write(self.out/'native_wait.json',{'returncode':result.returncode,'stdout':result.stdout[-20000:],'stderr':result.stderr[-20000:]})
        result.check_returncode();return result

def response(req,out,cfg,core):
    prior=earlier(req,cfg)
    import numpy as np,h5py
    row,ids,members,held,excluded=identities(req,cfg,np);source=Path(req['source']);pin(source,row['source_sha256']);hnsw,native=python_native(req,cfg)
    family=req['family'];phase=req['phase'];unit={'prefix':req['dataset'],'dataset':row['name']};bid=f"seed{req['seed']}_"+req['history'];key=row['name']+'_'+bid;summary={};waits=[]
    if family=='e1b':
        if phase=='selection':raise ValueError('E1b target_selection not part of experiment')
        selected=None if phase=='source' else prior['units'][key]['summary']['selected_source_action']
        if phase!='source' and selected is None:raise ValueError('No selected source action; fail closed')
        if phase=='evaluate':
            gs=[graph(req,cfg,s) for s in ('initial','refreshed')];truths=[truth_input(req['truths'][s],req,cfg,ids,np,s) for s in ('initial','refreshed')]
            arrays,summary=core.eval_response(ids,source,row,unit,[g[0] for g in gs],[g[1] for g in gs],selected,prior['units'][key]['summary']['decision'],truths,h5py,hnsw)
        else:
            state='initial' if phase=='source' else 'refreshed';g,count,_=graph(req,cfg,state);neighbors=truth_input(req['truths'][state],req,cfg,ids,np,state)
            if phase=='source':arrays,summary=core.source_response(ids,source,row,unit,g,{'member_count':count},np.asarray(cfg['action_grid'],dtype=np.int32),neighbors,h5py,hnsw)
            else:arrays,summary=core.cert_response(ids,source,row,unit,g,{'member_count':count},selected,neighbors,h5py,hnsw)
    else:
        g,count,_=graph(req,cfg);neighbors=truth_input(req['truths']['fixed'],req,cfg,ids,np)
        if phase=='source':arrays,summary=core.e1a_source_response(ids,source,SimpleNamespace(dataset=row['name']),g,{'serialized_count':count},{'action_grid':cfg['action_grid']},neighbors,key,h5py,hnsw)
        else:
            grid=cfg['action_grid'] if phase=='selection' else core.expected_grid(row['name'],bid,prior['policy'])[0] if phase=='certify' else core.action_grid(row['name'],bid,prior['policy'])
            profiles=Path(req['profiles_adapter']);pin(profiles/'config.json',cfg['dependencies']['profiles_config']);pin(profiles/'native_entry.py',cfg['dependencies']['profiles_entry'])
            pc=json.loads((profiles/'config.json').read_text())
            for file,h in pc['files'].items():pin(profiles/file,h)
            build=Path(req['native_build']);bd=json.loads((build/'completed.json').read_text())
            if (build/'failure.json').exists() or bd['status']!='PASS_NEW_BUILD_AND_SYNTHETIC_NATIVE_CHECKS' or bd['config_sha256']!=cfg['dependencies']['profiles_config'] or bd['entry_sha256']!=cfg['dependencies']['profiles_entry']:raise ValueError('Counter build receipt')
            counter=build/('replay1000' if phase=='evaluate' else 'replay500');pin(counter,bd['binaries'][counter.name])
            qb=out/'queries.qbin';query_binary(qb,source,ids,np,h5py);process=CheckedProcess(out)
            arrays,mismatches=getattr(core,'e1a_'+phase+'_response')(ids,len(ids),source,row['name'],g,{'serialized_count':count},grid,neighbors,counter,qb,out/'counter.csv',h5py,hnsw,process,row)
            if mismatches:raise ValueError('Native counter equivalence: '+str(mismatches[:10]))
            waits=process.waits;summary={'action_grid':grid,'query_binary_sha256':sha(qb),'counter_csv_sha256':sha(out/'counter.csv'),'counter_binary_sha256':sha(counter)}
    with (out/'response.npz').open('xb') as f:np.savez_compressed(f,**arrays)
    pin(out/'response.npz',cfg[family+'_response_pins'][phase][key]['sha256'])
    return {'status':'NEW_TRANSFER_RESPONSE_MATCHES_FROZEN_BYTES','unit':key,'dataset':req['dataset'],'seed':req['seed'],'history':req['history'],'summary':summary,'native':native,'subprocess_exit_codes':waits,'response_sha256':sha(out/'response.npz')}

def lock_panel(req,out,cfg,core):
    import numpy as np
    phase=req['phase'];family=req['family'];prior=earlier(req,cfg);units={}
    expected=set(cfg[family+'_response_pins'][phase])
    if len(req['responses'])!=16:raise ValueError('All 16 response units required')
    for path in req['responses']:
        folder,d=done(path,'NEW_TRANSFER_RESPONSE_MATCHES_FROZEN_BYTES',cfg);key=d['unit']
        if (d['family'],d['phase'])!=(family,phase) or key in units or key not in expected:raise ValueError('Wrong/duplicate response')
        pin(folder/'response.npz',cfg[family+'_response_pins'][phase][key]['sha256'])
        check_summary(folder/'response.npz',family,phase,d['summary'])
        units[key]={'directory':str(folder),'receipt_sha256':sha(folder/'completed.json'),'summary':d['summary'],'seed':d['seed'],'history':d['history'],'dataset':d['dataset']}
    if set(units)!=expected:raise ValueError('Incomplete response panel')
    policy={}
    if family=='e1a' and phase=='selection':
        policy={'directed_pair_actions':[],'target_global_actions':[]}
        for prefix,row in cfg['datasets'].items():
            responses={};sources=[]
            for key,r in units.items():
                if r['dataset']!=prefix:continue
                bid=f"seed{r['seed']}_"+r['history']
                with np.load(Path(r['directory'])/'response.npz',allow_pickle=False) as a:responses[bid]=(a['z_abs'].copy(),a['ndc'].copy())
                sources.append({'dataset':row['name'],'seed':r['seed'],'history':r['history'],'selected_source_action':prior['units'][key]['summary']['selected_source_action']})
            result=core.e1a_selection_policy(row['name'],responses,sources)
            for k in policy:policy[k].extend(result[k])
        if policy!=cfg['historical_policy_references']['actions']:raise ValueError('Selection policy differs from frozen policy')
    if family=='e1a' and phase=='certify':
        decisions=[]
        for key,r in units.items():
            name=cfg['datasets'][r['dataset']]['name'];bid=f"seed{r['seed']}_"+r['history'];grid,pairs,glob=core.expected_grid(name,bid,prior['policy'])
            with np.load(Path(r['directory'])/'response.npz',allow_pickle=False) as a:z=a['z_abs'].copy();ndc=a['ndc'].copy()
            efails=int(z[-1].sum());ucb=core.cp_upper(efails,500,.025);arms=[(None,'fixed_endpoint',2400),(None,'target_global',glob['selected_ef'])]
            arms.extend((x['source_build_id'],arm,x[field]) for x in pairs for arm,field in [('source_reuse','source_action_ef'),('one_rung','one_rung_ef'),('selected_ladder','selected_ef')])
            decisions.extend(core.outcome(name,bid,src,arm,int(ef),grid,z,ndc,efails,ucb,lambda f:core.cp_upper(f,500,.025)) for src,arm,ef in arms)
        policy={'decisions':decisions}
        # Traversal order is fixed below by dataset/seed/history, never caller order.
        order=lambda d:(d['dataset'],d['target_build_id'],str(d['source_build_id']),d['arm'])
        if sorted(decisions,key=order)!=sorted(cfg['historical_policy_references']['decisions']['decisions'],key=order):raise ValueError('Certification policy differs')
    return {'status':'NEW_TRANSFER_PANEL_LOCKED','units':units,'policy':policy,'downstream_queries_read':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--request',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--input-adapter',type=Path,required=True);ap.add_argument('--outstanding-growth-bytes',type=int,required=True);ap.add_argument('--authorize-new-stage',action='store_true');a=ap.parse_args()
    if not a.authorize_new_stage:ap.error('New-stage opt-in required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux x86_64 Python3.11 without -O required')
    cfg=json.loads((HERE/'config.json').read_text());req=json.loads(a.request.read_text());family=req['family'];phase=req['phase'];kind=req['kind']
    if family not in ('e1a','e1b') or phase not in ROLES or kind not in ('truth','response','panel') or (family=='e1b' and phase=='selection'):raise ValueError('Family/phase/kind')
    plan=dict(cfg['resource_plan']);plan.update(file_size_bytes=128*1024**2,max_output_growth_bytes=256*1024**2,cpu_seconds=7200,wall_seconds=7200)
    cpus={2} if kind!='truth' else set(range(4,20));threads=1 if kind!='truth' else 16
    plan['cpu_affinity']=sorted(cpus);plan['library_threads']=threads
    if not cpus<=os.sched_getaffinity(0):raise ValueError('Declared affinity unavailable')
    os.sched_setaffinity(0,cpus)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]=str(threads)
    adapter=load(a.input_adapter/'prepare_inputs.py','transfer_stage_resources',cfg['dependencies']['input_adapter'])
    out,telemetry=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{'config':HERE/'config.json','request':a.request},a.outstanding_growth_bytes)
    import resource
    for kindid,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kindid);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kindid,(cap,cap))
    core=load(HERE/'historical_core.py','transfer_phase_core',cfg['core_sha256'])
    if core.np.__version__!='1.26.4' or importlib.metadata.version('scipy')!='1.13.1' or importlib.metadata.version('h5py')!='3.11.0':raise ValueError('Pinned scientific Python versions')
    out.mkdir(mode=0o700);write(out/'start.json',{'status':'NEW_TRANSFER_STAGE_STARTED','family':family,'phase':phase,'kind':kind,'config_sha256':sha(HERE/'config.json'),'request_sha256':sha(a.request),'entry_sha256':sha(Path(__file__)),'telemetry':telemetry,'cpu_affinity':sorted(cpus),'threads':threads})
    def timeout(s,f):raise TimeoutError('Stage wall timeout')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        record={'truth':generate_truth,'response':response,'panel':lock_panel}[kind](req,out,cfg,core)
        growth=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        if growth>plan['max_output_growth_bytes']:raise ValueError('Stage aggregate output budget')
        record.update(family=family,phase=phase,kind=kind,config_sha256=sha(HERE/'config.json'),request_sha256=sha(a.request),new_run_not_historical_receipt=True)
        write(out/'completed.json',record);print(json.dumps({'status':record['status'],'family':family,'phase':phase}))
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_DEPENDENTS_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)

if __name__=='__main__':main()
