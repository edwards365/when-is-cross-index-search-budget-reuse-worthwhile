# Phase 3 baseline and Gate addendum

## Audit of strictness

Four requirements are non-negotiable: actual execution semantics, no use of
evaluation for selection, independent target safety certification, and full
lifecycle-cost accounting. A method that violates any of these cannot support
a Regular-track claim.

Three earlier requirements were unnecessarily universal and are replaced by
the following preregistered hierarchy:

1. A 5% exchangeable-build theorem is required only when such a theorem is
   claimed. TCP-HM9-TC may instead make a fixed-target query-risk claim backed
   by independent target certification.
2. Every dataset need not show a positive efficiency gain. Both datasets are
   always reported; a negative dataset is admissible only if a deployable
   applicability rule, frozen without its evaluation outcomes, rejects it.
3. Tail latency/cost need not strictly improve when mean work improves. The
   primary tail criterion is noninferiority: query-pooled p95 no more than 5%
   above the best deployable baseline and p99 no more than 10% above it. Tail
   values and bootstrap uncertainty remain mandatory, and a larger degradation
   blocks promotion even if mean work improves.

The primary efficiency criterion is a positive target-build nested-bootstrap
lower confidence bound for aggregate mean distance-computation reduction
versus the best deployable baseline. A 5% point estimate is the practical
materiality threshold; values below 5% are reported as statistically positive
but economically unresolved pending lifecycle cost.

## Frozen target split

The existing 500 target certification-role queries are deterministically
partitioned before this analysis:

- qid 0--249: target selection only;
- qid 250--499: independent target certification only;
- the existing 1,000 evaluation-role queries: evaluation only.

No query changes roles. TCP uses no target selection outcome but is certified
on the same 250 certification queries for label-budget comparability.

## Frozen baselines

- FIXED_ENDPOINT: preregistered efSearch=200.
- SOURCE_GLOBAL_FIXED: smallest ef whose one-sided 95% CP risk upper bound is
  at most 0.05 on every source build's 500 certification-role history queries.
- TARGET_ONLY_GLOBAL: smallest ef passing the same bound on the target's 250
  selection queries, followed by independent certification on qid 250--499.
- TCP-HM9-TC: the frozen stable-tail history-max policy.
- DARTH: raw output plus audit-before-deploy fallback; raw unsafe output is not
  a deployable baseline.

Each candidate is assessed per target build. Certification failure deploys the
fixed endpoint. Evaluation never changes an action or acceptance decision.

## Decision hierarchy

Safety is strict. Efficiency is assessed against the lowest-mean safe deployed
baseline among SOURCE_GLOBAL_FIXED and TARGET_ONLY_GLOBAL, with endpoint shown
as a safety reference. Mean, p95, p99, Recall, certification UCB, fallback,
LOBO, and largest-benefit deletions are reported separately. Passing this phase
does not waive lifecycle cost or prospective confirmation.
