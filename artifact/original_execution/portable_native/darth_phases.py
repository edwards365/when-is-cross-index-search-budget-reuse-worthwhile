"""Separately identified full-source DARTH build and genuine-IP model chain."""
import csv,importlib.metadata,importlib.util,json,os,shutil,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def audit_model_control(text):
    """All 363 unique authored one-hot/permutation predictions, not a marker."""
    import math
    lines=[x.split('\t') for x in text.splitlines() if x.startswith('PRED\t')]
    if len(lines)!=363:raise ValueError('All authored model predictions required')
    perm=[0,1,2,3,4,6,5,7,9,8,10];seen=set()
    for fields in lines:
        if len(fields)!=5:raise ValueError('Malformed authored prediction')
        _,arm,row,tree,value=fields
        arm,row,tree=int(arm),int(row),int(tree);value=float(value);key=(arm,row,tree)
        if arm not in range(3) or row not in range(11) or tree not in range(11) or key in seen:raise ValueError('Authored prediction identity')
        seen.add(key);active=perm[row] if arm==1 else row
        if not math.isfinite(value) or abs(value-float(active==tree))>1e-12:raise ValueError('Authored model prediction mismatch')
    return {'predictions':len(seen),'interface':'LGBM_BoosterPredictForMat','control_version':2}
def command(args,out,name,env=None,cwd=None):
    with (out/(name+'.stdout')).open('xb') as so,(out/(name+'.stderr')).open('xb') as se:
        process=subprocess.Popen(list(map(str,args)),stdout=so,stderr=se,env=env,cwd=cwd,start_new_session=True)
        try:
            code=process.wait(timeout=7200)
            if code:raise subprocess.CalledProcessError(code,args)
        except BaseException:
            # Only this invocation's newly owned, unreaped process group.
            if process.poll() is None:
                import signal
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            raise
def training_dependency(sha):
    lock=json.loads((HERE/'training_native_lock.json').read_text());dist=importlib.metadata.distribution('lightgbm');site=Path(dist.locate_file('')).resolve()
    if dist.version!=lock['version']:raise ValueError('Training LightGBM version')
    for rel,pin in lock['installed_payload'].items():
        if sha(site/rel)!=pin:raise ValueError('Training package payload')
    spec=importlib.util.find_spec('lightgbm')
    if spec is None or Path(spec.origin).resolve()!=site/'lightgbm/__init__.py':raise ValueError('Shadowed LightGBM')
    for name,want in [('numpy','1.26.4'),('pandas','2.2.2'),('scipy','1.14.1'),('scikit-learn','1.5.1')]:
        if importlib.metadata.version(name)!=want:raise ValueError('Training dependency '+name)

def model_structure(path):
    import math
    lines=path.read_text().splitlines();heads=dict(x.split('=',1) for x in lines[:25] if '=' in x)
    if heads.get('max_feature_idx')!='10' or not heads.get('objective','').startswith('regression'):raise ValueError('Native 11-column regression model required')
    trees=[int(x.split('=')[1]) for x in lines if x.startswith('Tree=')]
    if trees!=list(range(100)):raise ValueError('Exactly 100 ordered trees required')
    for line in lines:
        if line.startswith('split_feature=') and any(not 0<=int(x)<=10 for x in line.split('=',1)[1].split()):raise ValueError('Feature range')
        if line.startswith(('threshold=','leaf_value=','internal_value=')) and any(not math.isfinite(float(x)) for x in line.split('=',1)[1].split()):raise ValueError('Nonfinite model value')
    return {'tree_count':100,'max_feature':10,'finite_values':True}

