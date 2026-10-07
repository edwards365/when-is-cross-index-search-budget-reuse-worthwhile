"""Explicit future official Ada-ef stages; no archived launcher is imported."""
import argparse,csv,hashlib,importlib.util,json,math,os,platform,shlex,struct,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
ROLES={'source':'source_design','selection':'target_selection','certification':'target_certification','evaluation':'target_evaluation'}
FIELDS=['query_id','raw_action_ef','raw_score','raw_recall','raw_ndc','raw_topk','endpoint_ef','endpoint_recall','endpoint_ndc','endpoint_topk']
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def module(p,pin,name):
    if sha(p)!=pin:raise ValueError('Module SHA: '+p.name)
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def conf():
    c=json.loads((HERE/'config.json').read_text())
    for rel,pin in c['pins'].items():
        if sha(HERE/rel)!=pin:raise ValueError('Package pin')
    for rel,pin in c['official_files'].items():
        if sha(HERE/'official'/rel)!=pin:raise ValueError('Official source pin')
    return c
def done(ref,stage):
    folder=Path(ref['directory']).resolve(strict=True)
    if (folder/'failure.json').exists() or sha(folder/'completed.json')!=ref['sha256']:raise ValueError('Parent receipt')
    d=json.loads((folder/'completed.json').read_text())
    if d['stage']!=stage or d['config_sha256']!=sha(HERE/'config.json') or d['entry_sha256']!=sha(Path(__file__)):raise ValueError('Parent stage/config/entry')
    for rel,pin in d['outputs'].items():
        file=(folder/rel).resolve(strict=True)
        if not file.is_relative_to(folder) or sha(file)!=pin:raise ValueError('Parent payload')
    return folder,d
def previous(req):
    phase=req['phase'];required={'source':None,'selection':'source-panel','certification':'selection-lock','evaluation':'certification-lock'}[phase]
    return None if required is None else done(req['prior'],required)[1]
def role_row():return next(x for x in json.loads((HERE/'roles.json').read_text())['datasets'] if x['name']=='arxiv-nomic-1.34m-heldout')
def members(np):
    row=role_row();held=np.concatenate([np.asarray(row['roles'][x],dtype=np.int64) for x in ROLES.values()])
    if len(held)!=2500 or np.unique(held).size!=2500:raise ValueError('Four disjoint frozen roles')
    omitted=next(x for x in json.loads((HERE/'base_exclusions.json').read_text())['datasets'] if x['name']==row['name'])
    if omitted['excluded_index_row_ids']:raise ValueError('Unexpected Arxiv exclusions')
    keep=np.ones(row['train_shape'][0],dtype=bool);keep[held]=False;ids=np.flatnonzero(keep).astype(np.int64)
    if len(ids)!=1342143:raise ValueError('Frozen retained base')
    return row,held,keep,ids
def base(req,c,out):
    import numpy as np,h5py
    source=Path(req['source']);row,held,keep,ids=members(np)
    if sha(source)!=c['immutable_inputs']['raw_hdf5']['sha256']:raise ValueError('Raw source SHA')
    with h5py.File(source,'r') as src,h5py.File(out/'base.hdf5','x') as dest:
        raw=src['train']
        if list(raw.shape)!=row['train_shape'] or str(raw.dtype)!='float32':raise ValueError('Raw train metadata')
        train=dest.create_dataset('train',(len(ids),768),dtype='f4',chunks=(4096,768));cursor=0
        for begin in range(0,len(keep),4096):
            block=np.asarray(raw[begin:begin+4096][keep[begin:begin+4096]],dtype=np.float32)
            if not np.isfinite(block).all():raise ValueError('Nonfinite original vectors')
            train[cursor:cursor+len(block)]=block;cursor+=len(block)
        if cursor!=len(ids):raise ValueError('Base incomplete')
        dest.create_dataset('raw_ids',data=ids,dtype='i8');norms=np.empty(len(ids),dtype=np.float64)
        for begin in range(0,len(ids),4096):
            block=np.asarray(train[begin:begin+4096],dtype=np.float64);norms[begin:begin+len(block)]=np.einsum('ij,ij->i',block,block)
        dest.create_dataset('order_norm_ascending',data=np.lexsort((ids,norms)).astype(np.uint64),dtype='u8')
        for seed in (13,83,197,2029):dest.create_dataset(f'order_seed{seed}_random',data=np.random.RandomState(seed).permutation(len(ids)).astype(np.uint64),dtype='u8')
    return {'base_rows':len(ids),'source_sha256':sha(source),'forbidden_raw_datasets_accessed':[]}
