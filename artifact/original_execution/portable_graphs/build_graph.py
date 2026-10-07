"""One frozen graph unit, explicit new root; no query outcome or ANN search."""
import argparse,hashlib,importlib.util,json,os,platform,sys
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
def installed_source(cfg):
    import importlib.metadata as md
    d=md.distribution('hnswlib');data=json.loads(d.read_text('direct_url.json') or '{}')
    if d.version!='0.8.0' or data.get('archive_info',{}).get('hashes',{}).get('sha256')!=cfg['source_distribution']['sha256']:
        raise ValueError('Install the exact source URL/hash with --no-build-isolation --no-deps')
    import hnswlib
    spec=Path(hnswlib.__file__).resolve()
    if not spec.is_relative_to(Path(d.locate_file('')).resolve()):raise ValueError('Shadowed hnswlib')
    return hnswlib,{'source_sha256':cfg['source_distribution']['sha256'],'extension_sha256':digest(spec),
                    'historical_extension_identity_claimed':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('input-adapter','prepared','source','output-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--dataset',choices=('sift','arxiv'),required=True);p.add_argument('--seed',type=int,choices=(13,83,197,2029),required=True)
    p.add_argument('--history',choices=('random','norm_ascending'),required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-graph-build',action='store_true');p.add_argument('--measure-operational-unit',action='store_true',help='Use the exact original whole-unit timer boundary; new operational measurement, not formal timing');a=p.parse_args()
    if not a.authorize_graph_build:p.error('Explicit graph build opt-in required')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux x86_64 Python3.11 required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
    cfg=json.loads((HERE/'config.json').read_text());regpath=a.input_adapter/'registry.json'
    if digest(regpath)!=cfg['input_registry_sha256']:raise ValueError('Frozen input registry')
    reg=json.loads(regpath.read_text());start=json.loads((a.prepared/'start.json').read_text());done=json.loads((a.prepared/'completed.json').read_text())
    if (a.prepared/'failure.json').exists() or done['status']!='NEW_ROLE_BASE_QUERY_PREPARATION_COMPLETED':raise ValueError('Input stage incomplete')
    if start['registry_sha256']!=cfg['input_registry_sha256'] or start['adapter_sha256']!=cfg['input_adapter_sha256'] or digest(a.input_adapter/'prepare_inputs.py')!=cfg['input_adapter_sha256']:raise ValueError('Input receipt mismatch')
    # This stage reads role IDs and membership, not query qbins or truth.
    spec=importlib.util.spec_from_file_location('graph_input_adapter',a.input_adapter/'prepare_inputs.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    member=a.prepared/'tcp_fresh_roles_v1/membership.npz'
    if digest(member)!=reg['expected_membership_sha256'] or done['membership_sha256']!=reg['expected_membership_sha256']:raise ValueError('Membership identity')
    row=reg['datasets'][a.dataset];plan=cfg['resource_plan'];stem=a.dataset+f'_seed{a.seed}_'+a.history
    root=a.output_root.parent.resolve(strict=True)/a.output_root.name
    if root.is_symlink():raise ValueError('Output root symlink')
    if root.exists():
        r=json.loads((root/'root.json').read_text())
        if r['config_sha256']!=digest(HERE/'config.json') or any((root/'units').glob('*/failure.json')):raise ValueError('Different or failed graph root')
        exclusive=root/'units'/stem
    else:exclusive=root
    _,snapshot=adapter.preflight({'python_minor':[3,11],'resource_plan':dict(plan,max_output_growth_bytes=plan['max_total_output_growth_bytes'])},exclusive,{'raw':a.source,'membership':member},a.outstanding_growth_bytes)
    import resource,signal,time
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds_per_unit']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    if not root.exists():
        root.mkdir(mode=0o700);(root/'indexes').mkdir();(root/'units').mkdir()
        adapter.write_json(root/'root.json',{'config_sha256':digest(HERE/'config.json'),'purpose':'NEW_FROZEN_GRAPH_REGENERATION'})
    import fcntl
    root_lock=(root/'root.json').open('rb')
    fcntl.flock(root_lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    if any(p.is_dir() and not (p/'completed.json').is_file() for p in (root/'units').iterdir()):raise ValueError('Unfinished/failed graph unit; no new unit permitted')
    unit=root/'units'/stem;unit.mkdir(mode=0o700);index=root/'indexes'/(stem+'.bin')
    if index.exists():raise FileExistsError('Index already exists')
    adapter.write_json(unit/'start.json',{'status':'NEW_GRAPH_STARTED','resources':snapshot,'dataset':a.dataset,'seed':a.seed,'history':a.history,
        'prepared_receipt_sha256':digest(a.prepared/'completed.json'),'adapter_sha256':digest(Path(__file__))})
    def timeout(signum,frame):raise TimeoutError('Graph unit wall cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds_per_unit'])
    try:
        import numpy as np,h5py
        if np.__version__!='1.26.4' or h5py.__version__!='3.11.0':raise ValueError('Pinned libraries')
        hnsw,native=installed_source(cfg)
        input_core=adapter.load_core(reg);roles,allids,base=adapter.partition(reg,row,input_core)
        if digest(a.source)!=row['source_sha256']:raise ValueError('Source SHA')
        n,dim=row['train_shape']
        if a.measure_operational_unit:
            core=load(HERE/'operational_graph.py','operational_graph',cfg['operational_core_sha256'])
            result=core.construct(a.source,[n,dim],set(allids),np.asarray(row['expected_base_exclusions'],dtype=np.int64),len(base),cfg['datasets'][a.dataset]['metric'],a.seed,a.history,index,unit/'operational.json',unit/'operational_failure.json',hnsw,np,h5py,resource)
        else:
            keep=np.zeros(n,dtype=bool);keep[base]=True
            core=load(HERE/'historical_graph.py','historical_graph',cfg['core_sha256'])
            result=core.construct(a.source,n,dim,keep,base,cfg['datasets'][a.dataset]['metric'],a.seed,a.history,index,hnsw,np,h5py)
        expected=cfg['datasets'][a.dataset]['graphs'][f'seed{a.seed}_'+a.history]
        if result['index_sha256']!=expected['sha256'] or result['index_bytes']!=expected['bytes']:raise ValueError('Frozen graph bytes differ; stop, no retry/repinning')
        if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>plan['max_total_output_growth_bytes']:raise ValueError('Graph panel output cap')
        masks=[next(s for s in p.read_text().splitlines() if s.startswith('Cpus_allowed_list:')).split(':')[1].strip() for p in Path('/proc/self/task').glob('*/status')]
        if not masks or set(masks)!={'2'}:raise ValueError('All-thread affinity')
        adapter.write_json(unit/'completed.json',dict(result,status='NEW_GRAPH_MATCHES_FROZEN_BYTES',native=native,thread_masks=masks,
            query_outcomes_accessed=False,not_historical_build_receipt=True,operational_unit_measured=bool(a.measure_operational_unit)))
    except BaseException as e:adapter.write_json(unit/'failure.json',{'status':'FAILED_STOP_NEW_GRAPH_UNITS_AND_PROFILES','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
