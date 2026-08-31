# Direct prior-art report

## Verdict

`NO_DIRECT_SEVEN_CONDITION_PRIOR_FOUND`

No Level-A work checked in this round satisfies all seven direct-prior conditions. This does not justify a universal “first” claim: QBAT remained fulltext-unverified this round, and the generic statistical and portfolio-selection components are well established.

## Closest theorem modules

| Work | What it supplies | Missing relative to CIBS-Fixed | Overlap |
|---|---|---|---|
| Learn-Then-Test | FWER-valid selection from a fixed finite family | no Graph-ANNS build action, build cost, NDC/tail contract | `STRONG_THEOREM_OVERLAP` |
| RCPS | holdout risk UCB and fixed-target high-probability risk control | no build portfolio or safe-set cost selection | `STRONG_THEOREM_OVERLAP` |
| SafeBAI | safety-constrained arm identification with unknown safety response | bandit/dose feedback, not paired shared-query full information | `STRONG_THEOREM_OVERLAP` |
| Track-and-Stop / LUCB | fixed-confidence best-arm identification and gap complexity | objective identification, not simultaneous target recall certificates | `STRONG_THEOREM_OVERLAP` |
| Hyperband | resource-aware configuration racing | no valid recall-risk certificate | `PARTIAL_METHOD_OVERLAP` |
| SATzilla | algorithm portfolio selection | learned per-instance choice, no fixed-target safety guarantee | `SYSTEMS_BASELINE_ONLY` |
| ANNiE | per-query Graph-ANNS query-cost estimator | fixed/index-specific learned estimator; no simultaneous multi-build selection | `PARTIAL_METHOD_OVERLAP` |
| ConANN | conformal/CRC-style ANN error control on a fixed IVF index | no build-budget portfolio and no multi-build offline-cost analysis | `PARTIAL_METHOD_OVERLAP` |
| Correlated-arm BAI | correlation-aware arm elimination | pseudo-reward correlation differs from observing every action per query | `ANALOGY_ONLY` |
| Time-uniform Chernoff bounds | anytime-valid confidence sequences | generic tool only; relevant to future CIBS-Race | `STRONG_THEOREM_OVERLAP` |

## ANN-specific disposition

ANNiE defines query cost relative to reaching a recall target and learns a quantile estimator for a particular index. It does not certify a preregistered build×budget family under family-wise error. It also imputes an unreachable endpoint with a large cost; CIBS instead treats endpoint infeasibility as failure or a preregistered abstention.

ConANN supplies a fixed-index conformal risk-control route for IVF-style search. It is a close risk-control module but not a multi-build selection method. QBAT is a model-based query budget autotuner for clustering-based ANN; its complete theorem and proof content was not verified this round and therefore cannot clear the novelty risk.

## Claim consequence

Allowed: a narrow Graph-ANNS systems claim about jointly selecting a serialized build and raw fixed-`ef` with fixed-family simultaneous certification, shared truth accounting, endpoint-safe semantics, and build-service break-even.

Forbidden: “first safe index selection,” “new generic SafeBAI,” “new simultaneous certification theory,” “first rebuild-portable ANNS,” or any open-world guarantee.

