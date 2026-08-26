# Cross-Index G1 preregistration

This experiment freezes three 100K train-side datasets, new disjoint 250-query design and 750-query confirm sets, seeds 43/59/71, and histories random(seed 20260915), natural source order, and the existing frozen cluster-block order. Formal-test and validation-dev remain sealed.

hnswlib and Faiss use M=16, efConstruction=100, k=10, and ef `{10,16,24,32,48,64,96,128,192,256,384,512}`. Faiss receives an explicit `RandomGenerator(seed)` before addition. If the seed cannot be independently verified, the affected factor is labeled compound.

Vamana uses R=32 and alpha=1.2. Design-only build-L candidates are `{50,100,150}`; the smallest whose SIFT-10K design endpoint reaches mean Recall .95 is selected, otherwise 150 is frozen with `ENDPOINT_UNREACHABLE`. Its search beam ladder is `{10,16,24,32,48,64,96,128,192,256,384,512}` and is never extended after design.

Gate R0 is SIFT <=10K, three index families, histories random/natural, seeds 43/59, first 100 design queries, and every frozen budget. It requires exact truth, native/instrumented labels and distances, deterministic NDC, graph invariants/checksum, hnswlib reproduction, and deletion of temporary graphs.

Confirm statistics inherit stable budget, Omega, paired 5,000-query bootstrap seed991, rank correlation/inversion, transfer regret, Price of Index Blindness, top-1% trimming, seed/query robustness, Recall and NDC reporting. G1/G2 thresholds and stop labels are exactly those in the task protocol; no result-dependent grid, seed, history, dataset, or method changes are permitted.
