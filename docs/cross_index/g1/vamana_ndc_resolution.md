# Vamana exact-NDC resolution before Gate R0

The frozen Microsoft DiskANN source at `158126e64129d3c39f9df02199c2dcc06d4f9e7f` returns `diskann::graph::index::SearchStats` from the native graph search. Its `cmps` field is the number of query-to-index distance comparisons and is computed in the production search path; reading it does not add a search callback or alter graph traversal.

The official `diskann-inmem` integration benchmark independently exposes the feature-gated provider counter `query_distance`. In the committed official regression baseline, every reported KNN cell has exact equality between `misc.cmps` and `counters.query_distance` (for example 44,988, 49,075, and 74,001). Therefore Gate R0 will use native `SearchStats.cmps` as primary exact NDC and use the integration counter only as an audit oracle. Labels, distances, graph serialization, and `cmps` must repeat exactly for the frozen SIFT-10K matrix. A mismatch, inability to expose per-query `cmps`, or any search-path modification still yields `INVALID_CROSS_INDEX_INSTRUMENTATION`.

This resolves measurement feasibility only. It does not pass Gate R0, authorize the 100K matrix, alter any budget, seed, history, query, or threshold, or access validation-dev/formal-test.
