#!/usr/bin/env python3
"""Run two deterministic read/replay passes and compare core output hashes."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
RUNNER=ROOT/'tests/graph_anns_iclr_phase1_1/phase1_1_runner.py'
OUT=ROOT/'results/graph_anns_iclr_phase1_1'
FILES=('discrete_workpoint_equivalence.csv','discrete_hit_sensitivity.csv',
       'deterministic_semantic_reanalysis.csv','deterministic_gate_v2.csv',
       'faiss_100k_semantic_results.csv','faiss_100k_hit_sensitivity.csv',
       'faiss_100k_gate.csv')

def digest(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--runs',type=int,default=2); a=ap.parse_args()
    env=os.environ.copy(); env.setdefault('PYTHONPATH','/home/wlk/data500/graph_anns_faiss_external_validity/python'); env['PYTHONPATH']='/home/wlk/data500/graph_anns_faiss_external_validity/python:'+env.get('PYTHONPATH','')
    env['FAISS_LIMIT']='24'
    records=[]
    for i in range(a.runs):
        for mode in ('stage1','stage2','stage3'):
            subprocess.run([sys.executable,str(RUNNER),'--mode',mode],cwd=ROOT,env=env,check=True)
        records.append({'run':i+1,'hashes':{f:digest(OUT/f) for f in FILES if (OUT/f).exists()}})
    baseline=records[0]['hashes']; identical=all(r['hashes']==baseline for r in records[1:])
    out=OUT/'replay_hash_check.json'; out.write_text(json.dumps({'runs':records,'core_byte_identical':identical},indent=2)+'\n')
    print(json.dumps({'runs':a.runs,'core_byte_identical':identical},indent=2))
    if not identical: raise SystemExit(1)

if __name__=='__main__': main()
