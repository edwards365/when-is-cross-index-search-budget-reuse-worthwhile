# Cross-Index G1 final report

## Final decision

**SHRINK_TO_HNSWLIB_IMPLEMENTATION_BOUNDARY**. Gate G1 (Faiss HNSW cross-implementation replication): **FAIL** (0/3 datasets). Gate G2 (Vamana cross-index replication): **FAIL** (1/3 datasets; GloVe only).

## Experimental facts

The frozen matrix contains 81 graphs and 972,000 query-budget records: three datasets, three index families, three histories, three seeds, 1,000 train-side holdout queries, and 12 frozen search budgets. Gate R0 passed before the 100K matrix. No formal-test or validation-dev member was accessed.

Faiss shows nonzero per-query budget variation and rank reshaping, but its cross-order-minus-same-order regret is not positive with a 95% lower bound above zero on any dataset. Vamana shows a positive robust transfer effect on GloVe; SIFT has positive regret but lacks significant Oracle headroom, while Arxiv does not show the required positive effect. Thus neither Gate reaches the preregistered 2/3-dataset threshold.

## Statistical inference

All transfer intervals use 5,000 paired query-level bootstrap replicates with seed 991. Top-1% trimming is included in the Gate statistics. The evidence does not justify extending hnswlib's hardness non-portability claim to Faiss or to graph ANNS generally under this protocol.

## Unresolved and prohibited claims

Failure to pass is not proof that Faiss or Vamana are construction-history invariant. Vamana history factors remain compound where the official implementation cannot isolate every source of randomness. No adaptive algorithm conclusion follows. The requested Parquet artifact is marked NOT_ESTIMABLE because no Parquet engine is installed; the complete 5.1 MiB CSV remains the canonical per-query evidence.
