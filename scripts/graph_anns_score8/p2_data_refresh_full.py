#!/usr/bin/env python3
"""Full preregistered P2 data-refresh matrix. Heavy tensors live on data500."""
from __future__ import annotations
import csv, json, time
from pathlib import Path
import h5py, hnswlib, numpy as np

import importlib.util
BASEMOD = Path(__file__).with_name("p2_data_refresh.py")
sp = importlib.util.spec_from_file_location("refresh_base", BASEMOD)
b = importlib.util.module_from_spec(sp); sp.loader.exec_module(b)

CONFIGS = {
    "SIFT-100K": ("data/raw/sift-128-euclidean.hdf5", "l2", 1_000_000),
    "Arxiv-Nomic-100K": ("data/raw/arxiv-nomic-768-normalized.hdf5", "cosine", 1_344_643),
}
FRACTIONS = [0.01, 0.05, 0.10]
ROWS = []

def build_hits(base, ids, queries, truth, metric, seed):
    order = np.random.RandomState(seed).permutation(len(base))
    p = hnswlib.Index(space=metric, dim=base.shape[1])
    p.init_index(max_elements=len(base), ef_construction=100, M=16, random_seed=seed)
    p.set_num_threads(1); p.add_items(base[order], ids[order])
    h = np.zeros((len(queries), len(b.GRID)), np.int8)
    for j, ef in enumerate(b.GRID):
        p.set_ef(int(ef)); lab, _ = p.knn_query(queries, k=b.H, num_threads=1)
        h[:,j] = [len(set(x.tolist()) & set(y.tolist())) for x,y in zip(lab, truth)]
    return h

def action_from_pool(B, omit):
    pool = np.delete(B, omit, axis=0)
    assert len(pool) == 9
    finite = pool >= 0
    live = finite.all(0)
    # Registered rank 9 of 9 is the maximum; BOT means explicit abstention.
    action = np.where(live, pool.max(0), b.GRID[-1]).astype(int)
    return action, ~live

def evaluate(hits, action, abstain):
    j = np.searchsorted(b.GRID, action)
    fail = hits[np.arange(len(action)), j] < b.H
    return fail.astype(float), action.astype(float), abstain.astype(float)

def cluster_ci(values, seed=991, reps=5000):
    # values: builds x queries. Build is the outer inferential unit.
    rng = np.random.RandomState(seed); nb,nq = values.shape
    means = np.empty(reps)
    for r in range(reps):
        ib = rng.randint(0,nb,nb); iq = rng.randint(0,nq,(nb,nq))
        x = values[ib]
        means[r] = np.mean(np.take_along_axis(x, iq, axis=1))
    return np.quantile(means,[.025,.975]).tolist()

def summarize(dataset, frac, name, failures, actions, abstains, oracle):
    ratio = actions / np.maximum(oracle, 1)
    ci = cluster_ci(failures)
    # Deleting each target build is deterministic robustness, not an extra test.
    lobo = [float(np.delete(failures,i,0).mean()) for i in range(len(failures))]
    row = dict(dataset=dataset, refresh_fraction=frac, method=name,
               risk=float(failures.mean()), risk_ci_low=ci[0], risk_ci_high=ci[1],
               mean_ef=float(actions.mean()), p95_ef=float(np.quantile(actions,.95)),
               p99_ef=float(np.quantile(actions,.99)), abstention=float(abstains.mean()),
               budget_oracle_ratio=float(ratio.mean()), lobo_min=min(lobo), lobo_max=max(lobo))
    ROWS.append(row)

