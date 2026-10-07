"""Tiny new synthetic fixtures; no saved experiment is rerun."""
import ast,contextlib,hashlib,importlib.util,io,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import h5py
HERE=Path(__file__).resolve().parent
if sys.platform=='win32':
    sys.modules.setdefault('resource',types.SimpleNamespace(RUSAGE_SELF=0,getrusage=lambda _:types.SimpleNamespace(ru_maxrss=0)))
spec=importlib.util.spec_from_file_location('operational_core',HERE/'operational_core.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
def put(p,value):p.write_text(json.dumps(value));return p
class Operational(unittest.TestCase):
    def test_operational_array_bridge_accepts_only_new_complete_receipts(self):
        sys.path.insert(0,str(HERE))
        import materialize_operational as bridge
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);profiles=root/'profiles';profiles.mkdir();(profiles/'ops').mkdir();(profiles/'data').mkdir();truth=root/'truth';truth.mkdir();prepared=root/'prepared';prepared.mkdir()
            put(prepared/'completed.json',{'status':'synthetic'});(truth/'sift_source_design.npz').write_bytes(b'synthetic truth');(profiles/'data/queries.qbin').write_bytes(b'synthetic query')
            bids=['g0','g1'];spec={'truth_sha256':core.sha(truth/'sift_source_design.npz'),'qbin_sha256':core.sha(profiles/'data/queries.qbin'),'profiles':{}}
            for b in bids:
                f=profiles/'data'/(b+'.csv');f.write_bytes(b'synthetic csv');spec['profiles'][b]={'sha256':core.sha(f),'bytes':f.stat().st_size}
            pc={'datasets':{'sift':{'name':'synthetic','roles':{'source_design':spec}}},'build_ids':bids}
            r={'status':'NATIVE_PROFILES_COMPLETE_AUDIT_PENDING','dataset':'synthetic','role':'source_design','role_receipt_sha256':core.sha(prepared/'completed.json'),'truth_sha256':spec['truth_sha256'],'profiles':[{'build':b,'actual_exit_code':0} for b in bids]}
            final=put(profiles/'ops/final.json',r);put(profiles/'completed.json',{'status':'NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE','kind':'profiles','measured':{'record_sha256':core.sha(final)}});put(profiles/'start.json',{'config_sha256':core.sha(HERE/'operational_config.json')})
            self.assertEqual(bridge.validate_receipts(profiles,'sift','source_design',truth,prepared,pc),r)
            put(profiles/'failure.json',{'status':'failed'})
            with self.assertRaises(ValueError):bridge.validate_receipts(profiles,'sift','source_design',truth,prepared,pc)
    def test_exact_timing_boundary_start(self):
        tree=ast.parse((HERE/'operational_core.py').read_text())
        for name,clock in [('role_firewall','monotonic'),('profiles','perf_counter_ns'),('certification','perf_counter_ns')]:
            fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(fn.body[0].value.func.attr,clock)
        cfg=json.loads((HERE/'operational_config.json').read_text())
        self.assertEqual(hashlib.sha256((HERE/'operational_core.py').read_bytes()).hexdigest(),cfg['core_sha256'])
    def test_role_firewall_full_partition_tiny_vectors(self):
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);out=root/'data';out.mkdir();ops=root/'ops';ops.mkdir();roles={'datasets':[]};ex={'datasets':[]};arrays={}
            counts=dict(zip(core.ROLE_NAMES,[500,500,500,1000]));start=0;old={};new={}
            for role,n in counts.items():old[role]=list(range(start,start+n));new[role]=np.arange(2500+start,2500+start+n);start+=n
            for j,(name,prefix) in enumerate(core.DATASETS):
                source=root/(prefix+'.h5')
                with h5py.File(source,'w') as f:f['train']=np.random.default_rng(j).normal(size=(10020,4)).astype('f4')
                roles['datasets'].append(dict(name=name,relative_path=source.name,source_sha256=core.sha(source),train_shape=[10020,4],roles=old))
                ex['datasets'].append(dict(name=name,excluded_index_row_ids=[]))
                arrays.update({prefix+'_'+r+'_ids':v for r,v in new.items()})
            candidate=root/'candidate.npz';np.savez_compressed(candidate,**arrays)
            config={'seed':2026093001,'role_counts':counts,'forbidden_hdf5_datasets':['test','neighbors','distances']}
            result=core.role_firewall(root,put(root/'config.json',config),config,put(root/'roles.json',roles),candidate,roles,ex,out,ops)
            self.assertTrue(result['status'].startswith('PASS_'));self.assertGreaterEqual(result['wall_seconds'],0)
            self.assertEqual([r['effective_base_count'] for r in result['datasets']],[2520,2520])
            with np.load(out/'membership.npz') as a:
                for _,prefix in core.DATASETS:self.assertEqual(len(set(np.concatenate([a[prefix+'_'+r+'_ids'] for r in core.ROLE_NAMES]))),2500)
    def profile_fixture(self,root,failure=False):
        source=root/'source.h5'
        with h5py.File(source,'w') as f:f['train']=np.arange(600*4,dtype='f4').reshape(600,4)
        folder=root/'data';folder.mkdir();ops=root/'ops';ops.mkdir();graph=root/'index';graph.write_bytes(b'tiny mock graph')
        bids=['g'+str(i) for i in range(8)];graphs={}
        for b in bids:
            rp=put(root/(b+'.json'),dict(status='BUILT_NO_QUERY_OUTCOME_ACCESSED',effective_base_count=32,index_path=str(graph),index_sha256=core.sha(graph)))
            graphs[b]={'receipt_path':str(rp),'receipt_sha256':core.sha(rp)}
        calls=[]
        def run(argv,**kwargs):
            calls.append(argv);self.assertFalse(kwargs['check']);self.assertEqual(kwargs['timeout'],3600)
            Path(argv[-1]).write_text('synthetic response\n');return types.SimpleNamespace(returncode=3 if failure else 0)
        record={'profiles':[]}
        args=(source,np.arange(500),{'train_shape':[600,4]},folder,ops,record,{'build_ids':bids},{'graphs':graphs,'base_count':32},{'action_grid':[10,20,40,80,120,160,240,400,800,1200,1600]},{'wall_seconds_per_graph':3600},Path('fakebinary'),'l2',root,types.SimpleNamespace(dataset='synthetic',role='source_design'),types.SimpleNamespace(run=run))
        return args,calls,record
    def test_profile_includes_export_and_all_eight_waits(self):
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            args,calls,_=self.profile_fixture(Path(t));r=core.profiles(*args)
            self.assertEqual(len(calls),8);self.assertEqual(len(r['profiles']),8)
            self.assertGreater(r['whole_unit_ns'],r['query_read_ns']+r['query_export_fsync_ns'])
            self.assertEqual((Path(t)/'data/queries.qbin').read_bytes()[:8],b'E1AQ0001')
    def test_profile_failure_keeps_true_exit_and_final(self):
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            args,calls,r=self.profile_fixture(Path(t),True)
            with self.assertRaises(RuntimeError):core.profiles(*args)
            self.assertEqual(len(calls),1);self.assertEqual(r['profiles'][0]['actual_exit_code'],3)
            self.assertEqual(json.loads((Path(t)/'ops/final.json').read_text())['status'],'FAILED_STOP_DEPENDENT_POLICY')
    def test_certification_loads_only_qualification_inside_clock(self):
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);ops=root/'ops';ops.mkdir();grid=list(range(11));bids=['g'+str(i) for i in range(8)];audit={'rows':[]};events=[]
            for j,(name,prefix) in enumerate(core.DATASETS):
                hits=np.full((8,11,500),10,dtype='i2')
                if j:hits[0,-1,:100]=0
                path=root/(prefix+'.npz');np.savez_compressed(path,query_ids=np.arange(500),hits=hits,ndc=np.ones(hits.shape,dtype='u8'),action_grid=grid,build_ids=bids)
                audit['rows'].append(dict(dataset=name,role='target_certification',array_path=str(path),array_sha256=core.sha(path)))
            old=core.load_role
            def clock():events.append('clock');return len(events)*100
            def read(*a):events.append('array');self.assertEqual(a[2],'target_certification');return old(*a)
            policy={'datasets':[n for n,_ in core.DATASETS],'risk_limit':.05}
            with patch.object(core.time,'perf_counter_ns',clock),patch.object(core,'load_role',read):
                r=core.certification(ops,types.SimpleNamespace(phase='certify'),policy,audit,grid,bids,put(root/'config.json',{}),put(root/'audit.json',audit),{})
            self.assertEqual(events,['clock','array','array','clock']);self.assertEqual(len(r['rows']),16)
            self.assertEqual(r['rows'][0]['decision'],'TCP');self.assertEqual(r['rows'][8]['decision'],'UNDEPLOYABLE')
            self.assertTrue((ops/'certification_decision_lock.json').exists())
if __name__=='__main__':unittest.main()
