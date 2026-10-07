# Official Ada-ef: portable source-to-held-out execution

This is the **official Arxiv supplementary family**, not the separate metric-port, fresh-query, G1, DARTH, or Vamana experiments. It preserves the original official `EfAdapter`, `Sketch`, `ApproximatedScoreCalculator`, cosine-distance estimator (`cd`) and `adaptiveSearchKnn`. The project runner `e2_adaef_native.cpp` is copied unchanged. No sklearn model or replacement learned feature set is used by this C++ path.

The public upstream archive is pinned to commit `ed463f9993868f7ecc7c103920644e7f94abb377`, SHA `db439a8d2f80e387d7e81ceba7603d775c76533bc0967fe65a324f16eca39c76`; its 26 delivered files retain their original license and contents. The archive URL/file hashes are in `official_source_lock.json`. Archived project launchers are not imported or executed.

## Scientific boundaries

- Original float32 Arxiv vectors, **no new normalization**, native inner product, 1,342,143 retained base vectors, 768 dimensions, raw-ID graph labels. Four disjoint roles: source500, selection500, certification500, evaluation1000.
- Eight saved official graphs/adapters: seeds13/83/197/2029 × random/norm-ascending. Random order uses `RandomState(seed)`; norm order uses float64 squared norms with raw-ID ties. M16, efConstruction500, k10, target.95, quantile.001, statistics1025 and efUpperBound/endpoint2400 remain fixed.
- These are **not** the efConstruction100 E1a graphs or the 1,337,142-member fresh-query base. Only the unchanged E1a truth computation blocks and matching frozen truth/qbin identities are reused.
- Source graph construction and adapter training remain one `build-design` native call. It saves both artifacts before downstream use. This interface does not pretend those two internal operations were separately measured or independently replayable.
- Selection compares transferred, target-native and endpoint with delta.05/3; eligible arms minimize mean native distance calls, ties in that order. The observed historical selection is endpoint for all56 directions, without selection fallback. This reproduction interface checks that outcome and stops on divergence rather than inventing a different certification protocol.
- Certification uses eight endpoint response units shared across56 decisions, delta.05; the diagnostic adaptive columns do not become new candidates. Evaluation produces all56 transferred plus8 target-native responses, with endpoint reconciliation; it cannot select or retune.

## Installation and new native qualification

Use Linux x86-64 Python3.11 and `requirements.txt`. For exact truth, install the exact Faiss wheel in `../portable_truth/requirements.txt`. For independent endpoint checks, build hnswlib0.8.0 from the source/hash and build requirements in `../portable_graphs`; do not install an arbitrary hnswlib wheel.

Compilation requires a C++17 compiler, OpenMP, HDF5 C++ development wrapper `h5c++`, Eigen and Boost headers. On a CI Ubuntu host, `g++ libhdf5-dev libeigen3-dev libboost-dev` supply these categories. This is a **new build**: upstream CMake mentions Eigen3.4.0/Boost1.87.0, but the historical runtime's complete dependency identity was not attested. We do not claim that current distribution packages reproduce that toolchain. Instead declare the installed version-header hashes before compiling, record every compiler-resolved header and HDF5 wrapper input, then enforce historical graph/adapter bytes at full-data stages. A mismatch stops; no repinning or alternative library retry is authorized.

```sh
python prepare_dependencies.py --output /path/to/NEW-dependencies.json
python run_native_controls.py --output /path/to/NEW-tiny-native \
  --dependencies /path/to/NEW-dependencies.json \
  --graph-adapter ../portable_graphs --authorize-synthetic-only
```

The helper records/checks `/usr/include/eigen3/Eigen/src/Core/util/Macros.h` and `/usr/include/boost/version.hpp`, including versions; it installs nothing and refuses an existing output. Nonstandard include roots are explicit options.

Native CI compiles the unchanged production runner, then a clearly separate test-only derivative (only base/dimension/source-count checks become2048/16/32). Official algorithm parameters and headers are unchanged. It trains/reloads an actual adapter, runs adaptive and endpoint search, and checks endpoint ordered IDs against independent source-built hnswlib plus both recalls against synthetic truth. It uses one available CPU/library thread,8GiB AS,256MiB/file,900CPU seconds,2GiB free and512MiB output postcap; set an outer CI job timeout of15minutes. Each native child has a bounded wait. This is not a paper data run, full adapter equivalence result, full-panel reproduction or timing benchmark. Only an actual successful receipt establishes this native test as passed.

## New full-data stage interface

Every invocation needs an explicit JSON request, new output path and project resources:

```sh
python run_adaef.py --request request.json --output /path/to/NEW-stage \
  --input-adapter ../portable_fresh_inputs \
  --outstanding-growth-bytes 137438953472 --authorize-new-stage
```

All parent references have the form `{"directory":"/path/to/new-parent","sha256":"SHA256 of completed.json"}`. Receipts bind stage, configuration, entry source and every output file. Failed parents are rejected. Outputs are not overwritable and failed evidence is retained. The following examples are request structures, not automatic launch commands.

### 1. Base and compilation

```json
{"stage":"base","source":"/path/to/arxiv-nomic-768-normalized.hdf5"}
```

It validates the frozen raw HDF5 SHA, reads only `train`, removes all2,500 held-out IDs and writes the effective base/raw IDs/insertion orders. It does not open query outcomes.

For compile, use the `NEW-dependencies.json` contents plus `"stage":"compile"`. This invokes the unchanged runner with `h5c++`, explicit official/Eigen/Boost includes and single-library-thread runtime configuration. Compilation records actual exit, source/binary SHA, compiler version, HDF5 wrapper and resolved dependency hashes; no historical binary receipt is manufactured.

### 2. Role-isolated input and exact truth

