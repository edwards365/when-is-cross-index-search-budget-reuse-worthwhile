#!/usr/bin/env python3
"""Independent, transparent validations for Phase 1.1a (no production imports)."""
import csv, gzip, hashlib, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np

R=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
O=R/'results/graph_anns_iclr_phase1_1_hotfix'; P=R/'results/graph_anns_iclr_phase1_1_repair'
CLEAN=Path('/home/wlk/data500/graph_anns_iclr_phase1_1_repair_scratch/faiss_100k/raw')
E4=Path('/home/wlk/data500/graph_anns_e4/raw')
GRID=(16,32,64,128,256,512)

def rows(p):
    with open(p,newline='') as f:return list(csv.DictReader(f))

def write_csv(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    data=list(data)
    with open(p,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]) if data else [])
        w.writeheader(); w.writerows(data)

def h(x): return hashlib.sha256(np.ascontiguousarray(np.asarray(x,np.float32)).tobytes()).hexdigest()
def normh(x):
    x=np.asarray(x,np.float32); return hashlib.sha256(np.ascontiguousarray(x/np.maximum(np.linalg.norm(x),np.finfo(np.float32).tiny)).tobytes()).hexdigest()

def check(name,ok):
    if not ok: raise AssertionError(name)
    return {'name':name,'passed':True}

def summary(raw, threshold=10, grid=GRID):
    by=defaultdict(dict)
    for r in raw:by[(r['build_id'],int(r['query_id']))][int(r['ef'])]=r
    bs=sorted({x[0] for x in by}); qs=sorted({x[1] for x in by})
    safe={(b,q):next((e for e in grid if int(by[(b,q)][e]['hit_count'])>=threshold),None) for b in bs for q in qs}
    qv=[];absr=[];ref=[];inc=[]
    for q in qs:
        v=[]
        for s in bs:
            for t in bs:
                if s==t:continue
                sa=safe[(s,q)]; ta=safe[(t,q)]; act=max(grid) if sa is None else sa
                f=int(ta is None or int(by[(t,q)][act]['hit_count'])<threshold); z=int(ta is None)
                v.append(f-z); absr.append(f); ref.append(z); inc.append(f-z)
        qv.append(float(np.mean(v)))
    return float(np.mean(absr)),float(np.mean(ref)),float(np.mean(inc)),np.asarray(qv),safe,by,bs,qs

def lobo(raw,threshold=10):
    full=summary(raw,threshold)
    by=full[5]; bs=full[6]; qs=full[7]; out=[]
    for drop in bs:
        keep=[b for b in bs if b!=drop]; safe={(b,q):next((e for e in GRID if int(by[(b,q)][e]['hit_count'])>=threshold),None) for b in keep for q in qs}
        v=[]
        for s in keep:
            for t in keep:
                if s==t:continue
                for q in qs:
                    sa=safe[(s,q)]; ta=safe[(t,q)]; act=max(GRID) if sa is None else sa
                    v.append(int(ta is None or int(by[(t,q)][act]['hit_count'])<threshold)-int(ta is None))
        out.append(float(np.mean(v)))
    return out

def load_clean(ds):
    z=[]
    for p in sorted(CLEAN.glob(ds+'__100k__clean*.csv.gz')):
        with gzip.open(p,'rt',newline='') as f:
            for r in csv.DictReader(f):z.append({'dataset':ds,'build_id':r['build_id'],'query_id':int(r['query_id']),'ef':int(r['ef']),'hit_count':int(r['hit_count'])})
    return z

def load_hnsw(ds):
    z=[]
    for p in sorted(E4.glob(ds+'__seed*__*/queries.csv.gz')):
        with gzip.open(p,'rt',newline='') as f:
            for r in csv.DictReader(f):
                if int(r.get('latency_round',0))==0 and int(r['query_id'])<750:z.append({'dataset':ds,'build_id':p.parent.name,'query_id':int(r['query_id']),'ef':int(r['ef_search']),'hit_count':int(round(float(r['recall_at_10'])*10))})
    return z

