#!/usr/bin/env python3
import csv,gzip,hashlib,json
from pathlib import Path
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');RAW=ROOT/'results/hardness_portability_100k/realistic_raw';DER=ROOT/'results/hardness_portability_100k/realistic_derived'
expected={(d,s,o) for d in ('sift_100k','glove100_100k','arxiv_nomic_100k') for s in (43,59,71) for o in ('natural_source_order','cluster_block_order')};seen=set();evidence=[];fail=[]
for mp in sorted(RAW.glob('*.metadata.json')):
 m=json.loads(mp.read_text());key=(m['dataset'],m['graph_seed'],m['insertion_order']);seen.add(key);cp=mp.with_name(mp.name.replace('.metadata.json','.csv.gz'))
 if not cp.exists():fail.append('missing:'+cp.name);continue
 with gzip.open(cp,'rt',newline='') as f:rows=list(csv.DictReader(f))
 if len(rows)!=12000 or len({(r['query_id'],r['ef_search']) for r in rows})!=12000:fail.append('coverage:'+cp.name)
 evidence.append({'path':str(cp.relative_to(ROOT)),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'rows':len(rows),'metadata_sha256':hashlib.sha256(mp.read_bytes()).hexdigest()})
if seen!=expected:fail.append('matrix')
d=json.loads((DER/'realistic_history_decision.json').read_text())
if d['graphs']!=18 or d['rows']!=216000:fail.append('analysis_counts')
out={'schema_version':1,'protocol':'Query Hardness Is Not Portable 100K','status':d['status'] if not fail else 'INVALID_100K_SCALE_PROTOCOL','gate_pass':d['gate_pass'] and not fail,'gate_by_dataset':d['gate_by_dataset'],'graphs':len(seen),'rows':sum(x['rows'] for x in evidence),'failures':fail,'temporary_indexes_deleted':True,'formal_test_accessed':False,'decision_sha256':hashlib.sha256((DER/'realistic_history_decision.json').read_bytes()).hexdigest(),'evidence':evidence}
(ROOT/'manifests/hardness_portability_100k/realistic_history_gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('status','gate_pass','gate_by_dataset','graphs','rows','failures')},indent=2))
if fail:raise SystemExit(1)
