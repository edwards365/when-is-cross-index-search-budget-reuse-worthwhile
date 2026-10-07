"""Linux CI: actual native calls on a NEW 32-vector graph, never original data."""
import argparse,json,os,platform,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
from run_transfer import HERE,load,pin,sha
from run_phase import query_binary,write,CheckedProcess

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--profiles',type=Path,required=True);p.add_argument('--authorize-synthetic-only',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_only:p.error('Explicit synthetic opt-in required')
    if platform.system()!='Linux' or sys.version_info[:2]!=(3,11):raise ValueError('Linux3.11 required')
    if a.output.exists() or a.output.is_symlink():raise FileExistsError('New output only')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    import resource
    for k,v in ((resource.RLIMIT_AS,4*1024**3),(resource.RLIMIT_FSIZE,128*1024**2),(resource.RLIMIT_CPU,300),(resource.RLIMIT_CORE,0)):
        old=resource.getrlimit(k);cap=min([v]+[x for x in old if x>=0]);resource.setrlimit(k,(cap,cap))
    import numpy as np,h5py,hnswlib,faiss
    cfg=json.loads((HERE/'config.json').read_text());core=load(HERE/'historical_core.py','transfer_synthetic_core',cfg['core_sha256'])
    pin(a.profiles/'config.json',cfg['dependencies']['profiles_config']);helper=load(a.profiles/'native_entry.py','transfer_synthetic_build',cfg['dependencies']['profiles_entry'])
    for file,h in json.loads((a.profiles/'config.json').read_text())['files'].items():pin(a.profiles/file,h)
    out=a.output.parent.resolve(strict=True)/a.output.name;out.mkdir();write(out/'start.json',{'original_dataset_runs':0,'synthetic_base_rows':32,'query_rows':1000})
    try:
        native=out/'native';helper.build(native,'g++')
        vec=np.random.default_rng(814).normal(size=(1032,4)).astype('f4');ids=np.arange(32,1032,dtype='i8');members=np.arange(32,dtype='i8');src=out/'synthetic.h5'
        with h5py.File(src,'x') as f:f.create_dataset('train',data=vec)
        checks=[]
        for metric in ('l2','ip'):
            name='sift-1m-heldout' if metric=='l2' else 'arxiv-nomic-1.34m-heldout';prefix='sift' if metric=='l2' else 'arxiv';row={'name':name,'train_shape':[1032,4],'roles':{'source_design':ids[:500].tolist()}};graph=out/(metric+'.bin')
            core.build_e1a(vec,ids,np.array([],dtype='i8'),32,SimpleNamespace(seed=13,history='random',dataset=name),{'implementation':{'metric_by_dataset':{name:metric},'insertion_batch_rows':8192}},graph,metric,hnswlib)
            truths={}
            for phase in ('source','selection','certify','evaluate'):
                q=ids if phase=='evaluate' else ids[:500];held=set(map(int,ids))
                if phase=='source':tr=core.truth_e1a_source(row,{'metric':'squared_l2' if metric=='l2' else 'inner_product_on_original_normalized_float32','source_design_query_count':500},32,held,set(),src,8192,faiss,h5py)
                elif phase=='selection':tr=core.truth_e1a_selection(row,{name:{'metric':metric,'base_count':32}},SimpleNamespace(dataset=name),q,held,set(),src,faiss,h5py)
                else:tr=getattr(core,'truth_e1a_'+phase)(row,metric,32,q,held,set(),src,faiss,h5py)
                truths[phase]=tr['neighbor_raw_ids']
                ref=np.sum((vec[q,None,:].astype('f8')-vec[None,:32,:].astype('f8'))**2,axis=2) if metric=='l2' else -(vec[q].astype('f8')@vec[:32].T.astype('f8'))
                np.testing.assert_array_equal(tr['neighbor_raw_ids'],np.argsort(ref,axis=1)[:,:10])
                if phase!='selection':
                    if phase=='source':other=core.truth_e1b_source(row,metric,32,q,members,src,faiss,h5py)
                    else:other=getattr(core,'truth_e1b_'+phase)(row,{'metric':metric,'member_count':32},q,members,src,faiss,h5py)
                    for key in tr:np.testing.assert_array_equal(tr[key],other[key])
            source,s=core.e1a_source_response(ids[:500],src,SimpleNamespace(dataset=name),graph,{'serialized_count':32},{'action_grid':core.GRID},truths['source'],'synthetic',h5py,hnswlib)
            for phase in ('selection','certify','evaluate'):
                q=ids if phase=='evaluate' else ids[:500];folder=out/(metric+'_'+phase);folder.mkdir();qb=folder/'queries.qbin';query_binary(qb,src,q,np,h5py);proc=CheckedProcess(folder)
                arrays,errors=getattr(core,'e1a_'+phase+'_response')(q,len(q),src,name,graph,{'serialized_count':32},core.GRID,truths[phase],native/('replay1000' if phase=='evaluate' else 'replay500'),qb,folder/'counter.csv',h5py,hnswlib,proc,row)
                if errors or proc.waits!=[0]:raise ValueError('Native equivalence failed')
                checks.append({'metric':metric,'phase':phase,'native_rows':int(arrays['ndc'].size),'native_wait':0})
            source,s=core.source_response(ids[:500],src,row,{'prefix':prefix},graph,{'member_count':32},np.asarray(core.GRID,dtype=np.int32),truths['source'],h5py,hnswlib)
            cert,c=core.cert_response(ids[:500],src,row,{'prefix':prefix},graph,{'member_count':32},s['selected_source_action'],truths['certify'],h5py,hnswlib)
            ev,e=core.eval_response(ids,src,row,{'prefix':prefix},[graph,graph],[32,32],s['selected_source_action'],c['decision'],[truths['evaluate']]*2,h5py,hnswlib)
            if ev['topk'].shape!=(2,2,1000,10):raise ValueError('Paired evaluation shape')
        result={'status':'PASS_TRANSFER_NATIVE_SYNTHETIC','checks':checks,'truth_cores_tested':7,'metrics':['l2','ip'],'original_dataset_runs':0,'full_original_panel_validated':False,'historical_core_sha256':cfg['core_sha256']}
        write(out/'completed.json',result);print(json.dumps(result))
    except BaseException as e:write(out/'failure.json',{'error':repr(e)});raise

if __name__=='__main__':main()
