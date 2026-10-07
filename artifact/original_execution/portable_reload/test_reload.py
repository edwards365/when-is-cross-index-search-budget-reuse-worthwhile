"""Synthetic reload protocol tests; no original graph is opened."""
import json,os,platform,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import run_reload as e
CFG=json.loads((e.HERE/'config.json').read_text());C=e.load(e.HERE/'historical_reload.py','reload_core',CFG['core_sha256'])
class Tests(unittest.TestCase):
    def test_graph_dependency_pins_before_native_load(self):
        import hashlib
        graphs=e.HERE.parent/'portable_graphs'
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertEqual(CFG['graph_adapter_sha256'],digest(graphs/'build_graph.py'))
        self.assertEqual(CFG['graph_config_sha256'],digest(graphs/'config.json'))
        graph=json.loads((graphs/'config.json').read_text())
        self.assertEqual(graph['core_sha256'],digest(graphs/'historical_graph.py'))
    def test_clock_boundary(self):
        events=[]
        class Graph:
            def __init__(self,**kw):events.append(('init',kw))
            def load_index(self,*args,**kw):events.append(('load',args,kw))
            def set_num_threads(self,n):events.append(('threads',n))
            def get_current_count(self):return 32
        def clock():events.append(('clock',));return len(events)*100
        ns,count=C.measure(Path('tiny.bin'),'ip',4,32,SimpleNamespace(Index=Graph),SimpleNamespace(perf_counter_ns=clock))
        self.assertEqual([x[0] for x in events],['clock','init','load','threads','clock']);self.assertEqual(count,32);self.assertEqual(ns,400)
    def test_wrong_loaded_count(self):
        class Graph:
            def __init__(self,**kw):pass
            def load_index(self,*args,**kw):pass
            def set_num_threads(self,n):pass
            def get_current_count(self):return 31
        with self.assertRaises(ValueError):C.measure(Path('x'),'l2',4,32,SimpleNamespace(Index=Graph),SimpleNamespace(perf_counter_ns=lambda:1))
    def rows(self):return [{'status':'NEW_FRESH_PROCESS_RELOAD_COMPLETE','build':'a','rep':r,'index_sha256':'tiny','load_index_ns':n} for r,n in enumerate([100,9,25])]
    def test_median_three(self):self.assertEqual(e.summarize(self.rows(),['a']),{'a':25})
    def test_missing_rep(self):
        with self.assertRaises(ValueError):e.summarize(self.rows()[:2],['a'])
    def test_duplicate_rep(self):
        rows=self.rows();rows[2]['rep']=1
        with self.assertRaises(ValueError):e.summarize(rows,['a'])
    def test_mixed_graph(self):
        rows=self.rows();rows[2]['index_sha256']='other'
        with self.assertRaises(ValueError):e.summarize(rows,['a'])
    def test_nonpositive_duration(self):
        rows=self.rows();rows[2]['load_index_ns']=0
        with self.assertRaises(ValueError):e.summarize(rows,['a'])
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Pinned native build on Linux3.11 only')
    def test_native_separate_process_no_search(self):
        import hnswlib,numpy as np
        rng=np.random.default_rng(727);vectors=rng.normal(size=(32,4)).astype('f4')
        with tempfile.TemporaryDirectory() as temp:
            for metric in ('l2','ip'):
                path=Path(temp)/(metric+'.bin');g=hnswlib.Index(space=metric,dim=4);g.init_index(max_elements=32,ef_construction=100,M=16,random_seed=13);g.set_num_threads(1);g.add_items(vectors,np.arange(32));g.save_index(str(path));del g
                code='import historical_reload as c,hnswlib,time,sys,json;from pathlib import Path;print(json.dumps(c.measure(Path(sys.argv[1]),sys.argv[2],4,32,hnswlib,time)))'
                env=dict(os.environ,PYTHONPATH=str(e.HERE),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
                r=subprocess.run([sys.executable,'-c',code,str(path),metric],capture_output=True,text=True,env=env,timeout=15)
                self.assertEqual(r.returncode,0,r.stderr);ns,count=json.loads(r.stdout);self.assertGreater(ns,0);self.assertEqual(count,32)
if __name__=='__main__':unittest.main()
