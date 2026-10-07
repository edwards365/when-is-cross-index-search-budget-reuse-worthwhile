"""Bounded Linux CI controls: newly generated tiny vectors, never paper inputs."""
import argparse,csv,hashlib,json,os,platform,shutil,struct,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
import run_ambiguity as r

HERE=Path(__file__).resolve().parent
GRID=[10,32,128]

def synthetic(normalized):
    import numpy as np
    rng=np.random.default_rng(20261007)
    base=rng.normal(size=(256,32)).astype(np.float32)
    if normalized:base/=np.linalg.norm(base,axis=1,keepdims=True)
    query_ids=np.array([2,17,31,45,91,127,180,240]);queries=base[query_ids].copy()
    # Identity checking intentionally uses a new independent float64 reference.
    dist=((queries.astype(np.float64)[:,None,:]-base.astype(np.float64)[None,:,:])**2).sum(2)
    truth=np.argsort(dist,axis=1,kind='stable')[:,:10].astype(np.uint32)
    order=rng.permutation(len(base));inverse=np.empty(len(base),dtype=np.uint32);inverse[order]=np.arange(len(base),dtype=np.uint32)
    return base,queries,truth,order,inverse,query_ids

def check_ids(ids,q,base,truth,normalized):
    import numpy as np
    ids=np.asarray(ids,dtype=np.int64)
    if ids.shape!=(10,) or len(set(map(int,ids)))!=10 or ids.min()<0 or ids.max()>=len(base):raise ValueError('Ordered ID range/uniqueness')
    values=-(base[ids].astype(np.float64)@q.astype(np.float64)) if normalized else ((base[ids].astype(np.float64)-q.astype(np.float64))**2).sum(1)
    if np.any(np.diff(values)<-1e-5):raise ValueError('Returned ordering disagrees with independent metric')
    return len(set(map(int,ids))&set(map(int,truth)))/10

def faiss_controls(c,out):
    import numpy as np
    faiss,loaded=r.faiss_environment(c);checks=[]
    for normalized in (False,True):
        b,q,truth,order,inv,qids=synthetic(normalized)
        idx=faiss.IndexHNSWFlat(32,16,faiss.METRIC_INNER_PRODUCT if normalized else faiss.METRIC_L2)
        idx.hnsw.efConstruction=100;idx.hnsw.rng=faiss.RandomGenerator(43);idx.add(b[order])
        cells=[]
        for budget in GRID:
            idx.hnsw.efSearch=budget
            for qi,x in enumerate(q):
                faiss.cvar.hnsw_stats.reset();scores,positions=idx.search(x.reshape(1,-1),10)
                if np.any(positions<0) or np.any(positions>=len(b)):raise ValueError('Faiss native positions')
                ids=order[positions[0]];ndc=int(faiss.cvar.hnsw_stats.ndis)
                recall=check_ids(ids,x,b,truth[qi],normalized)
                reference=b[ids].astype(np.float64)@x.astype(np.float64) if normalized else ((b[ids].astype(np.float64)-x.astype(np.float64))**2).sum(1)
                np.testing.assert_allclose(scores[0],reference,rtol=2e-5,atol=2e-5)
                if ndc<=0 or (budget==128 and ids[0]!=qids[qi]):raise ValueError('Faiss counter/self-query identity')
                cells.append({'budget':budget,'query':qi,'ordered_raw_ids':ids.tolist(),'recall':recall,'native_ndis':ndc})
        checks.append({'metric':'normalized-ip' if normalized else 'l2','cells':cells})
    return {'native':loaded,'checks':checks,'native_execution_cells':48}

