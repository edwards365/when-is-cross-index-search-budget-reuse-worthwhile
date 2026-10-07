"""Tiny synthetic HDF5/array tests and frozen ID checks; no original data scan."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import platform
import struct
import tempfile
import unittest
from unittest.mock import patch
import h5py
import numpy as np
import prepare_inputs as stage


CFG=json.loads((stage.HERE/'registry.json').read_text())
CORE=stage.load_core(CFG)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        counts={r:1 for r in stage.ROLES}
        self.cfg={'seed':991,'role_counts':counts}
        self.row={'dataset':'synthetic','train_shape':[40,2],
                  'old_roles':{r:[i] for i,r in enumerate(stage.ROLES)},
                  'e1b_roles':{r:[i+4] for i,r in enumerate(stage.ROLES)},
                  'old_base_exclusions':[30],'expected_base_exclusions':[30],'expected_base_count':27}
        available=np.asarray(sorted(set(range(40))-set(range(8))-{30}),dtype=np.int64)
        self.row['expected_fresh_roles']={r:x.tolist() for r,x in CORE.fresh_ids('synthetic',991,available,counts).items()}
        self.train=np.arange(80,dtype=np.float32).reshape(40,2)
    def tearDown(self):self.tmp.cleanup()
    def test_partition(self):
        new,roles,base=stage.partition(self.cfg,self.row,CORE)
        self.assertEqual(len(roles),12);self.assertEqual(len(base),27)
        self.assertFalse(set(base)&set(roles));self.assertNotIn(30,base)
        self.assertEqual(base.tolist(),sorted(base))
    def test_role_overlap(self):
        self.row['e1b_roles']['source_design']=[0]
        with self.assertRaisesRegex(ValueError,'overlap'):stage.partition(self.cfg,self.row,CORE)
    def test_changed_seed(self):
        self.cfg['seed']+=1
        with self.assertRaisesRegex(ValueError,'frozen IDs'):stage.partition(self.cfg,self.row,CORE)
    def test_unsorted_prior_role(self):
        self.row['old_roles']['source_design']=[1,0]
        with self.assertRaises(ValueError):stage.partition(self.cfg,self.row,CORE)
    def test_excluded_query(self):
        self.row['expected_base_exclusions']=[0,30]
        with self.assertRaisesRegex(ValueError,'overlap'):stage.partition(self.cfg,self.row,CORE)
    def test_wrong_base_count(self):
        self.row['expected_base_count']-=1
        with self.assertRaisesRegex(ValueError,'base count'):stage.partition(self.cfg,self.row,CORE)
    def test_full_synthetic_scan(self):
        _,roles,_=stage.partition(self.cfg,self.row,CORE)
        with contextlib.redirect_stdout(io.StringIO()):ex=stage.scan_and_check(self.train,self.row,roles,CORE)
        self.assertEqual(ex.tolist(),[30])
    def test_query_query_duplicate_stops(self):
        _,roles,_=stage.partition(self.cfg,self.row,CORE);a,b=sorted(roles)[:2]
        self.train[b]=self.train[a]
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaisesRegex(ValueError,'Query-query'):
            stage.scan_and_check(self.train,self.row,roles,CORE)
    def test_base_duplicate_must_match_frozen_exclusion(self):
        _,roles,base=stage.partition(self.cfg,self.row,CORE);j=int(base[0]);self.train[j]=self.train[min(roles)]
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaisesRegex(ValueError,'frozen exclusions'):
            stage.scan_and_check(self.train,self.row,roles,CORE)
        self.row['expected_base_exclusions']=sorted([30,j])
        with contextlib.redirect_stdout(io.StringIO()):ex=stage.scan_and_check(self.train,self.row,roles,CORE)
        self.assertEqual(ex.tolist(),self.row['expected_base_exclusions'])
    def test_only_train_key_accessed(self):
        seen=[]
        class Handle:
            def __getitem__(inner,key):
                seen.append(key)
                if key!='train':raise AssertionError('Forbidden HDF5 role')
                return self.train
        self.assertIs(stage.train_only(Handle(),[40,2]),self.train)
        self.assertEqual(seen,['train'])
    def test_wrong_dtype(self):
        with self.assertRaisesRegex(ValueError,'dtype'):stage.train_only({'train':self.train.astype(np.float64)},[40,2])
    def test_wrong_shape(self):
        with self.assertRaisesRegex(ValueError,'shape'):stage.train_only({'train':self.train},[41,2])
    def test_synthetic_hdf5_and_qbin_bytes(self):
        p=self.root/'tiny.hdf5';q=self.root/'queries.qbin';ids=np.array([0,2],dtype=np.int64)
        self.train[0]=[-0.0,2.5]
        with h5py.File(p,'w') as f:
            f['train']=self.train;f['test']=np.array([999]);f['neighbors']=np.array([999]);f['distances']=np.array([999])
        with h5py.File(p,'r') as f:info=stage.write_queries(stage.train_only(f,[40,2]),ids,q,np)
        expected=b'E1AQ0001'+struct.pack('<QQ',2,2)+b''.join(struct.pack('<q',int(i))+self.train[i].astype('<f4').tobytes() for i in ids)
        self.assertEqual(q.read_bytes(),expected);self.assertEqual(info['sha256'],hashlib.sha256(expected).hexdigest())
        with self.assertRaises(FileExistsError):stage.write_queries(self.train,ids,q,np)
    def test_preparation_requires_opt_in(self):
        with patch('sys.argv',['prepare_inputs.py','prepare']),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):stage.main()
        self.assertEqual(list(self.root.iterdir()),[])
    def test_check_registry_cannot_take_raw_data(self):
        with patch('sys.argv',['prepare_inputs.py','check-registry','--sift','unused.hdf5']),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):stage.main()
    def test_windows_measurement_rejected(self):
        with patch('platform.system',return_value='Windows'),self.assertRaises(ValueError):
            stage.preflight(CFG,self.root/'new',{},16*1024**2)
        self.assertFalse((self.root/'new').exists())
    def test_frozen_id_membership_all_datasets(self):
        for prefix,row in CFG['datasets'].items():
            new,roles,base=stage.partition(CFG,row,CORE)
            self.assertEqual(sum(map(len,new.values())),2500);self.assertEqual(len(roles),7500)
            self.assertEqual(len(base),{'sift':992295,'arxiv':1337142}[prefix])
    def test_linux_membership_serialization(self):
        arrays={}
        for prefix,row in CFG['datasets'].items():
            for role in stage.ROLES:arrays[prefix+'_'+role+'_ids']=np.asarray(row['expected_fresh_roles'][role],dtype=np.int64)
            arrays[prefix+'_base_exclusion_ids']=np.asarray(row['expected_base_exclusions'],dtype=np.int64)
        stream=io.BytesIO();np.savez_compressed(stream,**arrays)
        if platform.system()=='Linux':self.assertEqual(hashlib.sha256(stream.getvalue()).hexdigest(),CFG['expected_membership_sha256'])
        else:
            # ZIP writer host-platform metadata differs on Windows; arrays must not.
            with np.load(io.BytesIO(stream.getvalue()),allow_pickle=False) as actual:
                for k,v in arrays.items():self.assertTrue(np.array_equal(actual[k],v))


if __name__=='__main__':unittest.main()
