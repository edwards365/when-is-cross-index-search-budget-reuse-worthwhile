import json, pathlib
r=pathlib.Path(__file__).resolve().parents[2]
x=json.loads((r/'manifests/graph_anns_e4_preregistration.json').read_text())
def test_frozen_contract():
 assert x['build_factorization']['total']==48
 assert x['search']['ef_grid']==[10,20,40,80,120,200]
 assert x['risk']['right_censored_is_failure']
