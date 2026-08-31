#!/usr/bin/env python3
import csv,json
from pathlib import Path
r=Path(__file__).resolve().parents[2]
m=json.loads((r/'manifests/icba_stable_build_pilot_decision.json').read_text())
c=[m['decision']=='INSUFFICIENT_STORAGE_FOR_REPRODUCIBLE_PILOT',m['resource_gate']=='FAIL',m['free_bytes']<m['mandatory_reserve_bytes']+m['expected_additions_bytes'],not m['validation_dev_accessed'],not m['formal_test_accessed'],not m['certification_reserved_accessed'],not m['evaluation_reserved_accessed'],not m['independent_confirmation_authorized'],m['sift_smoke']=='NOT_RUN',m['arxiv_pilot']=='NOT_RUN',m['tracer_fields_passed']==0,m['cfsr_lite']=='NOT_IMPLEMENTED']
c += [len(list((r/'docs/icba_stable_build_pilot').glob('*.md')))==13,len(list((r/'figures/icba_stable_build_pilot').glob('*.png')))==12,len(list((r/'figures/icba_stable_build_pilot').glob('*.pdf')))==12]
g=list(csv.DictReader((r/'results/icba_stable_build_pilot/unified_gate_table.csv').open())); c += [g[0]['status']=='FAIL',g[-1]['status']=='NOT_AUTHORIZED']
assert all(c),(len(c),[i for i,x in enumerate(c) if not x]); print('PASS',len(c),'checks')
