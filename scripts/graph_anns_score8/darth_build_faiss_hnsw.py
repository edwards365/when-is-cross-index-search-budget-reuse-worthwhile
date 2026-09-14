#!/usr/bin/env python3
"""Build a frozen CPU Faiss HNSW index from a DARTH fvec adapter."""
import argparse, hashlib, json, time
from pathlib import Path
import faiss, numpy as np

def read_fvecs(path):
    raw=np.fromfile(path,dtype="<f4"); d=raw.view("<i4")[0]; return np.ascontiguousarray(raw.reshape(-1,d+1)[:,1:])
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()
p=argparse.ArgumentParser(); p.add_argument("--base",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--metadata",type=Path,required=True); p.add_argument("--m",type=int,default=16); p.add_argument("--efc",type=int,default=100); a=p.parse_args()
x=read_fvecs(a.base); started=time.time(); index=faiss.IndexHNSWFlat(x.shape[1],a.m); index.hnsw.efConstruction=a.efc; index.add(x); a.output.parent.mkdir(parents=True,exist_ok=True); faiss.write_index(index,str(a.output))
a.metadata.write_text(json.dumps({"base":str(a.base),"shape":list(x.shape),"M":a.m,"efConstruction":a.efc,"seconds":time.time()-started,"index_sha256":sha(a.output)},indent=2)+"\n")
