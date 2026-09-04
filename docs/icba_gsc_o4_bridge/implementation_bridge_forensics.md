# Implementation-bridge forensics

The prior O4 artifact stopped at a 256-node exported adjacency fixture (`ANALYSIS_GRAPH_ONLY`). The bridge now connects proposal plan → layer-0 adjacency writeback → hnswlib `saveIndex` → reload → search/tracer. The adapter changes only layer 0; upper layers, labels, vectors, degree budgets, and the frozen O4 scoring rule remain untouched. The candidate pool is the baseline layer-0 neighbor set union the proposal-role original-only trace targets. The bridge is an engineering adapter, not a new operator.

`bridge_forensics.csv` records the chain and the explicit non-access of sealed roles.
