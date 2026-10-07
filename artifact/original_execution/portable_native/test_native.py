import io,json,struct,tarfile,tempfile,unittest
from pathlib import Path
import numpy as np
import run_native as entry
import native_inputs
import darth_phases
import refresh_phases
import input_bridge
class NativeTests(unittest.TestCase):
    def test_authored_probe_predictions(self):
        perm=[0,1,2,3,4,6,5,7,9,8,10]
        rows=[f'PRED\t{a}\t{r}\t{t}\t{int((perm[r] if a==1 else r)==t)}' for r in range(11) for a in range(3) for t in range(11)]
        self.assertEqual(darth_phases.audit_model_control('\n'.join(rows))['predictions'],363)
        cached=[f'PRED\t{a}\t{r}\t{t}\t{int(r==0)}' for r in range(11) for a in range(3) for t in range(11)]
        for bad in (cached,rows[:-1]+rows[:1],[rows[0].rsplit('\t',1)[0]+'\tnan']+rows[1:]):
            with self.assertRaises(ValueError):darth_phases.audit_model_control('\n'.join(bad))
    def test_probe_api_and_scientific_iteration_scope(self):
        import re
        v2=(entry.HERE/'darth_compiled_interface_probe_v2.cpp').read_text()
        self.assertIn('1, 11, 1, C_API_PREDICT_NORMAL, tree, 1,',v2)
        self.assertNotIn('LGBM_BoosterPredictForMatSingleRow(',v2)
        for path in ('darth_ip_DeclarativeRecall.cpp','darth-source/faiss/impl/DeclarativeRecall.cpp'):
            calls=re.findall(r'LGBM_BoosterPredictForMatSingleRow\((.*?)\);',(entry.HERE/path).read_text(),re.S)
            self.assertEqual(len(calls),3)
            for call in calls:self.assertRegex(call,r'C_API_PREDICT_NORMAL,\s*0,\s*-1,')
    def test_pins(self):
        c=entry.config();self.assertTrue(c['historical_tree_match']);self.assertEqual(c['rust_version'],'1.97.1')
    def test_whole_tree(self):
        c=entry.config()
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'source';entry.unpack(entry.HERE/'diskann-source.tar.gz',root)
            for rel,p in c['old_patches'].items():
                self.assertEqual(entry.sha(root/rel),p['upstream_sha256']);(root/rel).write_bytes((entry.HERE/p['file']).read_bytes())
            self.assertEqual(entry.tree_sha(root),c['historical_source_tree_sha256'])
    def test_unsafe_archive(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.tar.gz'
            with tarfile.open(p,'w:gz') as f:
                m=tarfile.TarInfo('root/../bad');m.size=1;f.addfile(m,io.BytesIO(b'x'))
            with self.assertRaises(ValueError):entry.unpack(p,Path(t)/'new')
    def test_mapping(self):
        core=entry.module('input_core');got=core.native_ids(np.array([2,4,9]),np.array([2,0,1]),np.array([[2,9]]))
        np.testing.assert_array_equal(got,[[1,0]])
        with self.assertRaises(ValueError):core.native_ids(np.array([2,4,9]),np.array([0,0,1]),np.array([[2]]))
    def test_score_bits(self):
        s=np.array([[2.,0.,-0.,-3.]],dtype=np.float32);got=native_inputs.native_distances(s,'inner_product')
        np.testing.assert_array_equal(got.view('<u4'),s.view('<u4')^np.uint32(0x80000000))
        with self.assertRaises(ValueError):native_inputs.native_distances(s,'squared_l2')
    def test_fbin(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'f';x=np.array([[1,-0.],[2,3]],dtype=np.float32);native_inputs.write_fbin(p,[x],2,2)
            self.assertEqual(p.read_bytes(),struct.pack('<II',2,2)+x.tobytes())
            with self.assertRaises(FileExistsError):native_inputs.write_fbin(p,[x],2,2)
    def test_native_spec(self):
        s=entry.native_spec(Path('/new/input'),Path('/new/out'));src=s['jobs'][0]['content']['source'];self.assertEqual(src['distance'],'inner_product');self.assertEqual(src['l_build'],64)
        s=entry.native_spec(Path('/new/input'),Path('/new/out'),Path('/new/index'),'squared_l2');src=s['jobs'][0]['content']['source'];self.assertEqual(src['index-source'],'Load');self.assertNotIn('save_path',src)
    def test_report(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'r';s={'search_n':10,'search_l':64,'num_tasks':1,'returned_ids_encoding':'canonical_unsigned_decimal_debug_to_u64_v1','returned_ids_by_repetition':[[list(range(10))]],'query_recalls':[1.0],'query_cmps':[12],'query_hops':[3]};p.write_text(json.dumps([{'results':{'search':{'Topk':[s]}}}]))
            r=entry.audit_report(p,np.arange(10).reshape(1,10),1,12);self.assertEqual(r['mean_recall'],1)
            s['returned_ids_by_repetition'][0][0][-1]=0;p.write_text(json.dumps([{'results':{'search':{'Topk':[s]}}}]))
            with self.assertRaises(ValueError):entry.audit_report(p,np.arange(10).reshape(1,10),1,12)
    def test_sift_conversion_bits(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);prep=root/'prep';prep.mkdir();out=root/'out';out.mkdir()
            base=np.arange(20,dtype='<f4').reshape(10,2)/3;base[0,0]=-0.;q=base[:1].copy()
            native_inputs.write_fbin(prep/'base.fbin',[base],10,2);native_inputs.write_fbin(prep/'queries.fbin',[q],1,2)
            ids=np.arange(10,dtype='<u4').reshape(1,10);scores=np.arange(10,dtype='<f4').reshape(1,10)/7
            (prep/'truth.bin').write_bytes(struct.pack('<II',1,10)+ids.tobytes()+scores.tobytes())
            self.assertEqual(darth_phases.sift_input(prep,prep/'base.fbin',out,'source_design'),'training')
            packed=np.fromfile(out/'input/SIFT100M/base.100M.fvecs',dtype='<u4').reshape(10,3)
            np.testing.assert_array_equal(packed[:,1:],base.view('<u4'))
            truth=np.fromfile(out/'input/SIFT100M/learn.groundtruth.1M.k1000.fvecs',dtype='<u4').reshape(1,11)
            np.testing.assert_array_equal(truth[:,1:],scores.view('<u4'))
    def test_dot_audit(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);base=np.arange(20,dtype='<f4').reshape(10,2);q=np.array([[-2,1]],dtype='<f4');ids=np.arange(10,dtype='<i8').reshape(1,10)
            native_inputs.write_fbin(root/'base.fbin',[base],10,2);native_inputs.write_fbin(root/'queries.fbin',[q],1,2)
            (root/'truth.bin').write_bytes(struct.pack('<II',1,10)+ids.astype('<u4').tobytes()+np.zeros(10,dtype='<f4').tobytes())
            scores=(base@q[0]).astype('<f4');p=root/'returned';p.write_bytes(struct.pack('<II',1,10)+ids.tobytes()+scores.tobytes())
            self.assertEqual(darth_phases.audit_ip(p,root,root/'base.fbin')['mean_recall'],1.)
            scores[0]+=1;p.write_bytes(struct.pack('<II',1,10)+ids.tobytes()+scores.tobytes())
            with self.assertRaises(ValueError):darth_phases.audit_ip(p,root,root/'base.fbin')
    def test_model_structure(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'model';body='max_feature_idx=10\nobjective=regression\n'+''.join('Tree='+str(i)+'\nleaf_value=0\nsplit_feature=10\n' for i in range(100));p.write_text(body)
            self.assertEqual(darth_phases.model_structure(p)['tree_count'],100)
            p.write_text(body.replace('leaf_value=0','leaf_value=nan',1))
            with self.assertRaises(ValueError):darth_phases.model_structure(p)
    def test_refresh_membership(self):
        old=np.arange(100000,dtype='<f4').reshape(-1,1);reserve=np.arange(100000,110000,dtype='<f4').reshape(-1,1)
        fresh,deleted=refresh_phases.membership(old,reserve);self.assertEqual(fresh.shape,old.shape);self.assertEqual(len(deleted),5000)
        np.testing.assert_array_equal(fresh[-5000:],reserve[:5000]);self.assertFalse(set(deleted)&set(fresh[:95000,0].astype(int)))
        import hashlib
        expected=entry.config()['refresh']['datasets']['sift100k']['deleted_ids_sha256'];self.assertEqual(hashlib.sha256(deleted.tobytes()).hexdigest(),expected)
    def test_refresh_source_pool(self):
        core=entry.module('refresh_analysis');rows={seed:np.array([i%7,(i+2)%7]) for i,seed in enumerate(core.SEEDS)}
        target=core.SEEDS[0];got=core.source_pool_indices(rows,target);np.testing.assert_array_equal(got,np.max([r for seed,r in rows.items() if seed!=target],axis=0))
        with self.assertRaises(ValueError):core.source_pool_indices({target:rows[target]},target)
    def test_inherited_limits(self):
        import ci_native
        class Resource:
            def getrlimit(self,k):return (123,456)
            def setrlimit(self,k,v):self.got=v
        r=Resource();ci_native.bounded_limit(r,0,999);self.assertEqual(r.got,(123,123))
    def test_source_only_bundle_full_bits(self):
        import h5py
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'raw.h5';raw=np.arange(128,dtype='<f4').reshape(32,4)/7;raw[7,1]=-0.
            with h5py.File(source,'x') as f:f['train']=raw
            qids=np.array([0,2],dtype=np.int64);keep=np.ones(32,bool);keep[qids]=False;keep[5]=False;ids=np.flatnonzero(keep).astype(np.int64);q=raw[qids];truth=np.tile(ids[:10],(2,1));pin=entry.sha(source);bundle=root/'bundle.hdf5'
            input_bridge.write_source_only(bundle,source,keep,ids,qids,q,truth,pin,h5py,chunk=8)
            audit=input_bridge.audit_source_only(bundle,source,keep,ids,qids,q,truth,pin,h5py,chunk=8);self.assertFalse(audit['future_role_vectors_or_truth_in_bundle'])
            with h5py.File(bundle,'r+') as f:f['train'][0,0]+=1
            with self.assertRaises(AssertionError):input_bridge.audit_source_only(bundle,source,keep,ids,qids,q,truth,pin,h5py,chunk=8)
    def test_new_role_gate(self):
        from types import SimpleNamespace
        self.assertIsNone(input_bridge.gate(SimpleNamespace(role='source_design')))
        with self.assertRaises(ValueError):input_bridge.gate(SimpleNamespace(role='target_evaluation',previous=None))
if __name__=='__main__':unittest.main()
