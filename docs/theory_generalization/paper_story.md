# Paper story

Graph construction randomness changes the environment in which a query is searched. Consequently, a query does not possess one portable scalar “difficulty”: its minimum stable sufficient budget is indexed by the realized graph. A policy that observes only a source-build summary compresses target-relevant information, so queries that look identical at the source may require different target budgets. ICBA formalizes the least achievable cost under progressively richer information, separates arbitrary summary aliasing from monotonicity-induced loss, relaxes pointwise safety to marginal risk, and quantifies whether finite calibration data can certify the resulting policy. This chain explains the preceding positive Oracle signals and negative deployment results without treating either as contradictory. Target-native sequential state is the principled escape route because it refines the policy's information beyond source-only summaries.

## Contributions

1. A general information-constrained formulation of quality-constrained budget adaptation with explicit pointwise, marginal, conditional, empirical, and certified risks.
2. A conditional-essential-supremum characterization of the minimum zero-risk source-summary policy and a least-safe-monotone-majorant specialization.
3. A finite-grid risk-matched optimization and an explicit treatment of right censoring rather than complete-case deletion.
4. Exact certification-power analysis showing how calibration size and policy multiplicity separate true safety from the probability of proving safety.
5. A frozen-data contact study across 81 Graph-ANNS builds that reports both general theoretical quantities and the narrower hnswlib actionable boundary.

## Positioning

The paper is a boundary-and-theory paper, not a new adaptive-search performance paper. Its novelty claim must remain “to our knowledge, under the reviewed literature scope.” Future methods should be derived only after deciding what target-native information can be observed cheaply and certified as part of the complete stopping policy.
