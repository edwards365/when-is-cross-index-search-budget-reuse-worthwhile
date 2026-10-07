"""Separated corrected Faiss-100K phases; no import-time dataset or native loading."""
import csv,importlib.metadata,importlib.util,json,os,platform,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def native(sha):
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11):
        raise ValueError('Pinned payload requires Linux x86_64 / Python 3.11')
    if any(k in os.environ for k in ('FAISS_OPT_LEVEL','FAISS_DISABLE_CPU_FEATURES','LD_PRELOAD')):
        raise ValueError('Dispatch/preload override not allowed')
    if any(n=='faiss' or n.startswith('faiss.') for n in sys.modules):raise ValueError('Fresh process required')
    lock=json.loads((HERE/'native_lock.json').read_text());dist=importlib.metadata.distribution('faiss-cpu')
    if dist.version!=lock['version']:raise ValueError('Wrong Faiss version')
    site=Path(dist.locate_file('')).resolve(strict=True)
    for rel,pin in lock['installed_payload'].items():
        p=(site/rel).resolve(strict=True)
        if not p.is_relative_to(site) or sha(p)!=pin:raise ValueError('Faiss payload mismatch: '+rel)
    spec=importlib.util.find_spec('faiss')
    if spec is None or Path(spec.origin).resolve()!=site/'faiss/__init__.py':raise ValueError('Shadowed Faiss')
    import faiss,numpy as np,h5py
    if faiss.__version__!='1.15.0' or np.__version__!='1.26.4' or h5py.__version__!='3.11.0':raise ValueError('Library version mismatch')
    modules=[]
    for name,m in tuple(sys.modules.items()):
        if name.startswith('faiss._swigfaiss'):
            p=Path(m.__file__).resolve();rel=p.relative_to(site).as_posix()
            if rel not in lock['installed_payload'] or sha(p)!=lock['installed_payload'][rel]:raise ValueError('Unexpected loaded module')
            modules.append(rel)
    if len(modules)!=1:raise ValueError('Expected one loaded native module')
    faiss.omp_set_num_threads(1)
    return faiss,np,h5py,{'payload_count':len(lock['installed_payload']),'loaded_native':modules,'historical_dispatch_attested':False}

def ids(c,ds,np):
    alias='sift' if ds=='sift_100k' else 'arxiv'
    with (HERE/(alias+'_old_role_ids.csv')).open(newline='') as f:old={int(r['source_id']) for r in csv.DictReader(f)}
    n=c['datasets'][ds]['source']['train_shape'][0]
    pool=np.asarray([i for i in range(100000,n) if i not in old],dtype=np.int64)
    got=np.random.default_rng(991).permutation(pool)[:750]
    with (HERE/'faiss100k_query_role_ledger.csv').open(newline='') as f:frozen=[int(r['source_id']) for r in csv.DictReader(f) if r['dataset']==ds]
    if got.tolist()!=frozen:raise ValueError('Corrected role mismatch')
    return got

def build(faiss,np,base,seed):
    perm=np.random.default_rng(seed).permutation(len(base)).astype(np.int64)
    core=faiss.IndexHNSWFlat(base.shape[1],16,faiss.METRIC_L2);core.hnsw.efConstruction=100
    idx=faiss.IndexIDMap2(core);idx.add_with_ids(base[perm],perm)
    return idx

def rows(faiss,q,truth,idx,ds,bid,grid):
    core=faiss.downcast_index(idx.index);out=[]
    for ef in grid:
        core.hnsw.efSearch=ef;_,I=idx.search(q,10)
        for qi in range(len(q)):
            answer=list(map(int,I[qi]))
            if len(set(answer))!=10 or min(answer)<0 or max(answer)>=idx.ntotal:raise ValueError('Invalid ANN IDs')
            hit=len(set(answer).intersection(map(int,truth[qi])))
            out.append(dict(dataset=ds,build_id=bid,query_id=qi,ef=ef,hit_count=hit,recall=hit/10,returned_top10='|'.join(map(str,answer))))
    return out

