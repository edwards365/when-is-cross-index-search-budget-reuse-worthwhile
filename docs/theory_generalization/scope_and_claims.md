# ICBA scope and claims

## Three-layer scope

| Layer | Supported scope | Evidence label |
|---|---|---|
| Mathematical | Finite or measurable budgeted-search systems with a well-defined quality target, cost, information sigma-field, and admissible policy class. Information ordering, safe envelopes, monotone majorants, finite-grid risk allocation, certification power, and sequential-information escape apply only under their stated assumptions. | GENERAL THEOREM, except T4 which remains PROOF_SKETCH_ONLY |
| Mechanism | Any environment change that can alter the per-query minimum stable sufficient budget can create information aliasing and source-policy transfer tax. Construction seed/order is one such mechanism; the theory does not require HNSW. | MECHANISM HYPOTHESIS plus GRAPH-ANNS MECHANISM EVIDENCE |
| Empirical | Direct frozen evidence covers hnswlib, Faiss HNSW and Vamana on SIFT-100K, GloVe-100K and Arxiv-Nomic-100K. Actionable, reproducible adaptation evidence remains hnswlib-specific; cross-implementation effects are descriptive boundaries. | HNSWLIB-SPECIFIC ACTIONABLE EFFECT / GRAPH-ANNS BOUNDARY EVIDENCE |

## Strongest supported claim

Under the reviewed literature scope, index rebuilding can make query budget difficulty environment-conditioned. For source-summary-only policies this produces an information-coarsening tax; adding monotonicity can add a further computable tax. Allowing marginal risk changes the optimum but does not remove finite-sample certification limits. Frozen Graph-ANNS data make these theoretical quantities measurable across three implementations, while deployable benefit is currently supported only within hnswlib.

## Claims that are not permitted

- ICBA does not prove that every ANN index exhibits a practically large rebuild tax.
- The 81-graph matrix does not establish cross-method or production generalization.
- Positive Oracle headroom, AUROC, or AUPRC does not certify a deployable stopping rule.
- T4's matching expression is not a general theorem outside its narrowed conditions.
- Clipped costs for right-censored queries are lower bounds, not identified safe costs.
- The 500-query prefix pilot is not a universal resumability theorem.
- No validation-dev or formal-test performance claim is available.

## Gate interpretation

Definition consistency, risk alignment, censoring treatment, empirical contact, novelty qualification, and method interface are satisfied in draft form. Proof validity is satisfied for T1/T2/T3/T5/T6/T7/T8 and remains deliberately qualified for T4. The expected final label is `GENERAL_FRAMEWORK_VALID_EMPIRICAL_SCOPE_HNSWLIB`, subject to final artifact and checksum audit.