def role_input(req,c,out):
    previous(req) # before any role vectors or truth access
    import numpy as np,h5py
    b,_=done(req['base'],'base');row,held,keep,rawids=members(np);role=ROLES[req['phase']];ids=np.asarray(row['roles'][role],dtype=np.int64);source=Path(req['source'])
    if sha(source)!=c['immutable_inputs']['raw_hdf5']['sha256']:raise ValueError('Raw source SHA')
    spec=c['immutable_inputs']['role_assets'];order=np.argsort(ids)
    with h5py.File(source,'r') as f:q=np.ascontiguousarray(np.asarray(f['train'][ids[order]],dtype=np.float32)[np.argsort(order)])
    qb=out/'queries.qbin'
    with qb.open('xb') as f:
        f.write(b'E1AQ0001'+struct.pack('<QQ',len(ids),768))
        for i,v in zip(ids,q):f.write(struct.pack('<q',int(i))+v.astype('<f4',copy=False).tobytes())
    if sha(qb)!=spec[role+'_queries'][1]:raise ValueError('Frozen qbin bytes')
    dest=out/'truth.npz'
    if req.get('sealed_truth'):
        import shutil
        supplied=Path(req['sealed_truth'])
        if sha(supplied)!=spec[role+'_truth'][1]:raise ValueError('Sealed truth identity')
        shutil.copy2(supplied,dest);truth_mode='imported_frozen_truth'
    else:
        helperdir=Path(req['truth_adapter']);helper=module(helperdir/'run_truth.py',c['truth_adapter_sha256'],'adaef_truth_native')
        if sha(helperdir/'native_lock.json')!=c['truth_native_lock_sha256']:raise ValueError('Truth native lock')
        faiss,_,_,native=helper.native_environment(json.loads((helperdir/'native_lock.json').read_text()))
        core=module(HERE/'truth_core.py',c['pins']['truth_core.py'],'adaef_truth_core');phase=req['phase'];empty=set();heldset=set(map(int,held))
        if phase=='source':arrays=core.truth_e1a_source(row,{'metric':'inner_product_on_original_normalized_float32','source_design_query_count':500},len(rawids),heldset,empty,source,8192,faiss,h5py)
        elif phase=='selection':arrays=core.truth_e1a_selection(row,{row['name']:{'metric':'ip','base_count':len(rawids)}},SimpleNamespace(dataset=row['name']),ids,heldset,empty,source,faiss,h5py)
        else:arrays=getattr(core,'truth_e1a_'+('certify' if phase=='certification' else 'evaluate'))(row,'ip',len(rawids),ids,heldset,empty,source,faiss,h5py)
        with dest.open('xb') as f:(np.savez if phase=='source' else np.savez_compressed)(f,**arrays)
        truth_mode='new_exact_truth_from_frozen_E1a_scientific_block'
    if sha(dest)!=spec[role+'_truth'][1]:raise ValueError('Frozen truth serialization mismatch')
    with np.load(dest,allow_pickle=False) as z:
        if not np.array_equal(z['query_ids'],ids):raise ValueError('Truth role IDs')
        truth=z['neighbor_raw_ids'].astype(np.int32)
    with h5py.File(out/'role.hdf5','x') as f,h5py.File(b/'base.hdf5','r') as src:
        for key in src:f[key]=h5py.ExternalLink(str((b/'base.hdf5').resolve()),'/'+key)
        f.create_dataset(role+'_query_ids',data=ids,dtype='i8');f.create_dataset(role+'_queries',data=q,dtype='f4');f.create_dataset(role+'_truth',data=truth,dtype='i4')
    return {'phase':req['phase'],'role':role,'base_ref':req['base'],'prior':req.get('prior'),'truth_mode':truth_mode,'role_count':len(ids),'native':locals().get('native')}
