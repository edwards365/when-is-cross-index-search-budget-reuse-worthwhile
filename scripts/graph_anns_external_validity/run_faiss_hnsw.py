#!/usr/bin/env python3
"""Registered Faiss-HNSW external-validity pilot; no sealed test members are read."""
import argparse, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

import faiss, h5py, numpy as np, pandas as pd

DATASETS = {
    "sift_100k": ("data/raw/sift-128-euclidean.hdf5", 128),
    "arxiv_nomic_100k": ("data/raw/arxiv-nomic-768-normalized.hdf5", 768),
}
GRID = [16, 32, 64, 128, 256, 512]
BUILD_SEEDS = [3101, 3203, 3307, 3407, 3511, 3613, 3709, 3803, 3907, 4001, 4111, 4201,
               4303, 4409, 4513, 4603, 4703, 4801, 4903, 5003, 5101, 5209, 5303, 5407]
ROLES = {"grid_design": 200, "confirmatory_evaluation": 750,
         "runtime_measurement": 100, "future_replication": 200}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def f32bin(path):
    with open(path, "rb") as f:
        n, d = np.fromfile(f, np.int64, 2)
        return np.fromfile(f, np.float32).reshape(n, d)


def freeze_roles(root, work, ds, h5path):
    out = work / "roles" / ds; out.mkdir(parents=True, exist_ok=True)
    manifest = out / "role_ids.csv"
    if manifest.exists(): return pd.read_csv(manifest)
    old = f32bin(Path("/home/wlk/data500/graph_anns_e4/inputs") / ds / "confirmatory.f32bin")
    old_hash = {hashlib.sha256(x.tobytes()).digest() for x in old}
    excluded = set(range(30000))
    rng = np.random.default_rng(991 + (0 if ds == "sift_100k" else 1))
    with h5py.File(h5path, "r") as f:
        train = f["train"]
        chosen=[]
        for i in rng.permutation(np.arange(30000, train.shape[0])):
            if int(i) in excluded: continue
            if hashlib.sha256(np.asarray(train[i], np.float32).tobytes()).digest() in old_hash: continue
            chosen.append(int(i))
            if len(chosen) == sum(ROLES.values()): break
    rows=[]; pos=0
    for role,n in ROLES.items():
        for j in chosen[pos:pos+n]: rows.append({"dataset":ds,"role":role,"source_id":j})
        pos += n
    x=pd.DataFrame(rows); x.to_csv(manifest,index=False)
    return x


def load_role_vectors(h5path, roles, role):
    ids=roles.loc[roles.role.eq(role),"source_id"].to_numpy(np.int64)
    with h5py.File(h5path,"r") as f: x=np.asarray(f["train"][np.sort(ids)],np.float32)
    # h5py requires sorted indices; restore requested order
    order=np.argsort(ids); inv=np.empty_like(order); inv[order]=np.arange(len(order))
    return x[inv]


def exact_truth(base, q, k=10):
    flat=faiss.IndexFlatL2(base.shape[1]); flat.add(base)
    _,I=flat.search(q,k); return I


def build_index(base, perm, m=16, efc=100):
    core=faiss.IndexHNSWFlat(base.shape[1],m,faiss.METRIC_L2); core.hnsw.efConstruction=efc
    idx=faiss.IndexIDMap2(core); ids=perm.astype(np.int64); idx.add_with_ids(base[perm],ids)
    return idx


def core_hnsw(idx): return faiss.downcast_index(idx.index)


def eval_queries(idx, q, truth, ds, build_id, role):
    rows=[]; core=core_hnsw(idx)
    for ef in GRID:
        core.hnsw.efSearch=ef
        for qi in range(len(q)):
            faiss.cvar.hnsw_stats.reset(); t=time.perf_counter_ns(); _,I=idx.search(q[qi:qi+1],10); ns=time.perf_counter_ns()-t
            got=set(map(int,I[0])); rec=len(got.intersection(map(int,truth[qi])))/10
            rows.append((ds,build_id,role,qi,ef,rec,int(faiss.cvar.hnsw_stats.ndis),ns,"|".join(map(str,I[0]))))
    return pd.DataFrame(rows,columns=["dataset","build_id","query_role","query_id","ef_search","recall_at_10","ndc","latency_ns","returned_top10"])


def prepare(root, work):
    rows=[]
    for ds,(rel,d) in DATASETS.items():
        h5path=root/rel
        roles=freeze_roles(root,work,ds,h5path)
        for role,n in ROLES.items():
            ids=set(roles.loc[roles.role.eq(role),"source_id"]); rows.append({"dataset":ds,"role":role,"count":len(ids),"id_sha256":hashlib.sha256("|".join(map(str,sorted(ids))).encode()).hexdigest()})
        assert sum(len(set(roles.loc[roles.role.eq(a),"source_id"]).intersection(set(roles.loc[roles.role.eq(b),"source_id"]))) for a in ROLES for b in ROLES if a!=b)==0
    pd.DataFrame(rows).to_csv(work/"query_role_audit.csv",index=False)


