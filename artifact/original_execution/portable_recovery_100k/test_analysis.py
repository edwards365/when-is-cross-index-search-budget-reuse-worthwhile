"""New synthetic statistics only; no saved dataset or historical analysis run."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import analyze_new as entry
import analysis3_runtime_core as r3,analysis4_runtime_core as r4
import analysis3_quality_core as q3,analysis4_quality_core as q4

def runtime(builds=('a',)):
    return pd.DataFrame([dict(dataset='tiny',target_build=b,query_position=q,repetition=r,ef_search=a,
        wall_ns=a+r,cpu_ns=a+r,ndc=a,top10_sha256=f'{b}_{q}_{a}') for b in builds for q in range(500) for r in range(7) for a in (256,512)])

class Tests(unittest.TestCase):
    def test_pins(self):
        cfg=json.loads((entry.HERE/'analysis_config.json').read_text())
        for f,h in cfg['cores'].items():self.assertEqual(entry.digest(entry.HERE/f),h)
        self.assertEqual(entry.digest(entry.HERE/'config.json'),cfg['recovery_config_sha256'])
    def test_seven_repeat_cube_and_mean(self):
        f=runtime();entry.validate_runtime(f,[256,512],'tiny','a')
        mean=r3.technical_cells(f);self.assertEqual(mean.iloc[0].wall_ns,259)
        for bad in (f.iloc[:-1],pd.concat([f,f.iloc[:1]])):
            with self.assertRaises(ValueError):entry.validate_runtime(bad,[256,512],'tiny','a')
        f.loc[0,'top10_sha256']='drift'
        with self.assertRaises(ValueError):entry.validate_runtime(f,[256,512],'tiny','a')
    def test_response_hash_complete_left_join(self):
        f=runtime();response=f.drop_duplicates(['target_build','query_position','ef_search']).rename(columns={'target_build':'build_id'})
        self.assertEqual(entry.verify_response_hashes(f,response),1000)
        with self.assertRaises(ValueError):entry.verify_response_hashes(f,response.iloc[1:])
    def test_crossed_statistics_and_runtime_wrappers(self):
        f=runtime(('a','b','c'));dec=pd.DataFrame([dict(dataset='tiny',source_build=s,target_build=t,deployed_action=256,executed_action=256,decision='CANDIDATE_ACCEPTED',deployable=True,arm='test') for t in ('a','b','c') for s in ('a','b','c') if s!=t])
        cells=r3.attach_decisions(dec,r3.technical_cells(f));quality=cells.assign(failure=0,endpoint_failure=0)
        for qc in (q3,q4):
            got=qc.crossed_bootstrap(quality,repeats=7,seed=991)
            self.assertEqual(got['risk'],[0.,0.]);self.assertEqual(got['ndc_gain'],[.5,.5])
        for module,name in ((r3,'crossed_bootstrap'),(r4,'bootstrap')):
            original=getattr(module,name)
            safety={'tiny':{'point':{'risk':0.},'crossed_target_query_95ci':{'risk':[0.,0.]}}}
            if module is r4:safety={'tiny':{'test':safety['tiny']}}
            with tempfile.TemporaryDirectory() as temp,patch.object(module,name,side_effect=lambda values:original(values,repeats=7,seed=991)):
                result=module.analyze(f,dec,safety,Path(temp),3000)
                self.assertTrue((Path(temp)/'technical_runtime_cells.csv.gz').is_file())
                value=result['tiny'] if module is r3 else result['tiny']['test']
                self.assertGreater(value['point']['wall_gain'],0)
                self.assertEqual(value['point']['ndc_gain'],.5)
if __name__=='__main__':unittest.main()
