"""Synthetic branch, calibration-role and no-leakage checks; no paper arrays."""
import ast, copy, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
import numpy as np
import historical_baselines as core
import run_baselines as runner
HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/'config.json').read_text())

def synthetic(n=500,offset=0):
    return dict(query_ids=np.arange(offset,offset+n,dtype=np.int64),action_grid=np.array(CFG['action_grid'],dtype=np.int32),
        build_ids=np.array(CFG['build_ids']),hits=np.full((8,11,n),10,dtype=np.int16),
        ndc=np.broadcast_to(np.arange(1,12,dtype=np.uint64)[None,:,None],(8,11,n)).copy())

class Baselines(unittest.TestCase):
    def setUp(self):
        self.s=synthetic();self.c=synthetic(offset=1000)
    def decide(self,size=500,method='TG1000'):
        return core.simple_decision(self.s['hits'][0],self.s['ndc'][0],self.c['hits'][0],size,method)
    def test_cp_boundary(self):
        self.assertEqual(core.cp(500,500,.025),1.0)
        self.assertAlmostEqual(core.cp(0,500,.025),1-.025**(1/500),places=13)
    def test_cost_minimum_not_budget_minimum(self):
        self.s['ndc'][:,4]=1;self.s['ndc'][:,0]=3
        self.assertEqual(self.decide()['candidate_index'],4)
    def test_cost_tie_grid_order(self):
        self.s['ndc'][:]=1
        self.assertEqual(self.decide()['candidate_index'],0)
    def test_no_selection_eligible_uses_endpoint_candidate(self):
        self.s['hits'][:]=9
        d=self.decide();self.assertEqual(d['eligible_actions'],[]);self.assertEqual(d['candidate_index'],10)
        self.assertEqual(d['decision'],'CANDIDATE')
    def test_candidate_failure_endpoint_fallback(self):
        self.c['hits'][:,0]=9
        d=self.decide();self.assertEqual(d['decision'],'ENDPOINT');self.assertEqual(d['deployed_index'],10)
    def test_endpoint_failure_undeployable(self):
        self.c['hits'][:,10]=9
        d=self.decide();self.assertEqual(d['decision'],'UNDEPLOYABLE');self.assertEqual(d['deployed_index'],-1)
    def test_fixed1600_does_not_select_by_cost(self):
        self.s['hits'][:]=9
        d=self.decide(method='fixed1600');self.assertEqual(d['candidate_index'],9);self.assertEqual(d['selection_n'],0)
    def test_tg500_is_nested_first_250(self):
        self.s['hits'][:,:,250:]=9;self.c['hits'][:,:,250:]=9
        small=self.decide(250,'TG500');large=self.decide()
        self.assertEqual(small['decision'],'CANDIDATE');self.assertEqual(small['selection_n'],250)
        self.assertEqual(large['decision'],'UNDEPLOYABLE');self.assertEqual(large['selection_n'],500)
    def test_all_targets_methods_order(self):
        rows=runner.decisions(self.s,self.c,'sift-1m-heldout',CFG,core,np)
        self.assertEqual(len(rows),32);self.assertEqual([r['method'] for r in rows[:4]],CFG['methods'])
        self.assertEqual(rows[0]['decision'],'REFERENCE')
    def test_overlap_reject(self):
        self.c['query_ids']=self.s['query_ids'].copy()
        with self.assertRaisesRegex(ValueError,'overlap'):runner.decisions(self.s,self.c,'sift-1m-heldout',CFG,core,np)
    def test_bad_grid_reject(self):
        self.s['action_grid']=self.s['action_grid'][::-1]
        with self.assertRaisesRegex(ValueError,'order'):runner.validate_array(self.s,'target_selection',CFG,np)
    def test_bad_response_reject(self):
        self.s['hits'][0,0,0]=11
        with self.assertRaisesRegex(ValueError,'range'):runner.validate_array(self.s,'target_selection',CFG,np)
    def test_undeployable_evaluation_no_fake_action(self):
        self.c['hits'][:,10]=9
        rows=runner.decisions(self.s,self.c,'sift-1m-heldout',CFG,core,np)
        result=runner.evaluate(synthetic(1000,2000),rows,'sift-1m-heldout',CFG,np)
        self.assertIsNone(result[1]['mean_ndc']);self.assertIsNone(result[1]['raw_risk']);self.assertIsNone(result[1]['action'])
        self.assertEqual(result[0]['action'],2400)
    def test_raw_failure_evaluation(self):
        rows=runner.decisions(self.s,self.c,'sift-1m-heldout',CFG,core,np);e=synthetic(1000,2000)
        e['hits'][0,0,0]=9
        out=runner.evaluate(e,rows,'sift-1m-heldout',CFG,np)
        self.assertEqual(out[2]['raw_failures'],1);self.assertEqual(out[2]['raw_risk'],.001)
    def test_expected_reference_identity_and_count(self):
        p=HERE/'expected_decisions.json';self.assertEqual(runner.digest(p),CFG['expected_decisions_sha256'])
        rows=json.loads(p.read_text());self.assertEqual(len(rows),64);self.assertNotIn('TCP',{r['method'] for r in rows})
    def test_source_identity(self):
        self.assertEqual(runner.digest(HERE/'historical_baselines.py'),CFG['core_sha256'])
    def test_invalid_lock_before_evaluation(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):runner.validated_lock(Path(d),None,CFG,[],None)
    def test_cli_lock_before_evaluation_loading(self):
        text=(HERE/'run_baselines.py').read_text();ast.parse(text)
        self.assertLess(text.index('lock=validated_lock('),text.index('with np.load('))
        self.assertIn("Lock cannot accept evaluation inputs",text)
        self.assertIn("Evaluation cannot change calibration",text)

if __name__=='__main__':unittest.main(verbosity=2)
