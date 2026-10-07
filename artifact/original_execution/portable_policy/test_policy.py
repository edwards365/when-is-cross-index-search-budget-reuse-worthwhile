"""Generated role arrays only. No stored experiment is analyzed by these tests."""
import json,tempfile,unittest
from pathlib import Path
import numpy as np
import run_policy as entry
CFG=json.loads((entry.HERE/'config.json').read_text())
C=entry.load(entry.HERE/'historical_policy.py','test_policy_core',CFG['core_sha256'])
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        self.policy={'action_grid':[10,20,40],'build_ids':['a','b','c'],'datasets':['tiny'],'risk_limit':.05}
    def tearDown(self):self.tmp.cleanup()
    def array(self,hits,role='target_certification'):
        p=self.p/(role+'.npz');n=hits.shape[2]
        np.savez_compressed(p,query_ids=np.arange(n,dtype=np.int64),hits=hits,ndc=np.full(hits.shape,100,dtype=np.uint64),action_grid=np.array([10,20,40]),build_ids=np.array(['a','b','c']))
        return {'rows':[{'dataset':'tiny','role':role,'array_path':str(p),'array_sha256':entry.digest(p)}]}
    def test_cp_zero(self):self.assertAlmostEqual(C.cp_upper(0,500),1-.05**(1/500),places=13)
    def test_cp_all(self):self.assertEqual(C.cp_upper(500,500),1)
    def test_target_excluded(self):
        selected,abstain,sources=C.candidates(np.array([[2,2],[0,0],[1,0]]),0,3)
        self.assertEqual(selected.tolist(),[1,0]);self.assertEqual(sources,[1,2]);self.assertFalse(abstain.any())
    def test_absent_tail_maps_endpoint(self):
        selected,abstain,_=C.candidates(np.array([[0],[3],[0]]),0,3)
        self.assertEqual(selected.tolist(),[2]);self.assertTrue(abstain[0])
    def test_nonmonotonic_tail(self):
        h=np.full((3,3,500),10,dtype=np.int16);h[0,1,0]=9;h[1,-1,0]=9
        audit=self.array(h);_,_,_,labels=C.load_role(audit,'tiny','target_certification',[10,20,40],['a','b','c'])
        self.assertEqual(labels[0,0],2);self.assertEqual(labels[1,0],3)
    def test_candidate_pass(self):
        rows=C.certify(self.array(np.full((3,3,500),10,dtype=np.int16)),self.policy)
        self.assertEqual([r['decision'] for r in rows],['TCP']*3)
    def test_endpoint_fallback(self):
        h=np.full((3,3,500),10,dtype=np.int16);h[0,0,:50]=9
        rows=C.certify(self.array(h),self.policy);self.assertEqual(rows[0]['decision'],'ENDPOINT');self.assertEqual(rows[0]['cert_tcp_failures'],50)
    def test_undeployable(self):
        h=np.full((3,3,500),10,dtype=np.int16);h[0,-1,:50]=9
        self.assertEqual(C.certify(self.array(h),self.policy)[0]['decision'],'UNDEPLOYABLE')
    def test_evaluation_union_not_raw(self):
        h=np.full((3,3,1000),10,dtype=np.int16);h[0,-1,0]=9
        lock={'rows':[{'dataset':'tiny','target_build':b,'decision':'TCP'} for b in ['a','b','c']]}
        row=C.evaluate(self.array(h,'target_evaluation'),self.policy,lock)[0]
        self.assertEqual(row['eval_tcp_candidate_failures'],1);self.assertEqual(row['eval_selected_failures_descriptive'],1)
        self.assertEqual(h[0,0,0],10)
    def test_wrong_axis(self):
        audit=self.array(np.full((3,3,500),10,dtype=np.int16))
        with self.assertRaises(ValueError):C.load_role(audit,'tiny','target_certification',[10,20,80],['a','b','c'])
    def test_wrong_role_size(self):
        with self.assertRaises(ValueError):C.certify(self.array(np.full((3,3,499),10,dtype=np.int16)),self.policy)
    def test_frozen_rows_mismatch(self):
        with self.assertRaises(ValueError):entry.same_rows([{'decision':'TCP'}],[{'decision':'ENDPOINT'}])
    def test_nonfinite_comparison(self):
        with self.assertRaises(ValueError):entry.same_rows([{'x':float('nan')}],[{'x':.05}])
    def test_lock_hash_before_parse(self):
        (self.p/'completed.json').write_text('not json')
        with self.assertRaisesRegex(ValueError,'SHA mismatch'):entry.validated_lock(self.p,'0'*64,CFG,[])
    def test_failed_lock(self):
        (self.p/'failure.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'Failed lock'):entry.validated_lock(self.p,'0'*64,CFG,[])
    def test_receipt_wrong_role(self):
        (self.p/'completed.json').write_text(json.dumps({'status':'NEW_ARRAY_MATCHES_FROZEN_BYTES','dataset':'sift','role':'target_evaluation','sha256':'x','bytes':1}))
        with self.assertRaises(ValueError):entry.role_inputs({'sift':self.p},'target_certification',CFG)
if __name__=='__main__':unittest.main()
