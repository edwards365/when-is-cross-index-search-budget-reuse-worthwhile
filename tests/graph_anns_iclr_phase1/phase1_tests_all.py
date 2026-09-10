#!/usr/bin/env python3
import runpy
import sys
from pathlib import Path
import numpy
sys.path.append('/home/wlk/data500/graph_anns_faiss_external_validity/python')
import faiss
S=Path('/home/wlk/projects/navigation-aware-resistance-hnsw/tests/graph_anns_iclr_phase1')
for name in ('test_phase1a_core.py','test_phase1b_seal.py','test_phase1c.py'):
 runpy.run_path(str(S/name),run_name='__main__')
print('PHASE1_ALL_TEST_SUITES_PASSED')
