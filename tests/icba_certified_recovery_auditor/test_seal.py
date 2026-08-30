#!/usr/bin/env python3
import csv,json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[2]
d=json.loads((r/'manifests/icba_certified_recovery_auditor_decision.json').read_text())
checks=[]
checks += [d['decision']=='NO_DEPLOYABLE_BASE_POLICY_CLOSE_RECOVERY_ROUTE', d['pilot']=='NOT_RUN_DUE_F1', d['confirmation']=='NOT_RUN_DUE_F1']
checks += [not d['validation_dev_accessed'],not d['formal_test_accessed'],not d['glove_accessed'],not d['new_index_built']]
checks += [(r/'docs/icba_certified_recovery_auditor'/x).exists() for x in ['final_report.md','stable_build_pivot_protocol.md','deployability.md','safety_statement.md']]
checks += [(r/'results/icba_certified_recovery_auditor'/x).exists() for x in ['trace_integrity.csv','base_policy.csv','rung_actions.csv','certification.csv','unified_gate.csv','total_cost.csv']]
g=list(csv.DictReader((r/'results/icba_certified_recovery_auditor/unified_gate.csv').open())); checks += [len(g)==7,g[0]['gate']=='T',g[1]['status']=='FAIL']
assert len(checks)>=20 and all(checks), (len(checks),[i for i,x in enumerate(checks) if not x])
print(f'PASS {len(checks)} checks')
