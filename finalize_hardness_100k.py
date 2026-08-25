#!/usr/bin/env python3
import csv,hashlib,json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');FIG=ROOT/'results/hardness_portability_100k/figures';FIG.mkdir(parents=True,exist_ok=False)
core=json.load(open(ROOT/'results/hardness_portability_100k/derived/core_gate_summary.json'));real=json.load(open(ROOT/'results/hardness_portability_100k/realistic_derived/realistic_history_decision.json'));prefix=json.load(open(ROOT/'results/hardness_portability_100k/single_prefix/decision.json'))
ds=['arxiv_nomic_100k','glove100_100k','sift_100k'];labels=['Arxiv','GloVe','SIFT'];x=np.arange(3);width=.35
def save(name,ylabel):plt.ylabel(ylabel);plt.xticks(x,labels);plt.tight_layout();plt.savefig(FIG/name,dpi=160);plt.close()
plt.figure(figsize=(6,4));plt.bar(x-width/2,[.2492,.4466,.2517],width,label='10K');plt.bar(x+width/2,[core['oracle'][d]['mean'] for d in ds],width,label='100K');plt.legend();save('oracle_10k_100k.png','Oracle headroom')
plt.figure(figsize=(6,4));plt.bar(x-width/2,[.264,.164,.375],width,label='10K');plt.bar(x+width/2,[core['omega'][d]['omega'] for d in ds],width,label='100K');plt.legend();save('omega_10k_100k.png','Omega')
plt.figure(figsize=(6,4));plt.bar(x,[core['portability'][d]['delta_history'] for d in ds]);save('same_vs_cross_transfer_regret.png','Cross-order minus same-order regret')
rank=list(csv.DictReader(open(ROOT/'results/hardness_portability_100k/derived/rank_reversal.csv')));same=[np.mean([float(r['rank_reversal_rate']) for r in rank if r['dataset']==d and r['same_order']=='True']) for d in ds];cross=[np.mean([float(r['rank_reversal_rate']) for r in rank if r['dataset']==d and r['same_order']=='False']) for d in ds]
plt.figure(figsize=(6,4));plt.bar(x-width/2,same,width,label='same order');plt.bar(x+width/2,cross,width,label='cross order');plt.legend();save('query_budget_rank_inversion.png','Rank reversal rate')
plt.figure(figsize=(7,4));plt.bar(x-.25,[core['portability'][d]['delta_history'] for d in ds],.25,label='LID order');plt.bar(x,[real['summary'][d]['natural_source_order']['excess_regret'] for d in ds],.25,label='natural');plt.bar(x+.25,[real['summary'][d]['cluster_block_order']['excess_regret'] for d in ds],.25,label='cluster block');plt.legend();save('artificial_vs_realistic_history.png','Excess transfer regret')
plt.figure(figsize=(7,4));oracle=np.array([core['oracle'][d]['mean'] for d in ds]);ideal=np.array([prefix['datasets'][d]['mean_ideal_reuse_net_gain'] for d in ds]);noreuse=np.array([prefix['datasets'][d]['mean_no_reuse_net_gain'] for d in ds]);plt.bar(x-.25,oracle,.25,label='Oracle');plt.bar(x,ideal,.25,label='ideal reuse');plt.bar(x+.25,noreuse,.25,label='no reuse');plt.axhline(0,color='black',linewidth=.8);plt.legend();save('oracle_probe_error_net_gain.png','Fractional net gain')

targets=[]
for rel in ('docs/hardness_portability_100k','manifests/hardness_portability_100k','results/hardness_portability_100k'):
 for path in sorted((ROOT/rel).rglob('*')):
  if path.is_file() and path.name!='checksums.sha256':targets.append(path)
lines=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT)) for p in targets]
(ROOT/'results/hardness_portability_100k/checksums.sha256').write_text('\n'.join(lines)+'\n')
print(json.dumps({'figures':6,'hashed_files':len(lines),'formal_test_accessed':False},indent=2))
