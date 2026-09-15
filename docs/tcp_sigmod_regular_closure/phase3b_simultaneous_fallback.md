# Phase 3b preregistration: simultaneous graded fallback

## Motivation

Phase 3 v2 showed that equal total target-label budgets materially change the
power comparison. It also exposed a separate issue: the original binary
deployment rule falls directly from TCP-HM9-TC to the ef=200 endpoint whenever
TCP misses certification. That rule is safe but may create an avoidable tail
tax. This addendum is frozen before inspecting the graded-fallback result.

## Fixed policy family and target labels

For every target build, the ordered deployment family is fixed in advance:

1. canonical TCP-HM9-TC;
2. SOURCE_GLOBAL_FIXED, whose ef is selected using source builds only;
3. the fixed-safe ef=200 endpoint.

All three policies use the same 500 target certification-role queries and no
target selection queries. Evaluation-role queries remain evaluation only.
There is no model fitting, tuning, or action selection from evaluation data.

## Simultaneous safety rule

For each target build, compute a one-sided Clopper--Pearson upper bound for
each of the three fixed policies at confidence `1 - 0.05/3`. Select the first
policy in the fixed order whose bound is at most 0.05. If the endpoint does not
pass, mark the build invalid rather than deploying an uncertified policy.

The Bonferroni allocation provides a simultaneous 95% familywise statement
for the three candidate policies within a target build. It is deliberately
more conservative than the single-policy 95% bounds in Phase 3 v2.

## Frozen decision criteria

- Safety: every deployed target build must have its simultaneous CP upper
  bound at most 0.05.
- Mean efficiency: at least 5% lower mean distance computations than the best
  deployable fixed baseline, with target-build nested-bootstrap 95% interval
  for the difference entirely below zero.
- Tail: query-pooled p95 ratio no greater than 1.05. p99 is reported as a
  diagnostic and is not assigned an unmotivated hard threshold.
- Robustness: all leave-one-build-out mean differences and the result after
  deleting the largest-gain build must remain favorable.

Passing on only one dataset is reported as partial fixed-target evidence, not
as universal cross-dataset closure. No build-level conformal theorem is
claimed from the nine source builds.
