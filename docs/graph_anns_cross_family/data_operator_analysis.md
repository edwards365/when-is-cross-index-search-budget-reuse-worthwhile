# Data and operator analysis

The evidence covers SIFT-100K and Arxiv-Nomic-100K under hnswlib HNSW, Faiss HNSW, and DiskANN3 Vamana-style search. Budgets are implementation-native and not numerically comparable: efSearch for HNSW and l_value for Vamana-style. Likewise NDC counters are only interpreted within implementation. The shared estimand is source-build policy transport to a target build at Recall@10 >= .95.