def run_dataset(name, cfg):
    rel, metric, ntrain = cfg; path=b.REPO/rel
    out=b.HEAVY/name.replace("-","_"); out.mkdir(parents=True,exist_ok=True)
    with h5py.File(path,"r") as f:
        old=np.ascontiguousarray(f["train"][:100000],np.float32)
        reserve=np.ascontiguousarray(f["train"][100000:110000],np.float32)
        queries=np.ascontiguousarray(f["train"][ntrain-1000:ntrain],np.float32)
    ids=np.arange(100000,dtype=np.int64)
    truth0=b.exact_truth(old,queries,"l2" if metric=="l2" else "cosine")
    # old labels equal row positions
    oldH=np.stack([build_hits(old,ids,queries,truth0,metric,s) for s in b.SEEDS])
    oldB=np.stack([b.bottoms(x) for x in oldH])
    np.savez_compressed(out/"old_hits.npz",hits=oldH,grid=b.GRID)
    for frac in FRACTIONS:
        n=int(100000*frac); rng=np.random.RandomState(991+int(frac*10000))
        deleted=np.sort(rng.choice(100000,n,replace=False)); keep=np.ones(100000,bool); keep[deleted]=False
        new=np.ascontiguousarray(np.vstack([old[keep],reserve[:n]]))
        newids=np.r_[ids[keep],np.arange(100000,100000+n,dtype=np.int64)]
        truthpos=b.exact_truth(new,queries,"l2" if metric=="l2" else "cosine")
        truth=newids[truthpos]
        targetH=np.stack([build_hits(new,newids,queries,truth,metric,s) for s in b.SEEDS])
        targetB=np.stack([b.bottoms(x) for x in targetH])
        np.savez_compressed(out/f"refresh_{int(frac*100):02d}_hits.npz",hits=targetH,grid=b.GRID,
                           deleted=deleted,newids=newids)
        oracle=np.where(targetB<0,b.GRID[-1],targetB).astype(float)
        methods={k:([],[],[]) for k in ["FIXED_EF_200","OLD_SNAPSHOT_SINGLE_BUILD_REUSE",
                                        "OLD_SNAPSHOT_K9_CONFORMAL","REFRESHED_SNAPSHOT_K9_CONFORMAL_ORACLE_UPPER_BOUND"]}
        for t in range(10):
            fixed=np.full(1000,b.GRID[-1]); zero=np.zeros(1000,bool)
            single=np.where(oldB[t]<0,b.GRID[-1],oldB[t]); single_abs=oldB[t]<0
            olda,olda_abs=action_from_pool(oldB,t); newa,newa_abs=action_from_pool(targetB,t)
            for mn,a,z in [("FIXED_EF_200",fixed,zero),("OLD_SNAPSHOT_SINGLE_BUILD_REUSE",single,single_abs),
                           ("OLD_SNAPSHOT_K9_CONFORMAL",olda,olda_abs),
                           ("REFRESHED_SNAPSHOT_K9_CONFORMAL_ORACLE_UPPER_BOUND",newa,newa_abs)]:
                f,aa,zz=evaluate(targetH[t],a,z); methods[mn][0].append(f); methods[mn][1].append(aa); methods[mn][2].append(zz)
        for mn,(f,a,z) in methods.items(): summarize(name,frac,mn,np.array(f),np.array(a),np.array(z),oracle)

def main():
    t=time.time(); b.SMALL.mkdir(parents=True,exist_ok=True)
    for name,cfg in CONFIGS.items():
        print("START",name,flush=True); run_dataset(name,cfg); print("DONE",name,flush=True)
    cols=list(ROWS[0]); csvp=b.SMALL/"data_refresh_matrix.csv"
    with csvp.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(ROWS)
    old=[r for r in ROWS if r["method"]=="OLD_SNAPSHOT_K9_CONFORMAL"]
    fresh={(r["dataset"],r["refresh_fraction"]):r for r in ROWS if r["method"].startswith("REFRESHED_")}
    safety=all(r["risk"]<=.10 and r["risk_ci_high"]<=.10 for r in old)
    transfer=all(r["risk"]-fresh[(r["dataset"],r["refresh_fraction"])]["risk"]<=.02 for r in old)
    robust=all(r["lobo_max"]<=.10 for r in old)
    fresh_safe=all(fresh[(r["dataset"],r["refresh_fraction"])]["risk_ci_high"]<=.10 for r in old)
    if safety and transfer and robust: label="DATA_REFRESH_TRANSFER_SUPPORTED"
    elif not transfer and fresh_safe: label="DATA_REFRESH_BREAKS_SOURCE_TRANSFER_BUT_WITHIN_SNAPSHOT_RECOVERS"
    elif safety: label="DATA_REFRESH_SAFETY_ONLY_COST_DEGRADED"
    else: label="DATA_REFRESH_BREAKS_CONFORMAL_TRANSPORT"
    verdict={"label":label,"strict_safety":safety,"transfer_noninferiority":transfer,"lobo_robust":robust,
             "rows":len(ROWS),"elapsed_seconds":time.time()-t,"heavy_root":str(b.HEAVY),
             "evidence_level":"EXPLORATORY_PREREGISTERED_DATA_REFRESH"}
    (b.SMALL/"verdict.json").write_text(json.dumps(verdict,indent=2)+"\n")
    print(json.dumps(verdict,indent=2))

if __name__=="__main__": main()
