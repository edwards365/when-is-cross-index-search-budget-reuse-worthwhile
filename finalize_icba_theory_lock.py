#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs');R=ROOT/'results/icba_theory_lock'
roots=[ROOT/'docs/icba_theory_lock',R,ROOT/'figures/icba_theory_lock']
files=[]
for base in roots:
 for p in base.rglob('*'):
  if p.is_file() and p.name not in {'checksums.sha256','final_inventory.json'}:files.append(p)
for p in (ROOT/'manifests').glob('icba_theory_lock_*.json'):files.append(p)
files=sorted(set(files),key=lambda p:str(p.relative_to(ROOT)))
inventory={'artifact_count_excluding_inventory_and_checksum':len(files),'validation_dev_accessed':False,'formal_test_accessed':False}
(R/'final_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
files.append(R/'final_inventory.json');files=sorted(files,key=lambda p:str(p.relative_to(ROOT)))
lines=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}' for p in files]
(R/'checksums.sha256').write_text('\n'.join(lines)+'\n');print(json.dumps(inventory,indent=2))
