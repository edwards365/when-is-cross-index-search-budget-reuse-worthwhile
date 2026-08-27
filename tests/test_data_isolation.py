import json
from pathlib import Path

ROOT=Path(__file__).parents[1]

def test_query_split_is_disjoint_and_complete():
    m=json.loads((ROOT/"manifests/icba_micro_closure_query_split.json").read_text())
    assert m["seed"]==991
    for x in m["datasets"].values():
        a=set(x["sentinel_query_ids"]); b=set(x["evaluation_query_ids"])
        assert len(a)==256 and len(b)==744 and not a&b and a|b==set(range(1000))

def test_firewall_manifest_is_sealed():
    m=json.loads((ROOT/"manifests/icba_micro_closure_query_split.json").read_text())
    assert m["firewall"]=={"validation_dev":"SEALED","formal_test":"SEALED"}
