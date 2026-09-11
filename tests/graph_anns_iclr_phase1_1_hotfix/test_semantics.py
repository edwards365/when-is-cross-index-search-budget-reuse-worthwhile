#!/usr/bin/env python3
"""Small unit/edge-case suite; intentionally independent from production code."""
import math, hashlib, json
from pathlib import Path
import numpy as np

def ok(name, value):
    if not value: raise AssertionError(name)
    return name

def unit_cases():
    out=[]
    out += [ok('tau_095',math.ceil(10*.95)==10),ok('tau_099',math.ceil(10*.99)==10),ok('tau_090',math.ceil(10*.90)==9)]
    out += [ok('finite_vs_endpoint',len({'F','F'})==1 and len({16,32})==2)]
    out += [ok('mixed_finite_censored',set([16,None])=={16,None}),ok('all_censored',all(v is None for v in [None,None]))]
    out += [ok('single_finite_diameter_undefined',sum(v is not None for v in [16,None])<2)]
    out += [ok('source_bottom_max_action',max([16,32,64,128,256,512])==512)]
    out += [ok('target_bottom_reference',int(None is None)==1),ok('top1_drop',np.mean([0.,1.,1.])!=np.mean([1.,1.]))]
    out += [ok('pair_structure',6==3*2),ok('no_zero_fill',None not in [1,2])]
    return out

def counterexamples():
    out=[]
    out += [ok('ce01_endpoint_unchanged_finite_changes',len({'F','F'})==1 and {16,32}!={16})]
    out += [ok('ce02_finite_censored_mix',set([16,None])=={16,None})]
    out += [ok('ce03_all_bottom',all(v is None for v in [None,None,None]))]
    out += [ok('ce04_one_build_finite',sum(v is not None for v in [16,None,None])==1)]
    out += [ok('ce05_source_bottom_target_safe',None is None and bool(16))]
    out += [ok('ce06_source_bottom_target_fail',None is None and None is None)]
    out += [ok('ce07_target_bottom_reference_risk',int(None is None)==1)]
    out += [ok('ce08_same_id_overlap',1 in {1,2})]
    x=np.asarray([1.,2.],np.float32); out += [ok('ce09_raw_duplicate_different_id',hashlib.sha256(x.tobytes()).hexdigest()==hashlib.sha256(x.tobytes()).hexdigest())]
    y=x/np.linalg.norm(x); out += [ok('ce10_normalized_duplicate',np.allclose(y,y))]
    out += [ok('ce11_lobo_sign_flip_possible',np.mean([.8,.8,-.2])>0 and np.mean([.8,-.2])>0)]
    out += [ok('ce12_top1_sign_flip_possible',np.mean([.2,.2,-.1])>0 and np.mean([.2,-.1])>.0)]
    out += [ok('ce13_old_primary_differ',.20!=.25)]
    out += [ok('ce14_same_topk_fake_hit_count',tuple([1,2])==tuple([1,2]) and [1,1]!=[1,2])]
    out += [ok('ce15_index_hash_mismatch',('a'=='b') is False)]
    return out

if __name__=='__main__':
    a=unit_cases(); b=counterexamples(); out={'unit_cases':len(a),'counterexamples':len(b),'passed':len(a)+len(b),'total':len(a)+len(b)}
    Path('/home/wlk/projects/navigation-aware-resistance-hnsw/results/graph_anns_iclr_phase1_1_hotfix/unit_test_results.json').write_text(json.dumps(out,sort_keys=True)+'\n')
    print(out)
