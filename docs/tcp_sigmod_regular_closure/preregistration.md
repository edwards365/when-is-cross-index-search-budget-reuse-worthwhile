# TCP SIGMOD Regular Closure preregistration

Frozen start: \`d62c0220186a1cc5e33e459c797a3785beccc1bd\`.

- Evidence level: fixed-target, multi-build exploratory method closure until
  prospective build/query confirmation.
- Datasets: SIFT-100K and Arxiv-Nomic-100K. No GloVe, validation-dev, or
  formal-test.
- Event: Recall@10 >= 0.90; risk limit 0.05 with one-sided 95% bounds.
- Actual efSearch grid: 10, 20, 40, 80, 120, 160, 200.
- Bootstrap: target build outer, query id inner, 5,000 repetitions, seed 991.
- Builds: 1103, 1229, 1361, 1499, 1621, 1747, 1877, 1999, 2131, 2267.

Each leave-one-build-out target has nine source builds, so the exchangeable
build resolution floor is 1/(9+1)=0.10. This matrix cannot support a formal 5%
build-level conformal certificate. Any 5% claim must come from independent
target-query certification and is per target build absent simultaneous
correction.

The historical Arxiv runner held --efSearch 200 fixed while changing
--fixed-amount-of-search, which is unused by DARTH no-early-stop. Old Arxiv TCP
and fixed-baseline conclusions are INVALIDATED_BY_EXECUTION_SEMANTICS. Raw
files remain immutable.

The repaired runner must vary --efSearch, omit --fixed-amount-of-search, write
only to a new data500 directory, record commands and hashes, pass a seven-value
dry run, and pass a minimal live smoke before the ten-build run. No parameter
may change after repaired Arxiv results are viewed.

Canonical TCP must represent BOT as +infinity/abstention, never clip an
unsupported order statistic, include every deployed query in risk and cost,
and keep selection, certification, and evaluation disjoint. Multi-action
certification requires fixed-sequence, simultaneous bounds, or a separate
selection set. Failure uses a frozen fixed-safe fallback.

Primary eligibility requires independent safety, Recall difference >= -0.001,
an improvement in a registered efficiency dimension without structural
p95/p99 degradation or hidden offline cost, LOBO and largest-build robustness,
and unseen query/build confirmation. A negative dataset may only be excluded
by a preregistered deployable applicability gate.