```json
{"stage":"role-input","phase":"source","base":{"directory":"NEW-base","sha256":"..."},
 "source":"/path/to/arxiv-nomic-768-normalized.hdf5","truth_adapter":"../portable_truth"}
```

For later phases use `selection`, `certification`, or `evaluation`, and add `prior` referring respectively to the source-panel, selection-lock or certification-lock. **The lock is checked before role vectors/truth are opened.** Each role produces a matching frozen qbin and NPZ. Source truth uses its original uncompressed NPZ operation; held-out roles retain original compressed NPZ operations, exact-search batching and16Faiss threads. A complete array hash mismatch stops rather than changing the truth or dispatch.

If matching sealed truth is already available, use `sealed_truth` instead of `truth_adapter`; it is imported only after validating the expected SHA. This is the original protocol's sealed-input route. Regeneration is a separate new-input operation, not a rerun of its historical source bundle builder.

`role.hdf5` exposes only that role and external links to the newly prepared base/order file. Its base parent is revalidated before native use. It intentionally does not reproduce the old all-role HDF5 container byte hash; the underlying frozen query/truth IDs/bits, raw base and orders are preserved and independently bound. Keep the new base directory available; moving it requires a new declared input package, not editing an existing receipt.

### 3. Eight source states, then one complete source lock

```json
{"stage":"source","key":"seed13_random","role_input":{"directory":"NEW-source-input","sha256":"..."},
 "compile":{"directory":"NEW-build","sha256":"..."},"graph_adapter":"../portable_graphs"}
```

Execute each of the eight registered keys once at a distinct output path. Every source call runs build-design and source-design response with actual waits, verifies both recalls and an independent reloaded-index endpoint, enforces the source endpoint CP gate, and requires the saved index and adapter SHA to match their frozen values. Unsafe raw-adaptive results are retained; they are not a tuning signal.

```json
{"stage":"source-panel","sources":[{"directory":"NEW-source-1","sha256":"..."}]}
```

Replace the illustrative one reference with all eight distinct source receipts. The panel refuses partial or duplicate coverage. No selection role is available before this complete lock.

### 4. Selection, certification and evaluation

After preparing the phase-specific role input, invoke one response per registered pair:

```json
{"stage":"response","phase":"selection","source_key":"seed13_random","target_key":"seed83_random",
 "prior":{"directory":"NEW-source-panel","sha256":"..."},
 "source_panel":{"directory":"NEW-source-panel","sha256":"..."},
 "role_input":{"directory":"NEW-selection-input","sha256":"..."},"graph_adapter":"../portable_graphs"}
```

Selection and evaluation need all64 source/target combinations, including8 self/native pairs. Certification needs8 self/native diagnostic calls only, because the frozen selected arm is endpoint. Evaluation `prior` must be the complete certification lock; certification `prior` must be the selection lock. Each response verifies the saved target/source state and independent endpoint ordered IDs, checks raw/endpoint recall against that role's frozen truth, and records native counts without claiming they were independently reconstructed.

```json
{"stage":"selection-lock","phase":"selection","prior":{"directory":"NEW-source-panel","sha256":"..."},
 "responses":[{"directory":"NEW-response-1","sha256":"..."}]}
```

Use every required response reference, not just the example. Replace stage/phase/prior with `certification-lock`/`certification`/selection-lock or `evaluation-lock`/`evaluation`/certification-lock as appropriate. Locks reconcile exact per-query endpoint IDs/recall/counts across arms, keep all56 directions and8targets, and reject drift from the frozen selected/deployed decisions.

Each evaluation unit writes `response.csv`; the final lock records all64 response references. These CSVs retain the original native schema but are **not required to match historical CSV hashes**: their own new hashes, recalls and endpoint reconciliation are recorded. The historical analysis identifier is `scripts/icde2027_1m/analyze_e2_adaef_arxiv_crossed_v1.py` (SHA `d5504b048aceb1e98abb94c79f89cbfe98a44b61fa4f25aeaa7aa2c22d4181e9`), registered in `manifests/icde2027_1m/e2_adaef_arxiv_crossed_analysis_v1.json`. Those are provenance identifiers, not a portable command for importing new outputs. This package does not supply a new-output crossed-bootstrap importer and does **not** run the historical analyzer or E9 replay. Source/response production and reconstruction of saved paper statistics remain distinct delivery levels.

## Resource and provenance limits

Full-data stages preserve fresh RAM/RSS/iowait preflight,160GiB available-RAM gate,200GiB projected disk floor and128GiB total outstanding growth ceiling. The declared per-stage bound is24GiB AS/expected16GiB RSS/8GiB per file/16GiB output growth/four-hour wall+CPU. Native build/search uses CPU2/library1. Exact-truth generation uses CPUs4–19 and its original16Faiss threads. Address space is not RSS; output cap is a postcondition, not a filesystem quota. Other project growth must be included in the outstanding-growth declaration. Existing stricter inherited limits are not raised.

**Historical caveats remain unchanged:** source `seed13_random` has `EXIT_STATUS_UNOBSERVED`; a new successful process cannot repair it retrospectively. Historical `adapter_seconds` covers only adapter construction, excludes estimator initialization and serialization/reload, and is not complete acquisition time. Full acquisition remains MISSING and E8 remains NOT_ESTIMABLE. New compilation/operational waits do not turn those into benchmark or lifecycle measurements.

Remaining full-data prerequisites are the original raw HDF5, declared Linux/native dependencies and sufficient resources. Native CI and strict full-data identity gates are different checks: a successful tiny test cannot establish full graph/adapter reproduction or independent-host scientific reproduction. No full experiment, original saved replay, source data export, model tuning or old worker was executed while preparing this package.
