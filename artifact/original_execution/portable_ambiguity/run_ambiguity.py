"""New G1 train-only inputs, native unit replay and frozen-source analysis."""
import argparse,csv,hashlib,importlib.util,json,os,platform,shutil,struct,subprocess,sys,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
FIELDS=['dataset','index','history','seed','query_id','query_split','budget','returned_top10_ids','recall_at_10','exact_ndc','graph_hash']
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def load(path,name,pin):
    if sha(path)!=pin:raise ValueError('Source identity: '+path.name)
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def receipt(folder,pin,stage):
    if folder is None or pin is None or (folder/'failure.json').exists() or sha(folder/'completed.json')!=pin:raise ValueError('Parent receipt identity')
    r=json.loads((folder/'completed.json').read_text())
    if r['stage']!=stage or r['config_sha256']!=sha(HERE/'config.json') or r.get('wrapper_sha256')!=sha(Path(__file__)):raise ValueError('Parent stage/config/wrapper')
    for rel,p in r['outputs'].items():
        f=(folder/rel).resolve()
        if not f.is_relative_to(folder.resolve()) or sha(f)!=p:raise ValueError('Parent payload')
    return r
def matrix(path,a,dtype,np,small=False):
    a=np.asarray(a,dtype=dtype,order='C')
    with path.open('xb') as f:f.write(struct.pack('<II' if small else '<QQ',*a.shape));a.tofile(f)
def permutation(order,n,np):
    if order.shape!=(n,) or order.dtype.kind not in 'iu' or not np.array_equal(np.sort(order),np.arange(n)):raise ValueError('Complete permutation required')
    return order
def vamana_spec(work,normalized,grid):
    return {'search_directories':[str(work)],'output_directory':None,'jobs':[{'type':'integration-test','content':{
        'build':{'alpha':1.2,'l_build':50,'max_degree':32,'pruned_degree':32},
        'data':{'data':'base.fbin','data_type':'f32','groundtruth':'truth.bin','metric':'cosine' if normalized else 'l2','queries':'queries.fbin','preprocess':[]},
        'layer':{'FullPrecision':{'data_type':'f32'}},'search':{'knn':[{'beam_width':None,'knn':10,'search_l':b} for b in grid]}}}]}
def prepare(a,c,out):
    import numpy as np,h5py
    membership=json.loads((HERE/'membership.json').read_text());record=next(r for r in membership['datasets'] if r['dataset']==a.dataset)
    if sha(a.source)!=record['source_sha256']:raise ValueError('Frozen raw HDF5 identity')
    ids=np.asarray(record['design_source_ids']+record['confirm_source_ids'],dtype=np.int64)
    if len(ids)!=1000 or len(set(map(int,ids)))!=1000 or int(ids.min())<100000 or hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest()!=record['source_ids_le_i64_sha256']:raise ValueError('Frozen train-side membership')
    order=np.argsort(ids)
    with h5py.File(a.source,'r') as h:q=np.asarray(h['train'][ids[order]],dtype=np.float32)[np.argsort(order)];base=np.asarray(h['train'][:100000],dtype=np.float32)
    norm='angular' in record['source_path'] or 'normalized' in record['source_path']
    if norm:q/=np.linalg.norm(q,axis=1,keepdims=True);base/=np.linalg.norm(base,axis=1,keepdims=True)
    if not np.isfinite(base).all() or not np.isfinite(q).all():raise ValueError('Nonfinite vectors; no normalization substitute')
    gt=load(HERE/'ground_truth.py','g1_ground_truth',c['pins']['ground_truth.py']);truth,dist=gt.exact_top_k(base,q,10,metric='l2')
    ref=next(r for r in json.loads((HERE/'truth.json').read_text())['datasets'] if r['dataset']==a.dataset)
    for name,v in [('queries',q),('truth',truth.astype(np.uint32)),('truth_distances',dist.astype(np.float64)),('source_ids',ids)]:
        p=out/(name+'.npy');np.save(p,v,allow_pickle=False)
        if sha(p)!=ref[name+'_sha256']:raise ValueError('Frozen query/truth serialization mismatch')
    np.save(out/'base.npy',base,allow_pickle=False)
    for name,v in [('random',np.random.default_rng(20260915).permutation(100000)),('natural_source_order',np.arange(100000)),
                   ('cluster_block_order',np.load(HERE/(a.dataset+'_cluster_block_order.npy'),allow_pickle=False))]:
        np.save(out/(name+'.npy'),permutation(v,100000,np),allow_pickle=False)
    return {'dataset':a.dataset,'normalized':norm,'raw_source_sha256':record['source_sha256'],'original_query_truth_bits_matched':True}
