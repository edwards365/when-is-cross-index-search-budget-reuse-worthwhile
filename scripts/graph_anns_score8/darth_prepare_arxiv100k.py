#!/usr/bin/env python3
"""Create the frozen Arxiv-Nomic-100K DARTH adapter without sealed query roles."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import h5py
import numpy as np

ROLES = {"training": (100000,102000), "certification": (102000,102500), "evaluation": (102500,103500)}

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def fvecs(path, x):
    x=np.asarray(x,dtype="<f4"); d=np.full((len(x),1),x.shape[1],dtype="<i4")
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(path,"wb") as f:
        for a,b in zip(d,x): f.write(a.tobytes()); f.write(b.tobytes())

def ivecs(path, x):
    x=np.asarray(x,dtype="<i4"); d=np.full((len(x),1),x.shape[1],dtype="<i4")
    with open(path,"wb") as f:
        for a,b in zip(d,x): f.write(a.tobytes()); f.write(b.tobytes())

def truth(base,q,k=100,block=25):
    out=np.empty((len(q),k),dtype=np.int32); dist=np.empty((len(q),k),dtype=np.float32)
    for lo in range(0,len(q),block):
        z=np.asarray(q[lo:lo+block],dtype=np.float32)
        scores=z@base.T
        ids=np.argpartition(scores,-k,axis=1)[:,-k:]
        vals=np.take_along_axis(scores,ids,axis=1)
        order=np.argsort(-vals,axis=1); ids=np.take_along_axis(ids,order,axis=1); vals=np.take_along_axis(vals,order,axis=1)
        out[lo:lo+len(z)]=ids; dist[lo:lo+len(z)]=2.0-2.0*vals
    return out,dist

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    target=a.output/"SIFT100M"; target.mkdir(parents=True,exist_ok=False)
    with h5py.File(a.input,"r") as h:
        base=np.asarray(h["train"][:100000],dtype=np.float32)
        fvecs(target/"base.100M.fvecs",base)
        ledger={"dataset":"Arxiv-Nomic-100K","official_loader_alias":"SIFT100M_PATH_ONLY","dimension":768,"base_ids":[0,100000],"roles":ROLES,"sealed_roles_accessed":False,"files":{}}
        names={"training":"learn.1M","certification":"validation.10K","evaluation":"query.10K"}
        for role,(lo,hi) in ROLES.items():
            q=np.asarray(h["train"][lo:hi],dtype=np.float32); ids,dists=truth(base,q)
            stem=names[role]; fvecs(target/f"{stem}.fvecs",q)
            if role == "training": gt="learn.groundtruth.1M.k1000"
            else: gt=f"{stem.split('.')[0]}.groundtruth.10K.k1000"
            ivecs(target/f"{gt}.ivecs",ids); fvecs(target/f"{gt}.fvecs",dists)
        for f in sorted(target.iterdir()): ledger["files"][f.name]={"bytes":f.stat().st_size,"sha256":sha(f)}
        (a.output/"adapter_ledger.json").write_text(json.dumps(ledger,indent=2)+"\n")
if __name__=="__main__": main()
