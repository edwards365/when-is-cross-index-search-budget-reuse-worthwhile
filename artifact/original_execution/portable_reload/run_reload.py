"""One explicitly selected fresh-process reload; never a cold-cache claim."""
import argparse,hashlib,importlib.util,json,os,platform,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def load(p,name,pin):
    if digest(p)!=pin:raise ValueError('Code identity')
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def graph_input(root,ds,build,cfg):
    name=ds+'_'+build;unit=root/'units'/name;path=root/'indexes'/(name+'.bin')
    r=json.loads((unit/'completed.json').read_text());pin=cfg['datasets'][ds]['graphs'][build]
    if (unit/'failure.json').exists() or r['status']!='NEW_GRAPH_MATCHES_FROZEN_BYTES':raise ValueError('Graph unit not complete')
    if r['index_sha256']!=pin['sha256'] or r['index_bytes']!=pin['bytes'] or r['effective_base_count']!=cfg['datasets'][ds]['expected_base_rows']:raise ValueError('Graph receipt identity')
    if path.stat().st_size!=pin['bytes'] or digest(path)!=pin['sha256']:raise ValueError('Graph bytes')
    return path,r,digest(unit/'completed.json')
def summarize(rows,builds):
    import statistics
    output={}
    if len(rows)!=3*len(builds):raise ValueError('Incomplete reload panel')
    for build in builds:
        selected=[r for r in rows if r['build']==build]
        if len(selected)!=3 or sorted(r['rep'] for r in selected)!=[0,1,2]:raise ValueError('Missing/duplicate repetitions')
        if any(r['status']!='NEW_FRESH_PROCESS_RELOAD_COMPLETE' or r['load_index_ns']<=0 for r in selected):raise ValueError('Invalid reload time')
        if len({r['index_sha256'] for r in selected})!=1:raise ValueError('Mixed graph identity')
        output[build]=statistics.median(r['load_index_ns'] for r in selected)
    return output
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('input-adapter','graph-adapter','graphs','output-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--dataset',choices=('sift','arxiv'),required=True);p.add_argument('--build',required=True);p.add_argument('--rep',type=int,choices=(0,1,2),required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-reload-measurement',action='store_true');a=p.parse_args()
    if not a.authorize_reload_measurement:p.error('Explicit new reload measurement required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux Python3.11 required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    cfg=json.loads((HERE/'config.json').read_text());plan=cfg['resource_plan']
    if a.build not in cfg['datasets'][a.dataset]['graphs']:raise ValueError('Unregistered graph')
    if digest(a.graph_adapter/'config.json')!=cfg['graph_config_sha256']:raise ValueError('Graph configuration')
    gp=load(a.graph_adapter/'build_graph.py','reload_graph_entry',cfg['graph_adapter_sha256'])
    adapter=load(a.input_adapter/'prepare_inputs.py','reload_resources',cfg['input_adapter_sha256'])
    index,receipt,receipt_sha=graph_input(a.graphs,a.dataset,a.build,cfg)
    root=a.output_root.parent.resolve(strict=True)/a.output_root.name
    if root.is_symlink():raise ValueError('Root symlink')
    name=a.dataset+'_'+a.build+'_rep'+str(a.rep)
    _,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},root/name if root.exists() else root,
        {'index':index},a.outstanding_growth_bytes)
    import resource,signal,fcntl
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[v for v in old if v>=0]);resource.setrlimit(kind,(cap,cap))
    if not root.exists():
        root.mkdir(mode=0o700);adapter.write_json(root/'panel.json',{'config_sha256':digest(HERE/'config.json'),'started_monotonic':time.monotonic(),
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
    stream=(root/'panel.json').open('rb');fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);panel=json.loads(stream.read())
    if panel['config_sha256']!=digest(HERE/'config.json') or panel['boot_id']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():raise ValueError('Different/rebooted panel')
    remaining=plan['panel_wall_seconds']-(time.monotonic()-panel['started_monotonic'])
    if remaining<=0:raise TimeoutError('Whole reload panel deadline')
    if any(p.is_dir() and not (p/'completed.json').is_file() for p in root.iterdir()):raise ValueError('Unfinished/failed prior unit')
    out=root/name;out.mkdir(mode=0o700)
    adapter.write_json(out/'start.json',{'status':'NEW_RELOAD_STARTED','resources':snapshot,'config_sha256':digest(HERE/'config.json'),
        'graph_receipt_sha256':receipt_sha,'dataset':a.dataset,'build':a.build,'rep':a.rep})
    def timeout(signum,frame):raise TimeoutError('Reload wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(max(1,int(min(remaining,plan['wall_seconds']))))
    try:
        hnsw,native=gp.installed_source(json.loads((a.graph_adapter/'config.json').read_text()))
        core=load(HERE/'historical_reload.py','new_reload_core',cfg['core_sha256'])
        duration,count=core.measure(index,cfg['datasets'][a.dataset]['metric'],cfg['dimensions'][a.dataset],receipt['effective_base_count'],hnsw,time)
        if duration<=0:raise ValueError('Nonpositive reload duration')
        adapter.write_json(out/'completed.json',{'status':'NEW_FRESH_PROCESS_RELOAD_COMPLETE','dataset':a.dataset,'build':a.build,'rep':a.rep,
            'load_index_ns':duration,'effective_base_count':count,'index_sha256':digest(index),'native':native,
            'cache_boundary':'Unknown OS page-cache state; index hashed before load; not cold-start',
            'query_accesses':0,'historical_costs_replaced':False,'cpu_affinity':sorted(os.sched_getaffinity(0))})
    except BaseException as e:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_NEW_RELOADS','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
