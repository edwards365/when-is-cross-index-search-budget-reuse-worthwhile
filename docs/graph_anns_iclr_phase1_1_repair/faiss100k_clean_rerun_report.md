# Faiss-100K clean rerun report

The 48 frozen Faiss 1.15.0/M=16/efConstruction=100 serialized indices were reused after registry/hash checks; no index was rebuilt. Seed-991 queries were selected by a fixed permutation of train IDs >=100000 after excluding historical role IDs. SIFT and Arxiv each have 750 queries, with zero ID/raw/normalized-content overlap to the base and historical evaluation roles. Exact FlatL2 truth and k=10 HNSW search were run on this clean role only; self-match count is zero. Native ndis is retained as NOT_ESTIMABLE_BATCH_CUMULATIVE.