def safe_extract(archive,out):
    with tarfile.open(archive) as tf:
        roots={m.name.split('/')[0] for m in tf.getmembers() if m.name}
        if len(roots)!=1:raise ValueError('Single source archive root required')
        root=next(iter(roots));destination=out/'source';destination.mkdir()
        for member in tf.getmembers():
            rel=Path(*Path(member.name).parts[1:])
            if str(rel)=='.':continue
            path=(destination/rel).resolve()
            if not path.is_relative_to(destination.resolve()) or member.issym() or member.islnk() or member.isdev():raise ValueError('Unsafe source archive')
            if member.isdir():path.mkdir(parents=True,exist_ok=True)
            elif member.isfile():
                path.parent.mkdir(parents=True,exist_ok=True)
                with tf.extractfile(member) as inp,path.open('xb') as f:shutil.copyfileobj(inp,f)
            else:raise ValueError('Unsupported archive member')
    return destination
def compile_vamana(a,c,out):
    spec=c['native_inputs'].get('diskann')
    if not spec:raise ValueError('Exact DiskANN archive/patch map not yet delivered')
    if sha(a.source_archive)!=spec['archive_sha256']:raise ValueError('DiskANN source archive identity')
    source=safe_extract(a.source_archive,out)
    provenance=json.loads((HERE/'diskann_provenance.json').read_text())
    if sha(source/'Cargo.lock')!=provenance['diskann']['cargo_lock_sha256']:raise ValueError('Wrong DiskANN lock')
    patch_receipts=[]
    for filename,relative in spec['patch_targets'].items():
        dest=(source/relative).resolve()
        if not dest.is_relative_to(source.resolve()) or not dest.is_file():raise ValueError('Patch target')
        before=sha(dest)
        dest.write_bytes((HERE/filename).read_bytes())
        if sha(dest)!=c['pins'][filename]:raise ValueError('Installed patch identity')
        patch_receipts.append({'target':relative,'original_sha256':before,'installed_sha256':sha(dest)})
    version=subprocess.check_output(['rustc','--version'],text=True).strip()
    if version!='rustc '+provenance['toolchain']['rustc']:raise ValueError('Frozen Rust toolchain required; no automatic upgrade')
    cargo_version=subprocess.check_output(['cargo','--version'],text=True).strip()
    if cargo_version!='cargo '+provenance['toolchain']['cargo']:raise ValueError('Frozen Cargo toolchain required')
    env=os.environ.copy();env['CARGO_HOME']=str(out/'cargo-home');env['CARGO_TARGET_DIR']=str(out/'target')
    cmd=['cargo','build','--locked','--release','-p','diskann-inmem','--features','integration-test','--bin','integration-test']
    with (out/'build.stdout').open('wb') as so,(out/'build.stderr').open('wb') as se:
        result=subprocess.run(cmd,cwd=source,env=env,stdout=so,stderr=se,timeout=c['resource_plan']['wall_seconds'])
    if result.returncode:raise ValueError('Native build failed: '+str(result.returncode))
    if sha(source/'Cargo.lock')!=provenance['diskann']['cargo_lock_sha256']:raise ValueError('Cargo.lock changed during build')
    shutil.copy2(out/'target/release/integration-test',out/'integration-test')
    return {'implementation':'vamana','source_commit':provenance['diskann']['source_commit'],'actual_exit_code':result.returncode,
            'historical_patched_binary_identity_attested':False,'rustc':version,'cargo':cargo_version,
            'cargo_lock_sha256':sha(source/'Cargo.lock'),'patches':patch_receipts}
