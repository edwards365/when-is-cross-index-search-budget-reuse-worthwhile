# TCP prospective confirmation and lifecycle seal

## Decision

The preregistered quality-preserving SIGMOD Regular gate **does not pass**.
This is not a global failure of TCP. It separates two estimands that must not
be conflated:

1. **SLA-risk-constrained efficiency:** passed on both datasets. TCP keeps the
   probability of Recall@10 below 0.90 within the certified 5% limit, improves
   mean distance computations by much more than 5%, preserves p95 within the
   registered 1.05 ratio, and remains favorable in every leave-one-build-out
   comparison.
2. **Quality-preserving efficiency:** failed on both datasets because mean
   Recall fell by substantially more than the preregistered -0.001 margin.

The Recall condition is not redundant with the risk condition. A policy can
place almost every query just above Recall@10=0.90 and therefore have low
failure risk while still losing material average quality against a baseline
near Recall 0.994. Removing this condition after observing the result would
change the paper's claim rather than correct an overly strict test.

## Prospective evidence

The analysis used fresh frozen query rows and target insertion-order seeds
2381, 2503, and 2633. The policy, source histories, action grid, fallback
sequence, thresholds, and bootstrap were fixed before target outcomes.

| Dataset | TCP eval risk | TCP simultaneous cert UCB (range) | Mean work gain | 95% paired bootstrap difference | Mean Recall difference | p95 ratio | p99 ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 2.57% | 3.00%--4.57% | 48.54% | -435.39 to -413.58 | -0.02123 | 1.0047 | 1.3696 |
| Arxiv-Nomic-100K | 2.00% | 2.73%--4.57% | 52.52% | -622.71 to -593.27 | -0.02240 | 0.9859 | 1.4701 |

TCP was certified and selected on all three prospective target builds in each
dataset. The frozen DARTH comparator was rejected on all six targets and used
the source-global fixed fallback, so it did not provide an adaptive deployment
gain in this run. All leave-one-target-build-out mean differences remained
negative. The elevated p99 ratios remain mandatory diagnostics and are not
converted into an unregistered hard threshold.

## Lifecycle accounting

At the target stage alone, TCP has immediate break-even because it uses the
same 500 target labels, consumes less certification search work in the
observed accepted cases, and has lower production work. That view is
insufficient for an economic claim: TCP-HM9-TC is a repeated-query cache and
requires source-side per-query history.

The complete cached-workload estimate therefore includes all nine source
builds across the seven ef values and one exhaustive 100K-base truth scan per
source-labelled query. It excludes common target rebuild and target
certification-truth costs. Under this conservative distance-computation
accounting, TCP reaches break-even against source-global fixed after about
370,407 cumulative SIFT queries and 289,512 Arxiv queries; against target-only
global profiling after about 552,217 and 431,687 queries, respectively. At
N=100,000 it is still 215.16% more costly than the best complete-cost baseline
on SIFT and 170.67% more costly on Arxiv. DARTH's complete lifecycle comparison
is not estimable because its training and feature-construction costs were not
instrumented.

## Claim boundary and next action

Current evidence supports TCP as a **high-reuse, fixed-query-workload,
risk-targeted compute-saving method**. It does not yet support the stronger
claim of quality-preserving savings or universal economic advantage at
N=100,000. ICBA's audit contribution is strengthened because it exposes this
otherwise hidden separation between threshold risk, average Recall, and
amortized cost.

No threshold is relaxed in this seal. A later experiment may test one frozen,
mechanically more conservative policy on unused queries and new builds. That
experiment must be preregistered as a response to this failure, use a new
evaluation role, and retain the original TCP result as the primary record.
