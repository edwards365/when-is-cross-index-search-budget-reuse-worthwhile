# Distinct million-scale Faiss E3/E6 delivery

This package retains the original Faiss 1.8 AVX2 fixed-member E3 protocol, not the
100K transfer or fresh-query hnswlib protocol. There are **24 registered graph
records per dataset**, including repeated serialized content (13 content
identities per dataset). All record weights and all 552 directions per dataset
remain; no deduplication is presented as independent reconstruction.

The original source files are frozen and never edited. `historical_core.py`
contains exact AST-selected scientific blocks with explicit portable bindings.
`config.json` records source hashes, all 192 response identities, graph identities,
and canonical hashes of the original selection/certification rows. It does not
ship private paths or the full historical multi-megabyte lock documents.

## E3 phase chain

1. Produce source truth with this package's `kind: truth` entry. It reuses the
   exact E1a scientific truth blocks, membership, native dispatch and frozen NPZ
   hashes, but not the HNSW campaign's prerequisite gate. No E1b or fresh-query
   truth is interchangeable.
2. Run 48 `graph` requests: two datasets × twelve seeds × two histories. This
   uses the original `RandomState(seed)` or ascending squared norm/raw-ID order,
   `IndexIDMap2(IndexHNSWFlat)`, M16/efConstruction100 and one AVX2 thread.
3. Run 48 `response` source requests then one `panel` source lock.
4. Generate each next role's two truth files with `kind: truth`, then repeat
   response/panel for selection, certification and evaluation, each
   requiring the complete preceding panel before requested query-role access.
   These gates are this Faiss campaign's 48-record locks; a separate HNSW
   campaign is not required. Truth runs preserve 16 threads on CPUs4–19.
   Selection recreates 1,104 directed pair rows and 48 target-global rows;
   certification recreates 3,408 decisions, compared with canonical frozen rows.

```
python run_faiss.py --request REQUEST.json --output NEW_DIRECTORY \
 --input-adapter ../portable_fresh_inputs --outstanding-growth-bytes 12884901888 \
 --authorize-new-stage
```

Graph requests: `kind: graph`, `dataset: sift|arxiv`, `seed`, `history`, `source`,
`transfer_adapter`, `truth_adapter`. Response requests add `kind: response`,
`phase: source|selection|certify|evaluate`, `graph` (new graph directory), `truth`
(the new exact-truth NPZ), and `prior_panel` except for source. Panel requests use
`kind: panel`, `phase`, `units` mapping all 48 full dataset/build keys to new
response directories, and the preceding `prior_panel` where required.
Truth requests use `kind: truth`, `phase`, `dataset`, `source`,
`transfer_adapter`, `truth_adapter`, and `prior_panel` except for source.
Successful truth receipts have status `NEW_FAISS1M_TRUTH_MATCHES_FROZEN_BYTES`;
each later truth receipt binds its own preceding Faiss panel's receipt hash.

The search grid is 16…4096 (nine powers of two), not the fresh-query eleven-action
grid. Source and selection search the full grid; subsequent phases execute the
union of locked candidate/endpoint actions. All ordered returned IDs, recall,
endpoint-aware events and frozen NPZ identities are checked. Build times are
new operational observations, not the saved paper measurements.

## E6 exact counter, separate from AVX2 timing

Obtain the exact public conda package specified in `generic_package_lock.json`.
The package SHA and all 124 header/library files are checked during safe
extraction. This is the **same Faiss GENERIC library payload** used by the
successful corrected counter; it is not the AVX2 Python wheel. Other compiler
and runtime libraries are resolved and recorded, not claimed to equal the old
environment. Install `zstandard==0.23.0` for the conda payload extraction and
Linux build prerequisites (C++17 compiler/OpenMP, `libblas3`, `liblapack3` and
compatible `libstdc++6`). Loader overrides are removed only in compiler/native/
ldd children; a Python setup runner's own library path is not misidentified as
the Faiss runtime. The resolved Faiss library must still match its exact pin.

```
python build_counter.py --package libfaiss-1.8.0-h72e5a87_2_cpu.conda \
 --output NEW_COUNTER_BUILD --authorize-new-build
```

`run_supplement.py` accepts the same explicit `--request`, `--output`,
`--input-adapter`, `--outstanding-growth-bytes`, `--authorize-new-stage` flags.
The declared growth must include the whole outstanding project, at least the
16 GiB bounded supplement allowance. Stages are:

* `export`: dataset/source; writes pinned source/evaluation fbin, original base
  vectors and raw-ID map. Only HDF5 `train` is read.
* `counter-source`: dataset/seed13/history=random, `inputs`, `counter_build`,
  `graph`, complete E3 source `response_panel`. Executes the unchanged corrected
  C++ counter with full event tracing, then the original independent event and
  original-vector-distance auditor in a separate process. Both actual waits
  must be zero. Run once for each dataset.
* `counter-target`: same fields with chosen registered graph and evaluation
  `response_panel`, plus `source_audits` mapping sift/arxiv to those new successful
  source directories. All locked target actions and ordered IDs are checked.
  Target counts remain source-validated native counts, not independently traced
  target events.
* `counter-panel`: `units` mapping all48 keys to new target-counter outputs and
  both `source_audits`; creates a new auditable closure, not a historical receipt.
* `latency`: dataset/seed/history, `inputs`, `graph`, evaluation `response_panel`,
  new `counter_panel`, `transfer_adapter`, `truth_adapter`, plus
  `--assert-isolated-host`. Uses the successful original AVX2 API timing core,
  16 warmup queries/action, five repetitions, 1,000 queries, original timer
  placement and ordered-output checks. CPU4 quiet intervals and a shared lease
  supplement caller-arranged isolation; they do not prove continuous isolation.

No failed ndis probe, wrong-reset counter build, or earlier incomplete latency
closure is rerun. Counters are not used as an AVX2 timing denominator. Newly
measured times can differ from published observations; no old-time identity or
end-to-end deployment claim is made.

## Bounded CI

```
python -m unittest discover -s portable_faiss_1m -p 'test_*.py' -v
python portable_faiss_1m/native_check.py --output NEW_TINY_E3 --authorize-synthetic-only
python portable_faiss_1m/build_counter.py --package PACKAGE --output NEW_COUNTER --authorize-new-build
python portable_faiss_1m/counter_check.py --native-check NEW_TINY_E3 \
 --counter-build NEW_COUNTER --output NEW_TINY_E6 --authorize-synthetic-only
```

Use Linux x86-64 Python3.11, pinned NumPy1.26.4/h5py3.11/Faiss1.8 AVX2/SciPy1.13.1.
Tiny E3 tests use only 32 newly generated base vectors.
Tiny native checks separately enforce one available CI CPU, one library thread,
4 GiB address space, 180 CPU seconds, 240 wall seconds and a 128 MiB output bound.
The production stage
entry has explicit affinity, RAM/disk/iowait checks, inherited resource limits,
new exclusive output directories, true child waits, and failure preservation.
No commands here execute a saved experiment or overwrite old evidence.