def faiss_environment(c):
    spec=c['native_inputs'].get('faiss')
    if not spec:raise ValueError('Frozen Faiss1.15.0 runtime not yet delivered; no1.8 fallback')
    import importlib.metadata
    dist=importlib.metadata.distribution('faiss-cpu')
    if dist.version!='1.15.0':raise ValueError('Faiss1.15.0 required')
    site=Path(dist.locate_file(''))
    for rel,pin in spec['payload_sha256'].items():
        p=(site/rel).resolve()
        if not p.is_relative_to(site.resolve()) or sha(p)!=pin:raise ValueError('Faiss payload identity')
    import faiss
    if faiss.__version__!='1.15.0' or Path(faiss.__file__).resolve()!= (site/'faiss/__init__.py').resolve():raise ValueError('Faiss import identity')
    faiss.omp_set_num_threads(1)
    loaded=[{'file':Path(m.__file__).name,'sha256':sha(Path(m.__file__))} for n,m in sys.modules.items() if n.startswith('faiss._swigfaiss')]
    if len(loaded)!=1 or loaded[0]['sha256'] not in spec['payload_sha256'].values():raise ValueError('Loaded native identity')
    return faiss,loaded
def hnsw_binary(a,c):
    # Reuse the separately delivered new compile, never an arbitrary binary.
    if sha(a.transfer_adapter/'hnsw_gate_a_benchmark.cpp')!=c['hnsw_benchmark_source_sha256']:raise ValueError('Benchmark source identity')
    conf=json.loads((a.transfer_adapter/'config.json').read_text())
    for name,pin in conf['source_pins'].items():
        if sha(a.transfer_adapter/name)!=pin:raise ValueError('Benchmark include identity')
    done=a.native_build/'completed.json'
    if sha(done)!=a.native_build_sha256 or (a.native_build/'failure.json').exists():raise ValueError('Compile receipt')
    r=json.loads(done.read_text())
    if r['phase']!='compile' or r['config_sha256']!=sha(a.transfer_adapter/'config.json'):raise ValueError('Compile phase/config')
    binary=a.native_build/'hnsw_gate_a_benchmark'
    if sha(binary)!=r['outputs'][binary.name]:raise ValueError('New binary identity')
    return binary
