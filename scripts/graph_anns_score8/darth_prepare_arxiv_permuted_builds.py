#!/usr/bin/env python3
"""Prepare ten frozen insertion-order Arxiv adapters for official DARTH."""
import argparse, hashlib, json, os, struct
from pathlib import Path
import numpy as np
SEEDS=[1103,1229,1361,1499,1621,1747,1877,1999,2131,2267]
Q=["learn.1M.fvecs","validation.10K.fvecs","query.10K.fvecs"]
I=["learn.groundtruth.1M.k1000.ivecs","validation.groundtruth.10K.k1000.ivecs","query.groundtruth.10K.k1000.ivecs"]
D=["learn.groundtruth.1M.k1000.fvecs","validation.groundtruth.10K.k1000.fvecs","query.groundtruth.10K.k1000.fvecs"]
def read(p,dt):
 r=np.fromfile(p,dtype=dt); d=r.view("<i4")[0]; return np.ascontiguousarray(r.reshape(-1,d+1)[:,1:])
def write(p,x,dt):
 x=np.asarray(x,dtype=dt); pre=struct.pack("<i",x.shape[1])
 with open(p,"wb") as f:
  for row in x: f.write(pre); f.write(row.tobytes())
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(8<<20),b""): h.update(b)
 return h.hexdigest()
p=argparse.ArgumentParser(); p.add_argument("--source",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--ledger",type=Path,required=True); a=p.parse_args()
base=read(a.source/"base.100M.fvecs","<f4"); assert base.shape==(100000,768)
truth={n:read(a.source/n,"<i4") for n in I}; builds=[]
for seed in SEEDS:
 d=a.output/f"seed_{seed}"/"SIFT100M"; d.mkdir(parents=True,exist_ok=False); perm=np.random.RandomState(seed).permutation(len(base)).astype("<i4"); inv=np.empty_like(perm); inv[perm]=np.arange(len(base),dtype="<i4")
 write(d/"base.100M.fvecs",base[perm],"<f4")
 for n in Q+D: os.symlink(a.source/n,d/n)
 for n,x in truth.items(): write(d/n,inv[x],"<i4")
 builds.append({"seed":seed,"base_sha256":sha(d/"base.100M.fvecs"),"permutation_sha256":hashlib.sha256(perm.tobytes()).hexdigest()})
a.ledger.write_text(json.dumps({"status":"PASS","shape":list(base.shape),"builds":builds,"query_symlinks":Q,"truth_distance_symlinks":D,"truth_ids_remapped":I},indent=2)+"\n")
