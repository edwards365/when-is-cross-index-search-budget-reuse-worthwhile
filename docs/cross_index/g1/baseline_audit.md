# Cross-Index G1 baseline audit

Frozen baseline `f43486d1d35efb147d060e9dc8baa36dc56586a7` and `results/rebuild_tax/checksums.sha256` verify without error. Work proceeds on `exp/cross_index_negative_mechanism_g1` in the 100K worktree. The separate legacy `navigation-aware-resistance-hnsw-ocgt` worktree contains unrelated uncommitted files and is excluded from all writes.

The inherited search grid is `{10,16,24,32,48,64,96,128,192,256,384,512}`, with `M=16`, `efConstruction=100`, `k=10`, graph seeds `{43,59,71}`, paired query bootstrap 5,000 times with seed 991, and primary cost `exact_ndc` (distance-function calls). Latency remains secondary.

For a query curve, the inherited minimum stable sufficient budget is the first frozen grid point `e` for which Recall@10 is at least the target at `e` and every larger frozen point; if no point qualifies it is right-censored at 1024. The historical 100K primary target is Recall@10 >= .90; rebuild-tax additionally used graph-fixed-quality preservation. This G1 protocol retains the explicit .90 primary threshold and reports .95/.99 endpoint reachability separately, without redefining stability after results.

The inherited Omega is computed on `Y(q,h)=log2 B(q,h)` after additive query and graph effects: interaction variance divided by query-plus-interaction variance. The three realistic histories are: random permutation with seed 20260915, ascending original train source ID (`natural_source_order`), and frozen 100-cluster MiniBatchKMeans blocks (`cluster_block_order`) with the committed per-dataset permutations and hashes.

Existing hnswlib instrumentation is reproducible and counts exact distance-function calls while verifying native labels per row. Faiss and DiskANN/Vamana are not installed in the project virtual environment, and no local official source checkout was found. Remote official-repository probing did not return within 30 seconds. Dependency acquisition, version freezing, build flags, seed control, and exact-NDC instrumentation therefore remain a pre-R0 gate; no new index may be built until resolved and preregistered.

Decision: `PASS_BASELINE_AUDIT_WITH_DEPENDENCY_GATE_PENDING`. No baseline-definition conflict was found. Formal-test and validation-dev were not accessed.
