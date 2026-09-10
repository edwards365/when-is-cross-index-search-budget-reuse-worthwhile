# Paper outline and figure plan

## Main paper

1. **Introduction** — rebuild portability assumption; hidden build environments; three-sentence story; five contributions.
2. **Related Work** — graph construction/search, learned query-budget adaptation, risk control/selective prediction, distribution and algorithmic reconfiguration. Explicitly distinguish ANNiE/QBAT-style index-specific profiling from cross-rebuild portability.
3. **Problem and ICBA** — finite environments/actions; endpoint-aware event; \(\bot\); native action semantics; audit pseudocode.
4. **Theory** — Main Theorem I, Main Theorem II, two corollaries; one paragraph separating classical tools from domain contribution.
5. **Experimental Protocol** — registered build families, role isolation, two datasets, three implementations, per-implementation budgets, estimands and uncertainty.
6. **Cross-Family Results** — six-cell risk results; HNSW/Vamana operator interaction; robustness; no universal cost claim.
7. **Falsification Ladder** — one summary table and four representative mechanisms, with details deferred to appendix.
8. **Limitations and Conclusion** — fixed registered scope, no deployable recovery, future environment-level replication.

## Main tables

- Table 1: notation, implementation instances, and scope.
- Table 2: two main theorems, assumptions, classical ingredients, and empirical role.
- Table 3: six-cell cross-family evidence with category variation, original/harmonized transport effects, and cost status.
- Table 4: four-rung falsification ladder.

## Main figures

- Figure 1: build reconfiguration diagram showing one dataset/configuration, multiple serialized graphs, and query-specific safe-budget shifts.
- Figure 2: six-cell forest plot of transport-violation effects with 95% intervals; cells grouped by implementation and colored by dataset.
- Figure 3: distribution of per-query budget categories across registered builds; \(\bot\) shown as a categorical state rather than numeric extension.
- Figure 4: ICBA flow from role/semantic validation through transport audit, certification, fallback/abstention, and economics.
- Figure 5: falsification ladder mapping each method family to the failed recovery condition.

## Appendix

- full proofs and classical citations;
- complete theorem crosswalk and conflict resolutions;
- detailed per-implementation protocols and native action semantics;
- robustness, checksum, provenance, and all method-family experiments;
- legacy 111/123 limitation and line-ending reconciliation.
