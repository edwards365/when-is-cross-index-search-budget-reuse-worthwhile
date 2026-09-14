#!/usr/bin/env python
"""P14-1: Vamana transport risk under repaired h=10 target-min-safe reference.
Recomputes incremental transport risk from frozen Vamana events.csv using the same
Eq.(20) caliber as HNSW cells: transported failure minus target-bottom failure."""
import numpy as np, pandas as pd, json

OUT = 'results/graph_anns_phase2_p11'
GRID = np.array([16, 32, 64, 128, 256, 512])
results = {}
for stage, path in (("vamana_sift", '/home/wlk/data500/icba_vamana_stage1/analysis/events.csv'),
                    ("vamana_arxiv", '/home/wlk/data500/icba_vamana_stage1_arxiv/analysis/events.csv')):
    e = pd.read_csv(path)
    names = sorted(e.source.unique())
    nq = int(e.q.max()) + 1
    # Build B matrices: B_s(q) from source rows, B_t(q) from target rows
    Bs = {}
    Bt = {}
    for s in names:
        sub = e[e.source == s].drop_duplicates('q').set_index('q')
        Bs[s] = sub.reindex(range(nq))['bs'].values
    for t in names:
        sub = e[e.target == t].drop_duplicates('q').set_index('q')
        Bt[t] = sub.reindex(range(nq))['bt'].values
    # incremental transport risk: mean over directed pairs of Pr[B_s < B_t] - Pr[B_tBOT]
    # (under monotone semantics: Z_t(q,a)=1 iff a < B_t(q))
    incr_all = []
    for t in names:
        bt = Bt[t]
        ref_fail = (bt < 0).astype(float)  # target-bottom failure = no safe action on target
        for s in names:
            if s == t: continue
            bs = Bs[s]
            z = (bs < bt).astype(float)  # deployed action < target min safe => fail
            incr_all.append((z - ref_fail).mean())
    incr = float(np.mean(incr_all))
    # variation
    fin = np.stack([~np.isnan(Bs[n]) & (Bs[n] >= 0) for n in names])
    nf = np.stack([Bs[n] >= 0 for n in names]).sum(axis=0)
    vfin = float(((nf > 0) & (nf > 1)).mean())
    nb = (~np.stack([Bs[n] >= 0 for n in names])).sum(axis=0)
    vend = float(((nb > 0) & (nb < len(names))).mean())
    unresolved = float((nb == len(names)).mean())
    results[stage] = {
        "incremental_risk_target_min_safe_ref": round(incr, 4),
        "finite_action_variation": round(vfin, 4),
        "endpoint_variation": round(vend, 4),
        "unresolved_mass": round(unresolved, 4),
        "caliber": "target-min-safe reference (same as Eq.20 for HNSW cells)"
    }
    print(stage, results[stage], flush=True)

json.dump(results, open(f'{OUT}/vamana_aligned_estimand.json', 'w'), indent=2)
print("saved")
