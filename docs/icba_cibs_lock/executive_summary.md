# CIBS theory, prior-art and semantic lock: executive summary

## Decision

**Primary decision:** `CIBS_FIXED_THEORY_AND_SEMANTICS_LOCKED`  
**Secondary race status:** `CIBS_RACE_THEORY_TEMPLATE_AUTHORIZED` for theory work only; implementation is not authorized before Stage I passes.  
**Pilot authorization:** CIBS-Fixed is authorized as a falsifiable pilot, not as a confirmed method gain.

CIBS-Fixed selects one preregistered graph build and one raw global fixed-`ef` from a finite action family. It uses shared, independent target sentinel queries to construct family-wise simultaneous one-sided risk bounds, chooses the lowest empirical mean-NDC certified action, and returns a preregistered fixed-safe fallback if none is certified. Its certificate is fixed-target and named-portfolio only.

## What is proved

- T-CIBS1: simultaneous bounds remain valid under arbitrary data-dependent cost selection within the certified set.
- T-CIBS2: Bonferroni one-sided exact-binomial certification is finite-sample valid. With `alpha=delta=0.05`, `K=3,L=12,n=256` permits at most 3 failures; `K=2,L=12,n=128` permits 0.
- T-CIBS3: conditional on simultaneous cost concentration and certification of the true safe optimum, empirical selection has a `2 eta_max` cost-regret bound. Safety does not need this result.
- T-CIBS4: paired full-information comparisons have the classical covariance-dependent variance identity; no unconditional efficiency dominance is claimed.
- T-CIBS5: the build-service break-even identity is valid; no finite break-even exists when per-query gain is nonpositive.
- T-CIBS6: classical testing/BAI lower bounds specialize to small safety and cost gaps in CIBS.
- T-CIBS7: fixed-target certification does not imply unseen-build, next-rebuild, shifted-query, or open-world safety.

## Prior art and novelty ceiling

Twelve Level-A full texts were checked in this round. No checked work simultaneously covers multiple Graph-ANNS builds, build-budget joint actions, shared target truth, simultaneous recall-risk certification, safe-set cost selection, full offline cost accounting, and independent portfolio validation. The closest modules are Learn-Then-Test/RCPS, SafeBAI/Track-and-Stop/LUCB, Hyperband/portfolio selection, confidence sequences, and ANNiE/ConANN.

Accordingly, the maximum defensible novelty is `NEW_COMBINATION_OF_CLASSICAL_RESULTS`, with a possible `POTENTIAL_GRAPH_ANNS_SPECIFIC_RESULT` for the joint action, endpoint, shared-truth, raw-`ef`, and build-service contract. It is not new generic SafeBAI or generic simultaneous inference.

## Frozen empirical status

The previously reported budget-proxy improvements are `EXPLORATORY_OFFLINE_SIMULATION`. They are not mean-NDC, p95, or deployment gains. The pilot must measure real NDC, tails, build time, truth and candidate-search cost, artifact replay, and break-even. Validation-dev, formal-test, evaluation truth, and future-confirm truth remain unaccessed.

