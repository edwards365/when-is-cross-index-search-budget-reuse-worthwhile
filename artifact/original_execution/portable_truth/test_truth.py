"""Tiny synthetic arrays only; no benchmark inputs or legacy auditors."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
import unittest
import h5py
import numpy as np
import run_truth as runner

HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/'config.json').read_text())
CORE=runner.load(HERE/'historical_truth.py','truth_test_core',CFG['core_sha256'])

class Flat:
    def __init__(self,dim,metric):self.metric=metric;self.rows=[];self.ntotal=0
    def add(self,b):self.rows.extend(b.copy());self.ntotal+=len(b)
    def search(self,q,k):
        b=np.asarray(self.rows)
        s=np.sum((q[:,None,:]-b[None,:,:])**2,axis=-1) if self.metric=='l2' else q@b.T
        pos=np.argsort(s if self.metric=='l2' else -s,axis=1)[:,:k]
        return np.take_along_axis(s,pos,axis=1).astype(np.float32),pos.astype(np.int64)

FAKE=types.SimpleNamespace(IndexFlatL2=lambda d:Flat(d,'l2'),IndexFlatIP=lambda d:Flat(d,'ip'))

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
        self.ids=np.array([12,13],dtype=np.int64);self.base=np.arange(12,dtype=np.int64)
    def tearDown(self):self.tmp.cleanup()
    def run_core(self,metric,backend=FAKE):
        rng=np.random.default_rng(719);data=rng.normal(size=(20,4)).astype('f4')
        source=self.p/'tiny.h5'
        with h5py.File(source,'w') as f:f['train']=data
        keep=np.zeros(20,dtype=bool);keep[:12]=True
        roles={r:self.ids for r in runner.ROLES}
        with contextlib.redirect_stdout(io.StringIO()):
            result=CORE.acquire(source,20,4,keep,self.base,roles,metric,self.p,'tiny',backend,np,h5py)
        for role in roles:
            path=self.p/('tiny_'+role+'.npz');runner.check_truth(path,self.ids,self.base,metric,np)
            with np.load(path) as a:
                b=data[:12].astype('f8');q=data[self.ids].astype('f8')
                score=np.sum((q[:,None]-b[None])**2,axis=2) if metric=='squared_l2' else q@b.T
                pos=np.argsort(score if metric=='squared_l2' else -score,axis=1)[:,:10]
                np.testing.assert_array_equal(a['neighbor_raw_ids'],pos)
                np.testing.assert_allclose(a['scores'],np.take_along_axis(score,pos,axis=1),rtol=2e-5,atol=2e-5)
        return result
    def truth(self,**changes):
        arrays={'query_ids':self.ids,'neighbor_raw_ids':np.tile(np.arange(10,dtype=np.int64),(2,1)),
                'scores':np.tile(np.arange(10,dtype=np.float32),(2,1))}
        arrays.update(changes);path=self.p/'truth.npz';np.savez_compressed(path,**arrays);return path
    def reject(self,**changes):
        with self.assertRaises(ValueError):runner.check_truth(self.truth(**changes),self.ids,self.base,'squared_l2',np)
    def test_core_l2(self):self.assertEqual(len(self.run_core('squared_l2')['roles']),4)
    def test_core_negative_ip(self):self.run_core('inner_product')
    def test_query_order(self):self.reject(query_ids=self.ids[::-1])
    def test_duplicate_ids(self):self.reject(neighbor_raw_ids=np.zeros((2,10),dtype=np.int64))
    def test_outside_base(self):self.reject(neighbor_raw_ids=np.tile(np.arange(30,40,dtype=np.int64),(2,1)))
    def test_score_dtype(self):self.reject(scores=np.zeros((2,10),dtype=np.float64))
    def test_score_nan(self):self.reject(scores=np.full((2,10),np.nan,dtype=np.float32))
    def test_score_order(self):self.reject(scores=np.tile(np.arange(10,dtype=np.float32)[::-1],(2,1)))
    def test_shape(self):self.reject(neighbor_raw_ids=np.zeros((2,9),dtype=np.int64))
    def test_extra_field(self):self.reject(extra=np.array([1]))
    def test_payload_drift(self):
        p=self.p/'mod.so';p.write_bytes(b'a');lock={'installed_payload':{'mod.so':hashlib.sha256(b'a').hexdigest()}}
        self.assertEqual(runner.pinned_payload(self.p,lock),1);p.write_bytes(b'b')
        with self.assertRaises(ValueError):runner.pinned_payload(self.p,lock)
    def test_payload_escape(self):
        with self.assertRaises((ValueError,FileNotFoundError)):runner.pinned_payload(self.p,{'installed_payload':{'../escape':'0'*64}})
    def test_core_pin(self):
        with self.assertRaises(ValueError):runner.load(HERE/'historical_truth.py','bad','0'*64)
    def test_independent_l2_scores(self):
        q=np.array([[1,2]],dtype='f4');b=np.array([[[3,4],[-1,-2]]],dtype='f4')
        runner.score_reference(q,b,np.array([[8,20]],dtype='f4'),'squared_l2',np)
        with self.assertRaises(ValueError):runner.score_reference(q,b,np.zeros((1,2),dtype='f4'),'squared_l2',np)
    def test_independent_ip_scores(self):
        q=np.array([[1,2]],dtype='f4');b=np.array([[[-3,-4],[0,0]]],dtype='f4')
        runner.score_reference(q,b,np.array([[-11,0]],dtype='f4'),'inner_product',np)
        with self.assertRaises(ValueError):runner.score_reference(q,b,np.array([[11,0]],dtype='f4'),'inner_product',np)
    def test_explicit_authorization(self):
        p=subprocess.run([sys.executable,str(HERE/'run_truth.py'),'generate'],capture_output=True)
        self.assertEqual(p.returncode,2);self.assertIn(b'explicit opt-in',p.stderr)
    def test_no_overwrite(self):
        self.run_core('squared_l2')
        with self.assertRaises(FileExistsError):self.run_core('squared_l2')
    def test_only_train(self):
        text=(HERE/'historical_truth.py').read_text()
        self.assertNotIn('handle["test"]',text);self.assertNotIn('normalize',text)
        self.assertEqual(text.count('handle["train"]'),2)
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Exact pinned wheel Linux3.11 only')
    def test_native_l2_and_identity(self):
        lock=json.loads((HERE/'native_lock.json').read_text())
        if not any(n=='faiss' for n in sys.modules):f,_,_,receipt=runner.native_environment(lock)
        else:import faiss as f
        f.omp_set_num_threads(1);self.run_core('squared_l2',f)
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Exact pinned wheel Linux3.11 only')
    def test_native_ip(self):
        import faiss
        faiss.omp_set_num_threads(1);self.run_core('inner_product',faiss)

if __name__=='__main__':unittest.main()
