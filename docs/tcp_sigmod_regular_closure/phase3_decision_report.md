# Phase 3 decision: valid certification and graded fallback

## Decision

The original safety and reproducibility standards were not globally too
strict. Two criteria were mis-specified: fairness must hold the *total target
label budget* fixed rather than force every method to discard labels until its
certification sample size matches a target-trained baseline, and p99 must not
become an arbitrary primary threshold when no p99 service objective is
claimed. The 5% risk limit, independent target certification, evaluation
firewall, clustered uncertainty, 5% mean materiality, and 5% p95
noninferiority remain unchanged.

The binary TCP-to-ef200 rule was the substantive design problem. The frozen
Phase 3b rule replaces it with a deployable TCP-to-source-fixed-to-endpoint
ladder. The three policies receive simultaneous one-sided Clopper--Pearson
bounds at confidence `1 - 0.05/3` on the same 500 certification-role queries;
the first certified policy in the frozen order is deployed. This is more
conservative than the earlier single-policy 95% audit and does not use
evaluation outcomes for selection.

## Equal-total-label Phase 3 v2 diagnostic

Against the best deployable baseline (source-global ef=80), canonical TCP with
direct endpoint fallback reduced mean distance computations by 44.80% on
SIFT-100K (difference -431.95, target-build nested-bootstrap 95% CI
[-438.85, -425.24]) and 37.34% on Arxiv-Nomic-100K (difference -437.20, CI
[-630.81, -58.65]). SIFT passed p95 noninferiority (ratio 1.018); Arxiv failed
(ratio 1.582) because one marginally uncertified build fell directly to ef=200.
This result identifies a fallback-tail problem rather than grounds for
weakening the safety threshold.

## Preregistered simultaneous graded fallback

| Dataset | TCP / ef80 / ef200 builds | Mean dists, method / baseline | Mean gain | 95% CI for difference | p95 ratio | Eval risk |
|---|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 8 / 2 / 0 | 618.880 / 964.247 | 35.82% | [-434.41, -216.40] | 1.009 | 2.11% |
| Arxiv-Nomic-100K | 7 / 3 / 0 | 733.465 / 1170.798 | 37.35% | [-621.01, -249.46] | 0.988 | 1.72% |

Every selected action has simultaneous CP UCB at most 5%. Both datasets pass
the 5% mean-materiality test, a bootstrap interval entirely below zero, and
the preregistered p95 noninferiority test. Every leave-one-build-out mean
difference remains favorable, as does deletion of the largest-gain build.
Query-pooled p99 ratios are 1.494 (SIFT) and 1.274 (Arxiv); these are material
tail diagnostics that must be disclosed and investigated, but they are not
silently converted into an unregistered hard Gate.

## Scope and next Gate

This is strong fixed-target, target-certified evidence for the TCP mechanism
and for a practical graded fallback. It is not a 5% build-distribution
certificate: nine source builds only provide a 0.10 empirical conformal
resolution floor, and the outer-build sample remains small. Promotion to a
SIGMOD Regular method claim still requires lifecycle total-cost accounting,
prospective fresh-query/build confirmation, and a clearly scoped theorem for
the simultaneous certification/fallback composition. Phase 4 should formalize
that composition; Phase 5 should run the frozen prospective confirmation.
