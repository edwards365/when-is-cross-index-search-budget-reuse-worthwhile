# Limitations

1. The structural-to-budget theorem is restricted to deterministic beam/greedy search with fixed tie-breaking, upward-closed success, preserved distances and a registered robust trace certificate. General HNSW need not satisfy it.
2. `B_G(q)` requires truth labels. The deployable construction objective therefore uses design-query traces and a calibrated surrogate; it cannot directly optimize the true population diameter.
3. The current work contains no new graph builds, latency measurements or pilot results. All build-cost, memory, p95 and break-even quantities remain symbolic.
4. Fixed-target certification cannot establish outer-build/open-world validity without a build law, independent build samples and support assumptions.
5. Right-censored and endpoint-infeasible queries are not assigned the maximum finite budget. They can destroy apparent stability and reduce the certifiable scope.
6. Consensus concentration controls edge-frequency estimation only. Edge dependence, degree pruning, connectivity repair and rare bridges can invalidate a naive consensus graph.
7. Critical paths are workload dependent and may overfit design queries. Tail and top-1% deletion robustness are separate Gates.
8. The Level-B and Level-C papers cannot support theorem-level novelty claims; unverified names remain discovery leads only.
9. The server checkout was unavailable in this environment. Remote commit identity and branch isolation were verified, but local server process ownership and its filesystem checksum state could not be re-audited directly.
10. The inherited `111/123` legacy reproduction anomaly remains. No frozen experimental result was altered.
