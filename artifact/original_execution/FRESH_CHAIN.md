# Fresh-query original-execution interfaces

This is a stage map, not an all-stage launcher. Run the saved-result entry in
the main artifact to rebuild published analyses. The entries below instead
describe new execution from original inputs. Delivery tests use synthetic
data; they do not re-execute the sealed benchmark or certify full-data success.

## Dependency order

1. [Input preparation](portable_fresh_inputs/README.md): original train-only
   membership, content exclusions and four disjoint roles per dataset.
2. Two input-dependent branches:
   - [Graph construction](portable_graphs/README.md): eight frozen graph
     configurations per dataset, one explicitly selected unit per invocation.
   - [Exact truth](portable_truth/README.md): pinned Faiss package payloads,
     original full-base exact search and eight frozen truth outputs.
3. [Native profiles](portable_profiles/README.md): unchanged 500/1000-query
   replay programs; one role across eight registered graphs, full action grid.
4. [Analysis arrays](portable_arrays/README.md): validated CSVs to the exact
   frozen NPZ schema consumed by saved-record analysis and cache measurement.
5. [Qualification and evaluation](portable_policy/README.md): frozen History-Max
   rule, certification-only lock, then explicitly SHA-bound evaluation. TG and
   fixed-budget baseline decisions remain separate.
6. [Cache entry](portable_cache/README.md): read-only seven-input validation
   or a separately authorized new cache measurement. Acquisition, API timing
   and cache lookup are distinct measurements.

Every original-data stage requires a new output location, frozen input/output
identities and explicit execution authorization. A failed identity gate is not
permission to adjust a pin, drop a target or repeat a run until it matches.
The commands and resource conditions are in the linked stage READMEs.

## What is verified and what is not

| Interface | Delivery verification | Still not established by these tests |
|---|---|---|
| Inputs | Synthetic partition, exclusions and serialization; historical membership identity | Full raw HDF5 scan in a new environment |
| Truth | Synthetic L2/IP native exact search with the pinned public wheel; 32 package/library payloads match the inspected original installation | Historical SIMD dispatch; full regenerated truth equivalence |
| Graphs | Hash-pinned source recipe; tiny two-metric/two-order native test in CI | Complete historical extension build provenance; full new graph byte equivalence |
| Profiles | Native compilation and tiny ordered-ID/count interface checks | Full eight-target response equivalence or original binary identity |
| Arrays | Synthetic schema, ordered grid, hit and identity rejection tests | Recomputed original arrays from a new full profile run |
| Policy | Synthetic lock/role guards, all three qualification branches and union-event arithmetic | New full-array certification/evaluation, baseline policy integration |
| Cache | Synthetic lookup-interface tests and saved seven-input checks | New benchmark cache timing or general cache-system performance |

Local validation JSON files describe local checks; Linux-only native outcomes
are reported separately by the fixed release's CI. Neither is an old audit
receipt. A published source recipe and a passing small test are not a claim
of complete experiment reproduction.

## Remaining delivery work

- Simple-baseline policy integration and native API timing entries, including
  timing aggregation and provenance; the original source views remain available.
- Reload/component measurement and lifecycle aggregation interfaces, keeping
  ledger allocations distinct from unavoidable deployment work.
- Other experiment families in `CHAINS.md` inside the separate
  [source archive](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-sources-v1):
  100K transfer/recovery, Deep1M, multi-implementation ambiguity, refresh and
  fixed-transfer extensions, and supplementary native coverage.
- Complete historical source/object provenance cannot be manufactured from
  an explicit new build. Keep missing attestations visible.

Earlier source-map and progress text is historical where it says these
entries are absent. This map does not supersede their scientific
protocols or the remaining-family limitations.
