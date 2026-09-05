# Shared-frontier cost realizability audit

## Input and scope

Frozen parent: `e2e5a5d86042b76220199582e152c1391d52a794`. The audit reuses the sealed CALS subset and fixed portal actions only. The 12,000 instrumentation rows and 9,000 outcome-joined rows are unchanged. Validation-dev, formal-test, certification, evaluation, future-confirm and GloVe roles were not accessed. Evidence levels are `COST_REALIZABILITY_AUDIT`, `EXPLORATORY_DEVELOPMENT`, and `NON_DEPLOYABLE_LOWER_BOUND`.

## Quality feasibility

Quality was assessed for the fixed portal union against the same-primary action and the next native ef in the frozen grid. Practical-tail risk uses Recall@10 < 0.90 and strong risk uses Recall@10 < 0.99. Both datasets contain quality-feasible fixed actions under the preregistered risk or practical-risk routes; this is a retrospective qualification, not deployment evidence.

## Critical compression

For every dataset, build and primary ef (8, 16, 32), the median cost critical coefficient is positive with complete query bootstrap intervals. Median `kappa*_cost` ranges from 0.0657 to 0.2052, implying required auxiliary-cost compression of 79.5%–93.4%. The candidate-union lower-bound coefficient is approximately 0.0069–0.0102, so the ideal lower-bound margin is positive (about 0.058–0.195). This margin is only a candidate-set lower bound; it is not visited overlap, distance-computation overlap, wall-clock, or a realizable shared queue.

## Decision

The 50% maximum-compression Gate fails even though ideal candidate-union arithmetic is favorable. Real shared-frontier cost is `NOT_ESTIMABLE`, so no microbenchmark was authorized. Final label: `SHARED_COST_ONLY_ORACLE_BOUND_NO_IMPLEMENTATION`. This closes the current portal method route at the cost-realizability stage without asserting that all future sharing implementations are impossible.
