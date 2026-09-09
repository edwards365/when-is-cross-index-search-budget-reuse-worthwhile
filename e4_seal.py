#!/usr/bin/env python3
import hashlib
from pathlib import Path
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
bases=[ROOT/'docs/graph_anns_e4',ROOT/'results/graph_anns_e4',ROOT/'figures/graph_anns_e4',ROOT/'tests/graph_anns_e4']
files=[ROOT/'e4_preregister.py',ROOT/'e4_run_matrix.py',ROOT/'e4_analyze.py',ROOT/'e4_seal.py',ROOT/'manifests/graph_anns_e4_preregistration.json',ROOT/'manifests/graph_anns_e4_role_manifest.json',ROOT/'manifests/graph_anns_e4_confirmatory_decision.json']
for base in bases:
    files.extend(p for p in base.glob('*') if p.is_file() and p.name not in {'checksums.sha256','preflight_checksums.sha256'})
rows=[]
for p in sorted(set(files)):
    h=hashlib.sha256(p.read_bytes()).hexdigest();rows.append(f'{h}  {p.relative_to(ROOT)}')
(ROOT/'results/graph_anns_e4/checksums.sha256').write_text('\n'.join(rows)+'\n')
print(f'sealed_files={len(rows)}')
