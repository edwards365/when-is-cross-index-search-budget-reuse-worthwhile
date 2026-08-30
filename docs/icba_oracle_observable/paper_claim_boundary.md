# Paper claim boundary

## Safe claims

- The oracle-observable decomposition distinguishes potential target-conditioned value from value recoverable with deployable evidence.
- A two-environment testing reduction gives an observability-dependent floor on decision regret, soft safety loss, or fallback cost in the declared finite recovery model.
- Under explicit finite-action risk/cost margins and valid uniform estimates, upper-confidence screening is fixed-target safe and near-oracle.
- Independent certification of only the selected action needs no Bonferroni correction; failure returns a separately safe fallback.
- Exact action accuracy can disagree with decision regret and should not be the primary method gate.
- Frozen Graph-ANNS evidence motivates the model and provides a negative/diagnostic witness; it does not validate the positive recovery assumptions.

## Claims requiring narrow scope

- “matched rate” must be followed by “for a known binary finite-alphabet observation channel”; otherwise use `PARTIALLY_MATCHED_RATE`.
- “safe” must be followed by “fixed target, with probability over the independent certification sample, assuming a safe fallback.”
- “general framework” may refer to the mathematical finite-budget abstraction, not cross-domain empirical validity.
- “Graph-ANNS theory-method closure” may mean a theoretical design template only, not an implemented method.

## Forbidden claims

- open-world or unseen-build certification;
- deployable recovery signal in the frozen data;
- confirmatory or formal-test evidence;
- general `m/n/k/M` sample complexity;
- first rebuild-portable ANNS method;
- new Le Cam, Fano, Blackwell, or Clopper-Pearson theory;
- oracle headroom as method performance;
- action accuracy as observable value;
- zero truth, control, or retraining cost;
- a safe maximum-budget fallback without endpoint proof.

## Recommended story

Lead with a systems-motivated statistical decision problem: Graph-ANNS rebuilds expose oracle efficiency headroom, but finite deployable evidence can leave it unrecoverable. Present the classical lower-bound lineage explicitly, then contribute the unified hard-safety/cost formulation, exact claim boundary, and a conditional split-certified recovery template. An ML-theory claim should wait for a non-modular joint rate or frontier; the current package is strongest as theory support for a database-systems method program.
