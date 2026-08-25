from pathlib import Path

def test_frozen_grid():
 assert [10,16,24,32,48,64,96,128,192,256,384,512]==sorted({10,16,24,32,48,64,96,128,192,256,384,512})

def test_split_counts():
 import json
 d=json.loads(Path('manifests/ocgt_v3_query_split.json').read_text())['splits']
 assert len(d['calibration'])==125 and len(d['confirmatory_audit'])==375
 assert set(d['calibration']).isdisjoint(d['confirmatory_audit'])
 assert set(d['calibration'])|set(d['confirmatory_audit'])==set(range(500))
