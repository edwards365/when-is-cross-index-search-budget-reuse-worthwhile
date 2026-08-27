#!/usr/bin/env python3
"""Create deterministic artifact checksums and final inventory."""
from pathlib import Path
import hashlib, json
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-rcrs')
targets=[]
for base in (ROOT/'docs/theory_generalization',ROOT/'results/theory_generalization',ROOT/'manifests'):
    if not base.exists(): continue
    for p in base.rglob('*'):
        if p.is_file() and p.name!='checksums.sha256' and (base.name!='manifests' or 'theory_generalization' in p.name): targets.append(p)
targets=sorted(set(targets),key=lambda p:str(p.relative_to(ROOT)))
lines=[]
for p in targets: lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}")
out=ROOT/'results/theory_generalization/checksums.sha256';out.write_text('\n'.join(lines)+'\n')
inventory={'artifact_count':len(targets),'checksum_file':str(out.relative_to(ROOT)),'validation_dev_accessed':False,'formal_test_accessed':False}
(ROOT/'results/theory_generalization/final_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
print(json.dumps(inventory,indent=2))
