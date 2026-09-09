#!/usr/bin/env python3
"""Recover missing registered build timings by deterministic temporary rebuild."""
import argparse, hashlib, time
from pathlib import Path
import faiss, h5py, numpy as np, pandas as pd
from scripts.graph_anns_external_validity.run_faiss_hnsw import DATASETS, build_index, sha

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--work",required=True);a=p.parse_args();root=Path(a.root);work=Path(a.work);reg=work/"build_registry.csv";x=pd.read_csv(reg);tmp=work/"timing_rebuild.tmp.faiss";faiss.omp_set_num_threads(1)
 x["build_seconds_status"]="MEASURED_ORIGINAL_RUN"
 for i,r in x[x.build_seconds.isna()].iterrows():
  rel,_=DATASETS[r.dataset]
  with h5py.File(root/rel,"r") as f:base=np.asarray(f["train"][:30000],np.float32)
  perm=np.random.default_rng(int(r.permutation_seed)).permutation(len(base)).astype(np.int64)
  t=time.perf_counter();idx=build_index(base,perm);elapsed=time.perf_counter()-t;faiss.write_index(idx,str(tmp))
  if sha(tmp)!=r.index_sha256:raise RuntimeError(f"serialization hash mismatch {r.build_id}")
  tmp.unlink();x.at[i,"build_seconds"]=elapsed;x.at[i,"build_seconds_status"]="MEASURED_DETERMINISTIC_REBUILD_AFTER_RESUME"
  print("TIMED",r.build_id,elapsed,flush=True)
 x.to_csv(reg,index=False)
if __name__=="__main__":main()
