# Fixed-member E1a and paired-refresh E1b execution interfaces

This package reconstructs the **original execution path**, not a new method.
It does not launch a panel by default and never locates old outputs implicitly.
Each command needs a new output directory and explicit authorization. All
original-data outputs must match the published frozen array/graph hashes;
failure preserves evidence and stops dependents, without retry, retuning,
repinning, or changing SIMD to chase matching results.

## What is preserved

| Family | Members and graph order | Query stages and decisions |
| --- | --- | --- |
| E1a | Train-only effective base: SIFT 997,420; Arxiv 1,342,143. Old roles and content counterparts excluded. RandomState permutation or float64 norm/raw-ID order. | 500 source → all 16 source locks → 500 selection → all 16 selection locks → 500 qualification → all 16 decision locks → 1,000 evaluation. |
| E1b | Repaired initial/refreshed members: SIFT 945,117; Arxiv 1,272,661. Each pair permutes the same sorted union then filters the state, preserving common-member order. | 500 initial-source → all 16 source locks → 500 refreshed qualification → all 16 decision locks → paired initial/refreshed 1,000 evaluation. Target-selection queries are never accessed. |

Both recipes keep M16, efConstruction100, seeds 13/83/197/2029, random and
norm-ascending histories, one insertion/search thread, k10 and raw IDs.
E1a's seed13/random historical pilot reuse is explicitly retained as a
provenance caveat: a new graph build cannot reproduce the historical design
timeline. E1b source truth for refreshed members is a diagnostic truth output,
not a source-policy selection input.

`historical_core.py` contains AST-delimited source blocks. Paths and imported
modules are explicit function inputs; no original globals or sealed directories
are monkeypatched. The graph, exact-search, approximate-search, event, CP and
selection blocks retain their original operations. E1a qualification `outcome`
receives its original CP function as an explicit dependency; its body is intact.
Seven truth blocks are separate: E1a design uses uncompressed NPZ, all other
truths use compressed NPZ. Exact queries remain a full 500/1,000-row batch,
base streaming remains 8,192 rows, and Faiss retains 16 threads.

## Environment and bounded interface tests

Use Linux x86_64 Python 3.11, NumPy1.26.4, h5py3.11.0, SciPy1.13.1.
Install the hash-pinned source-built hnswlib recipe from
`../portable_graphs/requirements-build.txt` then
`../portable_graphs/requirements-native.txt` with `--no-build-isolation --no-deps`.
Install the verified Faiss wheel in `../portable_truth/requirements.txt` and
`scipy==1.13.1`. No root/system installation is needed.

```sh
python -m unittest discover -s portable_transfer_1m -p test_transfer.py -v
python portable_transfer_1m/native_check.py --profiles portable_profiles \
  --output /path/to/NEW-synthetic-check --authorize-synthetic-only
```

The unit tests exercise separate order recipes, neutral trimming, seven truth
interfaces, three native-counter interfaces, policy selection, and phase-lock
negative controls. The second command additionally compiles the **unchanged**
500/1,000-query NDC sources through the existing portable-profile build, and
uses only a new 32-vector graph and 1,000 random queries, for both metrics.
It checks real Faiss exact IDs against float64 exhaustive results and actual
C++/Python ordered-ID, recall-event and NDC response equivalence. This is not
a full original-data rerun or a historical timing validation.

## Membership and one graph

Paths below are illustrative; bind actual new directories explicitly.

```sh
python portable_transfer_1m/run_transfer.py memberships \
  --input-adapter portable_fresh_inputs --output /path/to/NEW-memberships \
  --outstanding-growth-bytes 137438953472 --authorize-new-stage
python portable_transfer_1m/run_transfer.py graph --family e1a --dataset sift \
  --source /path/to/sift-128-euclidean.hdf5 --seed 13 --history random \
  --graph-adapter portable_graphs --input-adapter portable_fresh_inputs \
  --output /path/to/NEW-e1a-sift-seed13-random \
  --outstanding-growth-bytes 137438953472 --authorize-new-stage
```

For E1b graph construction add `--family e1b --state initial` (or `refreshed`)
and `--memberships /path/to/NEW-memberships`. The membership producer reuses
the frozen content-counterpart evidence; it does not repeat the content audit.
No query outcome is read during graph construction; the original full train
array is read before exclusion filtering, including held-out rows.

## Truth, responses and locks

Each stage uses an explicit JSON request, recorded before execution:

