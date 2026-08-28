# Z1 deployable information model

The frozen schemas contain a real but implementation-asymmetric Z1 channel. HNSWlib records exact NDC, returned IDs, returned distances, latency, entry point and max level for every query-budget row. Faiss and Vamana compact tables retain exact NDC and returned IDs but omit returned distances, latency and hierarchy fields. Exact NDC is a runtime work counter and does not require target truth; Recall@10 and stable sufficient budget do.

Derived unlabeled fields are allowed only when their parents are present: kth distance and distance gap from returned distances; result churn/stability from returned IDs at the fixed budgets; marginal work from exact-NDC increments. Visited/frontier/candidate-queue statistics are not in the frozen 81-graph tables and require instrumentation.

This passes Gate Z1-A for a **conditional HNSWlib-only frozen pilot**: at least one online, no-ground-truth, non-source-Oracle channel exists and its cost is estimable. It does not establish a common cross-implementation channel beyond NDC/returned-ID semantics, nor Gate Z1-B/C/D. The pilot may therefore use only preregistered SIFT-100K HNSWlib builds and fixed budgets 32/128/512; it remains `EXPLORATORY_INFORMATION_PILOT`.

No field may use Recall, exact truth, stable safe budgets on fingerprint queries, or target labels when constructing the fingerprint. Labeled stable budgets are permitted only on the disjoint 744 evaluation queries to score response control, consistent with the frozen split.