def native_unit(a,c,out):
    import numpy as np
    prep=receipt(a.prepared,a.prepared_sha256,'prepare')
    if prep['dataset']!=a.dataset:raise ValueError('Prepared dataset')
    b=np.load(a.prepared/'base.npy',allow_pickle=False);q=np.load(a.prepared/'queries.npy',allow_pickle=False);truth=np.load(a.prepared/'truth.npy',allow_pickle=False)
    order=permutation(np.load(a.prepared/(a.history+'.npy'),allow_pickle=False),100000,np);records=[];norm=prep['normalized'];identity={}
    if a.implementation=='faiss':
        faiss,loaded=faiss_environment(c);idx=faiss.IndexHNSWFlat(b.shape[1],16,faiss.METRIC_INNER_PRODUCT if norm else faiss.METRIC_L2)
        idx.hnsw.efConstruction=100;idx.hnsw.rng=faiss.RandomGenerator(a.seed);idx.add(b[order]);faiss.write_index(idx,str(out/'index.faiss'));gh=sha(out/'index.faiss')
        for budget in c['grid']:
            idx.hnsw.efSearch=budget
            for qi,x in enumerate(q):
                faiss.cvar.hnsw_stats.reset();_,found=idx.search(x.reshape(1,-1),10)
                records.append((budget,qi,order[found[0]],int(faiss.cvar.hnsw_stats.ndis)))
        identity={'loaded_native':loaded}
    elif a.implementation=='hnswlib':
        binary=hnsw_binary(a,c);matrix(out/'base.bin',b,np.float32,np);matrix(out/'queries.bin',q,np.float32,np);matrix(out/'truth.bin',truth,np.uint32,np)
        (out/'native').mkdir()
        with (out/'order.bin').open('xb') as f:f.write(struct.pack('<Q',len(order)));np.asarray(order,dtype='<u4').tofile(f)
        cmd=[str(binary),str(out/'base.bin'),str(out/'order.bin'),str(out/'queries.bin'),str(out/'truth.bin'),'-','ip' if norm else 'l2','16','100',str(a.seed),a.dataset,'original','-',','.join(map(str,c['grid'])),'0','1',c['pins']['preregistration.json'],'new-g1-unit',a.dataset+f'__seed{a.seed}__'+a.history,str(out/'native')]
        with (out/'native.stdout').open('wb') as so,(out/'native.stderr').open('wb') as se:run=subprocess.run(cmd,stdout=so,stderr=se,timeout=c['resource_plan']['wall_seconds'])
        if run.returncode:raise ValueError('HNSW native failure: '+str(run.returncode))
        gh=sha(out/'native/edges.csv')
        with (out/'native/queries.csv').open(newline='') as f:
            for row in csv.DictReader(f):records.append((int(row['ef_search']),int(row['query_id']),list(map(int,row['returned_top10'].split(';'))),int(row['ndc'])))
        identity={'actual_exit_code':run.returncode,'new_binary_sha256':sha(binary)}
    else:
        build=receipt(a.native_build,a.native_build_sha256,'compile-vamana');binary=a.native_build/'integration-test'
        if build['implementation']!='vamana':raise ValueError('G1Vamana build required')
        inverse=np.empty(len(order),dtype=np.uint32);inverse[order]=np.arange(len(order),dtype=np.uint32)
        matrix(out/'base.fbin',b[order],np.float32,np,True);matrix(out/'queries.fbin',q,np.float32,np,True);matrix(out/'truth.bin',inverse[truth],np.uint32,np,True)
        spec=vamana_spec(out,norm,c['grid']);(out/'input.json').write_text(json.dumps(spec),encoding='utf-8')
        with (out/'native.stdout').open('wb') as so,(out/'native.stderr').open('wb') as se:run=subprocess.run([str(binary),'run','--input-file',str(out/'input.json'),'--output-file',str(out/'native.json')],stdout=so,stderr=se,timeout=c['resource_plan']['wall_seconds'])
        if run.returncode:raise ValueError('DiskANN native failure: '+str(run.returncode))
        result=json.loads((out/'native.json').read_text())[0]['results'];gh=hashlib.sha256(json.dumps(result['graph'],separators=(',',':')).encode()).hexdigest()
        if len(result['knn'])!=len(c['grid']):raise ValueError('DiskANN grid incomplete')
        for budget,knn in zip(c['grid'],result['knn']):
            if len(knn['per_query'])!=1000:raise ValueError('DiskANN query count')
            for qi,row in enumerate(knn['per_query']):records.append((budget,qi,order[np.asarray(row['ids'][:10],dtype=np.int64)],int(row['misc']['cmps'])))
        identity={'actual_exit_code':run.returncode,'new_binary_sha256':sha(binary),'seed_is_repetition_label_not_rng_parameter':True}
    write_responses(out/'responses.csv',records,truth,gh,a,c,np)
    # Historical graph hashes are observations, not a reason to silently repin a
    # new compiler's serialized graph. When available they are a strict gate.
    expected=c['historical_runs'].get(a.implementation,[])
    match=[r for r in expected if r['dataset']==a.dataset and r.get('seed',r.get('graph_seed'))==a.seed and r.get('history',r.get('insertion_order'))==a.history]
    if len(match)!=1:raise ValueError('Exactly one historical graph identity required')
    if gh!=match[0]['graph_hash']:raise ValueError('Historical graph hash differs; preserve failure and stop')
    return {'implementation':a.implementation,'dataset':a.dataset,'seed':a.seed,'history':a.history,'graph_hash':gh,
            'rows':len(records),'prepared_receipt_sha256':a.prepared_sha256,'native':identity,'historical_graph_identity_checked':bool(match)}
def write_responses(path,records,truth,gh,a,c,np):
    seen=set()
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(FIELDS)
        for budget,qi,ids,ndc in records:
            key=(budget,qi);ids=list(map(int,ids))
            if key in seen or budget not in c['grid'] or not 0<=qi<1000 or len(ids)!=10 or len(set(ids))!=10 or min(ids)<0 or max(ids)>=100000 or ndc<=0:raise ValueError('Native response identity/range')
            seen.add(key);recall=len(set(ids)&set(map(int,truth[qi])))/10
            w.writerow([a.dataset,a.implementation,a.history,a.seed,qi,'design' if qi<250 else 'confirm',budget,';'.join(map(str,ids)),recall,ndc,gh])
    if len(seen)!=12000:raise ValueError('Full12budget×1000query response required')
