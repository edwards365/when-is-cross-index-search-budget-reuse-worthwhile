# Experiment log

All timestamps are UTC. Raw result directories are immutable once referenced by a report.

| Timestamp | Run ID | Purpose | Dataset | Config | Seed | Status | Notes |
|---|---|---|---|---|---:|---|---|
| 2026-08-22T03:38:39Z | `5c814131-a03b-4264-9f36-852f06a5b5c4` | HNSW pipeline smoke | synthetic narrow bridge 2K×16 | `configs/experiments/smoke.yaml` | 7 | success | Recall@10: 0.914/0.983/0.997/1.0 for ef 10/20/40/80. Raw query rows retained locally under the run ID; pre-commit metadata says `uncommitted`. |
| 2026-08-22T03:38Z | `mechanism-union-256-s7` | Exact resistance numerical check | first 256 synthetic base nodes | `configs/experiments/mechanism.yaml` | 7 | success | 1,532 weighted edges; max leverage 1.0000000000000133; no bound violations above tolerance. |
| 2026-08-22T03:36Z | n/a | Python test invocation | n/a | n/a | n/a | infrastructure failure | Parallel `conda run` calls collided on a temporary activation file; package was not installed and pytest collection consequently failed. Re-run serially with `.venv/python.exe`; this is not an algorithm test result. |
