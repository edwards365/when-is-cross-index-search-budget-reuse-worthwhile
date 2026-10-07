"""Build unchanged replay sources and test only a new 32-vector synthetic graph."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,x):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2);f.write('\n')
def validate_csv(path,ids,grid,allowed):
    allowed=set(map(int,allowed));count=0
    with path.open(newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['query_id','ef','ndc','topk']:raise ValueError('CSV header')
        for ef in grid:
            for qid in ids:
                row=next(reader,None)
                if row is None or int(row['ef'])!=ef or int(row['query_id'])!=int(qid):raise ValueError('CSV role/action order')
                top=list(map(int,row['topk'].split(';')))
                if len(top)!=10 or len(set(top))!=10 or not set(top)<=allowed or int(qid) in top:raise ValueError('CSV top-k identity')
                if int(row['ndc'])<=0:raise ValueError('CSV NDC')
                count+=1
        if next(reader,None) is not None:raise ValueError('CSV trailing rows')
    return count
def child_limits():
    import resource
    for kind,cap in ((resource.RLIMIT_AS,4*1024**3),(resource.RLIMIT_FSIZE,16*1024**2),(resource.RLIMIT_CPU,120),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(kind);cap=min([cap]+[x for x in old if x>=0]);resource.setrlimit(kind,(cap,cap))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def execute(argv,cwd):
    result=subprocess.run(argv,cwd=cwd,capture_output=True,timeout=150,preexec_fn=child_limits)
    if result.returncode:raise RuntimeError(result.stderr.decode('utf-8')[-2000:])
    return result.stdout.decode('utf-8')
def build(output,compiler):
    if platform.system()!='Linux' or platform.machine()!='x86_64':raise ValueError('Linux x86_64 required')
    cfg=json.loads((HERE/'config.json').read_text())
    for name,h in cfg['files'].items():
        if sha(HERE/name)!=h:raise ValueError('Source/header changed')
    if output.exists() or output.is_symlink():raise FileExistsError('New build directory required')
    output=output.parent.resolve(strict=True)/output.name;output.mkdir(mode=0o700)
    record={'status':'BUILD_AND_SYNTHETIC_CHECK_STARTED','config_sha256':sha(HERE/'config.json'),
            'entry_sha256':sha(Path(__file__)),'synthetic_fixture_sha256':sha(HERE/'tiny_fixture.cpp'),
            'historical_binary_identity_claimed':False,'original_dataset_runs':0}
    write_json(output/'start.json',record)
    try:
        import numpy as np
        binaries={};commands=[]
        for source,name in [('e1a_ndc_replay.cpp','replay500'),('e1a_ndc_replay_evaluation.cpp','replay1000'),('tiny_fixture.cpp','tiny_fixture')]:
            argv=[compiler,'-std=c++17','-O3','-march=native','-I',str(HERE/'include'),str(HERE/source),'-o',str(output/name)]
            execute(argv,output);binaries[name]=sha(output/name)
            commands.append({'source':source,'flags':['-std=c++17','-O3','-march=native'],'actual_exit_code':0})
        version=execute([compiler,'--version'],output).splitlines()[0]
        rng=np.random.default_rng(719);base=rng.normal(size=(32,4)).astype('<f4');query=rng.normal(size=(1000,4)).astype('<f4')
        (output/'tiny_base.f32').write_bytes(base.tobytes());grid=[10,40,2400];records=[]
        for count in (500,1000):
            with (output/f'queries{count}.qbin').open('xb') as f:
                f.write(b'E1AQ0001'+struct.pack('<QQ',count,4))
                for i,v in enumerate(query[:count]):f.write(struct.pack('<q',10000+i)+v.tobytes())
        for metric in ('l2','ip'):
            index=output/(metric+'.bin');execute([str(output/'tiny_fixture'),str(output/'tiny_base.f32'),metric,str(index)],output)
            responses={}
            for count in (500,1000):
                csvpath=output/f'{metric}{count}.csv'
                execute([str(output/f'replay{count}'),str(index),str(output/f'queries{count}.qbin'),metric,','.join(map(str,grid)),str(count),'32',str(csvpath)],output)
                rows=validate_csv(csvpath,range(10000,10000+count),grid,range(32))
                with csvpath.open(newline='') as f:values=list(csv.DictReader(f))
                responses[count]=values
                ref=np.sum((query[:count,None,:].astype('f8')-base[None,:,:].astype('f8'))**2,axis=2) if metric=='l2' else query[:count].astype('f8')@base.T.astype('f8')
                expected=np.argsort(ref if metric=='l2' else -ref,axis=1)[:,:10]
                for i,row in enumerate(values[-count:]):np.testing.assert_array_equal(list(map(int,row['topk'].split(';'))),expected[i])
                records.append({'metric':metric,'queries':count,'rows':rows,'endpoint_ordered_ids_vs_float64':'PASS'})
            for g in range(len(grid)):
                if responses[500][g*500:(g+1)*500]!=responses[1000][g*1000:g*1000+500]:raise ValueError('500/1000 common-query mismatch')
        # A wrong shape must fail before producing a CSV.
        bad=output/'wrong-shape.csv'
        rejected=subprocess.run([str(output/'replay500'),str(output/'l2.bin'),str(output/'queries1000.qbin'),'l2','10','500','32',str(bad)],capture_output=True,timeout=10,preexec_fn=child_limits)
        if rejected.returncode==0 or bad.exists():raise ValueError('Shape rejection failed')
        record.update(status='PASS_NEW_BUILD_AND_SYNTHETIC_NATIVE_CHECKS',compiler=version,binaries=binaries,
                      compile_commands=commands,synthetic_results=records,shape_rejection=True,
                      portability_scope='New binaries; not original binary bytes, full-panel equivalence, or timing')
        write_json(output/'completed.json',record)
        print(json.dumps(record))
    except BaseException as e:write_json(output/'failure.json',{'status':'FAILED_NO_OVERWRITE_OR_RETRY','error':repr(e)});raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--compiler',default='g++');ap.add_argument('--authorize-build-and-synthetic-tests',action='store_true');a=ap.parse_args()
    if not a.authorize_build_and_synthetic_tests:ap.error('Explicit synthetic build opt-in required')
    build(a.output,a.compiler)
if __name__=='__main__':main()
