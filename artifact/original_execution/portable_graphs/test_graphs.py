"""Synthetic 64-vector graph tests only, no original data or experiment rerun."""
import contextlib,importlib.util,io,json,platform,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import h5py
from unittest.mock import patch
from types import SimpleNamespace
import build_graph as entry
CFG=json.loads((entry.HERE/'config.json').read_text())
CORE=entry.load(entry.HERE/'historical_graph.py','graph_test_core',CFG['core_sha256'])
OP=entry.load(entry.HERE/'operational_graph.py','graph_test_operational',CFG['operational_core_sha256'])

class Tests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_core_identity(self):self.assertEqual(entry.digest(entry.HERE/'historical_graph.py'),CFG['core_sha256'])
    def test_no_query_search_in_core(self):
        s=(entry.HERE/'historical_graph.py').read_text();self.assertNotIn('knn_query',s);self.assertNotIn('handle["test"]',s)
    def test_operational_timer_boundary(self):
        s=(entry.HERE/'operational_graph.py').read_text();self.assertLess(s.index('began = time.perf_counter_ns()'),s.index('keep = np.ones'))
        self.assertLess(s.index('record["index_sha256"]'),s.index('record["whole_unit_ns"]'));self.assertLess(s.index('record["whole_unit_ns"]'),s.index('resource.getrusage'))
        self.assertNotIn('knn_query',s);self.assertEqual(entry.digest(entry.HERE/'operational_graph.py'),CFG['operational_core_sha256'])
    def test_operational_control_without_native(self):
        class FakeGraph:
            def __init__(self,**kw):self.rows=[]
            def init_index(self,**kw):pass
            def set_num_threads(self,n):pass
            def add_items(self,x,ids,**kw):self.rows.extend(zip(ids.tolist(),x.tolist()))
            def get_current_count(self):return len(self.rows)
            def save_index(self,path):Path(path).write_text(json.dumps(self.rows))
        fake=SimpleNamespace(Index=FakeGraph);resource=SimpleNamespace(RUSAGE_SELF=0,getrusage=lambda _:SimpleNamespace(ru_maxrss=123))
        data=np.arange(128,dtype='f4').reshape(32,4)
        with h5py.File(self.p/'tiny.h5','w') as f:f['train']=data
        keep=np.ones(32,bool);keep[[0,2,5,9]]=False;ids=np.flatnonzero(keep).astype(np.int64)
        with contextlib.redirect_stdout(io.StringIO()),patch('os.fsync',lambda fd:None):
            r=OP.construct(self.p/'tiny.h5',[32,4],{0,2},np.array([5,9]),28,'l2',13,'random',self.p/'op.bin',self.p/'op.json',self.p/'fail.json',fake,np,h5py,resource)
            base=CORE.construct(self.p/'tiny.h5',32,4,keep,ids,'l2',13,'random',self.p/'base.bin',fake,np,h5py)
        self.assertEqual(r['index_sha256'],base['index_sha256']);self.assertEqual(r['effective_base_count'],28);self.assertGreater(r['whole_unit_ns'],0);self.assertEqual(r['process_maxrss_kib'],123)
        self.assertEqual(json.loads((self.p/'op.json').read_text())['whole_unit_ns'],r['whole_unit_ns']);self.assertFalse((self.p/'fail.json').exists())
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(ValueError):OP.construct(self.p/'tiny.h5',[32,4],{0,2},np.array([5,9]),29,'l2',13,'random',self.p/'bad.bin',self.p/'bad.json',self.p/'bad_fail.json',fake,np,h5py,resource)
        fail=json.loads((self.p/'bad_fail.json').read_text());self.assertEqual(fail['status'],'FAILED_STOP_NEW_WORK');self.assertGreater(fail['whole_unit_ns'],0)
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Native source build Linux3.11 only')
    def test_native_orders_metrics(self):
        hnsw,provenance=entry.installed_source(CFG)
        self.assertFalse(provenance['historical_extension_identity_claimed'])
        rng=np.random.default_rng(107);data=rng.normal(size=(64,4)).astype('f4')
        keep=np.ones(64,dtype=bool);keep[[0,2,5,9]]=False;ids=np.flatnonzero(keep).astype(np.int64)
        with h5py.File(self.p/'tiny.h5','w') as f:f['train']=data
        for metric in ('l2','ip'):
            for history in ('random','norm_ascending'):
                path=self.p/(metric+'_'+history+'.bin')
                with contextlib.redirect_stdout(io.StringIO()):r=CORE.construct(self.p/'tiny.h5',64,4,keep,ids,metric,13,history,path,hnsw,np,h5py)
                import resource
                op_path=self.p/(metric+'_'+history+'_op.bin')
                with contextlib.redirect_stdout(io.StringIO()):op=OP.construct(self.p/'tiny.h5',[64,4],{0,2},np.array([5,9]),60,metric,13,history,op_path,self.p/(op_path.stem+'.json'),self.p/(op_path.stem+'.failure.json'),hnsw,np,h5py,resource)
                self.assertEqual(op['index_sha256'],r['index_sha256']);self.assertGreater(op['whole_unit_ns'],0)
                self.assertEqual(r['effective_base_count'],60);self.assertEqual(r['index_sha256'],entry.digest(path))
                graph=hnsw.Index(space=metric,dim=4);graph.load_index(str(path));graph.set_num_threads(1);graph.set_ef(2400)
                self.assertEqual(set(graph.get_ids_list()),set(ids));np.testing.assert_array_equal(graph.get_items(ids),data[ids])
                q=data[[0,2,5,9]];labels,scores=graph.knn_query(q,k=10,num_threads=1)
                ref=np.sum((q[:,None,:].astype('f8')-data[ids][None,:,:].astype('f8'))**2,axis=2) if metric=='l2' else q.astype('f8')@data[ids].T.astype('f8')
                pos=np.argsort(ref if metric=='l2' else -ref,axis=1)[:,:10];np.testing.assert_array_equal(labels,ids[pos])
                np.testing.assert_allclose(scores,np.take_along_axis(ref if metric=='l2' else 1-ref,pos,axis=1),atol=2e-5,rtol=2e-5)
if __name__=='__main__':unittest.main()
