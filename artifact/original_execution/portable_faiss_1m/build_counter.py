"""Build unchanged corrected counter against exact public Faiss1.8 GENERIC payload."""
import argparse,io,json,os,platform,subprocess,tarfile,zipfile
from pathlib import Path,PurePosixPath
from run_faiss import HERE,sha,pin,write
def extract(package,out,lock):
    pin(package,lock['sha256'])
    if package.stat().st_size!=lock['size']:raise ValueError('Package size')
    import zstandard
    seen=set();total=0
    with zipfile.ZipFile(package) as z:
        names=[n for n in z.namelist() if n.startswith('pkg-') and n.endswith('.tar.zst')]
        if len(names)!=1:raise ValueError('Conda payload member')
        with z.open(names[0]) as compressed,zstandard.ZstdDecompressor().stream_reader(compressed) as reader,tarfile.open(fileobj=reader,mode='r|') as tar:
            for m in tar:
                name=PurePosixPath(m.name)
                if name.is_absolute() or '..' in name.parts:raise ValueError('Unsafe archive member')
                if m.name not in lock['payload']:continue
                if not m.isfile() or m.name in seen:raise ValueError('Payload type/duplicate')
                expected=lock['payload'][m.name]
                if m.size!=expected['bytes']:raise ValueError('Payload size')
                total+=m.size
                if total>32*1024**2:raise ValueError('Extraction bound')
                dest=out.joinpath(*name.parts);dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as f:f.write(tar.extractfile(m).read())
                pin(dest,expected['sha256']);seen.add(m.name)
    if seen!=set(lock['payload']):raise ValueError('Incomplete pinned headers/library')
def clean_child_env():
    if os.environ.get('LD_PRELOAD'):raise ValueError('Uncontrolled preload')
    env=dict(os.environ);env.pop('LD_LIBRARY_PATH',None);env.pop('LD_PRELOAD',None)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[key]='1'
    return env
def dependencies(binary,library):
    result=subprocess.run(['ldd',str(binary)],capture_output=True,text=True,timeout=30,env=clean_child_env());result.check_returncode()
    if 'not found' in result.stdout:raise ValueError('Runtime dependency unavailable')
    rows={}
    for line in result.stdout.splitlines():
        items=line.strip().split();path=next((s for s in items if s.startswith('/')),None)
        if path:rows[items[0]]={'path':str(Path(path).resolve()),'sha256':sha(Path(path).resolve())}
    if 'libfaiss.so' not in rows or rows['libfaiss.so']['sha256']!=sha(library):raise ValueError('Wrong generic library resolution')
    return rows
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compiler',default='g++');p.add_argument('--authorize-new-build',action='store_true');a=p.parse_args()
    if not a.authorize_new_build or a.output.exists():raise ValueError('New exclusive build required')
    if platform.system()!='Linux' or platform.machine()!='x86_64':raise ValueError('Linux x86_64')
    env=clean_child_env()
    import resource
    for key,cap in [(resource.RLIMIT_AS,4*1024**3),(resource.RLIMIT_FSIZE,64*1024**2),(resource.RLIMIT_CPU,180),(resource.RLIMIT_CORE,0)]:
        old=resource.getrlimit(key);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(key,(cap,cap))
    cfg=json.loads((HERE/'config.json').read_text());lock=json.loads((HERE/'generic_package_lock.json').read_text());pin(HERE/'generic_package_lock.json',cfg['extra_files']['generic_package_lock.json']);source=HERE/'e6_faiss_exact_dc_reset_corrected_v1.cpp';pin(source,cfg['extra_files'][source.name]);a.output.mkdir(mode=0o700)
    try:
        extract(a.package,a.output,lock);binary=a.output/'counter';argv=[a.compiler,'-std=c++17','-O2','-fopenmp','-I'+str((a.output/'include').resolve()),str(source),'-L'+str((a.output/'lib').resolve()),'-Wl,-rpath,'+str((a.output/'lib').resolve()),'-lfaiss','-o',str(binary)]
        r=subprocess.run(argv,capture_output=True,text=True,timeout=180,env=env);write(a.output/'compile_wait.json',{'actual_exit_code':r.returncode,'stdout':r.stdout[-20000:],'stderr':r.stderr[-20000:]});r.check_returncode()
        deps=dependencies(binary,a.output/'lib/libfaiss.so');r=subprocess.run([str(binary.resolve()),'controls'],capture_output=True,text=True,timeout=30,env=env);write(a.output/'control_wait.json',{'actual_exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});r.check_returncode()
        if 'NEW_EXACT_DC_DELEGATION_CONTROLS_PASS version 1.8.0 options' not in r.stdout or 'GENERIC' not in r.stdout or 'AVX2' in r.stdout:raise ValueError('Corrected delegation control marker')
        write(a.output/'completed.json',{'status':'NEW_CORRECTED_COUNTER_BUILD_CONTROLS_PASS','config_sha256':sha(HERE/'config.json'),'source_sha256':sha(source),'binary_sha256':sha(binary),'generic_library_sha256':sha(a.output/'lib/libfaiss.so'),'runtime_dependencies':deps,'compiler':subprocess.check_output([a.compiler,'--version'],text=True).splitlines()[0],'compiler_or_all_runtime_equal_historical_claimed':False})
    except BaseException as e:write(a.output/'failure.json',{'status':'FAILED_NEW_BUILD_NO_RETRY','error':repr(e)});raise
if __name__=='__main__':main()
