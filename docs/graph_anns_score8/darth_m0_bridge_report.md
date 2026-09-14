# DARTH comparison M0 bridge report

Status: **PASS — M1 same-index comparison authorized**

This report seals engineering feasibility only. It does not claim that DARTH, TCP, or ICBA is scientifically superior.

## Frozen implementation

- DARTH official repository: `https://github.com/MChatzakis/DARTH`
- DARTH commit: `0d9bafcf31d1d79668bc71139fe93fa5e70b5185`
- License: MIT; SHA256 `52412d7bc7ce4157ea628bbaacb8829e0a9cb3c58f57f99176126bc8cf2bfc85`
- LightGBM commit: `3f7e6081275624edfca1f9b3096bea7a81a744ed`
- CPU-only build; GPU, validation-dev, formal-test, and future-replication were not used.

## Adapter and query firewall

The official fixed dataset label `SIFT100M` is backed here by the frozen SIFT-100K base and is never described as a 100M experiment. Source training (2,000), source validation (500), target certification (500), and target evaluation (1,000) use distinct source rows. Exact content-overlap checks are zero for all ten pairwise role/base comparisons. The generated files and hashes are recorded in `m0_sift100k_adapter_ledger.json`; heavy data remain under `/home/wlk/data500/graph_anns_score8/darth_comparison`.

## Executable checks

1. The official CPU HNSW driver and Faiss library build and link against the pinned LightGBM library.
2. A 100-query no-early-stop run on the saved SIFT-100K index reports Recall@10 = 1.0000; an independent Python/Faiss evaluator loads the same index and also obtains 1.0000 (100/100 query rows exact at Recall@10 = 1.0).
3. A 100-query DARTH inference completes with an official 11-feature model and reports aggregate Recall@10 = 0.9890. This is interface evidence only: that published model was trained for SIFT100M, M=32, efConstruction=500, efSearch=500, while this smoke uses SIFT-100K, M=16, efConstruction=100, efSearch=200.
4. An initial 17-feature model attempt was rejected by LightGBM because the runtime emitted 11 features. Feature-shape validation was not bypassed; the compatible official 11-feature variant was selected instead.

## Decision

M0 passes because the official checkout is clean, adapter identities are deterministic and role-disjoint, native full-search recall agrees with an independent evaluator, and the official DARTH inference path is executable. M1 must train a fresh, frozen 11-feature DARTH regressor on the registered source-training role before any scientific comparison. The pretrained smoke score is excluded from every M1–M4 table and gate.