def compile_native(req,c,out,source_override=None):
    # New compilation, not a claim to reconstruct the historical compiler binary.
    eigen=Path(req['eigen_include']).resolve(strict=True);boost=Path(req['boost_include']).resolve(strict=True)
    ep=eigen/'Eigen/src/Core/util/Macros.h';bp=boost/'boost/version.hpp'
    for file,pin in ((ep,req['eigen_version_header_sha256']),(bp,req['boost_version_header_sha256'])):
        if sha(file)!=pin:raise ValueError('Prospectively declared dependency version-header SHA')
    source_cpp=source_override or HERE/'e2_adaef_native.cpp'
    shown=subprocess.check_output(['h5c++','-show'],text=True).strip();cmd=['h5c++','-std=c++17','-O3','-fopenmp','-I'+str(HERE/'official'),'-I'+str(eigen),'-I'+str(boost),str(source_cpp),'-o',str(out/'e2_adaef_native')]
    with (out/'compile.stdout').open('wb') as so,(out/'compile.stderr').open('wb') as se:p=subprocess.run(cmd,cwd=out,stdout=so,stderr=se,timeout=600)
    if p.returncode:raise ValueError('Official source compile failure')
    # Record every compiler-resolved dependency, not only the version headers.
    depcmd=cmd[:-2]+['-M'];deps=subprocess.check_output(depcmd,cwd=out,text=True,timeout=60)
    tokens=shlex.split(deps.replace('\\\n',' '))[1:];mapping={str(Path(x).resolve()):sha(Path(x)) for x in tokens if Path(x).is_file()}
    write(out/'compiler_dependencies.json',mapping)
    linkage={x:sha(Path(x)) for x in shlex.split(shown) if Path(x).is_file()};write(out/'wrapper_link_inputs.json',linkage)
    return {'actual_exit_code':p.returncode,'compiled_source_sha256':sha(source_cpp),'binary_sha256':sha(out/'e2_adaef_native'),'hdf5_wrapper':shown,'compiler_version':subprocess.check_output(['h5c++','--version'],text=True).splitlines()[0],'declared_dependencies':{k:req[k] for k in ('eigen_version_header_sha256','boost_version_header_sha256')},'historical_toolchain_equivalence_claimed':False}
def binary(ref):
    folder,d=done(ref,'compile');return folder/'e2_adaef_native'
def audit_response(path,rolefile,index,graphadapter,c):
    import h5py,numpy as np
    folder=Path(graphadapter)
    if sha(folder/'config.json')!=c['graph_config_sha256']:raise ValueError('Independent HNSW config')
    helper=module(folder/'build_graph.py',c['graph_adapter_sha256'],'adaef_independent_hnsw');hnsw,native=helper.installed_source(json.loads((folder/'config.json').read_text()))
    with h5py.File(rolefile,'r') as f:
        roles=[x[:-10] for x in f if x.endswith('_query_ids')]
        if len(roles)!=1:raise ValueError('One role only')
        role=roles[0];ids=np.asarray(f[role+'_query_ids']);q=np.asarray(f[role+'_queries']);truth=np.asarray(f[role+'_truth']);raw=np.asarray(f['raw_ids'])
    idx=hnsw.Index(space='ip',dim=q.shape[1]);idx.load_index(str(index),max_elements=len(raw));idx.set_num_threads(1);idx.set_ef(2400)
    if idx.get_current_count()!=len(raw) or set(idx.get_ids_list())!=set(map(int,raw)):raise ValueError('Saved graph raw IDs')
    with path.open() as f:
        rd=csv.DictReader(f)
        if rd.fieldnames!=FIELDS:raise ValueError('Native response schema')
        rows=list(rd)
    if len(rows)!=len(ids):raise ValueError('Native role count')
    for i,row in enumerate(rows):
        if int(row['query_id'])!=ids[i] or not 10<=int(row['raw_action_ef'])<=2400 or int(row['endpoint_ef'])!=2400 or not math.isfinite(float(row['raw_score'])):raise ValueError('Native role/action')
        for prefix in ('raw','endpoint'):
            labels=list(map(int,row[prefix+'_topk'].split(';')))
            if len(labels)!=10 or len(set(labels))!=10 or int(row[prefix+'_ndc'])<=0:raise ValueError('Native IDs/count')
            recall=len(set(labels)&set(map(int,truth[i])))/10
            if abs(float(row[prefix+'_recall'])-recall)>1e-8:raise ValueError('Independent recall')
            if prefix=='endpoint':
                independent=idx.knn_query(q[i:i+1],k=10,num_threads=1)[0][0]
                if labels!=list(map(int,independent)):raise ValueError('Independent endpoint ordered IDs')
    return {'rows':len(rows),'independent_endpoint_and_recall_pass':True,'native_distance_calls_independently_recomputed':False,'native':native}
def run_process(cmd,out,label,timeout=14400):
    with (out/(label+'.stdout')).open('wb') as so,(out/(label+'.stderr')).open('wb') as se:p=subprocess.run(list(map(str,cmd)),stdout=so,stderr=se,timeout=timeout)
    if p.returncode:raise ValueError(label+' actual exit '+str(p.returncode))
    return p.returncode