def sift_input(prepared,basefile,out,role):
    import numpy as np
    import run_native as entry
    core=entry.module('input_core');dest=out/'input/SIFT100M';dest.mkdir(parents=True)
    with basefile.open('rb') as f:n,d=struct.unpack('<II',f.read(8))
    base=np.memmap(basefile,dtype='<f4',offset=8,shape=(n,d),mode='r')
    core.write_vecs(dest/'base.100M.fvecs',(base[i:i+8192] for i in range(0,n,8192)),d,'float')
    with (prepared/'queries.fbin').open('rb') as f:nq,dq=struct.unpack('<II',f.read(8))
    if dq!=d:raise ValueError('Query dimension')
    q=np.memmap(prepared/'queries.fbin',dtype='<f4',offset=8,shape=(nq,d),mode='r')
    with (prepared/'truth.bin').open('rb') as f:
        if struct.unpack('<II',f.read(8))!=(nq,10):raise ValueError('Truth shape')
        ids=np.frombuffer(f.read(nq*40),dtype='<u4').reshape(nq,10);scores=np.frombuffer(f.read(nq*40),dtype='<f4').reshape(nq,10)
        if f.read(1):raise ValueError('Truth EOF')
    stem,gt,qtype=('learn.1M','learn.groundtruth.1M.k1000','training') if role=='source_design' else (('query.10K','query.groundtruth.10K.k1000','testing') if role=='target_evaluation' else ('validation.10K','validation.groundtruth.10K.k1000','validation'))
    core.write_vecs(dest/(stem+'.fvecs'),[q],d,'float');core.write_vecs(dest/(gt+'.ivecs'),[ids],10,'int');core.write_vecs(dest/(gt+'.fvecs'),[scores],10,'float')
    return qtype
def audit_ip(path,prepared,basefile):
    import numpy as np
    with (prepared/'truth.bin').open('rb') as f:
        n,k=struct.unpack('<II',f.read(8));truth=np.frombuffer(f.read(n*k*4),dtype='<u4').reshape(n,k)
    with path.open('rb') as f:
        if struct.unpack('<II',f.read(8))!=(n,k):raise ValueError('Returned header')
        ids=np.frombuffer(f.read(n*k*8),dtype='<i8').reshape(n,k);scores=np.frombuffer(f.read(n*k*4),dtype='<f4').reshape(n,k)
        if f.read(1):raise ValueError('Returned EOF')
    with basefile.open('rb') as f:nb,d=struct.unpack('<II',f.read(8))
    if ids.min()<0 or ids.max()>=nb or any(len(set(row))!=k for row in ids) or not np.isfinite(scores).all():raise ValueError('Returned IDs/scores')
    base=np.memmap(basefile,offset=8,dtype='<f4',shape=(nb,d),mode='r');q=np.memmap(prepared/'queries.fbin',offset=8,dtype='<f4',shape=(n,d),mode='r')
    for i in range(n):
        products=base[ids[i]].astype(np.float64)*q[i].astype(np.float64);reference=products.sum(axis=1);tol=64*np.finfo(np.float32).eps*np.abs(products).sum(axis=1)+1e-6
        if np.any(np.abs(scores[i]-reference)>tol):raise ValueError('Independent raw-vector dot score audit')
    recalls=np.array([len(set(row)&set(map(int,truth[i])))/k for i,row in enumerate(ids)])
    return {'mean_recall':float(recalls.mean()),'below095':int((recalls<.95).sum()),'ordered_ids_checked':n*k,'score_reference':'float64 dot; 64eps*sumabs+1e-6'}
