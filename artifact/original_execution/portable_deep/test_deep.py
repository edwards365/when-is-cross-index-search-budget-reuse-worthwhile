import ast,csv,json,platform,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import run_deep as entry
HERE=Path(__file__).resolve().parent
class DeepTests(unittest.TestCase):
    def test_pins(self):self.assertEqual(len(entry.config()['expected_graphs']),8)
    def test_roles(self):self.assertEqual(len(entry.role_ids(entry.config())),1500)
    def test_core_bodies(self):
        names={n.name for n in ast.parse((HERE/'historical_core.py').read_text()).body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(names,{'normalize','write_vecs','exact_truth','build_index'})
    def test_safe_import(self):
        tree=ast.parse((HERE/'historical_core.py').read_text())
        self.assertTrue(all(isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)) or isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) for n in tree.body))
    def test_csv_reject_missing(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x.csv';p.write_text('build,query_id,ef,recall,ndc,wall_ns,topk\n')
            with self.assertRaises(ValueError):entry.validate_csv(p,'x',1,[200])
    def test_csv_exact_grid(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x.csv';p.write_text('build,query_id,ef,recall,ndc,wall_ns,topk\nx,0,200,1,10,1,0;1;2;3;4;5;6;7;8;9\n')
            entry.validate_csv(p,'x',1,[200])
            with p.open('a') as f:f.write('x,0,200,1,10,1,0;1;2;3;4;5;6;7;8;9\n')
            with self.assertRaises(ValueError):entry.validate_csv(p,'x',1,[200])
    def test_no_optin(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):entry.execute(SimpleNamespace(authorize_new_execution=False),entry.config())
    def test_test_member_optin(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):entry.execute(SimpleNamespace(authorize_new_execution=True,phase='prepare',authorize_historical_test_member=False),entry.config())
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Pinned native Linux environment')
    def test_tiny_native(self):
        import os,resource
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
        entry.native(entry.config());core=entry.module('historical_core');import hnswlib
        rng=np.random.default_rng(17);base=rng.normal(size=(64,16)).astype(np.float32);q=core.normalize(rng.normal(size=(12,16)).astype(np.float32));truth=core.exact_truth(base,q)
        expected=np.argsort(-(q.astype(np.float64)@core.normalize(base).astype(np.float64).T),axis=1)[:,:10]
        np.testing.assert_array_equal(truth,expected)
        def caps():
            for kind,limit in ((resource.RLIMIT_AS,4<<30),(resource.RLIMIT_FSIZE,16<<20),(resource.RLIMIT_CPU,120),(resource.RLIMIT_CORE,0)):resource.setrlimit(kind,(limit,limit))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);binary=root/'runner'
            subprocess.run(['g++','-std=c++17','-O3','-pthread','-I',str(HERE/'include'),str(HERE/'deep1m_counting_runner.cpp'),'-o',str(binary)],check=True,timeout=120,preexec_fn=caps)
            core.write_vecs(root/'q.fvecs',q,'<f4');core.write_vecs(root/'truth.ivecs',truth,'<i4')
            for history in ('random','norm_ascending'):
                index=root/(history+'.bin');core.build_index(base,3011,history,index)
                out=root/(history+'.csv');subprocess.run([str(binary),str(index),str(root/'q.fvecs'),str(root/'truth.ivecs'),'10,40,1200',history,str(out)],check=True,timeout=30,preexec_fn=caps)
                entry.validate_csv(out,history,12,[10,40,1200]);native=hnswlib.Index(space='cosine',dim=16);native.load_index(str(index));native.set_num_threads(1)
                rows=list(csv.DictReader(out.open()))
                for budget in (10,40,1200):
                    native.set_ef(budget);labels,_=native.knn_query(q,k=10)
                    got=np.asarray([list(map(int,r['topk'].split(';'))) for r in rows if int(r['ef'])==budget]);np.testing.assert_array_equal(got,labels)
                np.testing.assert_array_equal(got,expected)
if __name__=='__main__':unittest.main()
