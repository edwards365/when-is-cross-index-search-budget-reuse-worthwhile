# Phase 1.1 source and resource audit

- Parent commit: `5dac9079376785094fb33ff9a456b2c962eb6315`.
- Branch: `exp/graph_anns_iclr_phase1_semantic_scope_closure`.
- HDF5 source files are readable and hash-registered; SIFT train has 1,000,000 vectors and Arxiv-Nomic train has 1,344,643 vectors.
- Historical Faiss registry records `base_count=30000` for both datasets. The frozen runner explicitly executes `train[:30000]`; this is a loader truncation, not a 100K Faiss result.
- data500 free space: 865.35 GiB; projected 100K Faiss scratch reserve: 18.0 GiB; the 20 GiB post-run reserve is satisfied.
- Forbidden validation/formal/future/HDF5 test roles were not accessed.