def run(a,c,out):
    import run_native as entry
    if a.phase=='lightgbm-build':
        entry.unpack(HERE/'lightgbm-source.tar.gz',out/'source');install=out/'install'
        command(['cmake','-S',out/'source','-B',out/'build','-DCMAKE_BUILD_TYPE=Release','-DBUILD_CLI=OFF','-DBUILD_CPP_TEST=OFF','-DUSE_GPU=OFF','-DUSE_CUDA=OFF','-DUSE_OPENMP=ON','-DCMAKE_INSTALL_PREFIX='+str(install)],out,'configure')
        command(['cmake','--build',out/'build','--target','_lightgbm','--parallel','1'],out,'compile')
        command(['cmake','--install',out/'build'],out,'install')
        libraries=list(install.rglob('lib_lightgbm.so'))
        if len(libraries)!=1:raise ValueError('One installed library required')
        return {'library':libraries[0].relative_to(out).as_posix(),'include':'install/include','new_full_source_build':True,'historical_library_equal':entry.sha(libraries[0])==c['darth']['historical_cpp_library_sha256']}
    if a.phase=='darth-build':
        prior=entry.check_prior(a.prior,'lightgbm-build');source=out/'source';shutil.copytree(HERE/'darth-source',source)
        if a.flavor=='arxiv-ip':
            for name,target in [('darth_ip_DeclarativeRecall.cpp','faiss/impl/DeclarativeRecall.cpp'),('darth_ip_HNSW.cpp','faiss/impl/HNSW.cpp')]:shutil.copyfile(HERE/name,source/target)
        lib=a.prior/prior['library'];include=a.prior/prior['include'];build=out/'build'
        command(['cmake','-S',source,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DFAISS_ENABLE_GPU=OFF','-DFAISS_ENABLE_PYTHON=OFF','-DBUILD_TESTING=OFF','-DBUILD_SHARED_LIBS=ON','-DFAISS_OPT_LEVEL=generic','-DLIGHTGBM_INCLUDE_DIR='+str(include),'-DLIGHTGBM_LIBRARY_DIR='+str(lib.parent),'-DLIGHTGBM_LIB='+str(lib)],out,'configure')
        command(['cmake','--build',build,'--target','faiss','hnsw_test','--parallel','1'],out,'compile')
        env=dict(os.environ,LD_LIBRARY_PATH=str(build/'faiss')+os.pathsep+str(lib.parent));compiler=shutil.which('c++')
        if not compiler:raise ValueError('C++ compiler required')
        command([compiler,'-O3','-std=c++17','-fopenmp','-I'+str(source),'-I'+str(source/'faiss/impl'),'-I'+str(include),HERE/'darth_arxiv_ip_native_v1.cpp','-L'+str(build/'faiss'),'-lfaiss','-Wl,-rpath,'+str(build/'faiss'),'-o',out/'darth_ip'],out,'main')
        if a.flavor=='arxiv-ip':
            command([out/'darth_ip','--controls'],out,'ip_controls',env)
            if 'NEW_IP_AND_NEGATIVE_FEATURE_CONTROLS_PASS' not in (out/'ip_controls.stdout').read_text():raise ValueError('IP control marker missing')
        command([compiler,'-O2','-std=c++17','-I'+str(include),HERE/'darth_compiled_interface_probe_v2.cpp',lib,'-ldl','-Wl,-rpath,'+str(lib.parent),'-o',out/'model_control'],out,'model_compile')
        command([out/'model_control',HERE/'synthetic_model.txt'],out,'model_control',env)
        control=audit_model_control((out/'model_control.stdout').read_text())
        return {'flavor':a.flavor,'model_control':control,'lightgbm_build_receipt_sha256':entry.sha(a.prior/'completed.json'),'lightgbm_library':str(lib),'lightgbm_library_sha256':entry.sha(lib),'new_full_source_build':True,'historical_object_source_pairing_attested':False}
    build=entry.check_prior(a.native_build,'darth-build');lib=Path(build['lightgbm_library'])
    if entry.sha(lib)!=build['lightgbm_library_sha256']:raise ValueError('C++ model library changed')
    env=dict(os.environ,LD_LIBRARY_PATH=str(a.native_build/'build/faiss')+os.pathsep+str(lib.parent))
    if a.phase=='darth-train':
        source=entry.check_prior(a.prior,'darth-source');training_dependency(entry.sha)
        if source['native_build_receipt_sha256']!=entry.sha(a.native_build/'completed.json'):raise ValueError('Source/native build pairing')
        ds=source['dataset'];dataset=c['inputs'][ds]['dataset'];jobs=8 if ds=='arxiv' else 1
        ids=json.loads((HERE/'roles.json').read_text());rows=next(x['roles']['source_design'] for x in ids['datasets'] if x['name']==dataset);(out/'query_ids.json').write_text(json.dumps(rows))
        trainer='train_darth_arxiv_ip_cpu_v1.py' if ds=='arxiv' else 'train_darth_native_aligned_v1.py'
        command([sys.executable,HERE/trainer,'--input',a.prior/'search.csv','--model',out/'model.txt','--metadata',out/'model.json','--roles',HERE/'roles.json','--query-row-ids',out/'query_ids.json','--dataset',dataset],out,'train')
        meta=json.loads((out/'model.json').read_text())
        if meta['n_estimators']!=100 or meta['n_jobs']!=jobs or meta['random_state']!=42 or meta['model_sha256']!=entry.sha(out/'model.txt'):raise ValueError('Model configuration')
        import ast
        tree=ast.parse((HERE/trainer).read_text());features=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FEATURES' for t in n.targets))
        if meta['features']!=list(features):raise ValueError('Native feature order')
        return {'dataset':ds,'model_structure':model_structure(out/'model.txt'),'source_receipt_sha256':entry.sha(a.prior/'completed.json'),'native_build_receipt_sha256':entry.sha(a.native_build/'completed.json'),'train_cpus':list(range(4,12)) if jobs==8 else [2],'n_jobs':jobs,'n_jobs_is_not_os_thread_count':True}
    prep=entry.check_prior(a.prepared,'prepare')
    if build['flavor']!=('arxiv-ip' if prep['dataset']=='arxiv' else 'legacy-l2'):raise ValueError('Metric-specific build pairing')
    if a.phase=='darth-source':
        if prep['role']!='source_design':raise ValueError('Source role')
        mode='source';index=out/'index.faiss';model='NONE';base=a.prepared/'base.fbin';source_hash=None
    else:
        source=entry.check_prior(a.graph,'darth-source');model_record=entry.check_prior(a.model,'darth-train')
        if prep['role']=='source_design' or source['base_ids_sha256']!=prep['base_ids_sha256'] or source['native_build_receipt_sha256']!=entry.sha(a.native_build/'completed.json'):raise ValueError('Saved graph pairing')
        if model_record['source_receipt_sha256']!=entry.sha(a.graph/'completed.json'):raise ValueError('Model/source pairing')
        mode='role';index=a.graph/'index.faiss';model=a.model/'model.txt';base=Path(source['source_base']);source_hash=entry.sha(a.graph/'completed.json')
        if entry.sha(base)!=source['source_base_sha256']:raise ValueError('Base identity')
    if prep['dataset']=='arxiv':
        command([a.native_build/'darth_ip',mode,base,a.prepared/'queries.fbin',a.prepared/'truth.bin',out/'search',index,model,str(prep['query_rows'])],out,'native',env)
        audit=audit_ip(out/'search.returned.bin',a.prepared,base)
    else:
        qtype=sift_input(a.prepared,base,out,prep['role'])
        args=[a.native_build/'build/hnsw-test/hnsw_test','--dataset','SIFT100M','--dataset-dir-prefix',str(out/'input')+'/','--query-type',qtype,'--query-num',str(prep['query_rows']),'--k','10','--M','16','--efSearch','200','--index-filepath',index,'--output',out/'search.csv']
        args+=['--efConstruction','100','--save-index','--mode','early-stop-training','--logging-interval','5'] if mode=='source' else ['--mode','early-stop-testing','--predictor-model-path',model,'--target-recall','0.95','--initial-prediction-interval','1000','--min-prediction-interval','100']
        command(args,out,'native',env)
        if not (out/'search.csv').stat().st_size:raise ValueError('Native observations absent')
        audit={'recall_scope':'native self-report only; this legacy entry does not export ordered IDs','independent_returned_id_audit':False}
    return {'dataset':prep['dataset'],'role':prep['role'],'base_ids_sha256':prep['base_ids_sha256'],'native_build_receipt_sha256':entry.sha(a.native_build/'completed.json'),'source_receipt_sha256':source_hash,'source_base':str(base),'source_base_sha256':entry.sha(base),'summary':audit}
