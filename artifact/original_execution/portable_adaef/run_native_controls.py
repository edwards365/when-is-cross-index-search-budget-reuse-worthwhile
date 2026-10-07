"""Compile official production source and run only a test-size derivative."""
import argparse,json,os,platform,shutil,sys
from pathlib import Path
import run_adaef as r
def tiny_source(original):
    replacements={'constexpr size_t dim = 768;':'constexpr size_t dim = 16;',
      'constexpr size_t expected_base = 1342143;':'constexpr size_t expected_base = 2048;',
      'queries.rows() != 500':'queries.rows() != 32','truth.rows() != 500':'truth.rows() != 32',
      '\\"source_design_queries\\": 500':'\\"source_design_queries\\": 32'}
    for old,new in replacements.items():
        if original.count(old)!=1:raise ValueError('Test-only source shape substitution count: '+old)
        original=original.replace(old,new)
    return original
def fixture(path):
    import numpy as np,h5py
    rng=np.random.default_rng(20261007);base=rng.normal(size=(2048,16)).astype(np.float32);base/=np.linalg.norm(base,axis=1,keepdims=True)
    q=rng.normal(size=(32,16)).astype(np.float32);q/=np.linalg.norm(q,axis=1,keepdims=True)
    rawids=np.arange(2048,dtype=np.int64)*2+1000;truth=rawids[np.argsort(-(q.astype(np.float64)@base.astype(np.float64).T),axis=1,kind='stable')[:,:10]].astype(np.int32)
    with h5py.File(path,'x') as f:
        f.create_dataset('train',data=base);f.create_dataset('raw_ids',data=rawids)
        f.create_dataset('source_design_queries',data=q);f.create_dataset('source_design_truth',data=truth);f.create_dataset('source_design_query_ids',data=np.arange(32,dtype=np.int64)+10000)
        f.create_dataset('order_seed13_random',data=np.random.RandomState(13).permutation(len(base)).astype(np.uint64))
    return rawids,truth
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--dependencies',type=Path,required=True);p.add_argument('--graph-adapter',type=Path,required=True);p.add_argument('--authorize-synthetic-only',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_only:p.error('Explicit synthetic-only authorization required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11):raise ValueError('Linux Python3.11 required')
    out=a.output.resolve()
    if out.exists() or not out.parent.is_dir() or shutil.disk_usage(out.parent).free<2*1024**3:raise ValueError('Exclusive output with2GiBfree required')
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
    import resource
    for kind,cap in ((resource.RLIMIT_AS,8*1024**3),(resource.RLIMIT_FSIZE,256*1024**2),(resource.RLIMIT_CPU,900),(resource.RLIMIT_CORE,0)):
        limits=resource.getrlimit(kind);cap=min([cap]+[v for v in limits if v>=0]);resource.setrlimit(kind,(cap,cap))
    c=r.conf();req=json.loads(a.dependencies.read_text());out.mkdir();prod=out/'production-compile';prod.mkdir();toy=out/'tiny';toy.mkdir()
    try:
        import numpy,scipy,h5py
        if (numpy.__version__,scipy.__version__,h5py.__version__)!=('1.26.4','1.13.1','3.11.0'):raise ValueError('Pinned numerical dependencies')
        production=r.compile_native(req,c,prod)
        testsource=out/'tiny_test_only.cpp';testsource.write_text(tiny_source((r.HERE/'e2_adaef_native.cpp').read_text()))
        testbuild=r.compile_native(req,c,toy,source_override=testsource);fixture(toy/'input.hdf5');exe=toy/'e2_adaef_native'
        waits=[r.run_process([exe,'build-design',toy/'input.hdf5',toy/'index.hnsw',toy/'adapter.bin',toy/'summary.json','13','random'],toy,'design',120)]
        waits.append(r.run_process([exe,'run-role',toy/'input.hdf5','source_design',toy/'index.hnsw',toy/'adapter.bin',toy/'response.csv','32'],toy,'response',120))
        audit=r.audit_response(toy/'response.csv',toy/'input.hdf5',toy/'index.hnsw',a.graph_adapter,c)
        if sum(f.stat().st_size for f in out.rglob('*') if f.is_file())>512*1024**2:raise ValueError('512MiB output postcondition')
        r.write(out/'completed.json',{'status':'TINY_OFFICIAL_ADAEF_NATIVE_PASS_NOT_FULL_PANEL_REPRODUCTION','production_compile':production,'tiny_compile':testbuild,'actual_exit_codes':waits,'audit':audit,'config_sha256':r.sha(r.HERE/'config.json'),'test_entry_sha256':r.sha(Path(__file__)),'base_count':2048,'dimension':16,'source_queries':32,'official_algorithm_parameters_changed':False,'original_data_accessed':False})
    except BaseException as e:r.write(out/'failure.json',{'status':'FAILED_STOP','error':repr(e)});raise
if __name__=='__main__':main()
