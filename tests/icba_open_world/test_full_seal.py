#!/usr/bin/env python3
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
assert json.load(open(ROOT/'manifests/icba_open_world_final_decision.json'))['sealed_data_accessed'] is False
g=list(csv.DictReader(open(ROOT/'results/icba_open_world/unified_gate_table.csv')));assert g[-1]['status']=='OPEN_WORLD_IMPOSSIBILITY_SUPPORTED_STRUCTURE_UNRESOLVED'
b=list(csv.DictReader(open(ROOT/'results/icba_open_world/build_cluster_bootstrap.csv')));assert len(b)==6 and all(float(x['cluster_bootstrap_ci_low'])>.05 for x in b)
s=list(csv.DictReader(open(ROOT/'results/icba_open_world/sentinel_learning_curve.csv')));assert all(float(x['under_rate'])>.05 for x in s if int(x['sentinel_k'])==256)
for line in open(ROOT/'results/icba_open_world/checksums.sha256'):
 h,p=line.rstrip().split('  ',1);assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
print('FULL_SEAL_TEST_PASS')
