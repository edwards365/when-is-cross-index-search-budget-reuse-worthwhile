#!/usr/bin/env python3
import glob,json,math,os,sys
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
sys.path.insert(0,os.path.dirname(__file__))
from m0_m1 import load,cp,DATASETS,SEED

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
REPS=500
SPLIT=json.load(open(os.path.join(ROOT,"manifests/icba_micro_closure_query_split.json")))

def order(name): return name.split("__",2)[-1]
def q95_shift(vals):
    vals=np.sort(np.asarray(vals,dtype=int))
    idx=min(len(vals)-1,max(0,int(math.ceil(.95*(len(vals)+1)))-1))
    return int(max(0,vals[idx]))

rows=[]
for dataset in DATASETS:
    paths=sorted(glob.glob(os.path.join(ROOT,"results/cross_index/g1/main/hnswlib",f"{dataset}__*.csv.gz")))
    builds={os.path.basename(p).replace(".csv.gz",""):load(p) for p in paths}
    sentinel=sorted(map(int,SPLIT["datasets"][dataset]["sentinel_query_ids"]))
    evaluation=sorted(map(int,SPLIT["datasets"][dataset]["evaluation_query_ids"]))
    # Fixed deployable build fingerprint: mean standardized first-prefix X over unlabeled sentinel IDs.
    raw_fp={}
    for name,(d,b,q,X,y,c,ndc) in builds.items():
        pos={int(x):i for i,x in enumerate(q)}
        raw_fp[name]=X[[pos[x] for x in sentinel]].mean(axis=0)
    fp_mat=np.vstack(list(raw_fp.values())); mu=fp_mat.mean(0); sd=fp_mat.std(0); sd[sd==0]=1
    fp={n:(v-mu)/sd for n,v in raw_fp.items()}
    for sname,(sdta,sb,sq,sX,sy,sc,sndc) in builds.items():
        first=sdta[sdta.ef_search.astype(int)==sb[0]].sort_values("query_id")
        tr=first.query_split.to_numpy()=="cross_index_design"
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,penalty="l2",solver="lbfgs",max_iter=1000,random_state=SEED))
        model.fit(sX[tr],sy[tr])
        for tname,(td,b,q,X,y,c,ndc) in builds.items():
            if tname==sname: continue
            raw=model.predict(X).astype(int)
            pos={int(x):i for i,x in enumerate(q)}
            sidx=np.asarray([pos[x] for x in sentinel]); eidx=np.asarray([pos[x] for x in evaluation])
            allowed=[n for n in builds if order(n)!=order(tname)]
            # M2: all leave-one-history-out donor design residuals.
            hist=[]
            for dn in allowed:
                dd,db,dq,dX,dy,dc,dndc=builds[dn]
                dfirst=dd[dd.ef_search.astype(int)==db[0]].sort_values("query_id")
                dm=dfirst.query_split.to_numpy()=="cross_index_design"
                hist.extend((dy[dm]-model.predict(dX[dm]).astype(int)).tolist())
            m2base=q95_shift(hist)
            # M3: nearest three deployable-fingerprint donors, same LOOH firewall.
            ranked=sorted(allowed,key=lambda n:float(np.linalg.norm(fp[n]-fp[tname])))
            local=ranked[:3]
            localres=[]
            for dn in local:
                dd,db,dq,dX,dy,dc,dndc=builds[dn]
                dfirst=dd[dd.ef_search.astype(int)==db[0]].sort_values("query_id")
                dm=dfirst.query_split.to_numpy()=="cross_index_design"
                localres.extend((dy[dm]-model.predict(dX[dm]).astype(int)).tolist())
            m3base=q95_shift(localres)
            donor_d=[float(np.linalg.norm(fp[n]-fp[tname])) for n in allowed]
            support=bool(donor_d and donor_d[0] <= np.quantile([float(np.linalg.norm(fp[a]-fp[z])) for a in allowed for z in allowed if a<z],.95))
            ndcf=float(np.mean([ndc[(int(q[i]),b[-1])] for i in eidx]))
            pairseed=SEED+sum(ord(z) for z in sname+"|"+tname)
            for k in (32,64,128,256):
                rng=np.random.default_rng(pairseed+k)
                for method,base,donors in (("M2",m2base,len(allowed)),("M3",m3base,len(local))):
                    risks=[];ups=[];saves=[];shifts=[];refusals=[]
                    for rep in range(REPS):
                        si=sidx if k==256 else rng.choice(sidx,size=k,replace=False)
                        tshift=int(max(0,np.max(y[si]-raw[si])))
                        sh=max(base,tshift)
                        if method=="M3" and not support:
                            alloc=np.full_like(raw,len(b)-1); refusal=1.
                        else:
                            alloc=np.minimum(raw+sh,len(b)-1); refusal=0.
                        f=int(np.sum((alloc[eidx]<y[eidx])|c[eidx])); n=len(eidx)
                        online=float(np.mean([ndc[(int(q[i]),b[int(alloc[i])])] for i in eidx]))
                        risks.append(f/n);ups.append(cp(f,n));saves.append(1-online/ndcf);shifts.append(sh);refusals.append(refusal)
                    rows.append({"method":method,"dataset":dataset,"source_build":sname,"target_build":tname,
                     "k":k,"reps":REPS,"looh":True,"donor_builds":donors,"support":support,
                     "mean_risk":float(np.mean(risks)),"p95_risk":float(np.quantile(risks,.95)),
                     "p95_cp95_upper":float(np.quantile(ups,.95)),"gate_s_pass_fraction":float(np.mean(np.asarray(ups)<=.05)),
                     "mean_ndc_saving_vs_fixed":float(np.mean(saves)),"p05_ndc_saving_vs_fixed":float(np.quantile(saves,.05)),
                     "mean_shift_levels":float(np.mean(shifts)),"refusal_rate":float(np.mean(refusals)),
                     "gate_s":"PASS" if np.quantile(ups,.95)<=.05 else "FAIL",
                     "evidence_label":"EXPLORATORY_DESIGN_SIMULATION"})
out=pd.DataFrame(rows)
out.to_csv(os.path.join(ROOT,"results/rebuild_portability_recovery/m2_m3_looh.csv"),index=False)
summary=out.groupby(["method","dataset","k"]).agg(pairs=("gate_s","size"),pass_pairs=("gate_s",lambda x:(x=="PASS").sum()),
 median_saving=("mean_ndc_saving_vs_fixed","median"),min_saving=("mean_ndc_saving_vs_fixed","min"),
 median_refusal=("refusal_rate","median"),max_cp=("p95_cp95_upper","max")).reset_index()
summary.to_csv(os.path.join(ROOT,"results/rebuild_portability_recovery/m2_m3_summary.csv"),index=False)
print(summary.to_string(index=False))
