# Original source and protocol delivery

The [artifact-sources-v1 release](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-sources-v1) adds an inspectable, pinned upstream source/protocol package to the saved-record reconstruction in `artifact-paper-v2`.

**This release does not close portable original-experiment execution.** It contains 946 source/configuration views for eight paper execution families and 125 historical native operation/evidence records. Personal paths are transformed; original and delivered-view hashes are recorded separately. The text views use `.txt` suffixes because unchanged embedded pins must not be mistaken for executable relocated code.

## Download and check

Download `original-execution-source-view.zip` from the release, check the byte length and SHA256 in [release.json](release.json), then extract it into a new directory. Python 3.11+ standard library is sufficient:

```sh
python execution.py verify
python execution.py inspect recovery_100k
python -m unittest -v test_execution
```

The actual clean-archive test used Python 3.12.14 and passed all eight family inspections, file identities and twelve synthetic transport tests. See [validation.json](validation.json). No archived experiment module was imported; ANN runs, native builds and original auditor runs were all zero.

## Contents

- `CHAINS.md`: paper result → original stage → source file, with explicit remaining work.
- `inventory.json`: original commit/blob/SHA, delivered-view SHA, static CLI argument spellings and imports.
- `source-view/`: selected implementation, frozen configurations, role registries, native sources and local import dependencies from two fixed project commits.
- `native-records/`: Arxiv DARTH/Vamana command/identity/wait records, sampled resource logs, complete saved audit output and evidence inventories. These are historical records, not freshly executed audits.
- `datasets.json`: acquisition links and original input checksums for SIFT, Arxiv, GloVe and Deep; original datasets are not redistributed.
- `execution.py`: safe inspection, input-hash verification and explicit opt-in bounded download. It does not launch scientific stages.

The Arxiv provider's fixed-revision LFS identity matches the experiment's SHA256. ANN-Benchmarks HEAD requests for the other three inputs returned HTTP200 and their recorded sizes on 2026-10-07; no full dataset was downloaded by this task. Consult each provider's terms. [Dependency distinctions](DEPENDENCIES.md) are important: different Faiss builds, Arxiv normalization conventions and role policies must not be merged into one convenience environment.

## Remaining integration

Portable phase adapters, native dependency/build closure, receipt/pin rebinding in a fresh output tree and isolated execution checks remain open. Native historical record coverage in this tranche is Arxiv, not every SIFT/Faiss operation log. The archive lists the remaining items per family rather than labelling the presence of source code as a successful original execution.

The paper remains pinned to `artifact-paper-v2` until original-execution integration and the next full public delivery have been verified. Scientific methods, recorded results and figures are unchanged.

## Standalone cache entry

[portable_cache/README.md](portable_cache/README.md) supplies an executable, explicit-opt-in E2 stage separated from the historical multi-stage campaign. Its original lookup/workload/timer body is preserved with an enumerated input-location diff. Eighteen synthetic tests and seven pinned historical input/schema checks pass without invoking the timer. Original measurement results are unchanged. Prepared query/truth inputs are not redistributed here; raw-to-prepared-input generation and an actual Linux performance run remain outside this verification. The other original-execution families remain open as listed above.

## Fresh-query input entry

[portable_fresh_inputs/README.md](portable_fresh_inputs/README.md) supplies fixed role selection, effective-base exclusions and query-file generation on explicitly chosen input/output paths. The frozen ID partitions reconstruct exactly, and tiny synthetic HDF5 tests check content collisions, raw float32 encoding and train-only access. No original HDF5 scan or query export was rerun for delivery. The entry supplies membership and query files for the cache stage; exact-truth and audited profile generation remain separate unresolved integrations.

## Exact-truth entry

[portable_truth/README.md](portable_truth/README.md) identifies the original public wheel by all32 package/library payload hashes and connects new input receipts to exact top-10 generation. Synthetic L2/IP and rejection tests accompany the entry; original-data generation is not rerun for delivery. Native profile binaries, graph inputs and receipt integration remain separate gates.

## Native profile entry

[portable_profiles/README.md](portable_profiles/README.md) supplies the unchanged500/1000-query programs, pinned HNSW headers with license, a small native build/test command, and a one-role/eight-graph execution wrapper. New binaries and frozen CSV equivalence are distinct gates. It requires registered saved graphs; portable benchmark graph construction and CSV-to-array materialization remain open. No benchmark build or search was rerun.
