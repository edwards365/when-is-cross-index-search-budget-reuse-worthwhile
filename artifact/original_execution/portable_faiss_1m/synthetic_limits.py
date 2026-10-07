"""Own tiny-fixture resource contract; not a production resource-gate bypass."""
import os,platform,signal,sys
def install():
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11):raise ValueError('Synthetic native checks require Linux/Python3.11')
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    allowed=os.sched_getaffinity(0);cpu=min(allowed);os.sched_setaffinity(0,{cpu})
    import resource
    for k,cap in ((resource.RLIMIT_AS,4*1024**3),(resource.RLIMIT_FSIZE,128*1024**2),(resource.RLIMIT_CPU,180),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(k,(cap,cap))
    def timeout(s,f):raise TimeoutError('240-second tiny native contract')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(240)
    return {'affinity':[cpu],'address_space_bytes':4*1024**3,'single_file_bytes':128*1024**2,'cpu_seconds':180,'wall_seconds':240,'aggregate_output_bytes':128*1024**2}
def finish(out):
    total=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    if total>128*1024**2:raise ValueError('Synthetic aggregate output bound')
    signal.alarm(0);return total
