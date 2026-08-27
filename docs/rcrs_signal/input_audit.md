# RCRS Signal Pilot input audit

- Frozen start: `01c491f712700bd146227c44db18848dd41d356a`
- Query split: 256 design, 256 calibration, 256 design-evaluation queries; seed 20261020.
- Query SHA256: `b69de4be8788e01cd61a67d6f3ab302de56cfcc3e0d3f19948b478acca58e9c7`
- Truth SHA256: `aca6e0f84a8cafc9facbb6dd488d5f9b932a0f6a978b176013d5b067a42eedca`
- GloVe preprocessing: L2-normalized base and queries, matching frozen Gate A ingest.
- Existing indexes only: GloVe Original seeds 7, 17 and 29. No index was built.
- `validation-dev` and `formal-test` were not accessed.
- Correction audit: the initial temporary raw-vector materialization was detected by implausible fixed recall, invalidated before policy selection, and fully recomputed with the preregistered normalization. No grid, feature, seed, query or threshold was changed.
