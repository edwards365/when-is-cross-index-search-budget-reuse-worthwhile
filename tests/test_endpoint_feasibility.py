import csv
from pathlib import Path

ROOT=Path(__file__).parents[1]
ROWS=list(csv.DictReader((ROOT/"results/icba_micro_closure/endpoint_audit.csv").open()))

def test_all_81_graphs_complete_and_consistent():
    assert len(ROWS)==81
    assert all(x["grid_complete"]=="True" and x["protocol_consistent"]=="True" for x in ROWS)

def test_gate_e0_hnswlib_dataset_boundary():
    safe={d:sum(x["endpoint_status"]=="CURRENT_ENDPOINT_CERTIFIABLY_SAFE" for x in ROWS if x["implementation"]=="hnswlib" and x["dataset"]==d) for d in {x["dataset"] for x in ROWS}}
    assert safe=={"sift_100k":9,"arxiv_nomic_100k":9,"glove100_100k":0}
