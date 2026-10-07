# Original-execution delivery

Start with [FRESH_CHAIN.md](FRESH_CHAIN.md) for the current dependency order,
available commands, tested scope and remaining work. **The full paper's original
execution is not yet a one-command, independently reproduced pipeline.**

## Portable entries now supplied

| Entry | Purpose | Delivered verification |
|---|---|---|
| [Input preparation](portable_fresh_inputs/README.md) | Train-only roles, content exclusions, query files | 18 synthetic tests; frozen membership serialization |
| [Exact truth](portable_truth/README.md) | Fixed-role Faiss L2/IP truth generation | 20 tests on Linux, including native synthetic cases; pinned wheel payload identity |
| [Graph construction](portable_graphs/README.md) | One explicitly selected HNSW build unit | 3 tests; four tiny L2/IP/order graph cases |
| [Native profiles](portable_profiles/README.md) | Complete fixed action grid on eight graphs | 10 wrapper tests and two role-size native programs tested on tiny graphs |
| [Profile arrays](portable_arrays/README.md) | Ordered CSVs to frozen NPZ schema | 12 synthetic tests |
| [Policy lock](portable_policy/README.md) | History-Max qualification, then SHA-bound evaluation | 16 synthetic tests |
| [Baseline lock](portable_baselines/README.md) | Fixed-1600, TG500, TG1000 and endpoint, lock then evaluate | 18 synthetic tests |
| [Native API timing](portable_timing/README.md) | Prior-lock, one-graph native query timing | 14 tests; Linux native test uses tiny generated graphs |
| [Reload measurement](portable_reload/README.md) | Fresh-process reload, three repetitions | 8 tests; Linux native test uses tiny generated graphs |
| [Cache measurement](portable_cache/README.md) | Check inputs or explicitly measure a new cache workload | 18 synthetic tests; seven saved-input identities checked |

Tests of new entries do not re-execute the sealed experiments. Full benchmark
graph/truth/response equivalence is an enforced future gate, not a result of
the tiny tests. Current implementation status in this table supersedes older
stage README progress statements; their scientific boundaries remain valid.

Production commands require new outputs, pinned inputs, explicit opt-in and
resource checks. The native library/compiler identity, event being counted,
query role, timing boundary and missing provenance remain stage specific.
Different environments must not be collapsed into one convenience dependency.
See [dependency distinctions](DEPENDENCIES.md) and [dataset sources](datasets.json).

## Additional original families

- [100K recovery](portable_recovery_100k/README.md): S9-3 and paired S9-4, explicit preparation/build/profile/lock/evaluation/timing phases. The normalized Arxiv truth and physical L2 graph are preserved.
- [Deep1M recovery](portable_deep/README.md): historical cosine panel with three test-member query roles, separate preparation/build/native replay/analysis. Test-member access requires explicit opt-in; delivery does not execute it.

These entries have synthetic tests and frozen graph/input gates. They do not claim a new full-size reproduction or new benchmark times.

## Transfer and diagnostic recipes

- [100K transfer](portable_transfer_100k/README.md): original HNSW and corrected Faiss roles, distinct grids/metrics, separate preparation/build/replay and paper-row filtering.
- [Fixed-member transfer and paired refresh](portable_transfer_1m/README.md): 48 graph identities, separate state truth and locked role phases. The historical source NDC export is distinct from the no-NDC source-design response.
- [Three-implementation ambiguity](portable_ambiguity/README.md): 81 registered builds, 648 directions, exact no-finite-tail marker, four-patch locked DiskANN source recipe.
- [Cost component provenance](portable_costs/README.md): 79 original receipts and the 12-row fixed-cost bridge. It reconstructs original operational allocations without substituting newly measured wrapper times.

Native CI uses newly generated small vectors only. Full-size original execution is opt-in and has not been repeated during delivery. Historical binary attestation and new source reproducibility are separate records.

## Native and official-adapter execution

- [Native Vamana, DARTH and 100K refresh](portable_native/README.md): source dependencies, native builds, role-safe preparation, frozen training and saved-graph searches; historical and new build identities remain distinct.
- [Official Ada-ef](portable_adaef/README.md): original C++ adapter, role-isolated truth, source statistics, selection, certification and evaluation with independent endpoint checks.

These entries are undergoing Linux build and synthetic-input validation; original scientific datasets are not rerun by CI.

## Three separate delivery layers

1. [Saved-result reconstruction](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-paper-v2)
   supplies the paper's delivered saved-record analysis paths. It is not a new
   benchmark run.
2. [Original source archive](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-sources-v1)
   contains 946 source/configuration views, 125 historical native records,
   `CHAINS.md`, `inventory.json`, `source-view/`, `native-records/`, and the
   safe `execution.py` inspection tool. **Those files are inside the separate
   archive, not the current repository directory.** Download instructions and
   fixed identities are in [release.json](release.json). Personal paths were
   transformed; original and delivered hashes are separately recorded.
3. The portable entries above connect selected original stages to new inputs,
   receipts and output roots. They preserve missing historical attestations
   rather than replacing them with claims about a new build.

After extracting the separate source archive into a new directory, its safe
inspection commands are:

```sh
python execution.py verify
python execution.py inspect recovery_100k
python -m unittest -v test_execution
```

Do not execute historical default/all-stage scripts simply because their source
is present. Archived `.txt` source views are not portable launchers.

## Remaining coverage

Acquisition-component measurement and lifecycle aggregation still need
new-execution integration; saved-ledger reconstruction is already delivered. The 100K transfer,
multi-implementation ambiguity, refresh/fixed-transfer and supplementary native
families retain their separate gaps in the source archive's `CHAINS.md`.
Full DARTH source/object provenance cannot be retroactively established by a
new build. Historical record coverage must not be confused with new execution.

The manuscript, scientific methods, recorded results and figures stay unchanged
until the intended delivery coverage is genuinely complete and publicly checked.
