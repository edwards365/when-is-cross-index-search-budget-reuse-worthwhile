# OCGT-v2 theory notes

## Status taxonomy

Statements below distinguish mathematical propositions, empirical observations, inferences, and open questions.

## Proposition 1: query-only non-identifiability

For fixed data X and query q, two valid HNSW realizations G1 and G2 may require budgets a<b. Any predictor observing only phi(q,X) emits the same budget on both graphs. A budget below b can violate target recall on G2; a budget at least b over-spends by at least b/a on G1. This is an information limitation, not a claim that every dataset exhibits the gap.

## Proposition 2: scalar calibration insufficiency

If two queries reverse their required-budget ordering between graphs, no strictly monotone scalar mapping can reproduce both target-graph budgets exactly. The proof follows immediately because a monotone map preserves order.

## Proposition 3: realizable-gain upper bound

Realized normalized gain is bounded above by oracle headroom minus normalized probe and prediction-error costs. The bound is bookkeeping: any observation cost and over-search consumes part of the oracle saving.

## Proposition 4: finite-beam non-monotonicity

Adding reachable edges cannot reduce graph-theoretic reachability, but may change finite candidate-queue ordering and evict a useful state. Thus finite-beam recall need not be monotone under edge addition or larger local branching. This does not imply that increasing ef is generally harmful; it establishes only that monotonicity needs proof for the exact search implementation.

## Empirical observation

The 10K fixture shows large oracle headroom and substantial query-by-graph interaction, while probe-cost-aware predictors fail to realize it. Cross-order transfer is materially worse than same-order transfer.

## Inference

The most plausible scientific scope is HNSW construction-history sensitivity, not a graph-agnostic query-difficulty law. This inference is descriptive because OCGT-v2 is invalid as a confirmatory experiment.

## Open questions

Whether the pattern persists at 100K/1M scale, across independent queries, and in other graph-ANNS families remains open.
