"""Explicit new E1a/E1b membership and graph stages, with separate frozen recipes."""
import argparse,hashlib,importlib.util,json,os,platform,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def pin(p,h):
    if sha(p)!=h:raise ValueError('Pinned input differs: '+Path(p).name)
def load(p,name,h):
    pin(p,h);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def docs(cfg):
    roles={'datasets':[{k:v for k,v in row.items() if k in ('name','source_sha256','train_shape','roles')} for row in cfg['datasets'].values()]}
    exclusions={'datasets':[{'name':row['name'],'excluded_index_row_ids':row['excluded_index_row_ids']} for row in cfg['datasets'].values()]}
    return roles,exclusions
def make_memberships(core,cfg):
    roles,exclusions=docs(cfg);candidate=core.candidate_roles(roles,exclusions,cfg['e1b_specs'],cfg['role_counts']);arrays={}
    names=[r[0] for r in cfg['role_counts']]
    for prefix,row in cfg['datasets'].items():
        new,_=core.repair_one(roles,exclusions,candidate,cfg['content_evidence'],row['name'],prefix,cfg['e1b_counts'][prefix],names)
        arrays.update(new)
    return candidate,arrays
def e1a_members(row,np):
    heldout=np.concatenate([np.asarray(ids,dtype=np.int64) for ids in row['roles'].values()]);excluded=np.asarray(row['excluded_index_row_ids'],dtype=np.int64)
    if len(heldout)!=2500 or np.unique(heldout).size!=2500 or np.intersect1d(heldout,excluded).size:raise ValueError('Role/exclusion identity')
    keep=np.ones(row['train_shape'][0],dtype=bool);keep[heldout]=False;keep[excluded]=False
    raw=np.flatnonzero(keep).astype(np.int64)
    if len(raw)!=row['effective_base_count']:raise ValueError('Effective base size')
    return heldout,excluded,raw
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('memberships','graph'))
    p.add_argument('--input-adapter',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--outstanding-growth-bytes',type=int,required=True);p.add_argument('--authorize-new-stage',action='store_true')
    p.add_argument('--family',choices=('e1a','e1b'));p.add_argument('--dataset',choices=('sift','arxiv'))
    p.add_argument('--source',type=Path);p.add_argument('--graph-adapter',type=Path);p.add_argument('--memberships',type=Path)
    p.add_argument('--seed',type=int,choices=(13,83,197,2029));p.add_argument('--history',choices=('random','norm_ascending'))
    p.add_argument('--state',choices=('initial','refreshed'));a=p.parse_args()
    if not a.authorize_new_stage:p.error('Explicit new-stage opt-in required')
    if a.phase=='graph' and not all((a.family,a.dataset,a.source,a.graph_adapter,a.seed,a.history)):p.error('Graph bindings required')
    if a.family=='e1b' and not (a.state and a.memberships):p.error('E1b needs frozen memberships and state')
    if a.family=='e1a' and (a.state or a.memberships):p.error('E1a does not use E1b state/membership')
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11) or sys.flags.optimize:raise ValueError('Linux x86_64 Python3.11 required')
    if 2 not in os.sched_getaffinity(0):raise ValueError('CPU2 unavailable')
    os.sched_setaffinity(0,{2})
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    cfg=json.loads((HERE/'config.json').read_text());core=load(HERE/'historical_core.py','transfer_core',cfg['core_sha256'])
    adapter=load(a.input_adapter/'prepare_inputs.py','transfer_resources',cfg['dependencies']['input_adapter'])
    plan=dict(cfg['resource_plan'])
    if a.phase=='memberships':plan.update(address_space_bytes=4*1024**3,file_size_bytes=128*1024**2,expected_rss_bytes=2*1024**3,max_output_growth_bytes=128*1024**2,cpu_seconds=300,wall_seconds=600)
    sources={'config':HERE/'config.json'}
    if a.source:sources['source']=a.source
    out,telemetry=adapter.preflight({'python_minor':[3,11],'resource_plan':plan},a.output,sources,a.outstanding_growth_bytes)
    import resource,signal,numpy as np
    if np.__version__!='1.26.4':raise ValueError('Pinned NumPy1.26.4 required')
    for kind,cap in ((resource.RLIMIT_AS,plan['address_space_bytes']),(resource.RLIMIT_FSIZE,plan['file_size_bytes']),(resource.RLIMIT_CPU,plan['cpu_seconds']),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    out.mkdir(mode=0o700);adapter.write_json(out/'start.json',{'phase':a.phase,'family':a.family,'resources':telemetry,'config_sha256':sha(HERE/'config.json'),'entry_sha256':sha(Path(__file__)),'new_run_not_historical_receipt':True})
    def timeout(signum,frame):raise TimeoutError('Stage wall bound')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(plan['wall_seconds'])
    try:
        if a.phase=='memberships':
            candidate,members=make_memberships(core,cfg)
            for name,data,key in [('candidate_ids.npz',candidate,'e1b_candidate_sha256'),('final_membership_ids.npz',members,'e1b_membership_sha256')]:
                with (out/name).open('xb') as f:np.savez_compressed(f,**data)
                pin(out/name,cfg[key])
            record={'status':'NEW_E1B_MEMBERSHIPS_MATCH_FROZEN_BYTES','candidate_sha256':cfg['e1b_candidate_sha256'],'membership_sha256':cfg['e1b_membership_sha256'],'ANN_runs':0,
                'content_evidence':'Reuses frozen train-only counterpart IDs; content audit is not rerun'}
        else:
            pin(a.graph_adapter/'config.json',cfg['dependencies']['graph_config'])
            graph_adapter=load(a.graph_adapter/'build_graph.py','transfer_native',cfg['dependencies']['graph_adapter'])
            hnswlib,native=graph_adapter.installed_source(json.loads((a.graph_adapter/'config.json').read_text()))
            import h5py
            if h5py.__version__!='3.11.0':raise ValueError('Pinned h5py required')
            row=cfg['datasets'][a.dataset];pin(a.source,row['source_sha256'])
            with h5py.File(a.source,'r') as f:
                train=f['train']
                if list(train.shape)!=row['train_shape'] or str(train.dtype)!='float32':raise ValueError('Raw train shape/bits')
                vectors=np.ascontiguousarray(train[:],dtype=np.float32)
            pair=row['name']+f'_seed{a.seed}_'+a.history;index=out/'index.bin'
            if a.family=='e1a':
                heldout,excluded,members=e1a_members(row,np)
                args=SimpleNamespace(dataset=row['name'],seed=a.seed,history=a.history)
                core.build_e1a(vectors,heldout,excluded,len(members),args,{'implementation':cfg['e1a_implementation']},index,pair,hnswlib)
                pinrow=next(r for r in cfg['e1a_graphs'] if (r['dataset'],r['seed'],r['history'])==(row['name'],a.seed,a.history))
                historical_provenance=pinrow['evidence']
            else:
                done=json.loads((a.memberships/'completed.json').read_text())
                if (a.memberships/'failure.json').exists() or done['status']!='NEW_E1B_MEMBERSHIPS_MATCH_FROZEN_BYTES':raise ValueError('New E1b membership stage required')
                pin(a.memberships/'final_membership_ids.npz',cfg['e1b_membership_sha256'])
                with np.load(a.memberships/'final_membership_ids.npz',allow_pickle=False) as d:
                    initial=d[a.dataset+'_initial_member_ids'];refreshed=d[a.dataset+'_refreshed_member_ids'];members=(initial if a.state=='initial' else refreshed).copy();union=np.union1d(initial,refreshed)
                if len(members)!=cfg['e1b_counts'][a.dataset] or len(union)!=len(members)+cfg['e1b_turnover'][a.dataset]:raise ValueError('State/union count')
                args=SimpleNamespace(seed=a.seed,history=a.history,state=a.state)
                # Original core creates its graph directory; keep it distinct from receipts.
                core.build_e1b(vectors,union,members,len(members),args,row,a.dataset,out/'graph',pair,hnswlib)
                index=out/'graph/index.bin';pinrow=cfg['e1b_graphs'][pair][a.state];historical_provenance='MATCHED_PAIRED_REBUILD'
            pin(index,pinrow['index_sha256'])
            if index.stat().st_size!=pinrow['index_bytes']:raise ValueError('Serialized graph size')
            check=hnswlib.Index(space='l2' if a.dataset=='sift' else 'ip',dim=row['train_shape'][1]);check.load_index(str(index));np.testing.assert_array_equal(np.sort(check.get_ids_list()),members)
            record={'status':'NEW_TRANSFER_GRAPH_MATCHES_FROZEN_BYTES','family':a.family,'dataset':a.dataset,'pair':pair,'state':a.state,
                'index_relative_path':str(index.relative_to(out)),'index_sha256':sha(index),'bytes':index.stat().st_size,'native':native,
                'historical_provenance':historical_provenance,'new_build_does_not_recreate_pilot_design_history':True,
                'query_outcomes_read':False,'query_roles_selected_for_search':False,'full_train_read_including_heldout_rows_before_filtering':True}
        adapter.write_json(out/'completed.json',record)
    except BaseException as e:adapter.write_json(out/'failure.json',{'status':'FAILED_STOP_DEPENDENT_WORK_NO_RETRY','error':repr(e)});raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
