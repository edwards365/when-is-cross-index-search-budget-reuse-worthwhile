import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from run_timing import digest,validated_profile,operational_lock,OPERATIONAL_CONFIG_SHA
def put(p,x):p.write_text(json.dumps(x));return p
class Origin(unittest.TestCase):
    def test_profile_typed_origin(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'data').mkdir();(p/'ops').mkdir();csv=p/'data/g.csv';csv.write_bytes(b'tiny csv');q=p/'data/queries.qbin';q.write_bytes(b'tiny qbin')
            evaluation={'profiles':{'g':{'sha256':digest(csv),'bytes':csv.stat().st_size}},'qbin_sha256':digest(q),'qbin_bytes':q.stat().st_size}
            cfg={'build_ids':['g'],'datasets':{'sift':{'name':'tiny','evaluation':evaluation}}}
            r=put(p/'ops/final.json',{'status':'NATIVE_PROFILES_COMPLETE_AUDIT_PENDING','dataset':'tiny','role':'target_evaluation','profiles':[{'build':'g','actual_exit_code':0,'csv_sha256':digest(csv)}]})
            put(p/'start.json',{'config_sha256':OPERATIONAL_CONFIG_SHA});put(p/'completed.json',{'status':'NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE','kind':'profiles','measured':{'record_sha256':digest(r)}})
            self.assertEqual(validated_profile(p,'sift','g',cfg,True),csv)
            with self.assertRaises(ValueError):validated_profile(p,'sift','g',cfg,False)
    def test_lock_typed_origin_before_evaluation(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'ops').mkdir();rows=[{'decision':'TCP'}];r=put(p/'ops/certification_decision_lock.json',{'status':'DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ','rows':rows})
            put(p/'start.json',{'config_sha256':OPERATIONAL_CONFIG_SHA});done=put(p/'completed.json',{'status':'NEW_OPERATIONAL_BOUNDARY_MEASUREMENT_COMPLETE','kind':'decision','measured':{'record_sha256':digest(r)}})
            def equal(a,b):self.assertEqual(a,b)
            self.assertEqual(operational_lock(p,digest(done),SimpleNamespace(same_rows=equal),rows)['rows'],rows)
            with self.assertRaises(ValueError):operational_lock(p,'0'*64,SimpleNamespace(same_rows=equal),rows)
if __name__=='__main__':unittest.main()
