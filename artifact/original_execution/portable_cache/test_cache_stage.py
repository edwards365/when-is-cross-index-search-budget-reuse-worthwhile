"""Synthetic adapter tests: no E2 invocation and no performance measurements."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import cache_stage as stage


class CacheStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'inputs';self.root.mkdir()
        self.spec={'historical_query_count':4,'datasets':{}}
        self.ids=np.arange(4,dtype=np.int64)
        self.queries=np.arange(8,dtype=np.float32).reshape(4,2)
        self._npz('membership.npz',{'sift_target_evaluation_ids':self.ids})
        self.spec['membership']=self._pin('membership.npz')
        self.truth={'query_ids':self.ids,'neighbor_raw_ids':np.tile(np.arange(10,dtype=np.int64),(4,1)),
                    'scores':np.zeros((4,10),dtype=np.float32)}
        self.profile={'query_ids':self.ids,'hits':np.zeros((8,11,4),dtype=np.int16),
                      'ndc':np.zeros((8,11,4),dtype=np.int64),'topk':np.zeros((8,11,4,10),dtype=np.int64)}
        q=b'E1AQ0001'+struct.pack('<QQ',4,2)+b''.join(struct.pack('<q',int(i))+v.astype('<f4').tobytes() for i,v in zip(self.ids,self.queries))
        (self.root/'queries.qbin').write_bytes(q)
        self._npz('truth.npz',self.truth);self._npz('profile.npz',self.profile)
        self.spec['datasets']['sift']={'dimension':2,'files':{k:self._pin(v) for k,v in
            [('queries','queries.qbin'),('truth','truth.npz'),('profile','profile.npz')]}}

    def tearDown(self):self.tmp.cleanup()
    def _npz(self,path,arrays):np.savez(self.root/path,**arrays)
    def _pin(self,path):
        p=self.root/path
        return {'path':path,'bytes':p.stat().st_size,'sha256':stage.digest(p)}
    def _replace(self,key,arrays):
        self._npz(key+'.npz',arrays)
        self.spec['datasets']['sift']['files'][key]=self._pin(key+'.npz')
    def test_valid_schema(self):
        self.assertEqual(stage.check_inputs(self.spec,self.root,np)[0]['queries'],4)
    def test_hash_drift_rejected(self):
        (self.root/'queries.qbin').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'identity'):stage.check_inputs(self.spec,self.root,np)
    def test_truth_order_rejected(self):
        self.truth['query_ids']=self.ids[::-1];self._replace('truth',self.truth)
        with self.assertRaisesRegex(ValueError,'order'):stage.check_inputs(self.spec,self.root,np)
    def test_profile_order_rejected(self):
        self.profile['query_ids']=self.ids[::-1];self._replace('profile',self.profile)
        with self.assertRaisesRegex(ValueError,'order'):stage.check_inputs(self.spec,self.root,np)
    def test_duplicate_neighbors_rejected(self):
        self.truth['neighbor_raw_ids'][:]=0;self._replace('truth',self.truth)
        with self.assertRaisesRegex(ValueError,'Duplicate neighbor'):stage.check_inputs(self.spec,self.root,np)
    def test_nonfinite_scores_rejected(self):
        self.truth['scores'][0,0]=np.nan;self._replace('truth',self.truth)
        with self.assertRaisesRegex(ValueError,'Invalid truth'):stage.check_inputs(self.spec,self.root,np)
    def test_profile_shape_rejected(self):
        self.profile['ndc']=np.zeros((7,11,4));self._replace('profile',self.profile)
        with self.assertRaisesRegex(ValueError,'Profile shape'):stage.check_inputs(self.spec,self.root,np)
    def test_bad_magic_rejected(self):
        p=self.root/'queries.qbin';p.write_bytes(b'BADMAGIC'+p.read_bytes()[8:])
        with self.assertRaisesRegex(ValueError,'header'):stage.query_rows(np,p,4,2)
    def test_trailing_bytes_rejected(self):
        p=self.root/'queries.qbin';p.write_bytes(p.read_bytes()+b'x')
        with self.assertRaisesRegex(ValueError,'EOF'):stage.query_rows(np,p,4,2)
    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):stage.pinned(self.root,{'path':'../other'})
    def test_existing_output_rejected(self):
        out=self.root.parent/'old';out.mkdir()
        with self.assertRaisesRegex(ValueError,'new named'):stage.require_new_output(out,self.root)
    def test_nested_output_rejected(self):
        with self.assertRaisesRegex(ValueError,'separate'):stage.require_new_output(self.root/'new',self.root)
    def test_valid_output_has_no_side_effect(self):
        out=self.root.parent/'new'
        self.assertEqual(stage.require_new_output(out,self.root),out.resolve())
        self.assertFalse(out.exists())
    def test_historical_key_equality(self):
        frozen=json.loads((stage.HERE/'inputs.json').read_text());core=stage.load_core(frozen)
        q=b'\0\1\2\3';context=b'context\0';v=b'ids/scores'
        cache={core.cache_key(context,q):v}
        self.assertEqual(core.cache_get(cache,context,bytes(bytearray(q))),v)
        self.assertIsNone(core.cache_get(cache,b'other\0',q))
        self.assertIsNone(core.cache_get(cache,context,b'\1'+q[1:]))
    def test_check_never_calls_clock(self):
        with patch('time.perf_counter_ns',side_effect=AssertionError('No measurement permitted')):
            stage.check_inputs(self.spec,self.root,np)
    def test_measure_requires_explicit_opt_in(self):
        with patch('sys.argv',['cache_stage.py','measure','--input-root',str(self.root)]),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exc:stage.main()
        self.assertEqual(exc.exception.code,2)
    def test_wrong_platform_never_creates_output(self):
        spec=json.loads((stage.HERE/'inputs.json').read_text());out=self.root.parent/'new'
        with patch('platform.system',return_value='Windows'):
            with self.assertRaises(ValueError):stage.measure(spec,self.root,out,768*1024**2)
        self.assertFalse(out.exists())
    def test_array_bytes_are_preserved(self):
        p=stage.pinned(self.root,self.spec['datasets']['sift']['files']['truth'])
        out=stage.load_npz(np,p)
        self.assertEqual(out['scores'].tobytes(),self.truth['scores'].tobytes())


if __name__=='__main__':unittest.main()
