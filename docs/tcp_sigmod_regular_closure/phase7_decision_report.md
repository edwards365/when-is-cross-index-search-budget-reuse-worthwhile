# Phase 7 TCP-HM9-TC-R1 decision report

## Outcome

The preregistered one-rung repair does not close the strict SIGMOD Regular
method gate. It identifies a reproducible Recall--tail tradeoff rather than a
protocol failure.

TCP-HM9-TC-R1 was frozen before outcomes: every finite canonical TCP action
was moved upward by exactly one step on the seven-action ef grid, with ef=200
and BOT retained at the endpoint. No alternative shift, cap, threshold, source
subset, or target-dependent choice was inspected.

## Results

| Dataset | Eval risk | Max simultaneous cert UCB | Mean work gain | Bootstrap 95% CI | Mean Recall difference | p95 ratio | p99 ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 0.23% | 1.86% | 22.85% | -207.97 to -180.43 | -0.000067 | 1.3910 | 1.8629 |
| Arxiv-Nomic-100K | 0.23% | 0.82% | 25.85% | -320.08 to -284.35 | -0.001933 | 1.3536 | 1.8676 |

R1 was independently certified and selected on all three new target builds in
each dataset. All leave-one-build-out mean differences remained favorable.
The frozen DARTH comparator was rejected on all six targets and deployed the
source-global fixed fallback, which was also the best deployable comparison.

On SIFT, R1 repairs the Phase 5 average-Recall failure while preserving a
material mean-work improvement, but p95 increases by 39.10%. On Arxiv, the
average-Recall gap narrows substantially but remains 0.000933 beyond the
registered margin, while p95 increases by 35.36%. Thus the strict gate fails
on SIFT because of tail cost and on Arxiv because of both Recall fidelity and
tail cost. Safety, mean efficiency, materiality, and LOBO pass on both.

## Lifecycle cost

The complete cached-workload accounting includes nine source builds, seven ef
values, and one exhaustive 100K-base truth scan per source-labelled query. At
N=100,000, R1 remains 246.75% more costly than the best complete-cost baseline
on SIFT and 195.33% more costly on Arxiv. Its break-even against source-global
fixed is approximately 801,431 and 585,161 cumulative queries, respectively;
against target-only global profiling it is approximately 1,203,639 and
871,287 queries. Target-stage-only accounting breaks even immediately, but it
is not used as the complete economic claim.

## Interpretation and route decision

The original TCP and R1 form a clear frontier:

- canonical TCP: strong mean and p95 efficiency, but material average-Recall
  loss;
- R1: near-baseline average Recall on SIFT and much smaller Recall loss on
  Arxiv, but severe p95/p99 inflation and worse amortization.

Consequently, the current scalar history-max action family does not provide a
single quality-preserving, tail-preserving, N=100K-economic operating point.
The result must not be repaired by weakening the registered gate or selecting
a cap after viewing these evaluations. TCP remains supported only for a
declared high-reuse, SLA-risk-constrained workload where average-Recall and
tail tradeoffs are acceptable. The stronger general SIGMOD Regular method
closure is not supported.

Further TCP work, if undertaken, requires a new mechanism that directly
controls per-query tail exposure and reduces source-history construction cost;
another scalar rung shift is not justified. The ICBA audit contribution is
strengthened by this prospective separation of safety, mean quality, tail,
and amortized cost.
