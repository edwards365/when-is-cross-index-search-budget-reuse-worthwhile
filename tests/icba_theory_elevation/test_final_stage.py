#!/usr/bin/env python3
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
m=json.load(open(ROOT/'manifests/icba_theory_elevation_decision.json'))
assert m['decision']=='GENERAL_THEORY_STRENGTHENED_NO_RECOVERY_CHANNEL'
assert m['baseline_exactly_reproduced'] is False and not m['validation_dev_accessed'] and not m['formal_test_accessed']
assert m['tow1a']==m['tow1b']=='FORMAL_PROOF_COMPLETE' and not m['algorithm_design_authorized']
for line in open(ROOT/'results/icba_theory_elevation/checksums.sha256'):
 h,p=line.rstrip().split('  ',1); assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
print('THEORY_ELEVATION_FINAL_TEST_PASS')
