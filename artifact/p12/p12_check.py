"""Independent set-based objectives and norm/dot distance verification."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import h5py

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);a=ap.parse_args();c=json.loads(Path(a.config).read_text());out=Path(c['work_dir']);assert not (out/'check.json').exists()
    with np.load(c['response']) as z:ret=z['topk'];h=z['hits'];ids=z['query_ids'];n=z['ndc'].astype(np.int64);names=z['build_ids'].tolist()
    with np.load(c['truth']) as z:tr=z['neighbor_raw_ids'];scores=z['scores'];assert np.array_equal(ids,z['query_ids'])
    with np.load(out/'rescored.npz') as z:saved=z['tie_aware'];rd=z['returned_squared_l2'];td=z['truth_squared_l2']
    allids=sorted(set(map(int,ret.ravel()))|set(map(int,tr.ravel()))|set(map(int,ids)))
    vectors={}
    with h5py.File(c['hdf5'],'r') as f:
        ds=f['train'];cursor=0
        for start in range(0,len(ds),8192):
            end=start+8192;stop=cursor
            while stop<len(allids) and allids[stop]<end:stop+=1
            if stop>cursor:
                block=ds[start:end]
                for raw in allids[cursor:stop]:
                    v=block[raw-start];assert all(float(x).is_integer() and 0<=x<=255 for x in v);vectors[raw]=v.astype(np.int64)
            cursor=stop
    got=np.empty(h.shape,np.int16)
    for q in range(1000):
        query=vectors[int(ids[q])];qnorm=int(query@query)
        exact=np.array([int(vectors[int(i)]@vectors[int(i)])+qnorm-2*int(vectors[int(i)]@query) for i in tr[q]])
        assert np.array_equal(exact,scores[q]) and np.array_equal(exact,td[q])
        strict=set(int(i) for i,d in zip(tr[q],exact) if d<exact[-1]);truthset=set(map(int,tr[q]))
        for t in range(8):
            for aidx in range(11):
                rr=list(map(int,ret[t,aidx,q]));assert len(set(rr))==10
                dd=[int(vectors[i]@vectors[i])+qnorm-2*int(vectors[i]@query) for i in rr]
                assert dd==rd[t,aidx,q].tolist()
                assert len(set(rr)&truthset)==int(h[t,aidx,q])
                assert set(i for i,d in zip(rr,dd) if d<exact[-1])==set(rr)&strict
                got[t,aidx,q]=len(set(rr)&strict)+min(10-len(strict),sum(d==exact[-1] for d in dd))
    assert np.array_equal(got,saved)
    rows=list(csv.DictReader((out/'objectives.csv').open(encoding='utf-8')))
    for row in rows:
        mode=row['mode'];t=names.index(row['target']);hs=h if mode!='joint_ties' else got;ht=h if mode=='canonical' else got
        ix=list(range(1000)) if row['subset']=='all' else [q for q in range(1000) if h[t,-1,q]==10]
        groups={}
        for q in ix:
            labels=[]
            for s in range(8):
                if s!=t:labels.append(next((j for j in range(11) if all(hs[s,j:,q]==10)),11))
            key=(q,) if row['summary']=='identity' else tuple(labels) if row['summary']=='vector' else (max(labels),)
            groups.setdefault(key,[]).append(q)
        costs=[];empty=0
        for key in sorted(groups):
            members=groups[key];values=[]
            for j in range(11):
                ok=all(ht[t,j,q]==10 for q in members) if row['criterion']=='actual' else all(np.all(ht[t,j:,q]==10) for q in members)
                values.append(sum(int(n[t,j,q]) for q in members) if ok else None)
            empty+=int(all(v is None for v in values));costs.append(values)
        if row['summary']=='ordered_max':
            dp=costs[0]
            for vals in costs[1:]:
                new=[]
                for j,v in enumerate(vals):
                    prior=[x for x in dp[:j+1] if x is not None];new.append(v+min(prior) if v is not None and prior else None)
                dp=new
            finite=[v for v in dp if v is not None];total=min(finite) if finite else None
        else:total=None if empty else sum(min(v for v in vv if v is not None) for vv in costs)
        assert empty==int(row['empty_cells']) and (total is not None)==bool(int(row['feasible']))
        assert str(total) == row['total_ndc'] if total is not None else row['total_ndc']==''
    for r in csv.DictReader((out/'endpoint.csv').open(encoding='utf-8')):
        t=names.index(r['target']);x=h if r['mode']=='canonical' else got
        fail=[q for q in range(1000) if x[t,10,q]!=10]
        assert len(fail)==int(r['endpoint_fail'])
        assert sum(any(x[t,j,q]==10 for j in range(10)) for q in fail)==int(r['smaller_rescue'])
    result=dict(status='PASS',all_returned_distances_checked=int(ret.size),all_truth_distances_checked=int(tr.size),all_hits_checked=int(h.size),objectives_checked=len(rows),scope='independent selected-vector distance and saved-response analysis; saved exhaustive truth trusted for global optimality')
    with (out/'check.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=='__main__':main()
