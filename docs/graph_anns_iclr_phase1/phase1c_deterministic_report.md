# Phase 1C deterministic rebuild seal

Registered mitigation label: **DETERMINISTIC_REBUILD_ACTIONABLE_MITIGATION**.

D1 and D2 remain build- and search-variable on both datasets. D3 is byte-identical and search-identical across three repetitions on both datasets. Native finite safe budget is used as the implementation-internal cost because the Python-built indexes do not expose the frozen tracer NDC counter; no wall-clock equivalence claim is made.

- sift_100k: Recall delta -0.000317; mean safe-budget ratio 0.9740; p95 ratio 1.0000; build-time ratio 0.5237; all registered gates=True.
- arxiv_nomic_100k: Recall delta -0.000683; mean safe-budget ratio 0.9679; p95 ratio 1.0000; build-time ratio 0.3263; all registered gates=True.
