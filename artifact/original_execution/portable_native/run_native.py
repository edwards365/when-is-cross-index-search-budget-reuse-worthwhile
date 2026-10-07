"""New native source/build/control and saved-graph stages. Never resumes old runs."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def module(name):
    s=importlib.util.spec_from_file_location('native_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def config():
    c=json.loads((HERE/'config.json').read_text())
    for rel,pin in c['source_pins'].items():
        if sha(HERE/rel)!=pin:raise ValueError('Source identity: '+rel)
    return c
def tree_sha(root):
    h=hashlib.sha256()
    for p in sorted(root.rglob('*'),key=lambda p:PurePosixPath(p.relative_to(root).as_posix())):
        if p.is_symlink():raise ValueError('No source symlinks')
        if p.is_file():h.update(json.dumps([p.relative_to(root).as_posix(),p.stat().st_size,sha(p)],separators=(',',':')).encode()+b'\n')
    return h.hexdigest()
def check_prior(root,phase):
    r=json.loads((root/'completed.json').read_text())
    allowed={'NEW_EXECUTION'}
    if phase in ('lightgbm-build','darth-build'):allowed.add('NEW_CI_BUILD_ONLY')
    if r['phase']!=phase or r['status'] not in allowed or r['config_sha256']!=sha(HERE/'config.json') or (root/'failure.json').exists():raise ValueError('Prior stage identity/status')
    for rel,pin in r['files'].items():
        if sha(root/rel)!=pin:raise ValueError('Prior output pin')
    return r
def unpack(archive,out):
    out.mkdir()
    with tarfile.open(archive,'r:gz') as t:
        for m in t:
            rel=Path(*Path(m.name).parts[1:])
            if rel==Path('.') or m.isdir():continue
            if not m.isfile() or rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe archive member')
            p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:shutil.copyfileobj(t.extractfile(m),f)
def tools(toolchain,c):
    result={}
    for name,pin in c['tool_pins'].items():
        p=toolchain/'bin'/name
        if sha(p)!=pin:raise ValueError('Pinned Rust tool differs: '+name)
        result[name]=str(p)
    if not subprocess.check_output([result['rustc'],'--version'],text=True).startswith('rustc '+c['rust_version']+' '):raise ValueError('Rust version')
    return result
def native_spec(prepared,out,index=None,metric='inner_product'):
    source={'index-source':'Load','data_type':'float32','distance':metric,'load_path':str(index)} if index else {'index-source':'Build','data_type':'float32','distance':metric,'data':'base.fbin','save_path':str(out/'native/index'),'max_degree':32,'l_build':64,'alpha':1.2,'backedge_ratio':1,'num_threads':1,'start_point_strategy':'medoid','multi_insert':{'batch_size':1,'batch_parallelism':1,'intra_batch_candidates':'none'}}
    return {'search_directories':[str(prepared)],'output_directory':str(out/'native'),'jobs':[{'type':'graph-index-build','content':{'source':source,'search_phase':{'search-type':'topk','queries':'queries.fbin','groundtruth':'truth.bin','reps':1,'num_threads':[1],'runs':[{'search_n':10,'search_l':[64],'recall_k':10}]}}}]}
def audit_report(report,truth,rows,base_rows):
    import numpy as np
    r=json.loads(report.read_text())
    if len(r)!=1 or len(r[0]['results']['search']['Topk'])!=1:raise ValueError('Expected one native action')
    s=r[0]['results']['search']['Topk'][0]
    if (s['search_n'],s['search_l'],s['num_tasks'])!=(10,64,1) or s['returned_ids_encoding']!='canonical_unsigned_decimal_debug_to_u64_v1':raise ValueError('Wrong action/encoding')
    ids=s['returned_ids_by_repetition']
    if len(ids)!=1 or len(ids[0])!=rows:raise ValueError('Query repetition shape')
    recall=[]
    for i,row in enumerate(ids[0]):
        if len(row)!=10 or len(set(row))!=10 or any(type(x)is not int or x<0 or x>=base_rows for x in row):raise ValueError('ID validation')
        recall.append(len(set(row)&set(map(int,truth[i])))/10)
    if not np.allclose(recall,s['query_recalls'],rtol=0,atol=1e-6):raise ValueError('Independent recall mismatch')
    for name in ('query_cmps','query_hops'):
        a=np.asarray(s[name])
        if a.shape!=(rows,) or not np.isfinite(a).all() or (a<0).any():raise ValueError('Native counter shape/range')
    return {'mean_recall':float(np.mean(recall)),'below095':sum(x<.95 for x in recall),'native_cmps_independently_counted':False}
def run(a,c):
    if not a.authorize_new_execution:raise ValueError('Explicit opt-in required')
    cpus=set(range(4,12)) if a.phase=='darth-train' and check_prior(a.prior,'darth-source')['dataset']=='arxiv' else {2}
    if not cpus<=os.sched_getaffinity(0):raise ValueError('Required CPUs unavailable')
    os.sched_setaffinity(0,cpus)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[key]=str(len(cpus))
    plan=dict(c['resource_plan'],cpu_affinity=sorted(cpus));res=module('resources');out,snapshot=res.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,{},a.outstanding_growth_bytes)
    import resource,signal
    for kind,cap in ((resource.RLIMIT_AS,24<<30),(resource.RLIMIT_FSIZE,8<<30),(resource.RLIMIT_CPU,14400),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);limit=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(limit,limit))
    out.mkdir(mode=0o700);res.write_json(out/'start.json',{'phase':a.phase,'resources':snapshot,'config_sha256':sha(HERE/'config.json')})
    def timeout(sig,frame):raise TimeoutError('Phase wall limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(14400);record={}
    try:
        if a.phase.startswith('refresh-'):
            record=module('refresh_phases').run(a,c,out)
        elif a.phase=='lightgbm-build' or a.phase.startswith('darth-'):
            record=module('darth_phases').run(a,c,out)
        elif a.phase=='source':
            unpack(HERE/'diskann-source.tar.gz',out/'source')
            if sha(out/'source/Cargo.lock')!=c['diskann']['cargo_lock_sha256']:raise ValueError('Cargo.lock')
            for rel,p in c['old_patches'].items():
                if sha(out/'source'/rel)!=p['upstream_sha256']:raise ValueError('Patch upstream target')
                shutil.copyfile(HERE/p['file'],out/'source'/rel)
            if tree_sha(out/'source')!=c['reconstructed_old_patch_tree_sha256']:raise ValueError('Reconstructed source mismatch')
            for rel,p in c['ordered_id_patches'].items():shutil.copyfile(HERE/p['file'],out/'source'/rel)
            record={'source_tree_sha256':tree_sha(out/'source'),'historical_tree_match':c['historical_tree_match']}
        elif a.phase in ('fetch','build'):
            check_prior(a.prior,'source' if a.phase=='fetch' else 'fetch');tool=tools(a.toolchain,c)
            shutil.copytree(a.prior/'source',out/'source')
            if a.phase=='build':shutil.copytree(a.prior/'cargo',out/'cargo')
            env=dict(os.environ,CARGO_HOME=str(out/'cargo'),CARGO_TARGET_DIR=str(out/'target'),RUSTC=tool['rustc'],RUSTDOC=tool['rustdoc']);env['PATH']=str(a.toolchain/'bin')+os.pathsep+env.get('PATH','')
            phases=['fetch'] if a.phase=='fetch' else ['build','controls']
            for step in phases:
                with (out/(step+'.stdout')).open('xb') as so,(out/(step+'.stderr')).open('xb') as se:
                    subprocess.run([tool['cargo']]+c['cargo_commands'][step],cwd=out/'source',env=env,stdout=so,stderr=se,check=True,timeout=7200)
                if step=='controls' and '2 passed; 0 failed' not in (out/'controls.stdout').read_text():raise ValueError('Expected both ordered-ID controls')
            record={'toolchain':'1.97.1','steps':phases,'prior_receipt_sha256':sha(a.prior/'completed.json')}
        elif a.phase=='prepare':
            record=module('native_inputs').prepare(a,c,out)
        elif a.phase in ('source-search','heldout-search'):
            import numpy as np,struct
            p=check_prior(a.prepared,'prepare');check_prior(a.native_build,'build');index=None
            if a.phase=='source-search' and p['role']!='source_design':raise ValueError('Source role required')
            if a.phase=='heldout-search':
                s=check_prior(a.graph,'source-search')
                if p['role']=='source_design' or s['dataset']!=p['dataset']:raise ValueError('Held-out role/data mismatch')
                if s['native_build_receipt_sha256']!=sha(a.native_build/'completed.json') or s['base_ids_sha256']!=p['base_ids_sha256']:raise ValueError('Graph/binary/base pairing')
                index=a.graph/'native/index'
            (out/'native').mkdir();spec=native_spec(a.prepared,out,index,p['metric']);res.write_json(out/'native_config.json',spec)
            with (out/'native.stdout').open('xb') as so,(out/'native.stderr').open('xb') as se:
                subprocess.run([str(a.native_build/'target/release/diskann-benchmark'),'--quiet','run','--input-file',str(out/'native_config.json'),'--output-file',str(out/'native/run_report.json')],stdout=so,stderr=se,check=True,timeout=14000)
            with (a.prepared/'truth.bin').open('rb') as f:
                if struct.unpack('<II',f.read(8))!=(p['query_rows'],10):raise ValueError('Truth header')
                truth=np.frombuffer(f.read(p['query_rows']*40),dtype='<u4').reshape(-1,10)
            record=dict(p,summary=audit_report(out/'native/run_report.json',truth,p['query_rows'],p['base_rows']),native_build_receipt_sha256=sha(a.native_build/'completed.json'))
            for k in ('files','phase','config_sha256','status'):record.pop(k,None)
        else:raise ValueError('Unknown phase')
        files={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p.name!='start.json'}
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>c['resource_plan']['max_output_growth_bytes']:raise ValueError('Output growth cap')
        res.write_json(out/'completed.json',dict(record,phase=a.phase,status='NEW_EXECUTION',config_sha256=sha(HERE/'config.json'),files=files))
    except BaseException as e:res.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_PHASES','error':repr(e)});raise
    finally:signal.alarm(0)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['check','source','fetch','build','prepare','source-search','heldout-search','lightgbm-build','darth-build','darth-source','darth-train','darth-heldout','refresh-prepare','refresh-build','refresh-replay','refresh-analyze'])
    for name in ('output','prior','toolchain','bundle','truth','qbin','source_prepared','native_build','prepared','graph','model','hdf5'):p.add_argument('--'+name.replace('_','-'),type=Path)
    p.add_argument('--refresh-dataset',choices=['sift100k','arxiv_nomic_100k']);p.add_argument('--snapshot',choices=['old','target_refresh05']);p.add_argument('--seed',type=int);p.add_argument('--units',nargs='+',type=Path)
    p.add_argument('--flavor',choices=['arxiv-ip','legacy-l2'],default='arxiv-ip')
    p.add_argument('--dataset',choices=['sift','arxiv']);p.add_argument('--role',choices=['source_design','target_selection','target_certification','target_evaluation']);p.add_argument('--authorize-new-execution',action='store_true');p.add_argument('--outstanding-growth-bytes',type=int)
    a=p.parse_args();c=config()
    if a.phase=='check':print(json.dumps({'source_pins':'PASS','historical_tree_match':c['historical_tree_match'],'science_runs':0}));return
    need={'source':[],'fetch':['prior','toolchain'],'build':['prior','toolchain'],'prepare':['dataset','role','truth'],'source-search':['native_build','prepared'],'heldout-search':['native_build','prepared','graph'],'lightgbm-build':[],'darth-build':['prior'],'darth-source':['native_build','prepared'],'darth-train':['prior','native_build'],'darth-heldout':['native_build','prepared','graph','model'],'refresh-prepare':['hdf5','refresh_dataset'],'refresh-build':['prepared','snapshot','seed'],'refresh-replay':['prepared','graph','native_build'],'refresh-analyze':['units']}[a.phase]+['output','outstanding_growth_bytes']
    if any(getattr(a,k)is None for k in need):p.error('Required: '+','.join(need))
    run(a,c)
if __name__=='__main__':main()
