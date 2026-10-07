"""Synthetic/local package checks; never open original scientific arrays."""
import ast,csv,io,json,tarfile,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import run_ambiguity as r
import run_native_controls as nc

HERE=Path(__file__).resolve().parent
C=json.loads((HERE/'config.json').read_text())

class Synthetic(unittest.TestCase):
    def test_source_pins(self):
        for name,pin in C['pins'].items():self.assertEqual(r.sha(HERE/name),pin,name)
    def test_complete_registry(self):
        expected={(d,s,h) for d in C['datasets'] for s in C['seeds'] for h in C['histories']}
        for impl,rows in C['historical_runs'].items():
            self.assertEqual(len(rows),27)
            actual={(x['dataset'],x.get('seed',x.get('graph_seed')),x.get('history',x.get('insertion_order'))) for x in rows}
            self.assertEqual(actual,expected,impl)
    def test_native_pins(self):
        self.assertEqual(len(C['native_inputs']['faiss']['payload_sha256']),33)
        d=C['native_inputs']['diskann']
        self.assertEqual(len(d['patch_targets']),4)
        p=json.loads((HERE/'diskann_provenance.json').read_text())
        self.assertEqual(p['diskann']['source_commit'],'158126e64129d3c39f9df02199c2dcc06d4f9e7f')
        self.assertEqual(p['diskann']['package_version'],'0.56.0')
    def test_dependency_map(self):
        record=json.loads((HERE/'diskann_dependency_versions.json').read_text())
        self.assertEqual(record['cargo_lock_sha256'],json.loads((HERE/'diskann_provenance.json').read_text())['diskann']['cargo_lock_sha256'])
        self.assertTrue(all(x.get('name') and x.get('version') for x in record['packages']))
        self.assertTrue(all(x.get('checksum') for x in record['packages'] if x.get('source','').startswith('registry+')))
    def test_tiny_native_fixture(self):
        for normalized in (False,True):
            b,q,truth,order,inv,qids=nc.synthetic(normalized)
            self.assertEqual(b.shape,(256,32));self.assertEqual(q.shape,(8,32))
            np.testing.assert_array_equal(inv[order],np.arange(256))
            np.testing.assert_array_equal(truth[:,0],qids)
            for i in range(8):self.assertEqual(nc.check_ids(truth[i],q[i],b,truth[i],normalized),1.)
    def test_tiny_order_reject(self):
        b,q,truth,order,inv,qids=nc.synthetic(False)
        with self.assertRaises(ValueError):nc.check_ids(truth[0][::-1],q[0],b,truth[0],False)
    def test_role_disjoint(self):
        for x in json.loads((HERE/'membership.json').read_text())['datasets']:
            self.assertEqual(len(x['design_source_ids']),250)
            self.assertEqual(len(x['confirm_source_ids']),750)
            self.assertFalse(set(x['design_source_ids']) & set(x['confirm_source_ids']))
    def test_import_no_analysis(self):
        m=r.load(HERE/'historical_analysis.py','g1_test',C['pins']['historical_analysis.py'])
        self.assertFalse(hasattr(m,'BASE'))
        curve={b:(1.,1.) for b in C['grid']};curve[24]=(.8,1.)
        self.assertEqual(m.stable(curve),32)
        curve[512]=(.8,1.);self.assertEqual(m.stable(curve),1024)
        self.assertEqual(m.ceilgrid(1024),512) # legacy diagnostic behavior, not proof of safety
    def test_truth_tiny(self):
        m=r.load(HERE/'ground_truth.py','tiny_truth',C['pins']['ground_truth.py'])
        ids,dist=m.exact_top_k(np.array([[0.,0.],[2.,0.],[4.,0.]],dtype=np.float32),np.array([[.1,0.]],dtype=np.float32),2,metric='l2',base_batch=2)
        np.testing.assert_array_equal(ids,[[0,1]])
        np.testing.assert_allclose(dist,[[.01,3.61]],rtol=1e-6)
    def test_permutation(self):
        np.testing.assert_array_equal(r.permutation(np.array([2,0,1]),3,np),[2,0,1])
        for value in (np.array([1,1,0]),np.array([0.,1.,2.]),np.array([0,1])):
            with self.assertRaises(ValueError):r.permutation(value,3,np)
    def test_vamana_semantics(self):
        for norm,metric in ((True,'cosine'),(False,'l2')):
            spec=r.vamana_spec(Path('new-unit'),norm,C['grid']);job=spec['jobs'][0]['content']
            self.assertEqual(job['data']['metric'],metric)
            self.assertEqual(job['build'],{'alpha':1.2,'l_build':50,'max_degree':32,'pruned_degree':32})
            self.assertEqual([x['search_l'] for x in job['search']['knn']],C['grid'])
            self.assertNotIn('seed',json.dumps(spec))
    def test_safe_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);archive=root/'s.tar'
            with tarfile.open(archive,'w') as t:
                x=tarfile.TarInfo('root/a.txt');x.size=3;t.addfile(x,io.BytesIO(b'abc'))
            out=root/'out';out.mkdir();dest=r.safe_extract(archive,out)
            self.assertEqual((dest/'a.txt').read_bytes(),b'abc')
    def test_archive_rejects_escape_and_link(self):
        for name,link in [('root/../../outside',False),('root/link',True)]:
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);archive=root/'s.tar'
                with tarfile.open(archive,'w') as t:
                    x=tarfile.TarInfo(name)
                    if link:x.type=tarfile.SYMTYPE;x.linkname='/outside'
                    t.addfile(x)
                out=root/'out';out.mkdir()
                with self.assertRaises(ValueError):r.safe_extract(archive,out)
    def test_receipt_binding(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'a').write_bytes(b'1')
            record={'stage':'prepare','config_sha256':r.sha(HERE/'config.json'),'wrapper_sha256':r.sha(HERE/'run_ambiguity.py'),'outputs':{'a':r.sha(p/'a')}}
            (p/'completed.json').write_text(json.dumps(record));pin=r.sha(p/'completed.json')
            self.assertEqual(r.receipt(p,pin,'prepare')['stage'],'prepare')
            (p/'a').write_bytes(b'2')
            with self.assertRaises(ValueError):r.receipt(p,pin,'prepare')
    def test_receipt_rejects_wrong_stage(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'completed.json').write_text(json.dumps({'stage':'prepare','config_sha256':r.sha(HERE/'config.json'),'outputs':{}}))
            with self.assertRaises(ValueError):r.receipt(p,r.sha(p/'completed.json'),'unit')
    def test_complete_synthetic_responses(self):
        truth=np.tile(np.arange(10),(1000,1));a=SimpleNamespace(dataset='sift_100k',implementation='faiss',history='random',seed=43)
        rows=[(b,q,range(10),20) for b in C['grid'] for q in range(1000)]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.csv';r.write_responses(p,rows,truth,'synthetic',a,C,np)
            with p.open() as f:written=list(csv.DictReader(f))
            self.assertEqual(len(written),12000);self.assertEqual(sum(x['query_split']=='design' for x in written),3000)
            self.assertTrue(all(x['recall_at_10']=='1.0' for x in written))
    def test_responses_reject_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            a=SimpleNamespace(dataset='sift_100k',implementation='faiss',history='random',seed=43)
            with self.assertRaises(ValueError):r.write_responses(Path(td)/'r.csv',[(10,0,range(10),20)]*2,np.tile(np.arange(10),(1000,1)),'synthetic',a,C,np)
    def test_responses_reject_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            a=SimpleNamespace(dataset='sift_100k',implementation='faiss',history='random',seed=43)
            with self.assertRaises(ValueError):r.write_responses(Path(td)/'r.csv',[],None,'synthetic',a,C,np)
    def test_no_unconditional_driver_entry(self):
        tree=ast.parse((HERE/'historical_analysis.py').read_text())
        self.assertFalse(any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) for n in tree.body))

if __name__=='__main__':unittest.main()
