"""Bounded Linux full-source compilation plus synthetic controls; no datasets."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
import run_native as entry
import darth_phases

def receipt(out,phase,record):
    files={p.relative_to(out).as_posix():entry.sha(p) for p in out.rglob('*') if p.is_file()}
    (out/'completed.json').write_text(json.dumps(dict(record,phase=phase,status='NEW_CI_BUILD_ONLY',config_sha256=entry.sha(entry.HERE/'config.json'),files=files),indent=2))

def output_bytes(root):
    total=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if total>8<<30:raise ValueError('CI aggregate output exceeds 8 GiB; preserve failure and stop')
    return total

def bounded_limit(resource,kind,cap):
    old=resource.getrlimit(kind);limit=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(limit,limit))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--component',choices=['darth','vamana'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--toolchain',type=Path);a=p.parse_args()
    c=entry.config()
    if sys.platform!='linux':p.error('Linux source-build CI required')
    if a.output.exists():p.error('Fresh output required')
    a.output=a.output.resolve();a.output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(a.output.parent).free<12<<30:raise ValueError('At least 12 GiB free required for source-build CI')
    import resource,signal
    for kind,cap in [(resource.RLIMIT_AS,8<<30),(resource.RLIMIT_FSIZE,2<<30),(resource.RLIMIT_CORE,0),(resource.RLIMIT_CPU,5400)]:bounded_limit(resource,kind,cap)
    def stop(*args):raise TimeoutError('CI build wall cap')
    signal.signal(signal.SIGALRM,stop);signal.alarm(5400)
    cpu=min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS'):os.environ[k]='1'
    a.output.mkdir();started=time.monotonic()
    try:
        if a.component=='darth':
            lib=a.output/'lightgbm';lib.mkdir();r=darth_phases.run(SimpleNamespace(phase='lightgbm-build'),c,lib);output_bytes(a.output);receipt(lib,'lightgbm-build',r)
            for flavor in ('arxiv-ip','legacy-l2'):
                out=a.output/flavor;out.mkdir();r=darth_phases.run(SimpleNamespace(phase='darth-build',prior=lib,flavor=flavor),c,out);output_bytes(a.output);receipt(out,'darth-build',r)
        else:
            if a.toolchain is None:p.error('--toolchain required for exact Rust 1.97.1 binaries')
            tool=entry.tools(a.toolchain,c);source=a.output/'source';entry.unpack(entry.HERE/'diskann-source.tar.gz',source)
            for rel,r in c['old_patches'].items():shutil.copyfile(entry.HERE/r['file'],source/rel)
            if entry.tree_sha(source)!=c['historical_source_tree_sha256']:raise ValueError('Historical whole source identity')
            for rel,r in c['ordered_id_patches'].items():shutil.copyfile(entry.HERE/r['file'],source/rel)
            env=dict(os.environ,CARGO_HOME=str(a.output/'cargo'),CARGO_TARGET_DIR=str(a.output/'target'),RUSTC=tool['rustc'],RUSTDOC=tool['rustdoc']);env['PATH']=str(a.toolchain/'bin')+os.pathsep+env.get('PATH','')
            for step in ('fetch','build','controls'):
                darth_phases.command([tool['cargo']]+c['cargo_commands'][step],a.output,step,env,cwd=source)
                output_bytes(a.output)
            if '2 passed; 0 failed' not in (a.output/'controls.stdout').read_text():raise ValueError('Both synthetic ordered-ID controls required')
        (a.output/'ci_result.json').write_text(json.dumps({'status':'PASS','component':a.component,'science_runs':0,'datasets_opened':0,'seconds':time.monotonic()-started,'cpu':cpu,'output_bytes':output_bytes(a.output),'aggregate_bound_scope':'8GiB checked at each compile/fetch/control stage boundary, not kernel aggregate quota','production_resource_gate_bypassed':False,'scope':'Separate build-only CI contract; not a production phase receipt'},indent=2))
    except BaseException as e:(a.output/'failure.json').write_text(json.dumps({'status':'FAILED','error':repr(e)}));raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