def write_csv(path,rows):
    with path.open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def run(a,c,out,prerequisite,sha):
    import run_transfer as entry
    if a.phase=='faiss-analyze':
        data=[];numbers=set()
        for unit in a.units:
            r=prerequisite(unit,'faiss-replay')
            if r['dataset']!=a.dataset or r['build_number'] in numbers:raise ValueError('Repeated/wrong unit')
            numbers.add(r['build_number'])
            with (unit/'paper_rows.csv').open(newline='') as f:
                for row in csv.DictReader(f):data.append(dict(row,query_id=int(row['query_id']),ef=int(row['ef']),hit_count=int(row['hit_count']),recall=float(row['recall'])))
        if numbers!=set(range(24)):raise ValueError('All 24 registry units required, including repeated graph identities')
        analysis=entry.mod('historical_analysis');result=[dict(analysis.action_summary(data,h,c['faiss_grid']),h=h,ndc_mean='NOT_ESTIMABLE_BATCH_CUMULATIVE',ndc_p95='NOT_ESTIMABLE_BATCH_CUMULATIVE') for h in (8,9,10)]
        (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');write_csv(out/'lobo.csv',[r for h in (8,9,10) for r in analysis.lobo(data,h)])
        return {'dataset':a.dataset,'units':24},['analysis.json','lobo.csv']
    faiss,np,h5py,env=native(sha);record={'dataset':a.dataset,'native':env}
    if a.phase=='faiss-prepare':
        source=c['datasets'][a.dataset]['source']
        if sha(a.source)!=source['sha256']:raise ValueError('Raw HDF5 pin')
        qi=ids(c,a.dataset,np);order=np.argsort(qi)
        with h5py.File(a.source,'r') as f:
            train=f['train']
            if list(train.shape)!=source['train_shape'] or str(train.dtype)!='float32':raise ValueError('Train shape/dtype')
            base=np.asarray(train[:100000],np.float32);q=np.asarray(train[sorted(qi)],np.float32)[np.argsort(order)]
        flat=faiss.IndexFlatL2(base.shape[1]);flat.add(base);_,truth=flat.search(q,10)
        if any(int(qi[j]) in set(truth[j]) for j in range(750)):raise ValueError('Self truth')
        for name,x in [('base',base),('queries',q),('truth',truth),('source_ids',qi)]:np.save(out/(name+'.npy'),x,allow_pickle=False)
        return record,['base.npy','queries.npy','truth.npy','source_ids.npy']
    p=prerequisite(a.prepared,'faiss-prepare')
    if p['dataset']!=a.dataset:raise ValueError('Prepared dataset')
    if a.phase=='faiss-build':
        base=np.load(a.prepared/'base.npy',allow_pickle=False);seed=c['faiss_seeds'][a.build_number]
        idx=build(faiss,np,base,seed);faiss.write_index(idx,str(out/'index.faiss'))
        bid=f'{a.dataset}__100k__clean{a.build_number:02d}__seed{seed}'
        frozen=next(r for r in c['faiss_graphs'] if r['build_id']==bid)
        if sha(out/'index.faiss')!=frozen['index_sha256']:raise ValueError('New graph differs from frozen identity; stop dependent replay')
        record.update(build_number=a.build_number,build_id=bid,seed=seed,prepared_receipt_sha256=sha(a.prepared/'completed.json'))
        return record,['index.faiss']
    g=prerequisite(a.graph,'faiss-build')
    if g['dataset']!=a.dataset or g['prepared_receipt_sha256']!=sha(a.prepared/'completed.json'):raise ValueError('Graph/input pairing')
    idx=faiss.read_index(str(a.graph/'index.faiss'));q=np.load(a.prepared/'queries.npy',allow_pickle=False);truth=np.load(a.prepared/'truth.npy',allow_pickle=False)
    data=rows(faiss,q,truth,idx,a.dataset,g['build_id'],c['faiss_grid']);write_csv(out/'paper_rows.csv',data)
    record.update(build_number=g['build_number'],build_id=g['build_id'],graph_receipt_sha256=sha(a.graph/'completed.json'),ndc='NOT_ESTIMABLE_BATCH_CUMULATIVE')
    return record,['paper_rows.csv']
