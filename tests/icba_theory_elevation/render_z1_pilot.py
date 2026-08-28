#!/usr/bin/env python3
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
rows=list(csv.DictReader(open(ROOT/'results/icba_theory_elevation/z1_response_relation.csv')))
fig,axes=plt.subplots(1,3,figsize=(12,3.6),sharey=True)
versions=['NDC_QUANTILES','DISTANCE_GAP_QUANTILES','FIXED_PROBE_INCREMENT']
for ax,v in zip(axes,versions):
 r=[x for x in rows if x['version']==v]
 ax.scatter([float(x['fingerprint_distance']) for x in r],[float(x['budget_distance']) for x in r],s=24,alpha=.75)
 ax.set_title(v.replace('_',' ').title()); ax.set_xlabel('standardized fingerprint distance'); ax.grid(alpha=.2)
axes[0].set_ylabel('minimal-safe-budget response distance')
fig.suptitle('Exploratory HNSWlib SIFT-100K Z1 information pilot')
fig.tight_layout(); out=ROOT/'figures/icba_theory_elevation/z1_vs_budget_response.png'; out.parent.mkdir(parents=True,exist_ok=True); fig.savefig(out,dpi=180); plt.close(fig)
print(out)
