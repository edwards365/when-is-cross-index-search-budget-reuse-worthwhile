import csv,hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import h5py
import historical_core as core
from run_transfer import e1a_members

HERE=Path(__file__).resolve().parent
class Index:
    def __init__(self,**kw):self.ids=[];self.vectors=[];self.kw=kw
    def init_index(self,**kw):self.init=kw
    def set_num_threads(self,n):self.threads=n
    def add_items(self,v,ids,num_threads):self.ids.extend(ids.tolist());self.vectors.extend(v.tolist());assert num_threads==1
    def get_current_count(self):return len(self.ids)
    def save_index(self,p):Path(p).write_text(json.dumps(self.ids))
class SearchIndex:
    def __init__(self,**kw):pass
    def load_index(self,p,max_elements):self.count=max_elements
    def get_current_count(self):return self.count
    def set_num_threads(self,n):assert n==1
    def set_ef(self,n):self.ef=n
    def knn_query(self,q,k,num_threads):return np.tile(np.arange(10,dtype=np.int64),(len(q),1)),np.zeros((len(q),10),dtype=np.float32)
class Flat:
    def __init__(self,dim,ip=False):self.blocks=[];self.ntotal=0;self.ip=ip
    def add(self,v):self.blocks.append(v.copy());self.ntotal+=len(v)
    def search(self,q,k):
        b=np.concatenate(self.blocks);score=q@b.T if self.ip else np.sum((q[:,None,:]-b[None,:,:])**2,axis=2)
        pos=np.argsort(-score if self.ip else score,axis=1)[:,:k];return np.take_along_axis(score,pos,axis=1).astype('f4'),pos.astype('i8')
