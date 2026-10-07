# Bounded native CI controls (not the G1 paper experiment)

`run_native_controls.py` is a separate entry; it never accepts a dataset path or runs the old R0 auditor. Every mode creates only a fixed seeded 256×32 base and eight self-queries, uses a nontrivial permutation, budgets 10/32/128, and two metrics. It performs 48 query-budget cells per implementation. It does not call the full 100K unit or G1 bootstrap.

## Environment and resource declaration

- Linux x86-64, Python 3.11, NumPy1.26.4/SciPy1.13.1/h5py3.11.0. Use the package requirements. Faiss requires its own exact 1.15.0 wheel; do not reuse a 1.8.0 environment.
- At least 8 GiB free before execution; new exclusive output; at most one available CPU and one numerical-library thread. Synthetic CI deliberately uses the lowest available CPU rather than requiring historical CPU2.
- Effective inherited stricter limits are retained: 12 GiB address space, 1 GiB per file, no core dumps; CPU limit 300 seconds for Faiss/HNSW or 2,100 seconds for the Rust build/control family. Set CI job timeout to 5 minutes for Faiss/HNSW and 35 minutes for Rust. Native child calls separately timeout at 120 seconds, compilation at 1,800 seconds. Total wall/growth checks are postconditions; the CI job timeout is the outer wall bound. Aggregate output cap is 6 GiB, not a kernel aggregate quota.
- Rust mode uses **rustc1.97.1 and cargo1.97.1 with exact recorded version strings**, plus rust-src (source toolchain file), C/C++ linker and standard Linux build tools. Set `CARGO_BUILD_JOBS=1`; the entry also sets it. The source archive, four installed patch SHA values, Cargo.lock before and after `--locked` build, new binary and actual child exits are retained.
- `diskann_dependency_versions.json` lists every package/version/source/checksum directly from the archived root Cargo.lock. This is a dependency declaration, not a claim that all dependency archives have already been supplied offline. Missing exact toolchain or dependency acquisition is a hard failure, not a reason to use a current DiskANN checkout.

## CI invocation

Let `G1` be this directory and use absolute newly allocated output paths. Install package requirements first. For Faiss:

```sh
python -m pip install --no-deps --require-hashes -r "$G1/requirements-faiss.txt"
python "$G1/run_native_controls.py" faiss --output "$NEW_FAISS_CONTROL" --authorize-synthetic-native
```

The checks bind all 33 wheel payload files and loaded extension; independently verify returned raw-ID order and score values in float64, recall, and positive native NDC. The highest action must retrieve each exact self-query ID first. This does not assert universal exact recall for all budgets.

For HNSW, reuse the **new source compile** already produced by the sibling transfer100K job, not an arbitrary executable:

```sh
python "$G1/run_native_controls.py" hnswlib --transfer-adapter "$TRANSFER" \
  --native-build "$NEW_TRANSFER_BUILD" --native-build-sha256 "$BUILD_COMPLETED_SHA256" \
  --output "$NEW_HNSW_CONTROL" --authorize-synthetic-native
```

The original GateA benchmark checks traced ordered IDs against upstream `searchKnn` on each tiny cell. This wrapper additionally checks ID range/order and native recall against independent float64 identities, complete cell coverage, and positive reported counts. It does not claim an independent exact-distance-counter audit from the positive-count check alone.

For DiskANN, download only `native_inputs.diskann.url` from config.json and verify its archive SHA (the entry rechecks it). Install the exact declared toolchain; then:

```sh
python "$G1/run_native_controls.py" vamana --source-archive "$PINNED_G1_ARCHIVE" \
  --output "$NEW_VAMANA_CONTROL" --authorize-synthetic-native
```

This builds the four-patch G1 integration-test implementation before running L2 and cosine controls. Checks cover 256 base nodes plus the frozen start, degree/range/duplicate edges, ordered raw-ID mapping, per-query positive comparison counts, equality of their sum with both emitted aggregate counters, and independent/native recall agreement. No old R0 file, old array, old graph or registered G1 unit is executed. A new build is not historical final-binary attestation.

Upload `completed.json` and failure/build logs as CI evidence. A mode is native-qualified only when its actual job exits successfully and emits `SYNTHETIC_NATIVE_CONTROLS_PASS_NOT_PAPER_REPRODUCTION`. Definitions or skipped native jobs do not constitute native PASS. Local Windows tests exercise helper logic only.
