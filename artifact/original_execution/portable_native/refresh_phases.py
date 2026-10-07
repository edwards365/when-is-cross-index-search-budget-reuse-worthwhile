"""Recall95 fixed-5%-refresh family, preserving frozen membership and response roles."""
import csv,hashlib,importlib.metadata,importlib.util,json,os,shutil,sys
from pathlib import Path
import numpy as np
import run_native as entry
import darth_phases
HERE=Path(__file__).resolve().parent
ROLES={'selection':('learn.1M','learn.groundtruth.1M.k1000','training',500),'certification':('validation.10K','validation.groundtruth.10K.k1000','validation',500),'cold_evaluation':('query.10K','query.groundtruth.10K.k1000','testing',1000)}

def native():
    lock=json.loads((HERE/'refresh_native_lock.json').read_text());dist=importlib.metadata.distribution('faiss-cpu');site=Path(dist.locate_file('')).resolve()
    if dist.version!=lock['distribution_version'] or np.__version__!='1.26.4':raise ValueError('Refresh native versions')
    for rel,pin in lock['installed_payload'].items():
        if entry.sha(site/rel)!=pin:raise ValueError('Refresh package payload')
    if any(n=='faiss' or n.startswith('faiss.') for n in sys.modules):raise ValueError('Faiss must not be preloaded')
    if any(k in os.environ for k in ('FAISS_OPT_LEVEL','FAISS_DISABLE_CPU_FEATURES','LD_PRELOAD')):raise ValueError('No dispatch/preload override')
    spec=importlib.util.find_spec('faiss')
    if not spec or Path(spec.origin).resolve()!=site/'faiss/__init__.py':raise ValueError('Shadowed Faiss')
    import faiss
    faiss.omp_set_num_threads(1)
    return faiss

def membership(old,reserve,seed=1491):
    deleted=np.sort(np.random.RandomState(seed).choice(len(old),5000,replace=False));keep=np.ones(len(old),bool);keep[deleted]=False
    return np.ascontiguousarray(np.vstack([old[keep],reserve[:5000]]),np.float32),deleted.astype('<i4')

def read_vec(path):
    x=np.fromfile(path,dtype='<i4');d=int(x[0]);x=x.reshape(-1,d+1)
    if not np.all(x[:,0]==d):raise ValueError('Vector dimensions')
    return np.ascontiguousarray(x[:,1:].view('<f4'))

