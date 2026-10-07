"""Explicit new-output Deep recovery phases. Nothing executes at import."""
import argparse,csv,hashlib,importlib.util,json,os,platform,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def module(name):
    s=importlib.util.spec_from_file_location('deep_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def config():
    c=json.loads((HERE/'config.json').read_text())
    for rel,pin in c['files'].items():
        if digest(HERE/rel)!=pin:raise ValueError('Packaged source mismatch: '+rel)
    return c
def role_ids(cfg):
    import numpy as np
    r=json.loads((HERE/'roles.json').read_text());roles=r['roles']
    ids=np.asarray([i for role in cfg['role_order'] for i in roles[role]],dtype=np.int64)
    if len(ids)!=1500 or len(np.unique(ids))!=1500 or np.any(ids<0) or np.any(ids>=10000):raise ValueError('Role ranges/disjointness')
    if any(len(roles[k])!=500 or roles[k]!=sorted(roles[k]) for k in cfg['role_order']):raise ValueError('Role counts/order')
    prior=set(np.sort(np.random.RandomState(991).choice(10000,500,replace=False)).tolist())
    left=np.asarray([i for i in range(10000) if i not in prior]);old=set(np.sort(np.random.default_rng(2991).choice(left,1000,replace=False)).tolist())
    remain=np.asarray([i for i in range(10000) if i not in prior|old]);chosen=np.random.default_rng(3991).choice(remain,1500,replace=False)
    expected=np.concatenate([np.sort(chosen[i:i+500]) for i in range(0,1500,500)])
    if not np.array_equal(ids,expected):raise ValueError('Frozen role regeneration differs')
    return ids
def native(cfg):
    import importlib.metadata as md
    d=md.distribution('hnswlib');src=json.loads(d.read_text('direct_url.json') or '{}')
    if d.version!='0.8.0' or src.get('archive_info',{}).get('hashes',{}).get('sha256')!=cfg['source_distribution']['sha256']:raise ValueError('Pinned hnswlib source installation required')
    import hnswlib,numpy,h5py
    if numpy.__version__!='1.26.4' or h5py.__version__!='3.11.0':raise ValueError('Library versions')
    return {'hnswlib_extension_sha256':digest(hnswlib.__file__),'source_archive_sha256':cfg['source_distribution']['sha256'],'historical_binary_identity_claimed':False}
def receipt(folder,phase):
    if (folder/'failure.json').exists():raise ValueError('Failed prerequisite')
    x=json.loads((folder/'completed.json').read_text())
    if x['phase']!=phase or x['config_sha256']!=digest(HERE/'config.json'):raise ValueError('Prerequisite phase/config')
    for rel,pin in x['outputs'].items():
        if digest(folder/rel)!=pin:raise ValueError('Prerequisite payload changed')
    return x
def validate_csv(path,build,queries,grid):
    seen=set()
    with path.open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            key=(int(r['query_id']),int(r['ef']));ids=list(map(int,r['topk'].split(';')))
            if r['build']!=build or key in seen or not 0<=key[0]<queries or key[1] not in grid:raise ValueError('CSV identity/grid/duplicate')
            if len(ids)!=10 or len(set(ids))!=10 or min(ids)<0 or max(ids)>=1000000 or int(r['ndc'])<=0 or not 0<=float(r['recall'])<=1:raise ValueError('CSV payload')
            seen.add(key)
    if len(seen)!=queries*len(grid):raise ValueError('CSV incomplete')
def execute(a,c):
    if not a.authorize_new_execution:raise ValueError('Explicit new execution opt-in required')
    if a.phase=='prepare' and not a.authorize_historical_test_member:raise ValueError('Historical test-member access requires named opt-in')
    if platform.machine()!='x86_64':raise ValueError('x86_64 required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    resources=module('resources');sources={k:v for k,v in vars(a).items() if k!='output' and isinstance(v,Path)}
    out,snapshot=resources.preflight({'python_minor':[3,11],'resource_plan':c['resource_plan']},a.output,sources,a.outstanding_growth_bytes)
    import resource,signal
    plan=c['resource_plan']
    for kind,limit in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([limit]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);resources.write_json(out/'start.json',{'phase':a.phase,'config_sha256':digest(HERE/'config.json'),'adapter_sha256':digest(Path(__file__)),'resources':snapshot})
    def timeout(sig,frame):raise TimeoutError('Deep wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    result={};payload=[]
    try:
        if a.phase in ('prepare','build'):
            if not a.dataset or digest(a.dataset)!=c['dataset']['sha256']:raise ValueError('Raw Deep HDF5 SHA')
            result['native']=native(c);core=module('historical_core');import numpy as np,h5py
            with h5py.File(a.dataset,'r') as f:
                if f['train'].shape[0]<1000000 or f['train'].shape[1]!=96 or str(f['train'].dtype)!='float32':raise ValueError('Deep train shape/dtype')
                base=np.asarray(f['train'][:1000000],dtype=np.float32)
                if a.phase=='prepare':
                    if f['test'].shape!=(10000,96) or str(f['test'].dtype)!='float32':raise ValueError('Deep test shape/dtype')
                    ids=role_ids(c);all_queries=np.asarray(f['test'],dtype=np.float32);queries=core.normalize(all_queries[ids])
            if a.phase=='prepare':
                truth=core.exact_truth(base,queries);core.write_vecs(out/'queries.fvecs',queries,'<f4');core.write_vecs(out/'truth.ivecs',truth,'<i4')
                if digest(out/'queries.fvecs')!=c['expected_queries_sha256'] or digest(out/'truth.ivecs')!=c['expected_truth_sha256']:raise ValueError('Frozen query/truth bytes differ; stop without repinning')
                np.save(out/'external_ids.npy',ids,allow_pickle=False);payload=['queries.fvecs','truth.ivecs','external_ids.npy'];result['historical_test_member_access']=True
            else:
                stem=f'deep1m_seed{a.seed}_{a.history}';core.build_index(base,a.seed,a.history,out/(stem+'.bin'));payload=[stem+'.bin'];result.update(build=stem,seed=a.seed,history=a.history)
                if digest(out/(stem+'.bin'))!=c['expected_graphs'][stem]['sha256'] or (out/(stem+'.bin')).stat().st_size!=c['expected_graphs'][stem]['bytes']:raise ValueError('Frozen graph bytes differ; stop without repinning')
        elif a.phase=='compile':
            compiler=shutil.which('g++')
            if not compiler:raise FileNotFoundError('g++ required')
            binary=out/'deep1m_counting_runner';cmd=[compiler,'-std=c++17','-O3','-pthread','-I',str(HERE/'include'),str(HERE/'deep1m_counting_runner.cpp'),'-o',str(binary)]
            subprocess.run(cmd,check=True,timeout=120);payload=[binary.name];result['compiler']=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]
        elif a.phase=='replay':
            receipt(a.prepared,'prepare');receipt(a.native_build,'compile');units={}
            for folder in a.graphs:
                r=receipt(folder,'build');key=(r['seed'],r['history'])
                if key in units:raise ValueError('Duplicate graph unit')
                units[key]=(folder,r)
            if set(units)!={(s,h) for s in c['seeds'] for h in c['histories']}:raise ValueError('Require exact eight graph units')
            binary=a.native_build/'deep1m_counting_runner'
            for key,(folder,r) in sorted(units.items()):
                stem=r['build'];path=out/(stem+'.csv')
                subprocess.run([str(binary),str(folder/(stem+'.bin')),str(a.prepared/'queries.fvecs'),str(a.prepared/'truth.ivecs'),','.join(map(str,c['grid'])),stem,str(path)],check=True,timeout=1800)
                validate_csv(path,stem,1500,c['grid']);payload.append(path.name)
            result['prerequisites']={'prepared':digest(a.prepared/'completed.json'),'native_build':digest(a.native_build/'completed.json'),'graphs':[digest(p/'completed.json') for p in a.graphs]}
        elif a.phase=='analyze':
            r=receipt(a.replay,'replay')
            if len(r['outputs'])!=8:raise ValueError('Replay panel incomplete')
            import scipy
            if scipy.__version__!='1.13.1':raise ValueError('SciPy version')
            target=out/'analysis';subprocess.run([sys.executable,str(HERE/'historical_analysis.py'),'--replay',str(a.replay),'--output',str(target)],check=True,timeout=1800)
            payload=[str(p.relative_to(out)) for p in sorted(target.iterdir()) if p.is_file()];result['replay_receipt_sha256']=digest(a.replay/'completed.json')
        else:raise ValueError('Unknown phase')
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>plan['max_output_growth_bytes']:raise ValueError('Output cap')
        masks=[next(s for s in p.read_text().splitlines() if s.startswith('Cpus_allowed_list:')).split(':')[1].strip() for p in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'2'}:raise ValueError('Thread masks')
        resources.write_json(out/'completed.json',dict(result,phase=a.phase,config_sha256=digest(HERE/'config.json'),outputs={n:digest(out/n) for n in payload},thread_masks=masks,status='NEW_EXECUTION_COMPLETED_NOT_HISTORICAL_RECEIPT'))
    except BaseException as e:resources.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_STAGES','error':repr(e)});raise
    finally:signal.alarm(0)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['check','prepare','build','compile','replay','analyze'])
    for k in ('dataset','output','prepared','native-build','replay'):p.add_argument('--'+k,type=Path)
    p.add_argument('--graphs',type=Path,nargs='+');p.add_argument('--seed',type=int,choices=[3011,3203,3413,3617]);p.add_argument('--history',choices=['random','norm_ascending'])
    p.add_argument('--authorize-new-execution',action='store_true');p.add_argument('--authorize-historical-test-member',action='store_true');p.add_argument('--outstanding-growth-bytes',type=int)
    a=p.parse_args();c=config()
    if a.phase=='check':print(json.dumps({'status':'PASS_SOURCE_AND_FROZEN_ROLES','roles':len(role_ids(c)),'original_data_reads':0}));return
    required={'prepare':['dataset'],'build':['dataset','seed','history'],'compile':[],'replay':['prepared','native_build','graphs'],'analyze':['replay']}[a.phase]+['output','outstanding_growth_bytes']
    if any(getattr(a,k) is None for k in required):p.error('Required: '+', '.join(required))
    execute(a,c)
if __name__=='__main__':main()