def source(req,c,out):
    role,rd=done(req['role_input'],'role-input')
    if rd['phase']!='source':raise ValueError('Source-design only')
    done(rd['base_ref'],'base');exe=binary(req['compile']);state=next(x for x in c['states'] if x['key']==req['key'])
    waits=[run_process([exe,'build-design',role/'role.hdf5',out/'index.hnsw',out/'adapter.bin',out/'summary.json',state['seed'],state['history']],out,'build')]
    waits.append(run_process([exe,'run-role',role/'role.hdf5','source_design',out/'index.hnsw',out/'adapter.bin',out/'response.csv','500'],out,'source'))
    audit=audit_response(out/'response.csv',role/'role.hdf5',out/'index.hnsw',req['graph_adapter'],c)
    from scipy.stats import beta
    failures=sum(x['endpoint_recall']<.95 for x in read_rows(out).values());bound=1. if failures==500 else float(beta.ppf(.95,failures+1,500-failures))
    if bound>.05:raise ValueError('Original source endpoint safety gate failed')
    if sha(out/'index.hnsw')!=state['index_sha256'] or sha(out/'adapter.bin')!=state['adapter_sha256']:raise ValueError('Historical index/adapter bytes differ; stop without repinning')
    return {'key':req['key'],'actual_exit_codes':waits,'audit':audit,'endpoint_cp_ucb':bound,'role_input_ref':req['role_input'],'compile_ref':req['compile']}
def source_panel(req,c,out):
    units={}
    for ref in req['sources']:
        folder,d=done(ref,'source');key=d['key']
        if key in units:raise ValueError('Duplicate source')
        units[key]=ref
    if set(units)!={x['key'] for x in c['states']}:raise ValueError('All eight sources required')
    return {'units':units}
def response(req,c,out):
    prior=previous(req);panel=done(req['source_panel'],'source-panel')[1]
    role,rd=done(req['role_input'],'role-input')
    if rd['phase']!=req['phase'] or rd['prior']!=req['prior']:raise ValueError('Role phase lock')
    done(rd['base_ref'],'base');target,td=done(panel['units'][req['target_key']],'source');src,sd=done(panel['units'][req['source_key']],'source')
    if req['phase']=='certification' and req['target_key']!=req['source_key']:raise ValueError('Frozen endpoint-only certification uses eight native diagnostic units')
    exe=binary(td['compile_ref']);wait=run_process([exe,'run-role',role/'role.hdf5',ROLES[req['phase']],target/'index.hnsw',src/'adapter.bin',out/'response.csv','1000' if req['phase']=='evaluation' else '500'],out,'response',7200)
    audit=audit_response(out/'response.csv',role/'role.hdf5',target/'index.hnsw',req['graph_adapter'],c)
    return {'phase':req['phase'],'source_key':req['source_key'],'target_key':req['target_key'],'prior':req['prior'],'source_panel':req['source_panel'],'role_input_ref':req['role_input'],'actual_exit_code':wait,'audit':audit}
def read_rows(folder):
    with (folder/'response.csv').open() as f:return {int(x['query_id']):dict(x,raw_recall=float(x['raw_recall']),endpoint_recall=float(x['endpoint_recall']),raw_ndc=int(x['raw_ndc']),endpoint_ndc=int(x['endpoint_ndc'])) for x in csv.DictReader(f)}
def reconcile(req,c,phase):
    previous(req);expected={x['key'] for x in c['states']};responses={};refs={}
    for ref in req['responses']:
        folder,d=done(ref,'response');key=(d['source_key'],d['target_key'])
        if d['phase']!=phase or d['prior']!=req['prior'] or key in responses:raise ValueError('Response phase/identity')
        responses[key]=read_rows(folder);refs[key[0]+'__to__'+key[1]]=ref
    keys={(s,t) for s in expected for t in expected if phase!='certification' or s==t}
    if set(responses)!=keys:raise ValueError('Complete eight-target arm registry required')
    for t in expected:
        canonical=responses[t,t]
        for (s,target),rows in responses.items():
            if target!=t:continue
            if set(rows)!=set(canonical):raise ValueError('Shared query identity')
            for q in rows:
                if any(rows[q][k]!=canonical[q][k] for k in ('endpoint_topk','endpoint_ndc','endpoint_recall')):raise ValueError('Endpoint arm reconciliation')
    return responses,refs
