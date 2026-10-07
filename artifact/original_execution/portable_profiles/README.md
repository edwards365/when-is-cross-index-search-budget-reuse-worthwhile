# Native profile execution entry

This package supplies the unchanged 500-query and 1000-query replay programs,
the original HNSW header revision, a portable compiler entry, a32-vector native
integration test, and an explicit one-role/eight-graph profile command.
It does not build a benchmark graph or change the11-action grid.

## Source and counter identity

`include/hnswlib` is copied without edits from upstream commit
`3f3429661187e4c24a490a0f148fc6bc89042b3d` (v0.8.0); the Apache2.0 license is
preserved at `include/LICENSE`. The two C++ programs are the original project
sources, not algorithm replacements. The wrapper counter delegates the native
L2/IP function and counts each invocation, including upper and base layers.
All headers, program sources, sixteen graph identities, eight query-role
identities and64 output CSV identities are recorded in `config.json`.

```sh
python3.11 artifact/original_execution/portable_profiles/native_entry.py \
  --output /path/to/new-native-build --authorize-build-and-synthetic-tests
```

Requires Linux x86-64, g++, and NumPy1.26.4. The command compiles with the
historical `-std=c++17 -O3 -march=native` flags, records the actual compiler and
binaries, and tests both role-size programs and metrics. Child compilation/test
processes use one allowed CPU, AS4GiB, file16MiB, CPU120s and wall150s caps.
The synthetic fixture is separate from the benchmark constructor. Its endpoint
IDs are compared with float64 exhaustive references; common queries must yield
identical counts/IDs through both programs. Wrong role sizes must be rejected.

The historical binaries were compiled with GCC9.4.0. A new compiler or CPU can
produce different binary bytes. Passing the synthetic tests establishes the
tested interface, not original binary identity or full-panel equivalence.
Original-data profiles must additionally match every frozen CSV, without
fallback, repinning or excluding targets.

## Original-data role command

Requires the preceding input and truth adapters, their completed new receipts,
and eight **saved graphs with the exact registered hashes** for the selected
dataset. No index download or reconstruction is performed by this command.
Graph preparation is the next unresolved upstream stage; this dependency is
not satisfied by synthetic graphs or a generic hnswlib version number.

```sh
python3.11 artifact/original_execution/portable_profiles/run_profiles.py \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --truth-adapter artifact/original_execution/portable_truth \
  --prepared /path/to/new-prepared-inputs --truth /path/to/new-sift-truth \
  --graphs /path/to/registered-indexes --native-build /path/to/new-native-build \
  --dataset sift --role target_evaluation --output /path/to/new-role-profiles \
  --outstanding-growth-bytes 2147483648 --authorize-native-profiles
```

Index filenames are `{dataset}_{build}.bin`, for example
`sift_seed13_random.bin`. Roles are source_design, target_selection,
target_certification and target_evaluation; Arxiv uses its own truth and graph
inputs. Each role runs all eight graphs in registered order. Complete records
are retained on failure, and dependent stages must stop. No default-all or
automatic retry mode is supplied.

Original resource gates remain: CPU2, one library thread, AS8GiB,256MiB per-file,
CPU14400s per process, wall3600s per graph, expectedRSS4GiB,2GiB stage growth,
200GiB projected disk reserve and128GiB outstanding project growth. The budget
argument must include other outstanding stages. Child timeouts are enforced;
snapshots are not continuous RSS or aggregate-storage quotas.

The wrapper checks new preparation/truth receipts, all truth hashes, every
ordered response row and output hash. Timing is operational process time and
does not replace historical API timings or acquisition costs. The existing
cache entry still consumes its frozen profile NPZ interface, not these CSVs:
CSV-to-array audit/materialization remains a separate integration step.

No original graph build, profile, old equivalence audit or timing run is part
of this delivery. See CI for the actual new synthetic build/test outcome.
