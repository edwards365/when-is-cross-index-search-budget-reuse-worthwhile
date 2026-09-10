#!/usr/bin/env python3
import hashlib
import runpy
import sys
from pathlib import Path
import numpy  # load the compatible C++ runtime before pandas/h5py
sys.path.append('/home/wlk/data500/graph_anns_faiss_external_validity/python')
import faiss

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
S=ROOT/'tests/graph_anns_iclr_phase1'
for name in ('replay_phase1a.py','phase1a_supplement.py','phase1b_analyze_breakeven.py','phase1c_analyze.py','phase1_final_seal.py'):
 runpy.run_path(str(S/name),run_name='__main__')
files=sorted((ROOT/'results/graph_anns_iclr_phase1').glob('paper_table_P*.csv'))+sorted((ROOT/'results/graph_anns_iclr_phase1').glob('figure_P*_source.csv'))+[ROOT/'results/graph_anns_iclr_phase1/final_core.sha256']
for p in files:print(hashlib.sha256(p.read_bytes()).hexdigest(),p.relative_to(ROOT))
