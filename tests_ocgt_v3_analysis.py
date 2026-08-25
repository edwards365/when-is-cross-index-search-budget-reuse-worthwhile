import json
from pathlib import Path
def test_primary_matrix_contract():
 d=json.loads(Path('manifests/ocgt_v3_preregistration.json').read_text());assert d['graphs_planned']==27 and d['rows_planned']==162000 and len(d['ef_grid'])==12
def test_split_contract():
 d=json.loads(Path('manifests/ocgt_v3_query_split.json').read_text())['splits'];assert len(d['calibration'])==125 and len(d['confirmatory_audit'])==375
