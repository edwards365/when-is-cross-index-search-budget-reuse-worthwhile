# Fresh-query original-execution interfaces

This is the fresh-query stage map, not an all-stage launcher. The [ten-family execution map](EXECUTION_MAP.md) covers the other paper panels. Run the saved-result entry in
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
   fixed-budget baseline decisions use the separate
   [baseline lock entry](portable_baselines/README.md), with selection and
   qualification separated from final evaluation.
6. [Native API timing](portable_timing/README.md): separate native build and
   explicitly authorized one-graph measurement after the decision lock; seven
   repetitions retain the original arithmetic-mean aggregation.
7. [Fresh-process reload](portable_reload/README.md): independent reload units,
   three repetitions per graph; no cold-cache claim.
8. [Cache entry](portable_cache/README.md): read-only seven-input validation
   or a separately authorized new cache measurement. Acquisition, API timing
   and cache lookup are distinct measurements.
9. For lifecycle measurement, use [operational stages](portable_costs/README.md) and [the new-ledger bridge](portable_costs/NEW_LEDGER.md). Measure the original role/profile/decision boundaries, materialize their arrays, and bind them with new truth, graph/reload, policy, baseline, timing and cache receipts. The operational-profile option feeds timing without repeating the profile panel. Use the full graph-unit timing flag when standalone whole-graph costs are required.

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
| Policy | Synthetic lock/role guards, all three qualification branches and union-event arithmetic | New full-array certification/evaluation |
| Baselines | Synthetic original CP/selection arithmetic and prior-lock gates | Full new-array baseline reproduction |
| API timing | Unchanged native source; tiny native ID/time-schema tests in CI | New full-scale timing or historical binary/time identity |
| Reload | Original loader timing body; fresh-process tiny native tests in CI | Historical cache state or new full-panel reload times |
| Cache | Synthetic lookup-interface tests and saved seven-input checks | New benchmark cache timing or general cache-system performance |
| Operational lifecycle | Original timed boundaries, new-origin array/timing bridges, typed full synthetic receipt-chain tests | New full-dataset component measurements, hardware equivalence, complete unknown overhead or end-to-end performance |

Local validation JSON files describe local checks; Linux-only native outcomes
are reported separately by the fixed release's CI. Neither is an old audit
receipt. A published source recipe and a passing small test are not a claim
of complete experiment reproduction.

## Scope and remaining execution checks

The acquisition-component and lifecycle aggregation entries are supplied; their ledger allocations remain distinct from unavoidable deployment costs. See [EXECUTION_MAP.md](EXECUTION_MAP.md) for the other original-protocol families. The earlier source archive's `CHAINS.md` records source-delivery status at its own version and is not the current interface map.

The new commands have not regenerated every original full-scale dataset, graph, response or timing panel during packaging. Those outcomes require explicit production execution and successful identity gates. Tiny native CI is a separate validation layer. Missing historical source/object provenance cannot be manufactured from an explicit new build.

Earlier progress text saying that an upstream interface is absent is superseded by this map and the ten-family map. Their scientific conventions and historical limitations are not superseded.
