# Phase 7 preregistration: one-rung high-Recall repair and reuse-domain audit

Frozen after the Phase 5 failure was sealed at commit
`2c4f5698c584766437dbca6d594e87bef477d62e` and before any Phase 7 source or
target outcome is generated.

## Motivation and non-retroactivity

Phase 5 established SLA-risk-constrained efficiency but failed the registered
mean-Recall noninferiority margin on both datasets. It also showed that source
history construction is not amortized at N=100,000. Phase 7 does not change,
reinterpret, or rerun that decision. It tests one mechanically conservative
repair and reports the workload-reuse domain in which the complete cost is
recoverable.

## Frozen method

The only new candidate is **TCP-HM9-TC-R1**. Starting from canonical
TCP-HM9-TC, every finite action is moved exactly one step upward on the frozen
grid `(10,20,40,80,120,160,200)`; 200 remains 200 and BOT remains endpoint
fallback. There is no fitted parameter, target-dependent shift, candidate
race, or result-driven choice. Source-global fixed ef and fixed-safe ef=200
remain the fallback sequence. The family is certified with the same one-sided
Bonferroni Clopper-Pearson bounds at overall alpha 0.05.

## Fresh roles and builds

- SIFT certification rows `[995500,996000)`, evaluation rows
  `[996000,997000)`.
- Arxiv-Nomic certification rows `[105000,105500)`, evaluation rows
  `[105500,106500)`.
- Historical source build seeds remain
  `1103,1229,1361,1499,1621,1747,1877,1999,2131`.
- New prospective target insertion-order seeds are `2791,2903,3011`.
- M=16, efConstruction=100, CPU implementation, base snapshot, metric, and
  seven-action ef grid are unchanged.

The source history cache may use these query identities on historical source
builds before target execution, consistent with the repeated-query workload
scope. Target certification and evaluation outcomes are disjoint; evaluation
cannot change any action, threshold, fallback, seed, or query range.

## Primary and scoped gates

The strict quality-preserving gate is unchanged: every target build must have
selected-policy simultaneous UCB at most 0.05; pooled mean Recall difference
against the best deployable baseline must be at least -0.001; mean distance
computations must improve by at least 5% with paired bootstrap upper endpoint
below zero; p95 ratio must be at most 1.05; and all LOBO directions must be
favorable. p99 remains a mandatory diagnostic without a post-hoc threshold.

Complete cost is reported at N=`1e3,1e4,1e5,1e6,1e7`, including source-grid
search and an exhaustive-base-scan lower bound for source exact truth. The
original N=100,000 general economic gate remains visible. Separately, the
method may be described as economically eligible only inside the measured
high-reuse domain above its complete-cost break-even; this scoped statement
must quote the break-even and cannot be generalized to short-lived or cold
queries.

## Stop rules

Stop without efficacy interpretation on role overlap, input-hash mismatch,
target-index replay failure, invalid ef semantics, endpoint certificate
failure, or resource pressure. Do not add a second shift, tune the action
grid, inspect evaluation to select a policy, or replace a failed dataset.
Three target builds remain prospective pilot evidence, not a build-population
certificate.

Large adapters, indexes, logs, and per-query outputs are written only under
`/home/wlk/data500/tcp_sigmod_regular_closure/phase7_high_recall_v1`.
