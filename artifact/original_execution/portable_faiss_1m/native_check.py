"""Bounded new E3 native graph plus four response cores; never original inputs."""
import argparse,contextlib,io,json,os,sys
from pathlib import Path
from types import SimpleNamespace
from run_faiss import load,sha,write,HERE
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--authorize-synthetic-only',action='store_true');a=p.parse_args()
    if not a.authorize_synthetic_only or a.output.exists():raise ValueError('Fresh synthetic output required')
    from synthetic_limits import install,finish
    contract=install()
    os.environ['FAISS_OPT_LEVEL']='AVX2'
    import faiss,numpy as np,h5py
    if faiss.__version__!='1.8.0' or faiss.get_compile_options().strip()!='OPTIMIZE AVX2':raise ValueError('Pinned E3 Faiss1.8 AVX2 required')
    faiss.omp_set_num_threads(1);a.output.mkdir();cfg=json.loads((HERE/'config.json').read_text());core=load(HERE/'historical_core.py','native_faiss1m_core',cfg['core_sha256']);results=[]
    for metric in ('l2','ip'):
        folder=a.output/metric;folder.mkdir();vectors=np.random.RandomState(42).normal(size=(1100,8)).astype('f4');base=np.arange(32,dtype='i8');source=folder/'tiny.h5'
        with h5py.File(source,'w') as f:f['train']=vectors
        dataset='sift-1m-heldout' if metric=='l2' else 'arxiv-nomic-1.34m-heldout';graph=folder/'index.faiss'
        core.build(vectors,base,SimpleNamespace(history='random',seed=13,dataset=dataset),graph,'tiny32',faiss)
        exact=faiss.IndexFlatL2(8) if metric=='l2' else faiss.IndexFlatIP(8);exact.add(vectors[base]);protocol={'source_design':{'native_efSearch_grid':core.GRID},'native_search':{'action_grid':core.GRID}}
        for phase in ('source','selection','certify','evaluate'):
            ids=np.arange(32,1032 if phase=='evaluate' else 532,dtype='i8');_,neighbors=exact.search(vectors[ids],10);dest=folder/(phase+'.npz')
            getattr(core,'response_'+phase)(ids,source,graph,{'effective_base_count':32},protocol,dest,neighbors,[16,4096],'tiny32',faiss,h5py)
            with np.load(dest) as r:
                if r['topk'].shape[1:]!=(len(ids),10) or np.any(r['hits']!=10):raise ValueError('Tiny exact-output check')
                results.append({'metric':metric,'phase':phase,'cells':int(r['hits'].size),'sha256':sha(dest)})
    used=finish(a.output);write(a.output/'completed.json',{'status':'PASS_NEW_TINY_FAISS1M_CORES','results':results,'old_inputs_accessed':False,'original_science_rerun':False,'resources':contract,'output_bytes_before_receipt':used})
if __name__=='__main__':main()
