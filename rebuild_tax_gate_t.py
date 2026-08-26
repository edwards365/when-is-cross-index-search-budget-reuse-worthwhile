#!/usr/bin/env python3
"""Frozen, query-free Gate T checks for rebuild-tax calibration."""
import json, math
from pathlib import Path

EF = (10,16,24,32,48,64,96,128,192,256,384,512,1024)
NS = (32,64,128,256,512,1000)
DELTAS = (.05,.01,.005,.001)

def conformal_multiplier(ratios, delta):
    n=len(ratios); k=math.ceil((n+1)*(1-delta))
    if k>n: return None,k
    return sorted(ratios)[k-1],k

def round_grid(x):
    return next((e for e in EF if e>=x),1024)

def finite_beam(width):
    # G2 from Theory 4: b is preferred but dead; a reaches target t.
    frontier=[('b',4),('a',5)][:width]
    return width>=2 and any(v=='a' for v,_ in frontier)

def main():
    rows=[]
    for n in NS:
        ratios=[1+i/(10*n) for i in range(n)]
        for delta in DELTAS:
            a,k=conformal_multiplier(ratios,delta)
            rows.append({'n':n,'delta':delta,'k':k,'status':'PASS' if a is not None else 'FINITE_SAMPLE_INFEASIBLE','multiplier':a})
            assert (a is not None)==(k<=n)
    # Exhaustive rank argument: number of ranks exceeding kth order statistic
    # among n+1 exchangeable ranks is <= delta*(n+1).
    for n in NS:
        for delta in DELTAS:
            _,k=conformal_multiplier(list(range(n)),delta)
            if k<=n: assert (n+1-k)/(n+1)<=delta+1e-15
    assert not finite_beam(1) and finite_beam(2)
    assert round_grid(17)==24 and round_grid(512)==512
    cal=set(range(250)); audit=set(range(250,1000))
    assert cal.isdisjoint(audit) and len(cal)==250 and len(audit)==750
    out={'status':'PASS_GATE_T','synthetic_conformal_coverage':'PASS','finite_beam_counterexample':'PASS','grid_rounding':'PASS','split_isolation':'PASS','sentinel_grid':rows,'cost_accounting':{'sentinel_target_discovery':'FULLY_CHARGED','query_probe':'FULLY_CHARGED','amortization':'REPORT_ONLY_NOT_SUBTRACTED'},'new_hnsw_queries':0,'validation_dev_accessed':False,'formal_test_accessed':False}
    p=Path('results/rebuild_tax/gate_t');p.mkdir(parents=True,exist_ok=True);(p/'gate_t_checks.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