MOCK_FAISS=SimpleNamespace(IndexFlatL2=lambda dim:Flat(dim),IndexFlatIP=lambda dim:Flat(dim,True),omp_set_num_threads=lambda n:None)
class TransferTests(unittest.TestCase):
    def test_graph_crosspins_before_native_load(self):
        cfg=json.loads((HERE/'config.json').read_text());graphs=HERE.parent/'portable_graphs'
        for field,name in [('graph_adapter','build_graph.py'),('graph_config','config.json')]:
            self.assertEqual(cfg['dependencies'][field],hashlib.sha256((graphs/name).read_bytes()).hexdigest())
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def test_core_identity(self):
        cfg=json.loads((HERE/'config.json').read_text());self.assertEqual(hashlib.sha256((HERE/'historical_core.py').read_bytes()).hexdigest(),cfg['core_sha256'])
        self.assertEqual(len(cfg['e1a_graphs']),16);self.assertEqual(sum(map(len,cfg['e1b_graphs'].values())),32)
    def test_e1a_randomstate_order(self):
        v=np.arange(240,dtype=np.float32).reshape(60,4);held=np.array([2,8]);excluded=np.array([10]);ids=np.setdiff1d(np.arange(60),np.r_[held,excluded])
        args=SimpleNamespace(seed=13,history='random',dataset='toy');pr={'implementation':{'metric_by_dataset':{'toy':'l2'},'insertion_batch_rows':8192}}
        g=core.build_e1a(v,held,excluded,len(ids),args,pr,self.root/'a.bin','toy',SimpleNamespace(Index=Index))
        np.testing.assert_array_equal(g.ids,ids[np.random.RandomState(13).permutation(len(ids))])
        self.assertFalse(np.array_equal(g.ids,ids[np.random.default_rng(13).permutation(len(ids))]))
        self.assertEqual(g.init,dict(max_elements=57,M=16,ef_construction=100,random_seed=13))
    def test_e1a_norm_ties_raw_id(self):
        v=np.array([[1,0],[-1,0],[0,1],[0,0],[2,0]],dtype=np.float32)
        args=SimpleNamespace(seed=83,history='norm_ascending',dataset='toy');pr={'implementation':{'metric_by_dataset':{'toy':'ip'},'insertion_batch_rows':8192}}
        g=core.build_e1a(v,np.array([],dtype=int),np.array([],dtype=int),5,args,pr,self.root/'a.bin','toy',SimpleNamespace(Index=Index))
        self.assertEqual(g.ids,[3,0,1,2,4]);self.assertEqual(g.kw['space'],'ip')
    def test_e1b_shared_union_order(self):
        v=np.random.default_rng(99).normal(size=(30,4)).astype('f4');initial=np.arange(20);refreshed=np.arange(10,30);union=np.arange(30)
        for history in ('random','norm_ascending'):
            a=core.source_order(v,union,initial,history,197);b=core.source_order(v,union,refreshed,history,197)
            shared=np.intersect1d(initial,refreshed)
            np.testing.assert_array_equal(a[np.isin(a,shared)],b[np.isin(b,shared)])
            if history=='random':np.testing.assert_array_equal(a,union[np.random.RandomState(197).permutation(30)][np.isin(union[np.random.RandomState(197).permutation(30)],initial)])
    def test_e1b_graph_members_and_parameters(self):
        v=np.arange(80,dtype=np.float32).reshape(20,4);members=np.arange(3,18)
        g=core.build_e1b(v,np.arange(20),members,15,SimpleNamespace(seed=13,history='random',state='initial'),{'train_shape':[20,4]},'sift',self.root/'b','toy',SimpleNamespace(Index=Index))
        self.assertEqual(sorted(g.ids),members.tolist());self.assertEqual(g.threads,1);self.assertEqual(g.kw['space'],'l2')
    def test_candidate_roles_synthetic(self):
        row={'name':'toy','source_sha256':'toy','train_shape':[12000,4],'roles':{'old':list(range(2500))}}
        arrays=core.candidate_roles({'datasets':[row]},{'datasets':[{'name':'toy','excluded_index_row_ids':[]}]},[('toy','toy',991,7000,350,6650)],[('source_design',500),('target_selection',500),('target_certification',500),('target_evaluation',1000)])
        ids=np.concatenate([arrays['toy_'+r+'_ids'] for r in ('source_design','target_selection','target_certification','target_evaluation')])
        self.assertEqual(np.unique(ids).size,2500);self.assertFalse(np.intersect1d(ids,np.arange(2500)).size)
        self.assertEqual(len(arrays['toy_old_only_ids']),350);self.assertEqual(len(arrays['toy_new_only_ids']),350)
    def test_repair_synthetic_neutral_trim(self):
        row={'name':'toy','source_sha256':'toy','train_shape':[20,4],'roles':{'old':[0]}}
        cand={'toy_a_ids':np.array([1]),'toy_b_ids':np.array([2]),'toy_old_only_ids':np.array([3,4,5]),'toy_new_only_ids':np.array([6,7,8])}
        content={'datasets':[{'dataset':'toy','query_query_duplicate_pairs':[],'fresh_query_independence_pass':True,'new_counterpart_exclusion_ids':[3],'new_counterpart_exclusion_count':1}]}
        arrays,rows=core.repair_one({'datasets':[row]},{'datasets':[{'name':'toy','excluded_index_row_ids':[]}]},cand,content,'toy','toy',13,['a','b'])
        self.assertEqual(arrays['toy_neutral_trim_ids'].tolist(),[6]);self.assertEqual(rows[0]['effective_old_only_count'],2)
        self.assertFalse(np.intersect1d(arrays['toy_initial_member_ids'],[0,1,2,3,6,7,8]).size)
    def test_wrong_membership_count_rejected(self):
        with self.assertRaises(ValueError):e1a_members({'roles':{'bad':[1]},'excluded_index_row_ids':[],'train_shape':[10,2],'effective_base_count':9},np)
    def test_unknown_history_rejected(self):
        with self.assertRaises(ValueError):core.source_order(np.zeros((5,2)),np.arange(5),np.arange(5),'tuned',13)
    def fixture(self,n):
        ids=np.arange(32,32+n,dtype=np.int64);v=np.random.default_rng(714).normal(size=(32+n,4)).astype('f4');p=self.root/'train.h5'
        with h5py.File(p,'x') as f:f.create_dataset('train',data=v)
        return p,ids,np.arange(32,dtype=np.int64),{'train_shape':list(v.shape),'name':'sift-1m-heldout','roles':{'source_design':ids.tolist()}}
    def test_seven_truth_core_interfaces(self):
        p,ids,members,row=self.fixture(1000)
        for phase in ('source','selection','certify','evaluate'):
            n=1000 if phase=='evaluate' else 500;q=ids[:n];held=set(map(int,ids));metric='l2';r=dict(row,roles={'source_design':q.tolist()})
            if phase=='source':a=core.truth_e1a_source(r,{'metric':'squared_l2','source_design_query_count':500},32,held,set(),p,8192,MOCK_FAISS,h5py)
            elif phase=='selection':a=core.truth_e1a_selection(r,{r['name']:{'metric':metric,'base_count':32}},SimpleNamespace(dataset=r['name']),q,held,set(),p,MOCK_FAISS,h5py)
            else:a=getattr(core,'truth_e1a_'+phase)(r,metric,32,q,held,set(),p,MOCK_FAISS,h5py)
            self.assertEqual(a['scores'].shape,(n,10));self.assertTrue(np.isin(a['neighbor_raw_ids'],members).all())
            if phase!='selection':
                if phase=='source':b=core.truth_e1b_source(r,metric,32,q,members,p,MOCK_FAISS,h5py)
                else:b=getattr(core,'truth_e1b_'+phase)(r,{'metric':metric,'member_count':32},q,members,p,MOCK_FAISS,h5py)
                for k in a:np.testing.assert_array_equal(a[k],b[k])
    def test_e1a_source_and_e1b_response_interfaces(self):
        p,ids,members,row=self.fixture(1000);lib=SimpleNamespace(Index=SearchIndex);grid=np.asarray(core.GRID,dtype=np.int32);truth=np.tile(np.arange(10),(1000,1))
        a,s=core.e1a_source_response(ids[:500],p,SimpleNamespace(dataset=row['name']),p,{'serialized_count':32},{'action_grid':core.GRID},truth[:500],'synthetic',h5py,lib)
        self.assertEqual(s['selected_source_action'],10);self.assertFalse(a['z_abs'].any())
        a,s=core.source_response(ids[:500],p,row,{'prefix':'sift'},p,{'member_count':32},grid,truth[:500],h5py,lib)
        self.assertEqual(s['selected_source_action'],10)
        a,s=core.cert_response(ids[:500],p,row,{'prefix':'sift'},p,{'member_count':32},10,truth[:500],h5py,lib)
        self.assertEqual(s['decision'],'execute_candidate');self.assertEqual(a['topk'].shape,(2,500,10))
        a,s=core.eval_response(ids,p,row,{'prefix':'sift'},[p,p],[32,32],10,'endpoint_fallback',[truth,truth],h5py,lib)
        self.assertEqual(a['topk'].shape,(2,2,1000,10));self.assertEqual(int(a['executed_arm']),1)
    def test_three_native_equivalence_interfaces(self):
        p,ids,members,row=self.fixture(1000);lib=SimpleNamespace(Index=SearchIndex);truth=np.tile(np.arange(10),(1000,1))
        for phase in ('selection','certify','evaluate'):
            n=1000 if phase=='evaluate' else 500;grid=[10,2400];dest=self.root/(phase+'.csv')
            def run(command,**kw):
                with Path(command[-1]).open('x',newline='') as f:
                    w=csv.writer(f);w.writerow(['query_id','ef','ndc','topk'])
                    for ef in grid:
                        for q in ids[:n]:w.writerow([q,ef,100,';'.join(map(str,range(10)))])
            a,errors=getattr(core,'e1a_'+phase+'_response')(ids[:n],n,p,row['name'],p,{'serialized_count':32},grid,truth[:n],p,p,dest,h5py,lib,SimpleNamespace(run=run),row)
            self.assertEqual(errors,[]);self.assertEqual(a['ndc'].shape,(2,n));self.assertTrue((a['ndc']==100).all())
    def test_selection_and_qualification_policy(self):
        responses={f'seed{s}_{h}':(np.zeros((11,500),bool),np.ones((11,500),dtype=np.uint64)) for s in core.SEEDS for h in core.HISTORIES}
        sources=[{'dataset':'toy','seed':s,'history':h,'selected_source_action':40} for s in core.SEEDS for h in core.HISTORIES]
        a=core.e1a_selection_policy('toy',responses,sources);self.assertEqual(len(a['directed_pair_actions']),56);self.assertEqual(len(a['target_global_actions']),8)
        grid,pairs,g=core.expected_grid('toy','seed13_random',a);self.assertEqual(len(pairs),7)
        z=np.zeros((len(grid),500),bool);ndc=np.ones(z.shape);cp=lambda f:core.cp_upper(f,500,.025)
        good=core.outcome('toy','seed13_random',None,'target_global',10,grid,z,ndc,0,cp(0),cp);self.assertEqual(good['decision'],'ACCEPT')
        bad=core.outcome('toy','seed13_random',None,'target_global',10,grid,z,ndc,500,1,cp);self.assertEqual(bad['decision'],'ABSTAIN')
    def test_prior_lock_before_input_reads(self):
        from run_phase import earlier
        with self.assertRaises((KeyError,ValueError,FileNotFoundError)):earlier({'family':'e1b','phase':'evaluate','prior_panel':str(self.root)}, {})
    def test_mutated_source_decision_rejected(self):
        from run_phase import check_summary
        p=self.root/'response.npz';np.savez_compressed(p,action_grid=np.asarray(core.GRID),z_abs=np.zeros((11,500),bool))
        summary={'selected_source_action':10,'cp_ucb':[core.cp_upper(0,500,.05/11)]*11};check_summary(p,'e1b','source',summary)
        summary['selected_source_action']=20
        with self.assertRaises(ValueError):check_summary(p,'e1b','source',summary)
    def test_mutated_certification_decision_rejected(self):
        from run_phase import check_summary
        p=self.root/'response.npz';np.savez_compressed(p,action_ef=np.asarray([10,2400]),z_abs_candidate=np.ones(500,bool),z_abs_endpoint=np.zeros(500,bool))
        summary={'selected_source_action':10,'decision':'endpoint_fallback','cp_ucb':[1.0,core.cp_upper(0,500,.025)]};check_summary(p,'e1b','certify',summary)
        summary['decision']='execute_candidate'
        with self.assertRaises(ValueError):check_summary(p,'e1b','certify',summary)
    def test_completed_failure_is_not_a_predecessor(self):
        from run_phase import done
        (self.root/'failure.json').write_text('{}')
        with self.assertRaises(ValueError):done(self.root,'PASS',{})
    def test_complete_pin_coverage(self):
        c=json.loads((HERE/'config.json').read_text())
        for family,phases in [('e1a',['source','selection','certify','evaluate']),('e1b',['source','certify','evaluate'])]:
            for phase in phases:self.assertEqual(len(c[family+'_response_pins'][phase]),16)
        self.assertEqual(len(c['e1a_truth_pins']),8);self.assertEqual(len(c['e1b_truth_pins']),10)
if __name__=='__main__':unittest.main()
