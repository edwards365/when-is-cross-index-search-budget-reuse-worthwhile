#!/usr/bin/env python3
import argparse, glob, json, math, os, sys
import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED=991; TAU=.90; ALPHA=.05
DATASETS=("sift_100k","arxiv_nomic_100k")

def feat(row):
    ds=[float(x) for x in str(row.returned_top10_distances).split(";") if x!=""]
    d1=ds[0] if ds else 0.; d2=ds[1] if len(ds)>1 else d1; dk=ds[-1] if ds else 0.
    return [math.log1p(float(row.exact_ndc)),math.log1p(max(float(row.query_latency_ns),0.)),
            math.log1p(max(dk,0.)),(d2-d1)/max(abs(d1),1.),float(row.max_level)]

def cp(k,n):
    if k>=n:return 1.
    return float(beta.ppf(1-ALPHA,k+1,n-k))

def load(path):
    d=pd.read_csv(path,compression="gzip")
    budgets=sorted(d.ef_search.astype(int).unique())
    labels={}; cens={}
    for q,g in d.groupby("query_id",sort=True):
        r=dict(zip(g.ef_search.astype(int),g.recall_at_10.astype(float)))
        found=None
        for i,b in enumerate(budgets):
            if all(r.get(x,-1)>=TAU for x in budgets[i:]):found=i;break
        labels[int(q)]=len(budgets)-1 if found is None else found
        cens[int(q)]=found is None
    first=d[d.ef_search.astype(int)==budgets[0]].sort_values("query_id")
    qids=first.query_id.astype(int).to_numpy()
    X=np.asarray([feat(r) for r in first.itertuples()])
    y=np.asarray([labels[int(q)] for q in qids]); c=np.asarray([cens[int(q)] for q in qids])
    ndc={(int(r.query_id),int(r.ef_search)):float(r.exact_ndc) for r in d.itertuples()}
    return d,budgets,qids,X,y,c,ndc

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--reps",type=int,default=500)
    a=ap.parse_args(); out=os.path.join(a.root,"results/rebuild_portability_recovery"); os.makedirs(out,exist_ok=True)
    split=json.load(open(os.path.join(a.root,"manifests/icba_micro_closure_query_split.json")))
    m0=[]; m1=[]
    for dataset in DATASETS:
        paths=sorted(glob.glob(os.path.join(a.root,"results/cross_index/g1/main/hnswlib",f"{dataset}__*.csv.gz")))
        loaded={os.path.basename(p).replace(".csv.gz",""):load(p) for p in paths}
        models={}
        for name,(d,b,q,X,y,c,ndc) in loaded.items():
            mask=d[d.ef_search.astype(int)==b[0]].sort_values("query_id").query_split.to_numpy()=="cross_index_design"
            model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty="l2",solver="lbfgs",max_iter=1000,random_state=SEED))
            model.fit(X[mask],y[mask])
            confirm=~mask
            raw_confirm=model.predict(X[confirm]).astype(int)
            shift=int(max(0,np.max(y[confirm]-raw_confirm)))
            models[name]=(model,shift)
        sentinel=set(map(int,split["datasets"][dataset]["sentinel_query_ids"]))
        evaluation=set(map(int,split["datasets"][dataset]["evaluation_query_ids"]))
        assert len(sentinel)==256 and len(evaluation)==744 and not sentinel&evaluation
        for sname,(model,source_shift) in models.items():
            for tname,(td,b,q,X,y,c,ndc) in loaded.items():
                if sname==tname:continue
                pred=np.minimum(model.predict(X).astype(int)+source_shift,len(b)-1)
                pos={int(x):i for i,x in enumerate(q)}
                eidx=np.asarray([pos[x] for x in sorted(evaluation)])
                sidx_all=np.asarray([pos[x] for x in sorted(sentinel)])
                fail0=int(np.sum((pred[eidx]<y[eidx])|c[eidx])); n=len(eidx)
                ndc0=np.mean([ndc[(int(q[i]),b[int(pred[i])])] for i in eidx])
                ndcf=np.mean([ndc[(int(q[i]),b[-1])] for i in eidx])
                m0.append({"dataset":dataset,"source_build":sname,"target_build":tname,"n_eval":n,
                           "underbudget":fail0,"risk":fail0/n,"cp95_upper":cp(fail0,n),
                           "mean_ndc":ndc0,"fixed_safe_mean_ndc":ndcf,"ndc_saving_vs_fixed":1-ndc0/ndcf,
                           "source_shift_levels":source_shift,"gate_s":"PASS" if cp(fail0,n)<=.05 else "FAIL"})
                pair_seed=SEED+sum(ord(z) for z in sname+"|"+tname)
                for k in (32,64,128,256):
                    rng=np.random.default_rng(pair_seed+k)
                    risks=[]; uppers=[]; shifts=[]; ndcs=[]
                    for rep in range(a.reps):
                        si=sidx_all if k==256 else rng.choice(sidx_all,size=k,replace=False)
                        sh=int(max(0,np.max(y[si]-pred[si])))
                        alloc=np.minimum(pred+sh,len(b)-1)
                        f=int(np.sum((alloc[eidx]<y[eidx])|c[eidx]))
                        risks.append(f/n); uppers.append(cp(f,n)); shifts.append(sh)
                        ndcs.append(np.mean([ndc[(int(q[i]),b[int(alloc[i])])] for i in eidx]))
                    m1.append({"dataset":dataset,"source_build":sname,"target_build":tname,"k":k,"reps":a.reps,
                               "mean_risk":float(np.mean(risks)),"p95_risk":float(np.quantile(risks,.95)),
                               "mean_cp95_upper":float(np.mean(uppers)),"p95_cp95_upper":float(np.quantile(uppers,.95)),
                               "gate_s_pass_fraction":float(np.mean(np.asarray(uppers)<=.05)),
                               "mean_target_shift_levels":float(np.mean(shifts)),
                               "mean_ndc":float(np.mean(ndcs)),"fixed_safe_mean_ndc":ndcf,
                               "mean_ndc_saving_vs_fixed":float(1-np.mean(ndcs)/ndcf),
                               "gate_s":"PASS" if np.quantile(uppers,.95)<=.05 else "FAIL",
                               "evidence_label":"EXPLORATORY_DESIGN_SIMULATION"})
    d0=pd.DataFrame(m0); d1=pd.DataFrame(m1)
    d0.to_csv(os.path.join(out,"m0_frozen_transfer.csv"),index=False)
    d1.to_csv(os.path.join(out,"m1_target_residual_calibration.csv"),index=False)
    summary={"schema_version":"1.0","seed":SEED,"sentinel_reps":a.reps,"m0_pairs":len(d0),"m0_gate_pass":int((d0.gate_s=="PASS").sum()),
             "m1_rows":len(d1),"m1_gate_pass_by_k":{str(k):int(((d1.k==k)&(d1.gate_s=="PASS")).sum()) for k in (32,64,128,256)},
             "m1_total_pairs_by_k":len(d0),"k256_all_pass":bool((d1[d1.k==256].gate_s=="PASS").all()),
             "validation_dev_accessed":False,"formal_test_accessed":False,"evidence_label":"EXPLORATORY_DESIGN_SIMULATION"}
    json.dump(summary,open(os.path.join(out,"m0_m1_summary.json"),"w"),indent=2,sort_keys=True)
    print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
