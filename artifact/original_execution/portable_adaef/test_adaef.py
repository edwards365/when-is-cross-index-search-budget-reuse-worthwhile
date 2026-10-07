"""Small synthetic checks; no archived data, ANN builds or replay execution."""
import json,tempfile,unittest
from pathlib import Path
import numpy as np
import run_adaef as r
import run_native_controls as nc
import prepare_dependencies as pd
HERE=Path(__file__).resolve().parent
class Synthetic(unittest.TestCase):
    def test_graph_dependency_pins_before_native_compile(self):
        c=r.conf();graphs=HERE.parent/'portable_graphs'
        self.assertEqual(c['graph_adapter_sha256'],r.sha(graphs/'build_graph.py'))
        self.assertEqual(c['graph_config_sha256'],r.sha(graphs/'config.json'))
        g=json.loads((graphs/'config.json').read_text())
        self.assertEqual(g['core_sha256'],r.sha(graphs/'historical_graph.py'))
        self.assertEqual(g['core_sha256'],'62f37c5906c87bcdd9d0b95590341ea2b4ab0951bec2ad53d83432ccdec94c8c')
    def test_pins_and_panel(self):
        c=r.conf();self.assertEqual(len(c['states']),8)
        self.assertEqual({(x['seed'],x['history']) for x in c['states']},{(s,h) for s in (13,83,197,2029) for h in ('random','norm_ascending')})
    def test_native_features(self):
        text=(HERE/'e2_adaef_native.cpp').read_text()
        for marker in ('statistics_length = 1025','quantile_step = 0.001f','ef_construction = 500','ef_upper_bound = 2400','hnswdis::EfAdapter','hnswdis::Sketch','adaptiveSearchKnn','init_estimator("cd"'):self.assertIn(marker,text)
        self.assertNotIn('sklearn',text)
    def test_membership(self):
        row,held,keep,ids=r.members(np)
        self.assertEqual(len(ids),1342143);self.assertEqual(len(held),2500);self.assertEqual(len(set(held)),2500)
        self.assertFalse(np.intersect1d(ids,held).size)
    def test_cp_source_function(self):
        c=r.conf();m=r.module(HERE/'selection_core.py',c['pins']['selection_core.py'],'test_selection')
        self.assertLess(m.cp_ucb(0),.05);self.assertEqual(m.cp_ucb(500),1.)
        with self.assertRaises(ValueError):m.cp_ucb(501)
    def test_selection_tie(self):
        arms={x:{'screen_eligible':True,'mean_native_distance_calls':10} for x in ('transferred','target_native','endpoint')}
        self.assertEqual(r.choose(arms),('transferred',False));arms['transferred']['screen_eligible']=False
        self.assertEqual(r.choose(arms),('target_native',False))
    def test_selection_cost_and_fallback(self):
        arms={x:{'screen_eligible':True,'mean_native_distance_calls':v} for x,v in [('transferred',20),('target_native',30),('endpoint',10)]}
        self.assertEqual(r.choose(arms),('endpoint',False))
        for x in arms.values():x['screen_eligible']=False
        self.assertEqual(r.choose(arms),('endpoint',True))
    def test_role_gate_before_io(self):
        with self.assertRaises(KeyError):r.previous({'phase':'evaluation'})
        self.assertIsNone(r.previous({'phase':'source'}))
    def test_receipt_binding(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'payload').write_bytes(b'1');obj={'stage':'base','config_sha256':r.sha(HERE/'config.json'),'entry_sha256':r.sha(HERE/'run_adaef.py'),'outputs':{'payload':r.sha(p/'payload')}}
            r.write(p/'completed.json',obj);ref={'directory':str(p),'sha256':r.sha(p/'completed.json')}
            self.assertEqual(r.done(ref,'base')[1]['stage'],'base');(p/'payload').write_bytes(b'2')
            with self.assertRaises(ValueError):r.done(ref,'base')
    def test_tiny_source_changes_shapes_only(self):
        original=(HERE/'e2_adaef_native.cpp').read_text();tiny=nc.tiny_source(original)
        self.assertIn('expected_base = 2048;',tiny);self.assertIn('dim = 16;',tiny)
        for x in ('statistics_length = 1025','quantile_step = 0.001f','ef_construction = 500','ef_upper_bound = 2400'):self.assertIn(x,tiny)
        with self.assertRaises(ValueError):nc.tiny_source('wrong source')
    def test_tiny_fixture_no_formal_test(self):
        import h5py
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'toy.h5';ids,truth=nc.fixture(p)
            with h5py.File(p) as f:
                self.assertNotIn('test',f);self.assertEqual(f['train'].shape,(2048,16));self.assertEqual(f['source_design_queries'].shape,(32,16))
                self.assertTrue(np.isin(truth,ids).all())
    def test_dependency_capture(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);e=p/'Eigen/src/Core/util';e.mkdir(parents=True);(e/'Macros.h').write_text('#define EIGEN_WORLD_VERSION 3\n#define EIGEN_MAJOR_VERSION 4\n#define EIGEN_MINOR_VERSION 0\n');b=p/'boost';b.mkdir();(b/'version.hpp').write_text('#define BOOST_VERSION 108300\n')
            d=pd.record(p,p);self.assertEqual(d['eigen_version'],'3.4.0');self.assertEqual(d['boost_version'],'1.83.0')
if __name__=='__main__':unittest.main()
