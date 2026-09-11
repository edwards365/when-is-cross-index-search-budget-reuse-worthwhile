#!/usr/bin/env python3
"""Run the pure-code hotfix twice and compare byte hashes; no ANN search."""
import csv, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
OUT=ROOT/'results/graph_anns_iclr_phase1_1_hotfix'; DOC=ROOT/'docs/graph_anns_iclr_phase1_1_hotfix'; FIG=ROOT/'figures/graph_anns_iclr_phase1_1_hotfix'; MAN=ROOT/'manifests/graph_anns_iclr_phase1_1_hotfix_decision.json'

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def inventory():
    paths=[]
    for d in (DOC,OUT,FIG):
        for p in sorted(d.rglob('*')):
            if p.is_file() and p.name not in {'checksums.sha256','pure_code_replay.csv','replay_summary.json'} and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log'}: paths.append(p)
    for d in (ROOT/'scripts/graph_anns_iclr_phase1_1_hotfix', ROOT/'tests/graph_anns_iclr_phase1_1_hotfix'):
        for p in sorted(d.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log'}: paths.append(p)
    paths.append(MAN)
    return sorted(set(paths))

def make_checksum(paths):
    return '\n'.join(digest(p)+'  '+str(p.relative_to(ROOT)) for p in paths)+'\n'

def main():
    for p in (OUT/'checksums.sha256',OUT/'pure_code_replay.csv',OUT/'replay_summary.json'):
        if p.exists(): p.unlink()
    env=dict(os.environ); env['PYTHONPATH']='/home/wlk/data500/graph_anns_faiss_external_validity/python'
    snapshots=[]; checks=[]
    for i in (1,2):
        r=subprocess.run([sys.executable,'-m','scripts.graph_anns_iclr_phase1_1_hotfix.run_all'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if r.returncode: raise SystemExit(r.stderr)
        paths=inventory(); snapshots.append({str(p.relative_to(ROOT)):digest(p) for p in paths}); checks.append(make_checksum(paths))
    keys=sorted(set(snapshots[0])|set(snapshots[1]))
    rows=[{'path':k,'run1_sha256':snapshots[0].get(k,'MISSING'),'run2_sha256':snapshots[1].get(k,'MISSING'),'byte_identical':snapshots[0].get(k)==snapshots[1].get(k)} for k in keys]
    with open(OUT/'pure_code_replay.csv','w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={'run1_files':len(snapshots[0]),'run2_files':len(snapshots[1]),'all_core_byte_identical':all(x['byte_identical'] for x in rows),'manifest_byte_identical':snapshots[0].get(str(MAN.relative_to(ROOT)))==snapshots[1].get(str(MAN.relative_to(ROOT))),'checksum_inventory_byte_identical':checks[0]==checks[1],'ann_search_invoked':False}
    (OUT/'replay_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
