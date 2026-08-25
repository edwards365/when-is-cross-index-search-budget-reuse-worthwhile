#!/usr/bin/env python3
"""Run seeds 59/71 through the exact frozen Gate-R implementation.

Each graph is repeated twice as a conservative determinism audit. Only rep1 is
part of the preregistered 27-graph primary matrix; rep2 is audit-only.
"""
import hashlib, subprocess, sys, tempfile
from pathlib import Path

root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt-v3')
source=root/'run_ocgt_v3_gate_r.py'; frozen=source.read_text()
expected='db37a9915a63b2b18c5152b0e46f4e92b46e19d4c2903f0cb54d88e3e1ac8a77'
actual=hashlib.sha256(source.read_bytes()).hexdigest()
if actual!=expected: raise RuntimeError(f'Gate-R runner hash changed: {actual}')
for seed in (59,71):
    transformed=frozen.replace("OUT=ROOT/'results/index_conditionality/ocgt_v3/gate_r'",f"OUT=ROOT/'results/index_conditionality/ocgt_v3/main_seed{seed}'")
    transformed=transformed.replace("seed43",f"seed{seed}").replace("'43'",f"'{seed}'").replace(",43,",f",{seed},").replace("ocgt-v3-gate-r",f"ocgt-v3-main-seed{seed}")
    with tempfile.NamedTemporaryFile('w',suffix='.py',delete=False) as f:f.write(transformed);path=f.name
    subprocess.run([sys.executable,path],cwd=root,check=True)
