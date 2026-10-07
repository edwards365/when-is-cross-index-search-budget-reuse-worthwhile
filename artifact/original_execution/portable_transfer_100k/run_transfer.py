"""E4 HNSW: explicit preparation, native compilation, single unit and paper-row export."""
import argparse,csv,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def mod(name):
    s=importlib.util.spec_from_file_location('transfer_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def config():
    c=json.loads((HERE/'config.json').read_text())
    for rel,pin in (c['source_pins']|c['small_input_pins']).items():
        if sha(HERE/rel)!=pin:raise ValueError('Source pin mismatch: '+rel)
    return c
def role_check(c):
    import numpy as np
    for j,ds in enumerate(('sift_100k','arxiv_nomic_100k')):
        ids=np.sort(np.random.default_rng(991+1009*j).choice(np.arange(200000,300000,dtype=np.int64),1000,replace=False))
        if ids.tolist()!=c['datasets'][ds]['confirmatory_ids']:raise ValueError('Frozen confirmatory IDs differ')
def prerequisite(p,phase):
    if (p/'failure.json').exists():raise ValueError('Failed prerequisite')
    r=json.loads((p/'completed.json').read_text())
    if r['phase']!=phase or r['config_sha256']!=sha(HERE/'config.json'):raise ValueError('Prerequisite phase/config')
    for rel,pin in r['outputs'].items():
        if sha(p/rel)!=pin:raise ValueError('Prerequisite file mismatch')
    return r
def native_command(binary,prepared,dataset,seed,history,out,grid,warmup=100,rounds=5):
    return [str(binary),str(prepared/'base.f32bin'),str(prepared/(history+'.orderbin')),str(prepared/'confirmatory.f32bin'),str(prepared/'truth.u32bin'),'-','ip' if dataset=='arxiv_nomic_100k' else 'l2','16','100',str(seed),dataset,'original','-',','.join(map(str,grid)),str(warmup),str(rounds),'9d69be57fb67d566637c19b2c45bce1288d61f3f','new-delivery-cpu2',dataset+f'__seed{seed}__'+history,str(out)]
def validate_rows(p,query_count,grid,rounds):
    seen=set()
    with p.open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            k=(int(r['query_id']),int(r['ef_search']),int(r['latency_round']));ids=list(map(int,r['returned_top10'].split(';')))
            if k in seen or not 0<=k[0]<query_count or k[1] not in grid or not 0<=k[2]<rounds:raise ValueError('Rows/grid/round identity')
            if len(ids)!=10 or len(set(ids))!=10 or min(ids)<0 or int(r['ndc'])<=0 or not 0<=float(r['recall_at_10'])<=1:raise ValueError('Invalid native payload')
            seen.add(k)
    if len(seen)!=query_count*len(grid)*rounds:raise ValueError('Incomplete native output')
def paper_rows(source,destination,build):
    """Exact original repair load_h filter: round0 and local query_id<750."""
    with source.open(newline='',encoding='utf-8') as f,destination.open('x',newline='',encoding='utf-8') as out:
        w=csv.DictWriter(out,fieldnames=['build_id','query_id','ef','hit_count','recall'],lineterminator='\n');w.writeheader();n=0
        for r in csv.DictReader(f):
            if int(r.get('latency_round',0))==0 and int(r['query_id'])<750:
                w.writerow({'build_id':build,'query_id':int(r['query_id']),'ef':int(r['ef_search']),'hit_count':int(round(float(r['recall_at_10'])*10)),'recall':float(r['recall_at_10'])});n+=1
    return n
def execute(a,c):
    if not a.authorize_new_execution:raise ValueError('Explicit opt-in required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    resources=mod('resources');sources={k:v for k,v in vars(a).items() if k!='output' and isinstance(v,Path)}
    out,snapshot=resources.preflight({'python_minor':[3,11],'resource_plan':c['resource_plan']},a.output,sources,a.outstanding_growth_bytes)
    import resource,signal
    plan=c['resource_plan']
    for kind,limit in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([limit]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);resources.write_json(out/'start.json',{'phase':a.phase,'config_sha256':sha(HERE/'config.json'),'adapter_sha256':sha(Path(__file__)),'resources':snapshot})
    def timeout(sig,frame):raise TimeoutError('Transfer wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds']);payload=[];record={}
    try:
        if a.phase.startswith('faiss-'):
            record,payload=mod('faiss_phases').run(a,c,out,prerequisite,sha)
        elif a.phase=='analyze':
            analysis=mod('historical_analysis');data=[];seen=set()
            for unit in a.units:
                r=prerequisite(unit,'unit')
                if r['dataset']!=a.dataset:raise ValueError('Dataset mismatch')
                key=(r['seed'],r['history'])
                if key in seen:raise ValueError('Repeated build unit')
                seen.add(key)
                with (unit/'paper_rows.csv').open(newline='') as f:
                    for row in csv.DictReader(f):data.append(dict(row,query_id=int(row['query_id']),ef=int(row['ef']),hit_count=int(row['hit_count']),recall=float(row['recall'])))
            if seen!={(s,h) for s in c['seeds'] for h in c['histories']}:raise ValueError('Full 24-build panel required')
            resources.write_json(out/'analysis.json',analysis.action_summary(data,10,c['grid']));payload=['analysis.json'];record={'dataset':a.dataset,'units':len(seen)}
        elif a.phase=='prepare':
            row=c['datasets'][a.dataset];core=mod('historical_core');import numpy as np,h5py
            if np.__version__!='1.26.4' or h5py.__version__!='3.11.0':raise ValueError('Library versions')
            if sha(a.source)!=row['source']['sha256'] or sha(a.lid_order)!=row['lid_order_sha256']:raise ValueError('Frozen raw/order identity')
            ids=np.asarray(row['confirmatory_ids'],dtype=np.int64);lid=np.load(a.lid_order,allow_pickle=False)
            if lid.shape!=(100000,) or not np.array_equal(np.sort(lid),np.arange(100000)):raise ValueError('LID permutation')
            with h5py.File(a.source,'r') as f:
                train=f['train']
                if train.shape[1]!=row['source']['train_shape'][1] or str(train.dtype)!='float32':raise ValueError('Train shape/dtype')
                base=np.asarray(train[:100000],dtype=np.float32);q=np.asarray(train[ids],dtype=np.float32)
            if row['normalized']:
                base/=np.maximum(np.linalg.norm(base,axis=1,keepdims=True),1e-30);q/=np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-30)
            truth=core.exact(base,q);core.matrix(out/'base.f32bin',base);core.matrix(out/'confirmatory.f32bin',q);core.truthbin(out/'truth.u32bin',truth)
            for history,order in {'random':np.random.default_rng(20260915).permutation(100000),'lid_ascending':lid,'lid_descending':lid[::-1]}.items():core.orderbin(out/(history+'.orderbin'),order)
            payload=[p.name for p in out.iterdir() if p.suffix in ('.f32bin','.u32bin','.orderbin')];record['dataset']=a.dataset
        elif a.phase=='compile':
            compiler=shutil.which('g++')
            if not compiler:raise FileNotFoundError('g++ required')
            binary=out/'hnsw_gate_a_benchmark';subprocess.run([compiler]+c['new_compile_flags']+['-I',str(HERE/'include'),str(HERE/'hnsw_gate_a_benchmark.cpp'),'-o',str(binary)],check=True,timeout=180)
            payload=[binary.name];record['compiler']=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]
        elif a.phase=='unit':
            p=prerequisite(a.prepared,'prepare');prerequisite(a.native_build,'compile')
            if p['dataset']!=a.dataset:raise ValueError('Prepared dataset mismatch')
            target=out/'native';subprocess.run(native_command(a.native_build/'hnsw_gate_a_benchmark',a.prepared,a.dataset,a.seed,a.history,target,c['grid']),check=True,timeout=plan['wall_seconds'])
            validate_rows(target/'queries.csv',1000,c['grid'],5);stem=a.dataset+f'__seed{a.seed}__'+a.history
            if paper_rows(target/'queries.csv',out/'paper_rows.csv',stem)!=4500:raise ValueError('Paper row filter incomplete')
            payload=[str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p.name!='start.json'];record.update(dataset=a.dataset,seed=a.seed,history=a.history,prepared_receipt_sha256=sha(a.prepared/'completed.json'),native_receipt_sha256=sha(a.native_build/'completed.json'))
        else:raise ValueError('Unknown phase')
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>plan['max_output_growth_bytes']:raise ValueError('Output cap')
        resources.write_json(out/'completed.json',dict(record,status='NEW_EXECUTION_NOT_HISTORICAL_REPRODUCTION_ATTESTATION',phase=a.phase,config_sha256=sha(HERE/'config.json'),outputs={n:sha(out/n) for n in payload}))
    except BaseException as e:resources.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_STAGES','error':repr(e)});raise
    finally:signal.alarm(0)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['check','prepare','compile','unit','analyze','faiss-prepare','faiss-build','faiss-replay','faiss-analyze'])
    for k in ('source','lid-order','prepared','native-build','graph','output'):p.add_argument('--'+k,type=Path)
    p.add_argument('--units',type=Path,nargs='+');p.add_argument('--build-number',type=int,choices=range(24))
    p.add_argument('--dataset',choices=['sift_100k','arxiv_nomic_100k']);p.add_argument('--seed',type=int,choices=[83,97,109,127,149,163,181,197]);p.add_argument('--history',choices=['random','lid_ascending','lid_descending'])
    p.add_argument('--authorize-new-execution',action='store_true');p.add_argument('--outstanding-growth-bytes',type=int);a=p.parse_args();c=config()
    if a.phase=='check':role_check(c);print(json.dumps({'status':'SOURCE_ROLE_CHECK_PASS','query_vectors_read':0,'faiss':c['faiss_status']}));return
    required={'prepare':['dataset','source','lid_order'],'compile':[],'unit':['dataset','seed','history','prepared','native_build'],'analyze':['dataset','units'],'faiss-prepare':['dataset','source'],'faiss-build':['dataset','build_number','prepared'],'faiss-replay':['dataset','prepared','graph'],'faiss-analyze':['dataset','units']}[a.phase]+['output','outstanding_growth_bytes']
    if any(getattr(a,k) is None for k in required):p.error('Required: '+', '.join(required))
    execute(a,c)
if __name__=='__main__':main()
