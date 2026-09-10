# Limitations

The evidence is conditional on registered builds, frozen query distributions, two 100K-scale datasets, three implementations, and finite native action grids. It does not identify a population distribution over future builds and therefore cannot certify an unseen rebuild. Query bootstrap intervals quantify query-law uncertainty conditional on the registered build family; leave-one-build/seed/order analyses are robustness checks rather than environment-population confidence intervals.

The positive theorem is fixed-target and finite-action. It requires independent target evidence and either an independently safe fallback or honest abstention. It does not produce an observable recovery channel, guarantee candidate attainability, or ensure positive economic value. Several mechanism studies found partial signals—target recalibration, portal complementarity, and Oracle headroom—but none yielded a deployable algorithm under the registered safety, tail, and cost gates.

Native budgets and costs are implementation specific. `efSearch` and `l_value` are not numerically interchangeable, and NDC supports within-implementation comparisons only. Conservative-cost penalties are resolved for registered hnswlib and Faiss HNSW cells but not for DiskANN3/Vamana-style cells. The paper therefore claims a cross-family risk phenomenon with operator-dependent cost consequences.

The original 123-entry frozen baseline cannot be described as exactly reproduced: 111 entries matched, eight CSV hashes differed, and four listed `__pycache__` files were not versioned. Later stages have their own passing, source-specific checksums and deterministic replays, but this legacy provenance limitation remains disclosed.

Finally, the main lower-bound machinery, uniform concentration, Clopper–Pearson certification, and break-even algebra are classical. Novelty lies in the Graph-ANNS reconfiguration problem, its risk/cost instantiation, the conditional recovery interface, the cross-system evidence, and the theory-guided falsification program—not in new general statistical inequalities.
