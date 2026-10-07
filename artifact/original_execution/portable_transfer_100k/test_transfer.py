import csv,json,platform,subprocess,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import run_transfer as entry
HERE=Path(__file__).resolve().parent
class TransferTests(unittest.TestCase):
    def test_pins(self):self.assertEqual(len(entry.config()['seeds']),8)
    def test_roles(self):entry.role_check(entry.config())
    def test_orders(self):
        c=entry.config()
        for ds,row in c['datasets'].items():
            p=HERE/(ds+'_order.npy');self.assertEqual(entry.sha(p),row['lid_order_sha256']);np.testing.assert_array_equal(np.sort(np.load(p)),np.arange(100000))
    def test_faiss_roles(self):
        c=entry.config()
        with (HERE/'faiss100k_query_role_ledger.csv').open(newline='') as f:rows=list(csv.DictReader(f))
        for ds,alias in [('sift_100k','sift'),('arxiv_nomic_100k','arxiv')]:
            with (HERE/(alias+'_old_role_ids.csv')).open(newline='') as f:old={int(r['source_id']) for r in csv.DictReader(f)}
            n=c['datasets'][ds]['source']['train_shape'][0];pool=np.asarray([i for i in range(100000,n) if i not in old],dtype=np.int64)
            expected=np.random.default_rng(991).permutation(pool)[:750]
            np.testing.assert_array_equal([int(r['source_id']) for r in rows if r['dataset']==ds],expected)
    def test_faiss_lock(self):
        lock=json.loads((HERE/'native_lock.json').read_text())
        self.assertEqual(lock['version'],'1.15.0');self.assertEqual(len(lock['installed_payload']),33)
        self.assertFalse(lock['historical_actual_dispatch_attested'])
    def test_analysis_extraction(self):
        fn=entry.mod('historical_analysis').action_summary
        data=[dict(build_id=b,query_id=q,ef=e,hit_count=10,recall=1) for b in ('a','b') for q in range(4) for e in (10,20)]
        out=fn(data,10,[10,20]);self.assertEqual(out['incremental_transport_risk'],0);self.assertEqual(out['pairs'],2)
    def test_filter(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'raw';p.write_text('query_id,ef_search,latency_round,recall_at_10\n0,10,0,0.9\n749,10,0,1\n750,10,0,1\n0,10,1,1\n')
            self.assertEqual(entry.paper_rows(p,Path(t)/'out','x'),2)
    def test_exact(self):
        core=entry.mod('historical_core');rng=np.random.default_rng(12);b=rng.normal(size=(32,4)).astype(np.float32);q=rng.normal(size=(3,4)).astype(np.float32)
        got=core.exact(b,q);ref=np.argsort(((q[:,None].astype(np.float64)-b[None].astype(np.float64))**2).sum(axis=2),axis=1)[:,:10];np.testing.assert_array_equal(got,ref)
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Linux native compiler job')
    def test_faiss_native(self):
        import faiss_phases
        f,np,_,env=faiss_phases.native(entry.sha)
        self.assertEqual(env['payload_count'],33)
        rng=np.random.default_rng(28);b=rng.normal(size=(48,8)).astype(np.float32);q=rng.normal(size=(5,8)).astype(np.float32)
        flat=f.IndexFlatL2(8);flat.add(b);_,truth=flat.search(q,10)
        independent=np.argsort(((q[:,None].astype(np.float64)-b[None].astype(np.float64))**2).sum(axis=2),axis=1)[:,:10]
        np.testing.assert_array_equal(truth,independent)
        idx=faiss_phases.build(f,np,b,3101)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'g';f.write_index(idx,str(p));idx=f.read_index(str(p))
            rows=faiss_phases.rows(f,q,truth,idx,'synthetic','b',[16,512])
            self.assertEqual(len(rows),10)
            for row in rows[-5:]:self.assertEqual(row['hit_count'],10)
    @unittest.skipUnless(platform.system()=='Linux' and sys.version_info[:2]==(3,11),'Linux native compiler job')
    def test_native(self):
        import os,resource
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        def caps():
            for kind,limit in ((resource.RLIMIT_AS,4<<30),(resource.RLIMIT_FSIZE,32<<20),(resource.RLIMIT_CPU,180),(resource.RLIMIT_CORE,0)):resource.setrlimit(kind,(limit,limit))
        c=entry.config();core=entry.mod('historical_core');rng=np.random.default_rng(29)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);binary=root/'runner';subprocess.run(['g++']+c['new_compile_flags']+['-I',str(HERE/'include'),str(HERE/'hnsw_gate_a_benchmark.cpp'),'-o',str(binary)],check=True,timeout=180,preexec_fn=caps)
            for ds in c['datasets']:
                prepared=root/ds;prepared.mkdir();b=rng.normal(size=(32,8)).astype(np.float32);q=rng.normal(size=(4,8)).astype(np.float32)
                if ds.startswith('arxiv'):b/=np.linalg.norm(b,axis=1,keepdims=True);q/=np.linalg.norm(q,axis=1,keepdims=True)
                truth=core.exact(b,q);core.matrix(prepared/'base.f32bin',b);core.matrix(prepared/'confirmatory.f32bin',q);core.truthbin(prepared/'truth.u32bin',truth);core.orderbin(prepared/'random.orderbin',rng.permutation(32))
                out=prepared/'native';subprocess.run(entry.native_command(binary,prepared,ds,83,'random',out,[10,40,200],warmup=2,rounds=2),check=True,timeout=30,preexec_fn=caps)
                entry.validate_rows(out/'queries.csv',4,[10,40,200],2)
                with (out/'queries.csv').open(newline='') as f:rows=[r for r in csv.DictReader(f) if int(r['ef_search'])==200 and int(r['latency_round'])==0]
                for i,r in enumerate(rows):self.assertEqual(set(map(int,r['returned_top10'].split(';'))),set(truth[i]));self.assertEqual(float(r['recall_at_10']),1)
if __name__=='__main__':unittest.main()