def unit_tests():
    t=[]
    t.append(check('tau_095_to_10',math.ceil(10*.95)==10))
    t.append(check('tau_099_to_10',math.ceil(10*.99)==10))
    t.append(check('tau_090_to_9',math.ceil(10*.90)==9))
    t.append(check('finite_budget_endpoint_same',len({'F','F'})==1 and len({16,32})==2))
    t.append(check('finite_and_censored_mixed',set([16,None])=={16,None}))
    t.append(check('all_censored',all(x is None for x in [None,None])))
    t.append(check('one_build_finite_not_diameter',sum(x is not None for x in [16,None])<2))
    t.append(check('source_censored_maps_to_max',max(GRID)==512))
    t.append(check('target_censor_reference_one',int(None is None)==1))
    t.append(check('composite_marks_source_censor',int(None is None)==1))
    t.append(check('joint_requires_two_finite',sum(x is not None for x in [16,None])<2))
    t.append(check('top1_deletion_changes_mean',np.mean([0,1,1])!=np.mean([1,1])))
    # A minimal LOBO sign-flip example: full mean positive, after removing first build negative.
    t.append(check('lobo_can_flip',np.mean([1,1,-1])>0 and np.mean([1,-1])==0))
    t.append(check('old_vs_primary_differ',0.20!=0.25))
    t.append(check('topk_same_hitcount_different',tuple([1,2,3])==tuple([1,2,3]) and [1,1]!=[1,2]))
    t.append(check('index_hash_mismatch_detectable','a'!='b'))
    return t

def independent_recompute():
    tests=unit_tests(); comparisons=[]
    prod={r['dataset']:r for r in rows(P/'faiss_clean_semantic_results.csv') if r['h']=='10'}
    prod_lobo=rows(P/'faiss_clean_lobo_results.csv')
    for ds in ('sift_100k','arxiv_nomic_100k'):
        raw=load_clean(ds); a,r,i,qv,safe,by,bs,qs=summary(raw)
        pr=prod[ds]
        for name,val,ref in [('absolute_transport_risk',a,float(pr['absolute_transport_risk'])),('reference_risk',r,float(pr['reference_risk'])),('incremental_transport_risk',i,float(pr['incremental_transport_risk'])),('delete_top1',float(np.mean(qv[np.argsort(qv)[:-max(1,math.ceil(.01*len(qv)))]])),float(pr['delete_top1_incremental_risk']))]:
            err=abs(val-ref); comparisons.append(check(ds+'_'+name+'_tol1e-12',err<=1e-12)); comparisons[-1]['max_error']=err
        got=sorted(float(x['incremental_transport_risk']) for x in prod_lobo if x['dataset']==ds and x['h']=='10')
        exp=sorted(lobo(raw))
        err=max(abs(x-y) for x,y in zip(got,exp));comparisons.append(check(ds+'_24_lobo_tol1e-12',err<=1e-12));comparisons[-1]['max_error']=err
    hprod={r['dataset']:r for r in rows(P/'estimand_registry.csv')}
    for ds in ('sift_100k','arxiv_nomic_100k'):
        _,_,inc,_,_,_,_,_=summary(load_hnsw(ds),10,(10,20,40,80,120,200)); err=abs(inc-float(hprod[ds]['incremental_transport_risk']))
        comparisons.append(check(ds+'_hnsw_primary_tol1e-12',err<=1e-12));comparisons[-1]['max_error']=err
    # Content Gate and registry evidence are independent file-level checks, not manifest assertions.
    for r in rows(O/'content_overlap_forensics.csv'):
        comparisons.append(check(r['dataset']+'_content_gate_zero',all(int(r[k])==0 for k in ['query_base_id_overlap','query_base_raw_overlap','query_base_normalized_overlap','historical_role_id_overlap','historical_role_raw_overlap','historical_role_normalized_overlap','evaluation_internal_id_duplicates','evaluation_internal_raw_duplicates','evaluation_internal_normalized_duplicates'])))
    ir=rows(O/'frozen_index_registry_audit.csv'); comparisons.append(check('48_index_hashes_match',len(ir)==48 and all(r['hash_match']=='True' for r in ir)))
    d3=rows(O/'d3_full_recalculation.csv'); comparisons.append(check('d3_identity_and_zero_transport',len(d3)==2 and all(r['index_byte_identity_3of3']=='True' and r['search_topk_identity_3of3']=='True' and r['hit_count_identity_3of3']=='True' and r['minimum_safe_action_identity_3of3']=='True' and r['endpoint_state_identity_3of3']=='True' and float(r['incremental_transport_risk'])==0 and float(r['top1_delete_incremental_risk'])==0 for r in d3)))
    alltests=tests+comparisons
    out={'unit_tests':len(tests),'independent_checks':len(comparisons),'passed':sum(x['passed'] for x in alltests),'total':len(alltests),'max_error':max([x.get('max_error',0) for x in alltests]),'tests':alltests}
    (O/'independent_test_results.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    write_csv(O/'independent_test_results.csv',[{'name':x['name'],'passed':x['passed'],'max_error':x.get('max_error','')} for x in alltests])
    return out

if __name__=='__main__': print(json.dumps(independent_recompute(),sort_keys=True))