def analyze(a,c,out):
    import gzip
    rows=json.loads(a.unit_manifest.read_text());seen=set();links=[];base=out/'input-view';base.mkdir()
    if len(rows)!=81:raise ValueError('All81registered unit receipts required')
    for row in rows:
        folder=Path(row['directory']);r=receipt(folder,row['completed_sha256'],'unit');key=(r['implementation'],r['dataset'],r['seed'],r['history'])
        if key in seen or key[0] not in ('hnswlib','faiss','vamana') or key[1] not in c['datasets'] or key[2] not in c['seeds'] or key[3] not in c['histories']:raise ValueError('Unexpected/duplicate unit')
        seen.add(key);dest=base/'main'/key[0];dest.mkdir(parents=True,exist_ok=True)
        with (folder/'responses.csv').open('rb') as src,gzip.open(dest/(key[1]+f'__seed{key[2]}__'+key[3]+'.csv.gz'),'wb') as target:shutil.copyfileobj(src,target)
        links.append(row['completed_sha256'])
    derived=out/'derived';derived.mkdir();module=load(HERE/'historical_analysis.py','g1_explicit_analysis',c['pins']['historical_analysis.py']);module.run(base,derived)
    return {'unit_receipts':links,'analysis_is_original_G1_legacy_not_new_summary_cost_diagnostic':True,'bootstrap_recomputed_for_new_inputs':True}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['prepare','compile-vamana','unit','analyze'])
    for name in ('output','input-adapter'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('source','source-archive','prepared','native-build','transfer-adapter','unit-manifest'):p.add_argument('--'+name,type=Path)
    for name in ('prepared','native-build'):p.add_argument('--'+name+'-sha256')
    p.add_argument('--implementation',choices=['hnswlib','faiss','vamana']);p.add_argument('--dataset',choices=['sift_100k','glove100_100k','arxiv_nomic_100k']);p.add_argument('--seed',type=int,choices=[43,59,71]);p.add_argument('--history',choices=['random','natural_source_order','cluster_block_order'])
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-stage',action='store_true');a=p.parse_args()
    if not a.authorize_new_stage:p.error('Explicit new-stage authorization required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 without -O required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    c=json.loads((HERE/'config.json').read_text())
    for rel,pin in c['pins'].items():
        if sha(HERE/rel)!=pin:raise ValueError('Frozen package file: '+rel)
    adapter=load(a.input_adapter/'prepare_inputs.py','g1_resource',c['input_adapter_sha256']);out,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':c['resource_plan']},a.output,{},a.outstanding_growth_bytes)
    import resource,signal
    plan=c['resource_plan']
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);adapter.write_json(out/'start.json',{'stage':a.stage,'resources':snapshot,'config_sha256':sha(HERE/'config.json'),'source_sha256':sha(Path(__file__))})
    def timeout(sig,frame):raise TimeoutError('G1 stage wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        import numpy,scipy,h5py
        if (numpy.__version__,scipy.__version__,h5py.__version__)!=('1.26.4','1.13.1','3.11.0'):raise ValueError('Pinned Python dependencies')
        result=prepare(a,c,out) if a.stage=='prepare' else compile_vamana(a,c,out) if a.stage=='compile-vamana' else native_unit(a,c,out) if a.stage=='unit' else analyze(a,c,out)
        if sum(f.stat().st_size for f in out.rglob('*') if f.is_file())>plan['max_output_growth_bytes']:raise ValueError('Declared output growth exceeded; retain failure')
        result.update(stage=a.stage,status='NEW_G1_STAGE_COMPLETE',config_sha256=sha(HERE/'config.json'),wrapper_sha256=sha(Path(__file__)),
            outputs={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and f.name!='start.json'})
        adapter.write_json(out/'completed.json',result)
    except BaseException as e:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
