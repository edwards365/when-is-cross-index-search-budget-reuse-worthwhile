# ICBA/TCP versus DARTH: preregistered comparison design

## Scope and positioning

This comparison does not treat ICBA, TCP, and DARTH as interchangeable algorithms. ICBA is the audit and certification layer; TCP is the exchangeable-build conformal pooling policy for repeated queries with cached labels; DARTH is a learned, search-integrated early termination policy. DARTH is evaluated both as a strong adjacent baseline and as a policy under ICBA audit.

Universal dominance is not required. Safety remains a hard Gate. Once safety passes, a method may establish relative value through one statistically supported advantage in computation, tail behavior, target-label demand, refresh/retraining cost, cross-rebuild robustness, or certification, while every disadvantage remains visible.

## Comparison modules

### M0 — Official implementation bridge

Pin the official DARTH repository, license, build toolchain and CPU configuration. Convert the already-frozen SIFT/Arxiv inputs into DARTH's expected representation under an ID/hash ledger. Compile the official Faiss fork and `hnsw_test` outside the main filesystem, reproduce no-early-stop evaluation, and run one DARTH inference. Any failure here is an integration outcome only.

### M1 — Same-index efficacy

On an identical target Faiss HNSW build, compare target-trained DARTH, target-pool TCP, fixed ef, maximum ef, and a non-deployable per-query oracle. Primary efficiency is distance computations; controlled latency is secondary. Report recall risk, mean/p50/p95/p99 cost, fallback, abstention, training labels, truth work and model/pool construction.

### M2 — Cross-rebuild portability

Freeze the source-trained DARTH model and source TCP pool, then replay both on independent target rebuilds with unchanged data and hyperparameters. Target-retrained DARTH and target TCP are recovery comparators. ICBA reports blind-reuse risk, certification outcomes, additional target labels and fallback cost.

### M3 — Data-refresh recovery

At equal delete/insert refresh rates 1%, 5% and 10%, compare old DARTH, target-retrained DARTH, old TCP, refreshed TCP and maximum ef. Old TCP is explicitly outside Theorem 3's exchangeability premise; this cell measures boundary behavior, not theorem validity.

### M4 — Composition value

Treat DARTH as an input policy to ICBA. Compare blind reuse with audit-then-certify/fallback. The key question is whether ICBA prevents unsafe deployment or reduces target evidence at acceptable cost, even if DARTH remains faster within a fixed index.

## Decision rule

Safety is strict and cannot be traded for speed. Conditional value needs one paired, robust advantage rather than across-the-board superiority. Dataset-specific value is allowed but must be labeled as such. All target-build inference uses an outer build/inner query bootstrap with 5,000 repetitions and seed 991, with LOBO and deletion diagnostics.

Heavy source, converted data, build trees, indices, models and logs are confined to `/home/wlk/data500/graph_anns_score8/`. Only protocols, adapters, compact results, tests, checksums and decisions enter the main ANNS worktree.
