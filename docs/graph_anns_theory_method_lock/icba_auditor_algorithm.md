# ICBA certified auditing procedure

## Positioning

ICBA is a **certified diagnostic/auditing procedure** for index-build budget portability. It is not a new graph search algorithm and does not claim to improve ANN throughput. It determines whether a preregistered source policy transports to named target builds, whether target evidence can certify an alternative, whether a valid fallback exists, and whether any accepted route has measurable service value.

## Inputs

- registered source and target serialized builds;
- implementation-specific finite native actions;
- mutually exclusive design, selection, certification, evaluation, and future roles;
- exact truth for authorized labeled roles;
- a single endpoint-aware failure event;
- implementation-internal search cost and, when available, wall-clock and offline costs;
- \(\delta,\alpha\), frozen candidate policies, and a multiplicity plan;
- a fallback with independent safety evidence, or explicit abstention.

## Outputs

The audit returns response heterogeneity, transport violations, conservative cost, unresolved-grid mass, reuse/recalibrate/retrain/fallback/abstain/reject decisions, fixed-target certificates, tail-cost diagnostics, break-even status, and a machine-readable evidence scope.

## Procedure and guarantees

ICBA first validates role disjointness, artifact replay, and action semantics. It represents unresolved endpoints by \(\bot\), computes minimum observed safe actions without numeric imputation, evaluates directed source-to-target transport, and uses uncertainty procedures matched to the estimand. For fixed-target decisions it freezes the candidate family before certification, applies Bonferroni-valid one-sided bounds when several raw actions are considered, or certifies a single independently selected action. An action is accepted only when its valid upper bound is at most \(\delta\). Rejection leads to a separately certified fallback or `ABSTAIN_NO_SAFE_ACTION`.

Under the declared independence and event semantics, the probability that ICBA labels an unsafe fixed-target action as certified is bounded by \(\alpha\). ICBA does not guarantee that an efficient action exists, that it will beat profiling or retraining, that its mean savings improve tail latency, or that a fixed-target result transports to unseen builds.

## Statistical-unit boundary

Queries are resampled only for query-law uncertainty conditional on the registered builds. Builds are the environment-level units for cross-build generalization. Leave-one-build/seed/order analyses are robustness diagnostics, not substitutes for a population model over future builds.

## Economic gate

Safety and value are separate. A route is economically interpretable only when all online, control, fallback, truth, certification, build, and retraining costs are auditable. Mean, p95, p99, and break-even are reported separately. Missing costs produce `NOT_ESTIMABLE`, not zero.
