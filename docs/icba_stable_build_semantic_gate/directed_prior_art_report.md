# Directed prior-art closure

## Scope and reading discipline

This gate is a directed recheck, not a new comprehensive review. Ten Level-A papers were checked at full-text level for the four-part direct-prior test. Two were newly added in this round (Ma et al.; MARGO) and eight were directed rechecks from the frozen theory audit. Supporting fragments and metadata are excluded from theorem-level novelty decisions.

The direct-prior test requires one work to: (i) actively modify Graph-ANNS construction, (ii) target cross-build query-budget/search-response stability, (iii) formally connect structural change to risk, recall, or budget, and (iv) validate across independent builds. No checked work satisfies all four.

## Highest-risk results

1. **Yang et al., Revisiting the Index Construction of Proximity Graph-Based ANNS.** Theorems 4.1–4.2 connect path rank and successful navigation; Theorem 5.1 analyzes sampling. This is the closest formal path-quality prior, but neither cross-build budget stability nor certification is its object.
2. **MARGO.** It assigns monotonic-path-aware edge importance and optimizes page layout. This is strong trace/path component overlap, but it modifies physical layout rather than the logical graph for rebuild-portable safe budgets.
3. **Ma et al., Graph-Based ANNS Revisited.** It is directly relevant to graph-search theory. Its available v5 proof text was checked, including appendices. A sign/inequality step in the published HTML proof chain appears internally inconsistent, so it cannot be treated as a clean subsuming theorem. Even as stated, its object is not cross-build certified budget stability.
4. **Steiner-Hardness.** It is the strongest graph-native query-effort prior. It motivates workload-aware structural scores but does not define rebuild response stability or a certification interface.
5. **Elliott and Clark.** It empirically establishes insertion-order sensitivity. It threatens any claim that rebuild sensitivity itself is novel, but it does not give a stable construction method or theorem.

## Direct-prior decision

`NO_DIRECT_FOUR_CONDITION_PRIOR_FOUND`

The nearest works are labeled `STRONG_COMPONENT_OVERLAP_NOT_DIRECT_METHOD_PRECEDENT`. This does not justify a “first” claim: the search was directed, and workload-aware repair, deterministic construction, dynamic repair, and path-aware optimization are mature neighboring lines.

## Claim boundary

Delete claims that stable construction, path-aware graph optimization, deterministic construction, or rebuild sensitivity are new in general. Retain only the narrower problem combination: cross-build Graph-ANNS query-budget response, explicit separation of `ef`/expansion/NDC/time, design–calibration–certification–evaluation separation, and an empirical bridge from structural certificates to target-build `B_G^{ef}`.

## Reading inventory

Level A (10): Ma et al.; Yang et al.; Elliott–Clark; FreshDiskANN; NSG; DiskANN/Vamana; MonaVec; Steiner-Hardness; ANNiE; MARGO. Level B/supporting: Ponomarenko query-based repair, QBAT, and implementation/documentation fragments. Level B items do not support theorem-level exclusion or novelty.