def run(a,c,out):
    cfg=c['refresh'];core=entry.module('input_core')
    if a.phase=='refresh-prepare':
        import h5py
        ds=a.refresh_dataset;r=cfg['datasets'][ds]
        if entry.sha(a.hdf5)!=r['hdf5_sha256']:raise ValueError('Frozen HDF5 identity')
        faiss=native()
        with h5py.File(a.hdf5,'r') as f:
            old=np.ascontiguousarray(f['train'][:100000],np.float32);lo,hi=r['reserve'];reserve=np.ascontiguousarray(f['train'][lo:hi],np.float32)
            queries={role:np.ascontiguousarray(f['train'][lo:hi],np.float32) for role,(lo,hi) in r['query_ranges'].items()}
        refreshed,deleted=membership(old,reserve)
        if hashlib.sha256(deleted.tobytes()).hexdigest()!=r['deleted_ids_sha256']:raise ValueError('Frozen deleted membership')
        occupied={x.tobytes() for x in np.vstack([old,reserve])};seen=set()
        for q in queries.values():
            keys={x.tobytes() for x in q}
            if keys&occupied or keys&seen:raise ValueError('Role/base content overlap')
            seen|=keys
        for snap,base in [('old',old),('target_refresh05',refreshed)]:
            common=out/snap/'common';common.mkdir(parents=True);truths={};index=faiss.IndexFlatL2(base.shape[1]);index.add(base)
            for role,(stem,gt,qt,n) in ROLES.items():
                scores,ids=index.search(queries[role],100);truths[role]=ids
                core.write_vecs(common/(stem+'.fvecs'),[queries[role]],base.shape[1],'float');core.write_vecs(common/(stem+'.groundtruth.fvecs'),[scores],100,'float')
            for rel,pin in r['snapshots'][snap]['common_files'].items():
                if entry.sha(common/rel)!=pin:raise ValueError('Frozen common query/truth: '+rel)
            for b in r['snapshots'][snap]['builds']:
                seed=b['seed'];dest=out/snap/('seed_'+str(seed))/'SIFT100M';dest.mkdir(parents=True);perm=np.random.RandomState(seed).permutation(100000).astype('<i4');inverse=np.empty_like(perm);inverse[perm]=np.arange(100000)
                if hashlib.sha256(perm.tobytes()).hexdigest()!=b['permutation_sha256']:raise ValueError('Frozen permutation')
                core.write_vecs(dest/'base.100M.fvecs',[base[perm]],base.shape[1],'float')
                if entry.sha(dest/'base.100M.fvecs')!=b['source_base_sha256']:raise ValueError('Frozen permuted base bits')
                for role,(stem,gt,qt,n) in ROLES.items():
                    shutil.copyfile(common/(stem+'.fvecs'),dest/(stem+'.fvecs'));shutil.copyfile(common/(stem+'.groundtruth.fvecs'),dest/(gt+'.fvecs'))
                    original=dest/(stem+'.groundtruth.ivecs');core.write_vecs(original,[inverse[truths[role]]],100,'int')
                    if entry.sha(original)!=b['files'][original.name]:raise ValueError('Frozen mapped truth')
                    shutil.copyfile(original,dest/(gt+'.ivecs'))
        return {'dataset':ds,'metric':'squared_l2','membership_seed':1491,'all_frozen_input_hashes':'PASS','historical_faiss_dispatch_attested':False}
    if a.phase=='refresh-build':
        prep=entry.check_prior(a.prepared,'refresh-prepare')
        if a.seed not in cfg['seeds']:raise ValueError('Unregistered seed')
        faiss=native();base=read_vec(a.prepared/a.snapshot/('seed_'+str(a.seed))/'SIFT100M/base.100M.fvecs');index=faiss.IndexHNSWFlat(base.shape[1],16);index.hnsw.efConstruction=100;index.add(base);faiss.write_index(index,str(out/'index.faiss'))
        return {'dataset':prep['dataset'],'snapshot':a.snapshot,'seed':a.seed,'prepared_receipt_sha256':entry.sha(a.prepared/'completed.json'),'metric':'squared_l2','graph_identity':'NEW_BUILD; historical bitwise identity not asserted'}
    if a.phase=='refresh-replay':
        prep=entry.check_prior(a.prepared,'refresh-prepare');graph=entry.check_prior(a.graph,'refresh-build');build=entry.check_prior(a.native_build,'darth-build')
        if build['flavor']!='legacy-l2' or graph['prepared_receipt_sha256']!=entry.sha(a.prepared/'completed.json') or prep['dataset']!=graph['dataset']:raise ValueError('Refresh pairing')
        lib=Path(build['lightgbm_library'])
        if entry.sha(lib)!=build['lightgbm_library_sha256']:raise ValueError('C++ library identity')
        env=dict(os.environ,LD_LIBRARY_PATH=str(a.native_build/'build/faiss')+os.pathsep+str(lib.parent));prefix=a.prepared/graph['snapshot']/('seed_'+str(graph['seed']))
        for role,(stem,gt,qt,n) in ROLES.items():
            dest=out/role;dest.mkdir()
            for ef in cfg['grid']:
                output=dest/('ef_'+str(ef)+'.csv');args=[a.native_build/'build/hnsw-test/hnsw_test','--dataset','SIFT100M','--query-num',n,'--k',10,'--output',output,'--M',16,'--efConstruction',100,'--efSearch',ef,'--index-filepath',a.graph/'index.faiss','--mode','no-early-stop','--query-type',qt,'--dataset-dir-prefix',str(prefix)+'/']
                darth_phases.command(args,dest,'ef_'+str(ef),env)
                with output.open(newline='') as f:rows=list(csv.reader(f))
                if len(rows)!=n+1 or any(len(x)<27 for x in rows[1:]):raise ValueError('Native response shape')
                if [int(x[0]) for x in rows[1:]]!=list(range(n)):raise ValueError('Native query order')
        return {k:graph[k] for k in ('dataset','snapshot','seed')}|{'native_build_receipt_sha256':entry.sha(a.native_build/'completed.json'),'graph_receipt_sha256':entry.sha(a.graph/'completed.json'),'recall_scope':'native self-report'}
    if a.phase=='refresh-analyze':
        expected={(d,s,seed) for d in cfg['datasets'] for s in ('old','target_refresh05') for seed in cfg['seeds']};seen=set();builds=set();replay=out/'replay'
        for unit in a.units:
            r=entry.check_prior(unit,'refresh-replay');key=(r['dataset'],r['snapshot'],r['seed'])
            if key not in expected or key in seen:raise ValueError('Duplicate/unregistered refresh unit')
            seen.add(key);builds.add(r['native_build_receipt_sha256']);dest=replay/key[0]/key[1]/('seed_'+str(key[2]));dest.mkdir(parents=True)
            for role in ROLES:shutil.copytree(unit/role,dest/role)
        if seen!=expected or len(builds)!=1:raise ValueError('All 40 same-build refresh cells required')
        (replay/'STATUS').write_text('COMPLETE\n');analysis=entry.module('refresh_analysis');result=analysis.analyze(replay,out/'derived')
        return {'cells':40,'response_files':840,'scientific_stage':'saved new-response analysis','decision':result['decision']}
    raise ValueError('Unknown refresh phase')
