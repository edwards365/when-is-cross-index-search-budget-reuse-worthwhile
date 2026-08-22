# Frozen research questions (v0.1)

Freeze date: 2026-08-22. Any change must be logged before inspecting held-out performance.

H1 asks whether locally missing high-leverage edges add query-difficulty explanation beyond LID, relative contrast, nearest-neighbor gaps, density, degree/hubness, direction coverage, current distance, clustering coefficient, and candidate-set size.

H2 asks whether degree- and edge-budget-preserving replacement of low-leverage direction-redundant edges with high-leverage navigational candidates improves NDC or tail latency at matched Recall@10, while reducing seed/order sensitivity and avoiding material memory growth.

Primary intervention comparison: Original HNSW, Random Rewire, Distance-only, Geometry-only, Resistance-only, and Resistance+Direction. The primary target recalls are 0.95 and 0.99, selected using a validation split; the test split is evaluated once per frozen configuration.

The first frozen Resistance Bottleneck Score for a query is the maximum, over visited local neighborhoods, of the largest leverage among candidate edges rejected from the current node, aggregated without using query success labels. This definition is provisional until insertion-candidate instrumentation exists and must be versioned before H1 testing.

