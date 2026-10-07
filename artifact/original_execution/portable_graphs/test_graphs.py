"""Synthetic 64-vector graph tests only, no original data or experiment rerun."""
import contextlib,importlib.util,io,json,platform,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import h5py
import build_graph as entry
CFG=json.loads((entry.HERE/'config.json').read_text())
CORE=entry.load(entry.HERE/'historical_graph.py','graph_test_core',CFG['core_sha256'])

class Tests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_core_identity(self):self.assertEqual(entry.digest(entry.HERE/'historical_graph.py'),CFG['core_sha256'])
    def test_no_query_search_in_core(self):
        s=(entry.HERE/'historical_graph.py').read_text();self.assertNotIn('knn_query',s);self.assertNotIn('handle["test"]',s)
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
                self.assertEqual(r['effective_base_count'],60);self.assertEqual(r['index_sha256'],entry.digest(path))
                graph=hnsw.Index(space=metric,dim=4);graph.load_index(str(path));graph.set_num_threads(1);graph.set_ef(2400)
                self.assertEqual(set(graph.get_ids_list()),set(ids));np.testing.assert_array_equal(graph.get_items(ids),data[ids])
                q=data[[0,2,5,9]];labels,scores=graph.knn_query(q,k=10,num_threads=1)
                ref=np.sum((q[:,None,:].astype('f8')-data[ids][None,:,:].astype('f8'))**2,axis=2) if metric=='l2' else q.astype('f8')@data[ids].T.astype('f8')
                pos=np.argsort(ref if metric=='l2' else -ref,axis=1)[:,:10];np.testing.assert_array_equal(labels,ids[pos])
                np.testing.assert_allclose(scores,np.take_along_axis(ref if metric=='l2' else 1-ref,pos,axis=1),atol=2e-5,rtol=2e-5)
if __name__=='__main__':unittest.main()
