#!/usr/bin/env python3
import json,csv,hashlib
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path('/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k');BASE=ROOT/'results/cross_index/g1';DER=BASE/'derived';FIG=BASE/'figures';FIG.mkdir(exist_ok=True);DOC=ROOT/'docs/cross_index/g1'
d=json.load(open(ROOT/'manifests/cross_index_g1_final_decision.json')); S=d['summary'];datasets=['arxiv_nomic_100k','glove100_100k','sift_100k'];indexes=['hnswlib','faiss','vamana']
def plot(field,title,name):
 x=range(len(datasets));w=.25;plt.figure(figsize=(8,4))
 for j,idx in enumerate(indexes):plt.bar([i+(j-1)*w for i in x],[S[f'{idx}:{ds}'][field] for ds in datasets],w,label=idx)
 plt.xticks(list(x),datasets,rotation=15);plt.title(title);plt.legend();plt.tight_layout();plt.savefig(FIG/(name+'.png'),dpi=150);plt.savefig(FIG/(name+'.pdf'));plt.close()
plot('budget_variation_rate','Query budget variation across histories','budget_variation')
plot('rank_inversion','Mean pairwise rank inversion','rank_inversion')
plot('cross_minus_same_regret','Cross-order minus same-order regret','transfer_regret')
plot('price_of_blindness','Price of index blindness','price_of_blindness')
report=f'''# Cross-Index G1 final report\n\n## Final decision\n\n**{d['label']}**. Gate G1 (Faiss HNSW cross-implementation replication): **FAIL** (0/3 datasets). Gate G2 (Vamana cross-index replication): **FAIL** (1/3 datasets; GloVe only).\n\n## Experimental facts\n\nThe frozen matrix contains 81 graphs and 972,000 query-budget records: three datasets, three index families, three histories, three seeds, 1,000 train-side holdout queries, and 12 frozen search budgets. Gate R0 passed before the 100K matrix. No formal-test or validation-dev member was accessed.\n\nFaiss shows nonzero per-query budget variation and rank reshaping, but its cross-order-minus-same-order regret is not positive with a 95% lower bound above zero on any dataset. Vamana shows a positive robust transfer effect on GloVe; SIFT has positive regret but lacks significant Oracle headroom, while Arxiv does not show the required positive effect. Thus neither Gate reaches the preregistered 2/3-dataset threshold.\n\n## Statistical inference\n\nAll transfer intervals use 5,000 paired query-level bootstrap replicates with seed 991. Top-1% trimming is included in the Gate statistics. The evidence does not justify extending hnswlib's hardness non-portability claim to Faiss or to graph ANNS generally under this protocol.\n\n## Unresolved and prohibited claims\n\nFailure to pass is not proof that Faiss or Vamana are construction-history invariant. Vamana history factors remain compound where the official implementation cannot isolate every source of randomness. No adaptive algorithm conclusion follows. The requested Parquet artifact is marked NOT_ESTIMABLE because no Parquet engine is installed; the complete 5.1 MiB CSV remains the canonical per-query evidence.\n'''
(DOC/'final_report.md').write_text(report)
files=[ROOT/'manifests/cross_index_g1_final_decision.json',DOC/'final_report.md',DOC/'theory.md']+list(DER.glob('*'))+list(FIG.glob('*'))
with open(BASE/'checksums.sha256','w') as f:
 for p in sorted(files):f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))+'\n')
print(d['label'])
