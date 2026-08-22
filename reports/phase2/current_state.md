# Phase II current-state evidence ledger

Audit time: `2026-08-22T11:58:38Z`. Branch:
`exp/geometry-first-resistance-second`; audited HEAD: `c074962`. The worktree was clean
before the hardware detector refreshed its generated timestamp/resource fields.

## Proven or verified mathematics

- Standard effective resistance and leverage identities hold on the declared connected,
  undirected, positive-weight frozen reference graph.
- The frozen local leverage modular term, direction log-det term, and locality modular
  term form the declared monotone submodular local objective.
- GGR one-for-one exchanges preserve selected cardinality and terminate under strict
  frozen-leverage improvement plus the finite registered cap.
- These statements do not imply directed HNSW Recall, NDC, latency, or robustness.

## Experimental observations

- Phase I independent holdout remains a valid negative result: Trace+Resistance did
  not improve Recall and did not beat Geometry on the resistance-specific threshold.
- Three construction-only 10K audits (SIFT, GloVe-100, Arxiv-Nomic; seed 7; 128
  centers) found nonempty epsilon-zero exchange sets under the original absolute
  `1e-12` implementation tolerance.
- All 16 frozen Phase I artifacts and all 12 Phase II development artifacts pass their
  committed SHA-256 manifests.
- No official Phase II test query, test vector, or ground-truth member has been read.

## Unresolved

- Whether the reported epsilon-zero exchanges are strict, mixed-tolerance numerical
  equivalents, or artifacts of the original absolute tolerance.
- Whether proposed exchanges survive reciprocal insertion and reverse pruning in the
  final HNSW graph. The current public-data audit operates on query-derived candidate
  pools and an external selector, not an in-build final-link integration.
- Geometry-safe Random and Shuffled-Resistance specificity controls.
- Development-query Recall/NDC/latency, 100K multi-seed screening, structured insertion
  orders, cross-build variance, and the main epsilon amendment.

## Disproved or unsupported

- High effective resistance guarantees navigation value: disproved by Phase I
  counterexamples.
- Dynamic recomputation preserves the frozen submodular guarantee: disproved in
  general.
- Current GGR improves ANNS performance or robustness: unsupported; no Phase II search
  result exists.
- The greedy Geometry baseline is a global optimum: unsupported. Historical code and
  raw columns named it `geometry_star`; Gate 0 must replace that terminology with
  `geometry_base` without altering frozen raw artifacts.

## Validation receipt

- Python: `conda run -p .venv python -m pytest -q` -> 58/58 passed in 7.94 s;
  one previously recorded Intel/LLVM OpenMP coexistence warning.
- Lint: `conda run -p .venv ruff check python scripts tests theory/*.py` -> pass.
- Native: `.venv/Library/bin/ctest.exe --test-dir build --output-on-failure -C Release`
  -> 2/2 passed in 0.14 s.
- Hardware: Windows Tier 0, Intel 24 physical/32 logical cores, 15.627 GiB RAM,
  263.074 GiB free disk, RTX 4070 Laptop GPU; Python 3.11.16, MSVC 19.44,
  CMake 3.30.5, Git 2.54.0.
- Submodule: hnswlib `3f3429661187e4c24a490a0f148fc6bc89042b3d`.
- Phase I immutable tag: `phase1-local-resistance-null-v1` at `0e54d3f`.

## Current gate

Gate 0 is **not yet passed**. Formal tests remain sealed. The next authorized work is
the mixed-tolerance/high-precision epsilon-zero audit and final-graph treatment-strength
integration check; Gate A is not authorized.