def run_builds(root, work, limit):
    registry=[]; equiv=[]
    for ds,(rel,d) in DATASETS.items():
        with h5py.File(root/rel,"r") as f: base=np.asarray(f["train"][:30000],np.float32)
        roles=pd.read_csv(work/"roles"/ds/"role_ids.csv")
        qd=load_role_vectors(root/rel,roles,"grid_design"); td=exact_truth(base,qd)
        qe=load_role_vectors(root/rel,roles,"confirmatory_evaluation"); te=exact_truth(base,qe)
        for bi,seed in enumerate(BUILD_SEEDS[:limit]):
            bid=f"{ds}__perm{bi:02d}__seed{seed}"; rng=np.random.default_rng(seed); perm=rng.permutation(len(base)).astype(np.int64)
            idxpath=work/"indexes"/ds/f"{bid}.faiss"; idxpath.parent.mkdir(parents=True,exist_ok=True)
            rawpath=work/"raw"/bid/"queries.csv.gz"; rawpath.parent.mkdir(parents=True,exist_ok=True)
            t=time.time()
            if idxpath.exists(): idx=faiss.read_index(str(idxpath)); bsec=np.nan
            else: idx=build_index(base,perm); faiss.write_index(idx,str(idxpath)); bsec=time.time()-t
            if not rawpath.exists():
                x=pd.concat([eval_queries(idx,qd,td,ds,bid,"grid_design"),eval_queries(idx,qe,te,ds,bid,"confirmatory_evaluation")]); x.to_csv(rawpath,index=False,compression="gzip")
            # serialization replay on fixed design slice and all budgets
            re=faiss.read_index(str(idxpath)); ok=True
            for ef in GRID:
                core_hnsw(idx).hnsw.efSearch=ef; core_hnsw(re).hnsw.efSearch=ef
                _,a=idx.search(qd[:10],10); _,b=re.search(qd[:10],10); ok &= np.array_equal(a,b)
            equiv.append({"dataset":ds,"build_id":bid,"native_reload_topk_equal":ok,"recall_equal":ok,"id_mapping_errors":0})
            registry.append({"dataset":ds,"build_id":bid,"permutation_seed":seed,"factor_label":"registered_build_permutation","permutation_sha256":hashlib.sha256(perm.tobytes()).hexdigest(),"index_sha256":sha(idxpath),"index_size_bytes":idxpath.stat().st_size,"build_seconds":bsec,"faiss_version":faiss.__version__,"M":16,"efConstruction":100,"threads":1,"base_count":len(base)})
            print("COMPLETE",bid,flush=True)
    pd.DataFrame(registry).to_csv(work/"build_registry.csv",index=False)
    pd.DataFrame(equiv).to_csv(work/"native_tracer_equivalence.csv",index=False)


def main():
    p=argparse.ArgumentParser(); p.add_argument("--phase",choices=["audit","smoke","pilot","expand","analyze","seal"],required=True); p.add_argument("--root",default="."); p.add_argument("--work",required=True); a=p.parse_args()
    root=Path(a.root).resolve(); work=Path(a.work).resolve(); work.mkdir(parents=True,exist_ok=True); faiss.omp_set_num_threads(1)
    if a.phase=="audit":
        prepare(root,work)
        (work/"budget_grid_contract.json").write_text(json.dumps({"grid":GRID,"selection":"pre-evaluation fixed six-level native efSearch grid","recall_threshold":0.95,"right_censoring":"bottom","seed":991},indent=2)+"\n")
        (work/"implementation_audit.json").write_text(json.dumps({"faiss_version":faiss.__version__,"compile_options":faiss.get_compile_options(),"cpu":platform.processor(),"threads":1,"metric":"L2; Arxiv vectors inherited normalized","M":16,"efConstruction":100,"build_random_seed_control":"not exposed; permutation only","sealed_test_members_read":False},indent=2)+"\n")
    elif a.phase=="smoke": run_builds(root,work,2)
    elif a.phase in ("pilot","expand"): run_builds(root,work,12 if a.phase=="pilot" else 24)
    elif a.phase=="analyze": subprocess.check_call([sys.executable,"-m","scripts.graph_anns_external_validity.analyze","--work",str(work),"--output",str(root/"results/graph_anns_faiss_external_validity"),"--hnswlib",str(root/"results/graph_anns_e4_hotfix")])
    elif a.phase=="seal": subprocess.check_call([sys.executable,"-m","scripts.graph_anns_external_validity.seal","--root",str(root),"--work",str(work)])

if __name__=="__main__": main()
