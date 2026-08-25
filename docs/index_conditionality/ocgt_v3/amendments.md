# OCGT-v3 protocol amendments

## 2026-08-25 — recorder implementation commit

- Reason: the preregistration froze endpoints and schema before the dedicated Gate R recorder existed. Commit `03c8c31323a2a8411c5a81c2f32cf9a5bf55834d` implements the already-frozen schema and exact native-versus-tracer comparison.
- Scope: implementation only; no dataset, query, seed, insertion order, ef value, endpoint, threshold, or analysis rule changed.
- Timing: recorded before any OCGT-v3 HNSW construction or performance query.
- Tests: 2/2 dedicated runner tests and the prior 80/80 Python tests pass.
