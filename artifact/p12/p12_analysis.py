"""SIFT1M saved-return rescoring and conditional objectives; no ANN execution."""
import argparse, csv, json
from pathlib import Path
import h5py
import numpy as np

def write(p, rows):
    with p.open('x', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def solve(keys, safe, cost, ordered):
    _, inv=np.unique(keys, axis=0, return_inverse=True)
    table=np.array([np.where(safe[:,inv==j].all(1),cost[:,inv==j].sum(1),np.inf) for j in range(inv.max()+1)])
    bad=int((~np.isfinite(table).any(1)).sum())
    if bad:return None,bad
    if not ordered:return int(table.min(1).sum()),0
    dp=table[0]
    for r in table[1:]:dp=r+np.minimum.accumulate(dp)
    return (int(dp.min()) if np.isfinite(dp).any() else None),0

def objectives(h0,h1,ndc,names):
    rows=[]
    for mode,hs,ht in [('canonical',h0,h0),('target_ties',h0,h1),('joint_ties',h1,h1)]:
        ps=hs==10; pt=ht==10
        tails=np.logical_and.accumulate(ps[:,::-1],axis=1)[:,::-1]
        labels=np.where(tails.any(1),tails.argmax(1),11)
        tailt=np.logical_and.accumulate(pt[:,::-1],axis=1)[:,::-1]
        for t,target in enumerate(names):
            for subset in ['all','original_endpoint']:
                ix=np.arange(h0.shape[2]) if subset=='all' else np.flatnonzero(h0[t,-1]==10)
                v=np.delete(labels,t,axis=0)[:,ix].T
                for criterion,p in [('actual',pt),('stable_tail',tailt)]:
                    for summary in ['identity','vector','max','ordered_max']:
                        keys=np.arange(len(ix))[:,None] if summary=='identity' else v if summary=='vector' else v.max(1)[:,None]
                        total,bad=solve(keys,p[t][:,ix],ndc[t][:,ix],summary=='ordered_max')
                        rows.append(dict(mode=mode,target=str(target),subset=subset,criterion=criterion,summary=summary,n_query=len(ix),empty_cells=bad,feasible=int(total is not None),total_ndc='' if total is None else total,mean_ndc='' if total is None else total/len(ix)))
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);a=ap.parse_args();c=json.loads(Path(a.config).read_text());out=Path(c['work_dir']);out.mkdir(parents=True,exist_ok=False)
    with np.load(c['response']) as z:h=z['hits']; ret=z['topk']; qids=z['query_ids']; ndc=z['ndc'].astype(np.int64);names=z['build_ids'];grid=z['action_grid']
    with np.load(c['truth']) as z:truth=z['neighbor_raw_ids'];scores=z['scores'];assert np.array_equal(qids,z['query_ids'])
    assert h.shape==(8,11,1000) and ret.shape==(8,11,1000,10)
    assert np.all(np.diff(np.sort(ret,axis=-1),axis=-1)>0)
    wanted=np.unique(np.concatenate([qids,ret.ravel(),truth.ravel()]));vec=np.empty((len(wanted),128),np.int16)
    with h5py.File(c['hdf5'],'r') as f:
        train=f['train'];assert train.shape==(1000000,128)
        for b in range(0,len(train),8192):
            lo,hi=np.searchsorted(wanted,[b,min(b+8192,len(train))])
            if hi>lo:
                v=train[b:b+8192][wanted[lo:hi]-b];assert np.all(v==np.rint(v)) and v.min()>=0 and v.max()<=255
                vec[lo:hi]=v
    dists=np.empty(ret.shape,np.int64);td=np.empty(truth.shape,np.int64);tie=np.empty(h.shape,np.int16)
    for q in range(1000):
        vq=vec[np.searchsorted(wanted,qids[q])].astype(np.int64)
        dif=vec[np.searchsorted(wanted,ret[:,:,q])].astype(np.int64)-vq
        dists[:,:,q]=np.sum(dif*dif,axis=-1)
        dif=vec[np.searchsorted(wanted,truth[q])].astype(np.int64)-vq;td[q]=np.sum(dif*dif,axis=-1)
        assert np.array_equal(td[q],scores[q]) and np.all(np.diff(td[q])>=0)
        canonical=np.isin(ret[:,:,q],truth[q]).sum(-1);assert np.array_equal(canonical,h[:,:,q])
        boundary=td[q,-1];strict=truth[q,td[q]<boundary];ns=len(strict)
        assert np.all(np.isin(ret[:,:,q],strict)==(dists[:,:,q]<boundary))
        tie[:,:,q]=np.isin(ret[:,:,q],strict).sum(-1)+np.minimum(10-ns,(dists[:,:,q]==boundary).sum(-1))
    assert np.all(tie>=h)
    with (out/'rescored.npz').open('xb') as f:np.savez_compressed(f,canonical=h,tie_aware=tie,returned_squared_l2=dists,truth_squared_l2=td,query_ids=qids,build_ids=names,action_grid=grid)
    diag=[]
    for t,n in enumerate(names):
        for mode,x in [('canonical',h),('tie_aware',tie)]:
            fail=x[t,-1]<10;rescue=fail&(x[t,:-1]==10).any(0)
            diag.append(dict(target=str(n),mode=mode,endpoint_fail=int(fail.sum()),smaller_rescue=int(rescue.sum()),all_actions_fail=int(((x[t]<10).all(0)).sum()),changed_pass_events=int(((h[t]<10)&(x[t]==10)).sum())))
    write(out/'endpoint.csv',diag);write(out/'objectives.csv',objectives(h,tie,ndc,names))
    result=dict(status='ANALYSIS_COMPLETE_CHECK_PENDING',selected_vectors=len(wanted),all_truth_scores_exact=True,all_canonical_hits_exact=True,changed_hit_events=int((tie!=h).sum()),changed_pass_events=int(((h<10)&(tie==10)).sum()))
    (out/'analysis.json').write_text(json.dumps(result),encoding='utf-8')
    print((out/'analysis.json').read_text())
if __name__=='__main__':main()
