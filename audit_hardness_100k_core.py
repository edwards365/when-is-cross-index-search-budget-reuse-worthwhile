#!/usr/bin/env python3
import csv, gzip, hashlib, json
from pathlib import Path

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k')
RAW=ROOT/'results/hardness_portability_100k/core_raw'
expected={(d,s,o) for d in ('sift_100k','glove100_100k','arxiv_nomic_100k') for s in (43,59,71) for o in ('random','lid_ascending','lid_descending')}
seen=set(); evidence=[]; failures=[]
for meta_path in sorted(RAW.glob('*.metadata.json')):
 meta=json.loads(meta_path.read_text());key=(meta['dataset'],meta['graph_seed'],meta['insertion_order']);seen.add(key)
 csv_path=meta_path.with_name(meta_path.name.replace('.metadata.json','.csv.gz'))
 if not csv_path.exists():failures.append('missing:'+csv_path.name);continue
 with gzip.open(csv_path,'rt',newline='') as handle:
  reader=csv.DictReader(handle); rows=list(reader)
 cells={(int(r['query_id']),int(r['ef_search'])) for r in rows}
 if len(rows)!=12000 or len(cells)!=12000:failures.append('coverage:'+csv_path.name)
 if any(r['success']!='True' or r['native_or_instrumented']!='instrumented_verified_against_native_per_row' for r in rows):failures.append('native:'+csv_path.name)
 evidence.append({'path':str(csv_path.relative_to(ROOT)),'sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest(),'rows':len(rows),'metadata_path':str(meta_path.relative_to(ROOT)),'metadata_sha256':hashlib.sha256(meta_path.read_bytes()).hexdigest()})
if seen!=expected:failures.append('matrix:'+str(sorted(expected-seen)))
summary_path=ROOT/'results/hardness_portability_100k/derived/core_gate_summary.json'
summary=json.loads(summary_path.read_text())
if summary['graphs']!=27 or summary['rows']!=324000:failures.append('analysis_counts')
audit={'schema_version':1,'protocol':'Query Hardness Is Not Portable 100K','status':'PASS_CORE_MATRIX_AUDIT' if not failures else 'INVALID_100K_SCALE_PROTOCOL','graphs':len(seen),'rows':sum(x['rows'] for x in evidence),'failures':failures,'temporary_indexes_deleted':True,'formal_test_accessed':False,'core_gate_status':summary['status'],'analysis_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),'evidence':evidence}
path=ROOT/'manifests/hardness_portability_100k/run_matrix_audit.json';path.write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:audit[k] for k in ('status','graphs','rows','failures','core_gate_status')},indent=2))
if failures:raise SystemExit(1)
