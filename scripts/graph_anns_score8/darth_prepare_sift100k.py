#!/usr/bin/env python3
"""Create a hash-audited SIFT-100K adapter for the official DARTH driver."""
from __future__ import annotations
import hashlib, json, struct, time
from pathlib import Path
import h5py, numpy as np

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "data/raw/sift-128-euclidean.hdf5"
OUT = Path("/home/wlk/data500/graph_anns_score8/darth_comparison/datasets/SIFT100M")
SMALL = REPO / "results/graph_anns_score8/darth_comparison"
ROLES = {
    "training": (990000, 992000, "learn.1M"),
    "validation": (992000, 992500, "validation.10K"),
    "certification": (992500, 993000, "certification.500"),
    "testing": (993000, 994000, "query.10K"),
}
TOP = 100

def file_sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for x in iter(lambda:f.read(8<<20),b""): h.update(x)
    return h.hexdigest()

def rows_sha(x): return hashlib.sha256(np.ascontiguousarray(x,"<f4").tobytes()).hexdigest()
def row_keys(x):
    y=np.ascontiguousarray(x,"<f4")
    return {bytes(r) for r in y.view(np.uint8).reshape(len(y),-1)}

def fvecs(p,x):
    x=np.ascontiguousarray(x,"<f4")
    with open(p,"wb") as f:
        for r in x: f.write(struct.pack("<i",len(r))); f.write(r.tobytes())

def ivecs(p,x):
    x=np.ascontiguousarray(x,"<i4")
    with open(p,"wb") as f:
        for r in x: f.write(struct.pack("<i",len(r))); f.write(r.tobytes())

def truth(base,q):
    b2=(base*base).sum(1); ids=[]; ds=[]
    for s in range(0,len(q),16):
        z=q[s:s+16]; d=(z*z).sum(1)[:,None]+b2[None,:]-2*(z@base.T)
        ix=np.argpartition(d,TOP-1,axis=1)[:,:TOP]
        sd=np.take_along_axis(d,ix,axis=1); order=np.argsort(sd,axis=1)
        ids.append(np.take_along_axis(ix,order,axis=1).astype(np.int32))
        ds.append(np.take_along_axis(sd,order,axis=1).astype(np.float32))
    return np.vstack(ids),np.vstack(ds)

def main():
    t=time.time(); OUT.mkdir(parents=True,exist_ok=True); SMALL.mkdir(parents=True,exist_ok=True)
    with h5py.File(SOURCE,"r") as f:
        base=np.ascontiguousarray(f["train"][:100000],np.float32)
        qs={k:np.ascontiguousarray(f["train"][a:z],np.float32) for k,(a,z,_) in ROLES.items()}
    hashes={"base":rows_sha(base)}; seen={hashes["base"]}
    for k,x in qs.items():
        hashes[k]=rows_sha(x)
        if hashes[k] in seen: raise RuntimeError("role content hash collision")
        seen.add(hashes[k])
    keysets={"base":row_keys(base),**{k:row_keys(x) for k,x in qs.items()}}
    overlaps={}
    names=list(keysets)
    for i,a in enumerate(names):
        for z in names[:i]: overlaps[f"{z}__{a}"]=len(keysets[z]&keysets[a])
    if any(overlaps.values()): raise RuntimeError(f"content overlap: {overlaps}")
    fvecs(OUT/"base.100M.fvecs",base)
    files=[]
    for role,x in qs.items():
        stem=ROLES[role][2]; fvecs(OUT/(stem+".fvecs"),x)
        gt,gd=truth(base,x); ivecs(OUT/(stem+".groundtruth.ivecs"),gt); fvecs(OUT/(stem+".groundtruth.fvecs"),gd)
        if role in ("training","validation","testing"):
            canonical={"training":"learn.groundtruth.1M.k1000","validation":"validation.groundtruth.10K.k1000","testing":"query.groundtruth.10K.k1000"}[role]
            # Copying these compact generated files is intentional: the official loader has fixed filenames.
            (OUT/(canonical+".ivecs")).write_bytes((OUT/(stem+".groundtruth.ivecs")).read_bytes())
            (OUT/(canonical+".fvecs")).write_bytes((OUT/(stem+".groundtruth.fvecs")).read_bytes())
    for p in sorted(OUT.iterdir()):
        if p.is_file(): files.append({"path":str(p),"bytes":p.stat().st_size,"sha256":file_sha(p)})
    ledger={"adapter":"DARTH official dataset name SIFT100M backed by frozen SIFT-100K base",
            "source":str(SOURCE),"source_sha256":file_sha(SOURCE),"base_rows":[0,100000],
            "roles":{k:{"rows":[a,z],"count":z-a,"vector_sha256":hashes[k]} for k,(a,z,_) in ROLES.items()},
            "content_overlap_counts":overlaps,"all_content_overlaps_zero":True,"groundtruth_topk":TOP,
            "metric":"squared_l2","files":files,"elapsed_seconds":time.time()-t}
    (SMALL/"m0_sift100k_adapter_ledger.json").write_text(json.dumps(ledger,indent=2)+"\n")
    print(json.dumps({"status":"PASS","files":len(files),"elapsed_seconds":ledger["elapsed_seconds"]},indent=2))

if __name__=="__main__": main()
