# Vamana implementation preflight

Evidence level: implementation-semantic and reproducibility preflight only; this is not a Vamana scientific result.

The frozen DiskANN3 Rust source at `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475` compiled with Rust/Cargo 1.97.1 in release mode. The source archive SHA256 is `23e5da9966cde00dd83ae9ad79363312c178e59b81da3dc2d51e5952921df6d3`. The controlled environment uses squared-L2 float32, degree 32, L-build 64, alpha 1.2, medoid start, beam width 1, and one build/search thread.

Three identical synthetic builds produced the same index SHA256 `439363222f77640cb0e31819743964d2ede301d30ed59f20e8123d11c0327016`, hence `BYTE_IDENTICAL`. Three pre-registered input permutations produced three distinct artifacts and permutation 7103 replayed byte-identically. Each permutation passed 10,000 samples in both external→internal and internal→external directions with zero error.

The design-only budget grid is frozen at L={16,32,64,128,256,512}, k=10 and Recall@10 threshold 0.95. Recall was 0.9484, 0.9926, 0.9996, 1.0000, 1.0000, 1.0000 and mean internal distance-computation counts were 473.186, 718.076, 1053.028, 1423.808, 1742.476, 1932.266. `l_value` enters the native search and changes exploration; `beam_width=1` is supported and is an independent setting. Neither is asserted numerically equivalent to HNSW `efSearch` or a strict time/expansion limit.

A minimal result recorder exposes per-query Recall, `SearchStats.cmps`, `SearchStats.hops`, and a top-k ID hash without modifying search. Across six budgets × 500 queries, build/search and save/load values matched exactly for every recorded field; top-k hash mismatches were zero. Cost bridge is established within this implementation. Raw cost values are not cross-family comparable.

No evaluation, future-replication vectors/truth, validation-dev, or formal-test roles were accessed. Query bootstrap scope and the three required semantic patches are frozen in `stage1_contract.json`.

Decision: `READY_FOR_VAMANA_STAGE1`.
