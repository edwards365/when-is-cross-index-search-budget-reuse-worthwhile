# SGDR reproducibility and execution record

All commands run from `/home/wlk/projects/navigation-aware-resistance-hnsw` on branch
`exp/sgdr_3day_feasibility`.

```bash
.venv/bin/python scripts/sgdr_3day/analyze_query_oracle.py
.venv/bin/python scripts/sgdr_3day/generate_delta_plans.py
.venv/bin/cmake -S . -B build-r0 -DCMAKE_BUILD_TYPE=Release
.venv/bin/cmake --build build-r0 --target hnsw_sgdr_gate_o_search -j 3
.venv/bin/python scripts/sgdr_3day/run_gate_o_matrix.py --workers 3
.venv/bin/python scripts/sgdr_3day/analyze_gate_o_stage.py
.venv/bin/python scripts/sgdr_3day/make_boundary_artifacts.py
```

Tests and invariants:

- Preregistration and aggregation addendum committed before inspecting new outputs.
- SIFT seed-7 smoke: 33,000 query-mode-ef rows; diagnostic Original labels and NDC
  exactly matched native `searchKnn` for all 500 queries and six frozen ef values.
- Full matrix: nine exact Original reconstructions; 297,000 paired rows; native
  equivalence passed in all runs; zero non-empty stderr logs; all indexes deleted.
- Data firewall: only frozen 10K train prefixes and 500-query E0 design-dev inputs;
  no validation-dev or formal-test access; no truth recomputation.
- Hardware: AMD EPYC 7542, 128 logical CPUs, 251 GiB RAM, four RTX 3090 GPUs (unused
  for Gate O); free disk remained above the 10 GiB stop threshold.

Tracked study commits through the decision:

- `68dc35b`: preregistration and environment audit
- `bb47bd8`: Gate O aggregation addendum
- `4435957`: query-oracle analyzer
- `659f12a`: query-oracle evidence and theory
- `df4d359`: exact diagnostic search compiled
- `e72ca84`: frozen delta-plan generator
- `ab0a4b9`: recoverable nine-run matrix
- `8ef58d2`: outcome-blind stage adjudication
- `f7ca393`: Gate O stop decision
- `b410383`: boundary figures and literature audit

The working tree also contains preserved, untracked historical build/log/result
directories. They are not part of the SGDR code diff and were not overwritten.
