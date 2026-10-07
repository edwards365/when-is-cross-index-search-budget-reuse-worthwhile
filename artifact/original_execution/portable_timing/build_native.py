"""Compile unchanged timing source and test new 32-vector L2/IP fixtures only."""
import argparse
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
from timing import digest,pin,write_json,query_ids,reference,validate

HERE=Path(__file__).resolve().parent

def dependencies(folder,cfg):
    for name,h in cfg['dependencies']['portable_profiles'].items():pin(folder/name,h)
    pc=json.loads((folder/'config.json').read_text())
    for name,h in pc['files'].items():pin(folder/name,h)

def build(output,profiles,compiler='g++'):
    if platform.system()!='Linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11): raise ValueError('Linux x86_64 Python3.11 required')
    cfg=json.loads((HERE/'config.json').read_text());dependencies(profiles,cfg);pin(HERE/'e1a_runtime_native.cpp',cfg['source_sha256'])
    if output.exists() or output.is_symlink():raise FileExistsError('New output required')
    spec=importlib.util.spec_from_file_location('timing_profile_native',profiles/'native_entry.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    output=output.parent.resolve(strict=True)/output.name;output.mkdir(mode=0o700)
    write_json(output/'start.json',{'status':'NEW_NATIVE_BUILD_AND_TINY_TEST_STARTED','original_data_runs':0})
    try:
        import numpy as np,struct
        bins={}
        for source,name in [(HERE/'e1a_runtime_native.cpp','runtime'),(profiles/'e1a_ndc_replay_evaluation.cpp','profile'),(profiles/'tiny_fixture.cpp','fixture')]:
            helper.execute([compiler,'-std=c++17','-O3','-march=native','-I',str(profiles/'include'),str(source),'-o',str(output/name)],output)
            bins[name]=digest(output/name)
        rng=np.random.default_rng(914);base=rng.normal(size=(32,4)).astype('<f4');queries=rng.normal(size=(1000,4)).astype('<f4')
        (output/'base.f32').write_bytes(base.tobytes())
        qbin=output/'queries.qbin'
        with qbin.open('xb') as f:
            f.write(b'E1AQ0001'+struct.pack('<QQ',1000,4))
            for i,q in enumerate(queries):f.write(struct.pack('<q',10000+i)+q.tobytes())
        ids=query_ids(qbin);grid=cfg['action_grid'];checks=[]
        for metric in ('l2','ip'):
            graph=output/(metric+'.bin');profile=output/(metric+'_profile.csv');timed=output/(metric+'_timed.csv')
            helper.execute([str(output/'fixture'),str(output/'base.f32'),metric,str(graph)],output)
            helper.execute([str(output/'profile'),str(graph),str(qbin),metric,','.join(map(str,grid)),'1000','32',str(profile)],output)
            expected=reference(profile,ids,grid)
            scores=np.sum((queries[:,None,:].astype('f8')-base[None,:,:].astype('f8'))**2,axis=2) if metric=='l2' else -(queries.astype('f8')@base.T.astype('f8'))
            truth=np.argsort(scores,axis=1)[:,:10]
            for i in range(1000):np.testing.assert_array_equal(expected[(2400,i)],truth[i])
            helper.execute([str(output/'runtime'),str(graph),str(qbin),metric,','.join(map(str,grid)),'32',str(profile),'1000','991','7',str(timed)],output)
            _,_,audit=validate(timed,ids,grid,expected);checks.append({'metric':metric,**audit})
        rejected=subprocess.run([str(output/'runtime'),str(graph),str(qbin),'ip',','.join(map(str,grid)),'32',str(profile),'1000','991','6',str(output/'bad.csv')],capture_output=True,timeout=10,preexec_fn=helper.child_limits)
        if rejected.returncode==0 or (output/'bad.csv').exists():raise ValueError('Wrong repetition count not rejected')
        record={'status':'PASS_NEW_NATIVE_TIMING_BUILD_AND_SYNTHETIC_CHECKS','config_sha256':digest(HERE/'config.json'),
            'build_entry_sha256':digest(Path(__file__)),'validator_sha256':digest(HERE/'timing.py'),'binaries':bins,
            'compiler':helper.execute([compiler,'--version'],output).splitlines()[0],'flags':['-std=c++17','-O3','-march=native'],
            'synthetic_results':checks,'wrong_reps_rejected':True,'original_data_runs':0,'historical_timing_replaced':False}
        write_json(output/'completed.json',record);print(json.dumps(record))
    except BaseException as e:write_json(output/'failure.json',{'status':'FAILED_NO_RETRY','error':repr(e)});raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--profiles',type=Path,required=True)
    p.add_argument('--compiler',default='g++');p.add_argument('--authorize-build-and-synthetic-tests',action='store_true');a=p.parse_args()
    if not a.authorize_build_and_synthetic_tests:p.error('Explicit synthetic build opt-in required')
    build(a.output,a.profiles.resolve(strict=True),a.compiler)

if __name__=='__main__':main()