def hnsw_controls(a,c,out):
    import numpy as np
    if a.native_build is None:
        # This opt-in helper compiles source only; it never invokes the full-data CLI.
        if a.transfer_adapter is None:raise ValueError('Transfer source directory required')
        conf=json.loads((a.transfer_adapter/'config.json').read_text())
        for name,pin in conf['source_pins'].items():
            if r.sha(a.transfer_adapter/name)!=pin:raise ValueError('Compile source identity')
        a.native_build=out/'synthetic-build';a.native_build.mkdir()
        binary=a.native_build/'hnsw_gate_a_benchmark'
        cmd=['g++']+conf['new_compile_flags']+['-I',str(a.transfer_adapter/'include'),str(a.transfer_adapter/'hnsw_gate_a_benchmark.cpp'),'-o',str(binary)]
        with (a.native_build/'stdout').open('wb') as so,(a.native_build/'stderr').open('wb') as se:
            subprocess.run(cmd,stdout=so,stderr=se,check=True,timeout=180)
        done=a.native_build/'completed.json'
        done.write_text(json.dumps({'phase':'compile','purpose':'new synthetic CI only','config_sha256':r.sha(a.transfer_adapter/'config.json'),'outputs':{binary.name:r.sha(binary)}})+'\n')
        a.native_build_sha256=r.sha(done)
    binary=r.hnsw_binary(a,c);checks=[]
    for normalized in (False,True):
        target=out/('ip' if normalized else 'l2');target.mkdir();b,q,truth,order,inv,qids=synthetic(normalized)
        r.matrix(target/'base.bin',b,np.float32,np);r.matrix(target/'queries.bin',q,np.float32,np);r.matrix(target/'truth.bin',truth,np.uint32,np)
        with (target/'order.bin').open('xb') as f:f.write(struct.pack('<Q',len(order)));np.asarray(order,dtype='<u4').tofile(f)
        cmd=[str(binary),str(target/'base.bin'),str(target/'order.bin'),str(target/'queries.bin'),str(target/'truth.bin'),'-','ip' if normalized else 'l2','16','100','43','synthetic-g1','original','-',','.join(map(str,GRID)),'0','1',r.sha(HERE/'config.json'),'synthetic-ci','synthetic-g1',str(target/'native')]
        with (target/'stdout').open('wb') as so,(target/'stderr').open('wb') as se:run=subprocess.run(cmd,stdout=so,stderr=se,timeout=120)
        if run.returncode:raise ValueError('HNSW original tracer/native ordered results check failed')
        with (target/'native/queries.csv').open() as f:rows=list(csv.DictReader(f))
        seen=set()
        for row in rows:
            qi=int(row['query_id']);budget=int(row['ef_search']);key=(budget,qi)
            if key in seen or budget not in GRID or not 0<=qi<8 or int(row['latency_round'])!=0:raise ValueError('HNSW synthetic coverage')
            seen.add(key);ids=list(map(int,row['returned_top10'].split(';')));recall=check_ids(ids,q[qi],b,truth[qi],normalized)
            if abs(recall-float(row['recall_at_10']))>1e-8 or int(row['ndc'])<=0 or (budget==128 and ids[0]!=qids[qi]):raise ValueError('HNSW independent recall/counter/self query')
        if len(seen)!=24:raise ValueError('HNSW complete tiny grid required')
        checks.append({'metric':'normalized-ip' if normalized else 'l2','actual_exit_code':run.returncode,'cells':len(seen),'original_tracer_native_ordered_id_guard_passed':True})
    return {'new_binary_sha256':r.sha(binary),'compile_receipt_sha256':a.native_build_sha256,'checks':checks,'native_execution_cells':48}

