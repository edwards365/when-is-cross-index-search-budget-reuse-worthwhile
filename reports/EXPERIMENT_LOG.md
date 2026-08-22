# Experiment log

All timestamps are UTC. Raw result directories are immutable once referenced by a report.

| Timestamp | Run ID | Purpose | Dataset | Config | Seed | Status | Notes |
|---|---|---|---|---|---:|---|---|
| 2026-08-22T03:38:39Z | `5c814131-a03b-4264-9f36-852f06a5b5c4` | HNSW pipeline smoke | synthetic narrow bridge 2K×16 | `configs/experiments/smoke.yaml` | 7 | success | Recall@10: 0.914/0.983/0.997/1.0 for ef 10/20/40/80. Raw query rows retained locally under the run ID; pre-commit metadata says `uncommitted`. |
| 2026-08-22T03:38Z | `mechanism-union-256-s7` | Exact resistance numerical check | first 256 synthetic base nodes | `configs/experiments/mechanism.yaml` | 7 | success | 1,532 weighted edges; max leverage 1.0000000000000133; no bound violations above tolerance. |
| 2026-08-22T03:36Z | n/a | Python test invocation | n/a | n/a | n/a | infrastructure failure | Parallel `conda run` calls collided on a temporary activation file; package was not installed and pytest collection consequently failed. Re-run serially with `.venv/python.exe`; this is not an algorithm test result. |
| 2026-08-22T03:55Z | n/a | HNSW instrumentation harness build | synthetic C++ fixture | CMake Release | 7 | compile failure | `getListCount` in upstream hnswlib requires a non-const link-list pointer; harness used `const auto*`. Corrected without changing upstream. |
| 2026-08-22T03:57Z | `hnsw-cpp-instrumentation-s7` | Upstream counter audit | synthetic 512×8 | M=16 efConstruction=100 efSearch=40 | 7 | invalid metric discovered | Recall@10=1 and graph invariants passed, but upstream mean distance metric=24.4375 because base-layer collection is disabled by the default template argument. Do not use as total NDC; counter-wrapped distance function added for exact calls. |
| 2026-08-22T03:59Z | `hnsw-cpp-counting-space-s7` | Exact HNSW NDC and graph-export smoke | synthetic 512×8 | M=16 efConstruction=100 efSearch=40 | 7 | success | Recall@10=1; exact mean NDC=199 versus upstream metric=24.4375; mean high-layer hops=3.3125; 5,487 directed layer-0 edges, 5,372 reciprocal directed edges, max degree 32; invariants passed. |
| 2026-08-22T04:08Z | `repair-smoke-s7-q23` | Six-way degree-preserving repair | exported hnswlib 512×8 layer 0 | `configs/experiments/repair_smoke.yaml` | graph 7 / repair 19 / query 23 | negative success | Original ef10 recall=.995 mean NDC=98.05. Resistance+Direction first exceeds .95 at ef20 recall=.984 mean NDC=135.94. Resistance first exceeds .95 at ef40 mean NDC=182.05 and never reaches .99. All failures retained. |
