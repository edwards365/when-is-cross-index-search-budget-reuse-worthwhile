import os
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
R = os.path.join(ROOT, "results", "active_recovery_headroom_reaudit")
rng = np.random.default_rng(991)
h2 = pd.read_csv(os.path.join(R, "h2_randomized_summary.csv"))
h2 = h2.loc[h2.groupby("dataset")["mean_ndc"].idxmin()].set_index("dataset")
rows=[]; boots=[]; lotos=[]
for code,fn in [("H3b","h3_environment_oracle_crossfit.csv"),("H4b","h4_pair_oracle_crossfit.csv")]:
    d=pd.read_csv(os.path.join(R,fn))
    for ds,g in d.groupby("dataset"):
        base=float(h2.loc[ds,"mean_ndc"]); basep=float(h2.loc[ds,"p95_ndc"])
        b=g.groupby("target_build",as_index=False).agg(mean_ndc=("mean_ndc","mean"),p95_ndc=("p95_ndc","mean"),abs_fail=("abs_fail","sum"),n=("n","sum"))
        b["headroom"]=1-b.mean_ndc/base
        ids=np.arange(len(b)); vals=np.empty(5000)
        for i in range(5000): vals[i]=1-b.mean_ndc.to_numpy()[rng.choice(ids,len(ids),replace=True)].mean()/base
        maxb=b.loc[b.headroom.idxmax(),"target_build"]
        drop=b[b.target_build!=maxb]
        for omit in b.target_build:
            z=b[b.target_build!=omit]
            lotos.append(dict(dataset=ds,oracle=code,omitted_target_build=omit,headroom=1-z.mean_ndc.mean()/base,abs_risk=z.abs_fail.sum()/z.n.sum()))
        risk=g.abs_fail.sum()/g.n.sum()
        row=dict(dataset=ds,oracle=code,headroom=1-g.mean_ndc.mean()/base,ci_low=np.quantile(vals,.025),ci_high=np.quantile(vals,.975),delete_max_build_headroom=1-drop.mean_ndc.mean()/base,p95_not_worse=g.p95_ndc.mean()<=basep,abs_risk=risk,risk_le_005=risk<=.05,max_contribution_build=maxb,gate_strong_components=False,evidence_label="EXPLORATORY_HEADROOM_REAUDIT")
        row["gate_strong_components"]=row["headroom"]>=.10 and row["ci_low"]>.05 and row["delete_max_build_headroom"]>.05 and row["p95_not_worse"] and row["risk_le_005"]
        rows.append(row)
        boots.extend(dict(dataset=ds,oracle=code,draw=i,headroom=v) for i,v in enumerate(vals))
pd.DataFrame(rows).to_csv(os.path.join(R,"gate_h_robustness.csv"),index=False)
pd.DataFrame(boots).to_csv(os.path.join(R,"gate_h_target_build_bootstrap.csv.gz"),index=False,compression="gzip")
pd.DataFrame(lotos).to_csv(os.path.join(R,"gate_h_loto.csv"),index=False)
print(pd.DataFrame(rows).to_string(index=False))
