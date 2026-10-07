"""Tiny synthetic S9-3/S9-4 arithmetic and native mechanics only."""
import ast,hashlib,io,json,platform,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import input_core,decision3_core as d3,decision4_core as d4,decision4_lock_core as dl
import run_recovery as r
HERE=Path(__file__).resolve().parent;CFG=json.loads((HERE/'config.json').read_text())

def rows(role='source_design',count=500):
    return pd.DataFrame([dict(dataset='tiny',build_id=b,query_role=role,ef_search=a,query_position=q,
        failure=0,recall_at_10=1.0,ndc=10+a) for b in ('a','b') for a in CFG['grid'] for q in range(count)])

class Recovery(unittest.TestCase):
    def test_registered_pins_complete(self):
        self.assertEqual(len(CFG['graphs']),16)
        self.assertEqual({p:len(v) for p,v in CFG['input_pins'].items()},{'3':6,'4':6})
    def test_roles(self):
        roles=json.loads((HERE/'roles.json').read_text())
        for phase,row in roles.items():
            for dataset,ids in row['ids'].items():self.assertEqual(len(r.validate_role_ids(ids,row['names'])),1500)
    def test_role_overlap_reject(self):
        x={key:list(range(100000,100500)) for key in ('a','b','c')}
        with self.assertRaisesRegex(ValueError,'overlap'):r.validate_role_ids(x,list(x))
    def test_normalization_preserved(self):
        b,q=r.normalized(np.array([[3.,4.]],np.float32),np.array([[0.,0.]],np.float32),'ip',np)
        np.testing.assert_array_equal(b,np.array([[.6,.8]],np.float32));self.assertTrue(np.isfinite(q).all())
    def test_l2_not_normalized(self):
        b=np.array([[3.,4.]],np.float32);a,_=r.normalized(b.copy(),b.copy(),'l2',np)
        np.testing.assert_array_equal(a,b)
    def test_exact_truth_l2(self):
        rng=np.random.default_rng(91);b=rng.normal(size=(32,4)).astype(np.float32);q=rng.normal(size=(3,4)).astype(np.float32)
        actual=input_core.exact_top10(b,q,'l2')
        expected=np.argsort(((b.astype(float)[None]-q.astype(float)[:,None])**2).sum(2),axis=1)[:,:10]
        np.testing.assert_array_equal(actual,expected)
    def test_exact_truth_ip(self):
        rng=np.random.default_rng(5);b=rng.normal(size=(32,4)).astype(np.float32);q=rng.normal(size=(3,4)).astype(np.float32)
        actual=input_core.exact_top10(b,q,'ip');expected=np.argsort(-(q.astype(float)@b.astype(float).T),axis=1)[:,:10]
        np.testing.assert_array_equal(actual,expected)
    def test_cp_and_source(self):
        self.assertEqual(d3.cp_upper(5,5,.025),1.0);self.assertEqual(d3.select_source(rows(),CFG['grid'],.05),16)
        self.assertEqual(d3.next_rung(16,CFG['grid']),32);self.assertEqual(d3.next_rung(512,CFG['grid']),512)
    def test_s3_all_decision_branches(self):
        for action,expected in ((None,'CANDIDATE_ACCEPTED'),(32,'FIXED_SAFE_FALLBACK'),(512,'ABSTAIN_ENDPOINT_UNQUALIFIED')):
            c=rows('target_certification')
            if action:c.loc[c.ef_search.eq(action),'failure']=1
            x=d3.make_decisions(pd.concat([rows(),c]),CFG['grid'],.05)
            self.assertEqual(set(x.decision),{expected})
    def test_s4_first_eligible_not_lowest_ndc(self):
        x=rows('baseline_selection');x.loc[x.ef_search.eq(16),'ndc']=999999
        self.assertEqual(d4.choose_action(x,500),16)
    def test_s4_nested_250(self):
        x=rows('baseline_selection');x.loc[x.query_position.ge(250)&x.ef_search.lt(512),'failure']=1
        self.assertEqual(d4.choose_action(x,250),16);self.assertEqual(d4.choose_action(x,500),512)
    def test_s4_lock_excludes_oracle(self):
        x=pd.concat([rows('baseline_selection'),rows('baseline_certification')]);source={('tiny',b):(16,32) for b in ('a','b')}
        locked=dl.make_decisions(x,source)
        self.assertEqual(len(locked),16);self.assertNotIn('O1_EVALUATION_ORACLE',set(locked.arm))
        full=d4.make_decisions(pd.concat([x,rows('baseline_evaluation')]),source)
        pd.testing.assert_frame_equal(locked.reset_index(drop=True),full[~full.arm.eq('O1_EVALUATION_ORACLE')].reset_index(drop=True))
    def test_no_eval_field_in_lock_core(self):
        text=(HERE/'decision4_lock_core.py').read_text();self.assertNotIn('baseline_evaluation',text);self.assertNotIn('O1_EVALUATION_ORACLE',text)
    def test_source_and_expected_identity(self):
        for name,pin in CFG['core_hashes'].items():self.assertEqual(r.digest(HERE/name),pin)
        self.assertEqual(r.digest(HERE/'expected_source_decisions.csv'),CFG['expected_source_decisions_sha256'])
    def test_lock_first_before_eval_reads(self):
        text=(HERE/'run_recovery.py').read_text();tree=ast.parse(text)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate')
        body=ast.get_source_segment(text,fn);self.assertLess(body.index('prior=receipt'),body.index('response_frame'))
    def test_newreceipt_hash_required(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):r.receipt(Path(t),None,'x',CFG)
    def test_build_metric_is_l2(self):
        text=(HERE/'native_core.py').read_text();self.assertIn('faiss.METRIC_L2',text);self.assertNotIn('METRIC_INNER_PRODUCT',text)
    @unittest.skipUnless(platform.system()=='Linux','Pinned Linux Faiss wheel required')
    def test_tiny_native_graph(self):
        import faiss,native_core as nc
        faiss.omp_set_num_threads(1);nc.faiss=faiss
        rng=np.random.default_rng(99);base=rng.normal(size=(32,4)).astype(np.float32);q=rng.normal(size=(2,4)).astype(np.float32)
        for normalized in (False,True):
            b=base.copy();queries=q.copy()
            if normalized:b,queries=r.normalized(b,queries,'ip',np)
            index=nc.build_index(b,rng.permutation(32));nc.core(index).hnsw.efSearch=512
            with tempfile.TemporaryDirectory() as t:
                path=Path(t)/'tiny.faiss';faiss.write_index(index,str(path));index=faiss.read_index(str(path));nc.core(index).hnsw.efSearch=512
                distances,ids=index.search(queries,10);ref=((b.astype(float)[None]-queries.astype(float)[:,None])**2).sum(2)
                np.testing.assert_array_equal(ids,np.argsort(ref,axis=1)[:,:10]);np.testing.assert_allclose(distances,np.take_along_axis(ref,ids,axis=1),atol=1e-5)
                self.assertEqual(index.ntotal,32)

if __name__=='__main__':unittest.main(verbosity=2)