def diskann_controls(a,c,out):
    import numpy as np
    build=out/'build';build.mkdir();bounded=dict(c,resource_plan=dict(c['resource_plan'],wall_seconds=1800))
    os.environ['CARGO_BUILD_JOBS']='1'
    provenance=r.compile_vamana(a,bounded,build);binary=build/'integration-test';checks=[]
    for normalized in (False,True):
        target=out/('cosine' if normalized else 'l2');target.mkdir();b,q,truth,order,inv,qids=synthetic(normalized)
        r.matrix(target/'base.fbin',b[order],np.float32,np,True);r.matrix(target/'queries.fbin',q,np.float32,np,True);r.matrix(target/'truth.bin',inv[truth],np.uint32,np,True)
        (target/'input.json').write_text(json.dumps(r.vamana_spec(target,normalized,GRID)))
        command=[str(binary),'run','--input-file',str(target/'input.json'),'--output-file',str(target/'native.json')]
        with (target/'stdout').open('wb') as so,(target/'stderr').open('wb') as se:run=subprocess.run(command,stdout=so,stderr=se,timeout=120)
        if run.returncode:raise ValueError('G1 DiskANN tiny native failure')
        obj=json.loads((target/'native.json').read_text())[0]['results'];graph=obj['graph']
        if len(graph)!=257 or any(len(x)>32 or len(set(x))!=len(x) or any(v<0 or v>=257 for v in x) for x in graph):raise ValueError('G1 graph/frozen-start/range/degree')
        if len(obj['knn'])!=3:raise ValueError('G1 tiny grid missing')
        rec=[]
        for budget,knn in zip(GRID,obj['knn']):
            rows=knn['per_query']
            if len(rows)!=8:raise ValueError('G1 tiny queries missing')
            total=0;recalls=[]
            for qi,row in enumerate(rows):
                positions=np.asarray(row['ids'][:10],dtype=np.int64)
                if len(positions)!=10 or np.any(positions<0) or np.any(positions>=256):raise ValueError('G1 native positions')
                ids=order[positions];recalls.append(check_ids(ids,q[qi],b,truth[qi],normalized));cmps=int(row['misc']['cmps']);total+=cmps
                if cmps<=0 or (budget==128 and ids[0]!=qids[qi]):raise ValueError('G1 counter/self-query identity')
            if total!=knn['misc']['cmps'] or total!=knn['counters']['query_distance']:raise ValueError('Instrumented G1 aggregate counter disagreement')
            if abs(float(np.mean(recalls))-knn['recall']['average'])>1e-8:raise ValueError('G1 native/independent recall disagreement')
            rec.append({'budget':budget,'counter_sum':total,'independent_mean_recall':float(np.mean(recalls))})
        checks.append({'metric':'cosine' if normalized else 'l2','actual_exit_code':run.returncode,'checks':rec})
    return {'build':provenance,'new_binary_sha256':r.sha(binary),'checks':checks,'native_execution_cells':48}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('implementation',choices=['faiss','hnswlib','vamana']);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--transfer-adapter',type=Path);p.add_argument('--native-build',type=Path);p.add_argument('--native-build-sha256');p.add_argument('--source-archive',type=Path)
    p.add_argument('--authorize-synthetic-native',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_native:p.error('Explicit bounded synthetic native authorization required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 without -O required')
    out=a.output.resolve()
    if out.exists():raise ValueError('New exclusive output required')
    if not out.parent.is_dir() or shutil.disk_usage(out.parent).free<8*1024**3:raise ValueError('CI output parent/free-space preflight')
    allowed=os.sched_getaffinity(0);os.sched_setaffinity(0,{min(allowed)})
    for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='1'
    import resource
    wall=2100 if a.implementation=='vamana' else 300
    for kind,cap in ((resource.RLIMIT_AS,12*1024**3),(resource.RLIMIT_FSIZE,1024**3),(resource.RLIMIT_CPU,wall),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    c=json.loads((HERE/'config.json').read_text())
    for rel,pin in c['pins'].items():
        if r.sha(HERE/rel)!=pin:raise ValueError('Package source identity')
    out.mkdir(mode=0o700);a.output=out
    if a.source_archive:a.source_archive=a.source_archive.resolve()
    started=time.monotonic()
    try:
        import numpy,scipy,h5py
        versions={k:v.__version__ for k,v in [('numpy',numpy),('scipy',scipy),('h5py',h5py)]}
        if list(versions.values())!=['1.26.4','1.13.1','3.11.0']:raise ValueError('Pinned control dependencies')
        result=faiss_controls(c,out) if a.implementation=='faiss' else hnsw_controls(a,c,out) if a.implementation=='hnswlib' else diskann_controls(a,c,out)
        if time.monotonic()-started>wall or sum(f.stat().st_size for f in out.rglob('*') if f.is_file())>6*1024**3:raise ValueError('Synthetic CI time/growth cap')
        result.update(status='SYNTHETIC_NATIVE_CONTROLS_PASS_NOT_PAPER_REPRODUCTION',implementation=a.implementation,config_sha256=r.sha(HERE/'config.json'),wrapper_sha256=r.sha(Path(__file__)),versions=versions,cpu_affinity=sorted(os.sched_getaffinity(0)),source_data='seeded synthetic 256x32 base,8queries,2metrics,3budgets',outputs={str(f.relative_to(out)):r.sha(f) for f in out.rglob('*') if f.is_file()})
        (out/'completed.json').write_text(json.dumps(result,indent=2)+'\n')
    except BaseException as e:
        (out/'failure.json').write_text(json.dumps({'status':'FAILED_STOP','error':repr(e)},indent=2)+'\n');raise
if __name__=='__main__':main()
