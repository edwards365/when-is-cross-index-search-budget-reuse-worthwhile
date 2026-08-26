# Cross-Index G1 dependency and instrumentation audit

The task-local dependency directory is `.deps/cross_index_g1` and is excluded from frozen evidence. `faiss-cpu==1.15.0` and `diskannpy==0.7.0` were installed with `--no-deps` against the existing NumPy 1.26.4 environment. Faiss reports AVX2 optimization and exposes `IndexHNSWFlat` plus the process-global `faiss.cvar.hnsw_stats.ndis` counter. R0 must prove that resetting/reading this counter leaves labels, distances, graph serialization, and repeated per-query results unchanged.

The official Microsoft DiskANN repository was cloned at commit `158126e64129d3c39f9df02199c2dcc06d4f9e7f`. The current official in-memory implementation contains feature-gated integration counters; `query_distance` counts query-to-index distance evaluations and is a candidate exact NDC. Production builds make these counters no-ops. R0 must therefore compare production and `integration-test` builds from the same commit, using single-threaded deterministic search, and require identical returned labels, graph bytes, and search results. If the counters cannot be surfaced without changing the execution path, Vamana must stop as `INVALID_CROSS_INDEX_INSTRUMENTATION`; visited nodes or latency may not substitute for NDC.

DiskANN Python wheel metadata does not expose an NDC field and is not sufficient by itself for the primary experiment. It may be used only as an additional native-label reference if its graph construction can be matched exactly; it is not the authoritative instrumented runner.

Compiler baseline is GCC 9.4.0 and CMake 3.16.3; the official current DiskANN repository uses Cargo for its benchmark/in-memory stack. Exact Cargo/Rust versions, feature flags, thread count, and binary hashes must be frozen after successful compilation and before R0 graph construction.

No index has been built. Formal-test and validation-dev remain sealed.
