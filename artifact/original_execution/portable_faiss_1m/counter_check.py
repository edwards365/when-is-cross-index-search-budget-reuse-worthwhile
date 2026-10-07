"""Tiny native successful-source counter/event checks, both metrics, original auditor."""
import argparse,json,struct,sys
from pathlib import Path
from run_faiss import HERE,sha,write
from run_supplement import wait,check_stage
def fbin(p,x):
    x=np.ascontiguousarray(x,dtype='<f4')
    with p.open('xb') as f:f.write(struct.pack('<II',*x.shape));f.write(x.tobytes())
def main():
    p=argparse.ArgumentParser();p.add_argument('--native-check',type=Path,required=True);p.add_argument('--counter-build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--authorize-synthetic-only',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_only or a.output.exists():raise ValueError('Fresh synthetic output')
    from synthetic_limits import install,finish
    contract=install()
    global np
    import numpy as np,h5py
    native=json.loads((a.native_check/'completed.json').read_text());build=json.loads((a.counter_build/'completed.json').read_text())
    if native['status']!='PASS_NEW_TINY_FAISS1M_CORES' or build['status']!='NEW_CORRECTED_COUNTER_BUILD_CONTROLS_PASS':raise ValueError('New native prerequisites')
    a.output.mkdir();results=[];audits=[];folders={}
    for metric in ('l2','ip'):
        root=a.output/metric;root.mkdir();folders[metric]=root;src=a.native_check/metric
        with h5py.File(src/'tiny.h5','r') as f:vectors=f['train'][:]
        fbin(root/'base.fbin',vectors[:32]);fbin(root/'source.fbin',vectors[32:532]);fbin(root/'evaluation.fbin',vectors[32:1032]);(root/'raw.i64').write_bytes(np.arange(32,dtype='<i8').tobytes())
        with np.load(src/'source.npz') as f:actions=f['action_grid'].tolist();ids=f['query_ids'].tolist()
        prefix=root/'source';wait([str((a.counter_build/'counter').resolve()),str((src/'index.faiss').resolve()),str((root/'source.fbin').resolve()),','.join(map(str,actions)),str(prefix.resolve()),'events'],root,'native_source',120)
        c={'query_count':500,'dim':8,'prefix':str(prefix.resolve()),'actions':actions,'query':str((root/'source.fbin').resolve()),'base':str((root/'base.fbin').resolve()),'base_count':32,'base_raw_ids':str((root/'raw.i64').resolve()),'reference':str((src/'source.npz').resolve()),'query_ids':ids,'metric':metric.upper(),'pins':{}}
        config=root/'source_audit_config.json';write(config,c);wait([sys.executable,str(HERE/'audit_e6_faiss_exact_dc_v1.py'),'--config',str(config)],root,'source_audit',120)
        report=json.loads((root/'source_audit.stdout').read_text());write(root/'source_audit.json',report);audits.append(str((root/'source_audit.json').resolve()));results.append({'metric':metric,'source_events':report['event_count'],'source_status':report['status']})
    for metric,root in folders.items():
        src=a.native_check/metric
        with np.load(src/'evaluate.npz') as f:actions=f['action_grid'].tolist();ids=f['query_ids'].tolist()
        prefix=root/'target';wait([str((a.counter_build/'counter').resolve()),str((src/'index.faiss').resolve()),str((root/'evaluation.fbin').resolve()),','.join(map(str,actions)),str(prefix.resolve()),'none'],root,'native_target',120)
        roles=root/'roles.json';write(roles,{'datasets':[{'name':'tiny','roles':{'target_evaluation':ids}}]});config=root/'target_audit_config.json';write(config,{'role':'target_evaluation','query_count':1000,'dim':8,'prefix':str(prefix.resolve()),'actions':actions,'query_ids':ids,'dataset':'tiny','build':'tiny','roles':str(roles.resolve()),'source_audit_reports':audits,'reference':str((src/'evaluate.npz').resolve()),'pins':{}})
        wait([sys.executable,str(HERE/'audit_e6_faiss_target_counts_v1.py'),'--config',str(config)],root,'target_audit',120)
        report=json.loads((root/'target_audit.stdout').read_text());results.append({'metric':metric,'target_status':report['status'],'target_cells':len(actions)*1000})
    used=finish(a.output);write(a.output/'completed.json',{'status':'PASS_TINY_CORRECTED_COUNTER_SOURCE_EVENTS_AND_TARGET_IDS','results':results,'native_and_audit_waits':8,'original_data_accessed':False,'resources':contract,'output_bytes_before_receipt':used})
if __name__=='__main__':main()