```sh
python portable_transfer_1m/run_phase.py --request /path/to/request.json \
  --input-adapter portable_fresh_inputs --output /path/to/NEW-stage \
  --outstanding-growth-bytes 137438953472 --authorize-new-stage
```

All requests contain `family` (`e1a`/`e1b`), `phase`
(`source`/`selection`/`certify`/`evaluate`), and `kind`
(`truth`/`response`/`panel`). Every stage after source includes `prior_panel`.
The prior **complete 16-unit** lock is checked before target queries/truth are
opened. Initial-source query access requires no later-role lock.

Truth example:

```json
{"kind":"truth","family":"e1a","phase":"source","dataset":"sift",
 "source":"/path/to/sift-128-euclidean.hdf5","truth_adapter":"/path/to/portable_truth"}
```

For E1b add `memberships` and `state`. `certify` requires refreshed state;
`evaluate` produces each of initial and refreshed truth separately. E1a uses
the verified wheel's native dispatch without an override; E1b explicitly binds
its required AVX2 payload before import. Package files and loaded extension
are checked. Any output hash mismatch stops; no alternate dispatch is tried.

Response example (E1a selection):

```json
{"kind":"response","family":"e1a","phase":"selection","dataset":"sift",
 "seed":13,"history":"random","source":"/path/to/sift-128-euclidean.hdf5",
 "prior_panel":"/path/to/NEW-source-panel","graph_adapter":"/path/to/portable_graphs",
 "graphs":{"fixed":"/path/to/NEW-e1a-sift-seed13-random/index.bin"},
 "truths":{"fixed":"/path/to/NEW-selection-truth/truth.npz"},
 "profiles_adapter":"/path/to/portable_profiles","native_build":"/path/to/NEW-profile-build"}
```

Create the new profile build using `portable_profiles/native_entry.py` first;
its completed synthetic-test receipt pins the new binaries. Source responses
do not need native-build parameters. E1a certification/evaluation derives the
action subset from prior locked actions/decisions, not an arbitrary full grid.
The unchanged native programs run synchronously with real return-code checks;
CSV ordered IDs, recall events and counts must agree with Python hnswlib.

E1b responses also specify `memberships`; `graphs` and `truths` use `initial`
for source, `refreshed` for qualification, and both keys for evaluation.
Its original responses are Python-native ID/recall outputs, **not** NDC or
formal timing measurements. Selected ef and deployment decisions come from
the previous phase lock, never from evaluation outcomes.

Panel request:

```json
{"kind":"panel","family":"e1a","phase":"selection",
 "prior_panel":"/path/to/NEW-source-panel",
 "responses":["/path/to/NEW-response-1","/path/to/NEW-response-2"]}
```

Replace the illustrative two paths with **all 16** distinct dataset/seed/history
units. A panel lock checks frozen NPZ hashes, recomputes source/qualification
decisions from responses, and rejects missing, repeated, stale or failed units.
E1a selection produces 112 directed-pair plus 16 target-global actions;
qualification produces 368 decisions with the original union-event CP rules.
New policies must match the frozen policy values before downstream access.
Caller paths and timestamps are new-run metadata, not historical receipt IDs.

Follow the stage order in the first table. Publish/use `completed.json` only
after process exit0; `failure.json` means dependent execution stops. Final
evaluation arrays retain original field names and can feed the separately
delivered saved-output analysis paths; this entry does not rerun bootstrap,
change analysis weights, or manufacture an old analysis/time receipt.

## Resource and evidence limits

Original-data stages require at least 160GiB available RAM, the preserved
post-reservation RAM/60%-machine-RSS gates, projected disk free >=200GiB,
and all outstanding project growth <=128GiB. Unknown budgets fail closed.
CPU2 is used for graph/search; truth uses CPUs4–19 with 16 Faiss threads.
Graph stages use 24GiB AS, 8GiB single-file/output bound and 4h CPU/wall;
truth/response/panel stages use 24GiB AS, 128MiB single-file and 256MiB
aggregate-output bound, 2h CPU/wall. AS is not an RSS quota; output growth
is checked after operations, not advertised as a filesystem quota. Existing
stricter inherited limits are retained. Native child processes inherit these
limits and have an additional 600s wait timeout.

Successful synthetic tests establish interfaces and scientific-block behavior
on fixtures. They do not establish full-panel regeneration, complete historical
source/extension provenance, native timing equivalence, or independent-host
scientific reproduction. All original input, role, graph, truth, response,
policy and source pins are in `config.json`; historical source archives and
counter headers are delivered separately, not silently downloaded at runtime.
