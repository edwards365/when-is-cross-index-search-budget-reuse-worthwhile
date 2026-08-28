#!/usr/bin/env python3
import csv, gzip, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/"results/cross_index/g1/main"
OUT=ROOT/"results/icba_open_world"; OUT.mkdir(parents=True,exist_ok=True)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

inventory=[]; total=0
for path in sorted(RAW.glob("*/*.csv.gz")):
    with gzip.open(path,"rt",newline="") as h:
        reader=csv.DictReader(h); rows=sum(1 for _ in reader)
    total+=rows
    inventory.append({"artifact":"frozen_graph_query_budget","path":str(path.relative_to(ROOT)),"implementation":path.parent.name,
                      "graph_file":path.name,"rows":rows,"bytes":path.stat().st_size,"sha256":sha(path),"status":"FROZEN_READ_ONLY"})
for rel,kind in [
 ("results/icba_micro_closure/endpoint_audit.csv","endpoint_labels"),
 ("results/icba_micro_closure/graph_replay.csv","closed_open_replay"),
 ("results/icba_micro_closure/open_world_leave_build_out.csv","open_world_replay"),
 ("manifests/icba_micro_closure_query_split.json","query_split"),
 ("manifests/icba_micro_closure_decision.json","frozen_decision"),
 ("results/icba_micro_closure/checksums.sha256","frozen_checksums")]:
    p=ROOT/rel; inventory.append({"artifact":kind,"path":rel,"implementation":"","graph_file":"","rows":"",
                                  "bytes":p.stat().st_size,"sha256":sha(p),"status":"FROZEN_READ_ONLY"})
assert len(list(RAW.glob("*/*.csv.gz")))==81 and total==972000
with (OUT/"input_inventory.csv.tmp").open("w",newline="") as h:
    w=csv.DictWriter(h,fieldnames=list(inventory[0]));w.writeheader();w.writerows(inventory)
(OUT/"input_inventory.csv.tmp").replace(OUT/"input_inventory.csv")

fields=[
 ("dataset","DEPLOYMENT_OBSERVABLE","declared index collection"),("implementation","DEPLOYMENT_OBSERVABLE","declared serving implementation"),
 ("base_size","DEPLOYMENT_OBSERVABLE","index metadata"),("query_id","OFFLINE_ONLY","evaluation bookkeeping"),
 ("query_split","OFFLINE_ONLY","frozen design partition"),("query_vector_hash","OFFLINE_ONLY","membership audit"),
 ("truth_hash","REQUIRES_TARGET_LABEL","exact top-10 truth provenance"),("graph_seed","DEPLOYMENT_OBSERVABLE","build metadata if retained"),
 ("insertion_order/history","DEPLOYMENT_OBSERVABLE","known construction history label; not query response"),
 ("graph_hash","OFFLINE_ONLY","integrity identifier"),("construction_wall_time","OFFLINE_ONLY","post-build audit"),
 ("peak_build_memory","OFFLINE_ONLY","post-build audit"),("ef_search/budget","DEPLOYMENT_OBSERVABLE","chosen action"),
 ("returned_top10_ids","DEPLOYMENT_OBSERVABLE","native search output"),("returned_top10_distances","DEPLOYMENT_OBSERVABLE","unlabeled native search output; absent in compact Faiss/Vamana tables"),
 ("recall_at_10","REQUIRES_TARGET_LABEL","requires exact target truth"),("exact_ndc","DEPLOYMENT_OBSERVABLE","runtime distance-count counter"),
 ("query_latency_ns","DEPLOYMENT_OBSERVABLE","runtime counter; absent in compact Faiss/Vamana tables"),
 ("entry_point/max_level","DEPLOYMENT_OBSERVABLE","index metadata; absent in compact Faiss/Vamana tables"),
 ("stable_sufficient_budget","SOURCE_ORACLE","requires complete labeled source budget curve per query"),
 ("target_sentinel_stable_budget","REQUIRES_TARGET_LABEL","uses labeled target Recall across budget grid"),
 ("endpoint_status","OFFLINE_ONLY","derived from labeled target failures"),
 ("visited/frontier/prefix trajectory","UNKNOWN_PROVENANCE","not present in 81-graph Cross-Index schema"),
]
obs=[{"field":a,"classification":b,"reason":c} for a,b,c in fields]
with (OUT/"observable_field_inventory.csv.tmp").open("w",newline="") as h:
    w=csv.DictWriter(h,fieldnames=list(obs[0]));w.writeheader();w.writerows(obs)
(OUT/"observable_field_inventory.csv.tmp").replace(OUT/"observable_field_inventory.csv")

split=json.loads((ROOT/"manifests/icba_micro_closure_query_split.json").read_text())
for x in split["datasets"].values():
    assert len(x["sentinel_query_ids"])==256 and len(x["evaluation_query_ids"])==744
    assert not set(x["sentinel_query_ids"]) & set(x["evaluation_query_ids"])
print(json.dumps({"graphs":81,"rows":total,"directed_pairs":648,"inventory_rows":len(inventory),"observable_fields":len(obs)}))
