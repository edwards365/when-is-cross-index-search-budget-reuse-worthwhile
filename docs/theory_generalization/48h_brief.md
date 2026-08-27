# ICBA theory-generalization brief

## Decision

The sprint supports `GENERAL_FRAMEWORK_VALID_EMPIRICAL_SCOPE_HNSWLIB`. Information-Constrained Budget Adaptation (ICBA) is mathematically meaningful for general budgeted-search systems under explicit information, risk, and cost assumptions. Frozen empirical contact spans hnswlib, Faiss HNSW, and Vamana, but a deployable adaptive advantage is not established across implementations; the actionable boundary remains hnswlib.

## What was proved and checked

T1, T2, T3, T5, T6, T7, and T8 are marked `FORMALLY_PROVED`. T4, the rank-inversion matching lower bound, is deliberately `PROOF_SKETCH_ONLY` under a finite uncensored grid, additive/linear budget-gap cost, and vertex-disjoint matching. Exhaustive checks for query counts 2–8 and budget levels 2–6 found no counterexample within those conditions; 12 unit tests passed. This computation supports but does not replace a proof.

The key chain is: richer information weakly improves the attainable risk-constrained value; a zero-risk source-summary policy must choose the conditional essential supremum of target demand; a monotone source-budget policy is the prefix-maximum majorant; marginal-risk relaxation becomes a finite allocation problem; and target-native sequential state lies outside the source-summary lower-bound class.

## Frozen empirical contact

All four input commits passed frozen-object checksum audit: Cross-Index 17/17, Tournament 20/20, RCRS Fast 18/18, and Signal Pilot 21/21. The unified analysis reused 81 graphs and 972,000 query–budget rows, producing 648 directed source→target pairs and 2,592 risk-frontier rows with 5,000 paired query bootstrap replicates (seed 991). Mean budget-change rates across implementation×dataset groups range from 13.70% to 61.73%; mean rank inversion ranges from 9.42% to 23.51%. Safe monotone tax is positive in all nine groups, averaging approximately 1.06–3.13 fixed-NDC units, but NDC is implementation-local.

Of the risk-frontier cells, 1,632 are exact on the frozen grid, 424 are feasible only after treating censored targets as mandatory failures, and 536 are infeasible under the selected δ/grid. GloVe right censoring averages about 4.76%–5.67%, SIFT-hnswlib about 0.059%, and the remaining groups approximately zero. Observed-only, clipped lower-bound, and unbounded-without-assumption interpretations are all retained.

## Certification and stopping

For n=256, M=16, alpha=delta=0.05, exact Clopper–Pearson/Bonferroni certification permits at most three observed failures. Seventy-five exact power cells and 100,000-trial Monte Carlo checks quantify the distinction between being safe and proving safety. A continuous construction gives identical AUROC 0.8566 and AUPRC 0.9779 for two monotone-related scores but unsafe-given-stop rates of 3.10% and 0.77% at the same numeric threshold. Ranking quality therefore cannot substitute for calibration and tail-risk certification.

The earlier SIFT design signal—AUROC 0.9070, AUPRC 0.9810, empirical risk 2.8%, apparent 65.84% NDC saving—remains design evidence only. On the independent GloVe calibration split, none of 16 complete policies certified. ICBA explains this as an information-and-certification boundary, not as evidence that target-native stopping is impossible.

## Scope and next interface

The strongest defensible claim is that, to our knowledge under the reviewed literature scope, rebuild-conditioned budget portability can be analyzed as information loss plus risk-constrained certification, and that these quantities are measurable in the frozen Graph-ANNS matrix. It is forbidden to claim universal ANN rebuild tax, cross-method deployability, or certification from AUC. A future method must observe cheap target-native sequential state, reuse search prefixes exactly, retain a fixed fallback, include all costs, and certify the complete frozen policy. No new method run is authorized by this sprint.

The optional IVF-Flat pilot was skipped because only about 11 GiB remained—roughly 1 GiB above the 10 GiB hard stop—so no non-Graph empirical generalization claim is made. Neither validation-dev nor formal-test was accessed.