def selection_lock(req,c,out):
    rows,refs=reconcile(req,c,'selection');core=module(HERE/'selection_core.py',c['pins']['selection_core.py'],'adaef_selection');decisions=[]
    for (s,t),r in sorted(rows.items()):
        if s==t:continue
        arms={'transferred':core.summary(r,'raw_recall','raw_ndc'),'target_native':core.summary(rows[t,t],'raw_recall','raw_ndc'),'endpoint':core.summary(rows[t,t],'endpoint_recall','endpoint_ndc')}
        chosen,fallback=choose(arms)
        decisions.append({'source_key':s,'target_key':t,'selected_arm':chosen,'selection_fallback':fallback,'arms':arms})
    if any(d['selected_arm']!='endpoint' or d['selection_fallback'] for d in decisions):raise ValueError('Frozen official selection outcome differs; retain and stop, no generic substitute protocol')
    write(out/'decisions.json',decisions);return {'decisions':decisions,'responses':refs,'prior':req['prior']}
def choose(arms):
    order=('transferred','target_native','endpoint');eligible=[x for x in order if arms[x]['screen_eligible']]
    return (min(eligible,key=lambda x:(arms[x]['mean_native_distance_calls'],order.index(x))),False) if eligible else ('endpoint',True)
def certification_lock(req,c,out):
    from scipy.stats import beta
    rows,refs=reconcile(req,c,'certification');prior=done(req['prior'],'selection-lock')[1];decisions=[]
    for d in prior['decisions']:
        f=sum(x['endpoint_recall']<.95 for x in rows[d['target_key'],d['target_key']].values());u=1. if f==500 else float(beta.ppf(.95,f+1,500-f))
        decisions.append({k:d[k] for k in ('source_key','target_key','selected_arm')}|{'failures':f,'cp_ucb':u,'action':'execute_endpoint' if u<=.05 else 'abstain'})
    if any(d['action']!='execute_endpoint' for d in decisions):raise ValueError('Frozen certification outcome differs; stop without evaluation')
    write(out/'decisions.json',decisions);return {'decisions':decisions,'responses':refs,'prior':req['prior']}
def evaluation_lock(req,c,out):
    rows,refs=reconcile(req,c,'evaluation');prior=done(req['prior'],'certification-lock')[1]
    return {'responses':refs,'locked_decisions':prior['decisions'],'prior':req['prior'],'transferred_directions':56,'target_native_units':8,'evaluation_queries_per_unit':1000,'evaluation_does_not_select':True}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--input-adapter',type=Path,required=True);p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-stage',action='store_true');a=p.parse_args()
    if not a.authorize_new_stage:p.error('Explicit new-stage authorization required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 without -O required')
    req=json.loads(a.request.read_text());c=conf();stage=req['stage'];plan=dict(c['resources'])
    if stage=='role-input' and not req.get('sealed_truth'):plan['cpu_affinity']=list(range(4,20))
    cpus=set(plan['cpu_affinity'])
    if not cpus.issubset(os.sched_getaffinity(0)):raise ValueError('Declared CPUs unavailable')
    os.sched_setaffinity(0,cpus)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    helper=module(a.input_adapter/'prepare_inputs.py',c['input_adapter_sha256'],'adaef_resources');out,snapshot=helper.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{},a.outstanding_growth_bytes)
    import resource,signal
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);write(out/'start.json',{'stage':stage,'request':req,'resources':snapshot,'config_sha256':sha(HERE/'config.json')})
    def timeout(sig,frame):raise TimeoutError('Stage wall limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        import numpy,scipy,h5py
        if (numpy.__version__,scipy.__version__,h5py.__version__)!=('1.26.4','1.13.1','3.11.0'):raise ValueError('Pinned Python dependencies')
        handlers={'base':base,'role-input':role_input,'compile':compile_native,'source':source,'source-panel':source_panel,'response':response,'selection-lock':selection_lock,'certification-lock':certification_lock,'evaluation-lock':evaluation_lock}
        result=handlers[stage](req,c,out)
        if sum(f.stat().st_size for f in out.rglob('*') if f.is_file())>plan['max_output_growth_bytes']:raise ValueError('Output growth cap')
        result.update(stage=stage,status='NEW_ADAEF_STAGE_COMPLETE_NOT_HISTORICAL_ATTESTATION',config_sha256=sha(HERE/'config.json'),entry_sha256=sha(Path(__file__)),outputs={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and f.name!='start.json'})
        write(out/'completed.json',result)
    except BaseException as e:write(out/'failure.json',{'status':'FAILED_STOP_DEPENDENTS','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
