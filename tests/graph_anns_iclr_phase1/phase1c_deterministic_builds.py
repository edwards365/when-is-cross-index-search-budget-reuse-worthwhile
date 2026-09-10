#!/usr/bin/env python3
"""Run preregistered hnswlib D1-D3 rebuild regimes on data500."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import resource
import shutil
import struct
import time
from pathlib import Path

import hnswlib
import numpy as np

REPO=Path("/home/wlk/projects/navigation-aware-resistance-hnsw")
SCRATCH=Path("/home/wlk/data500/graph_anns_iclr_phase1_scratch/phase1c")
INPUT=Path("/home/wlk/data500/graph_anns_e4/inputs")
GRID=(10,20,40,80,120,200)
CONTRACT={
 "D1":{"seeds":(1009,1013,1019,1021,1031,1033),"threads":8},
 "D2":{"seeds":(991,991,991,991,991,991),"threads":8},
 "D3":{"seeds":(991,991,991),"threads":1},
}

def f32(path):
 with path.open("rb") as f:n,d=struct.unpack("<QQ",f.read(16))
 return np.memmap(path,dtype="<f4",mode="r",offset=16,shape=(n,d))
def u32(path):
 with path.open("rb") as f:n,k=struct.unpack("<QQ",f.read(16))
 return np.memmap(path,dtype="<u4",mode="r",offset=16,shape=(n,k))
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def digest_topk(index,q):
 h=hashlib.sha256()
 for ef in GRID:
  index.set_ef(ef); labels,_=index.knn_query(q,k=10); h.update(np.asarray(labels,dtype="<u4").tobytes())
 return h.hexdigest()
def run(dataset,regime):
 if shutil.disk_usage(SCRATCH.parent).free < 20*2**30: raise RuntimeError("DATA500_BELOW_20_GIB_STOP_LINE")
 bp=INPUT/dataset/"base.f32bin"; qp=INPUT/dataset/"confirmatory.f32bin"; tp=INPUT/dataset/"truth.u32bin"
 base=f32(bp); q=np.asarray(f32(qp)[:750]); truth=np.asarray(u32(tp)[:750]); dim=base.shape[1]
 metric="ip" if dataset.startswith("arxiv") else "l2"
 rows=[]
 for repeat,seed in enumerate(CONTRACT[regime]["seeds"],1):
  rid=f"{dataset}__{regime}__r{repeat:02d}__seed{seed}"
  rd=SCRATCH/dataset/regime/rid; done=rd/"COMPLETE.json"
  if done.exists(): rows.append(json.loads(done.read_text())); continue
  if shutil.disk_usage(SCRATCH.parent).free < 20*2**30: raise RuntimeError("DATA500_BELOW_20_GIB_STOP_LINE")
  rd.mkdir(parents=True,exist_ok=True); ip=rd/"index.bin"
  index=hnswlib.Index(space=metric,dim=dim)
  index.init_index(max_elements=len(base),ef_construction=100,M=16,random_seed=seed)
  t0=time.perf_counter(); c0=time.process_time()
  index.add_items(np.asarray(base),np.arange(len(base),dtype=np.int64),num_threads=CONTRACT[regime]["threads"])
  build_wall=time.perf_counter()-t0; build_cpu=time.process_time()-c0
  index.save_index(str(ip)); index.set_num_threads(CONTRACT[regime]["threads"])
  diagnostic_before=digest_topk(index,q[:500])
  del index
  loaded=hnswlib.Index(space=metric,dim=dim); t0=time.perf_counter(); loaded.load_index(str(ip),max_elements=len(base)); load_seconds=time.perf_counter()-t0
  loaded.set_num_threads(CONTRACT[regime]["threads"]); diagnostic_after=digest_topk(loaded,q[:500])
  if diagnostic_before!=diagnostic_after: raise RuntimeError("SERIALIZATION_TOPK_MISMATCH")
  raw=[]
  for ef in GRID:
   loaded.set_ef(ef)
   for qi in range(len(q)):
    t=time.perf_counter_ns(); labels,_=loaded.knn_query(q[qi:qi+1],k=10); elapsed=time.perf_counter_ns()-t
    recall=len(set(map(int,labels[0])).intersection(map(int,truth[qi])))/10
    raw.append((rid,regime,repeat,seed,CONTRACT[regime]["threads"],ef,qi,recall,elapsed,"|".join(map(str,labels[0]))))
  with gzip.open(rd/"queries.csv.gz","wt",newline="") as f:
   w=csv.writer(f);w.writerow(("run_id","regime","repeat","seed","threads","ef_search","query_id","recall_at_10","latency_ns","returned_top10"));w.writerows(raw)
  record={"dataset":dataset,"regime":regime,"repeat":repeat,"seed":seed,"threads":CONTRACT[regime]["threads"],"canonical_order":"external_id_ascending","build_wall_seconds":build_wall,"build_cpu_seconds":build_cpu,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"index_bytes":ip.stat().st_size,"index_sha256":sha(ip),"query_output_sha256":sha(rd/"queries.csv.gz"),"diagnostic_topk_sha256":diagnostic_after,"serialize_reload_seconds":load_seconds,"serialize_reload_topk_equal":True,"base_sha256":sha(bp),"query_sha256":sha(qp),"truth_sha256":sha(tp),"future_roles_accessed":False,"status":"COMPLETE"}
  done.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n");rows.append(record)
  (SCRATCH/"progress.json").write_text(json.dumps({"last":rid,"dataset":dataset,"regime":regime,"complete":repeat,"required":len(CONTRACT[regime]["seeds"]),"free_gib":shutil.disk_usage(SCRATCH.parent).free/2**30,"time":time.time()},indent=2)+"\n")
  print("COMPLETE",rid,build_wall,flush=True)
 out=REPO/"results/graph_anns_iclr_phase1"/f"phase1c_{dataset}_{regime}_registry.csv"
 with out.open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--dataset",choices=("sift_100k","arxiv_nomic_100k"),required=True);p.add_argument("--regime",choices=tuple(CONTRACT),required=True);a=p.parse_args();run(a.dataset,a.regime)
