# Target-certified post-seal replication

This compact record describes the independent target-certification stage added after the source-only boundary test and manuscript evidence seal.

- The candidate family and primary `+1` lane were frozen before the new target roles were accessed.
- Each dataset uses 24 registered Faiss HNSW builds and all 552 non-diagonal source--target directions.
- Each direction uses 500 target-certification queries and 500 mutually exclusive target-evaluation queries. Both roles are disjoint from every earlier registered query role.
- Candidate and endpoint each receive a one-sided Clopper--Pearson error allocation of 0.025. If the endpoint fails, the decision abstains; otherwise the candidate executes when its UCB is at most 0.05 and the endpoint executes as fallback when it is not.
- Candidate selection never uses either new target role. Evaluation never changes the candidate, threshold, grid, action, certificate, or fallback.
- Primary efficiency is native distance computations. Target-build bootstrap intervals use 5,000 seed-991 resamples. Wall-clock measurements are a fixed-machine interleaved sensitivity only.
- Target-stage cost charges exact target truth (`500 x 100,000` distances) plus measured candidate/endpoint certification searches, deduplicating identical actions. The pairwise scenario charges each direction separately; the shared-target scenario reuses one target audit across 23 source histories.
- Historical source-policy acquisition NDC and exact-truth wall time are unavailable. They are not assigned zero, so complete cold lifecycle and full wall-clock economics remain not estimable.

The compact package contains all 1,104 pair decisions, 48 target-build summaries, four cost summaries, and the two registered cost ledgers. Native raw-query replay still requires the separately provisioned datasets, indexes, and binaries.
