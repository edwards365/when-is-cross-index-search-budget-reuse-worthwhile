# Native Vamana and DARTH future execution

These are **new-output, opt-in execution interfaces**, not a replay of sealed
workers. Packaging, source verification and tiny synthetic controls do not run
any original dataset. Existing successful scientific runs must not be resumed.

## Dependencies and source provenance

Use Linux x86-64, Python 3.11 and NumPy 1.26.4; install CMake, a C++17 compiler,
make, OpenMP, BLAS/LAPACK development packages (`build-essential cmake
libopenblas-dev liblapack-dev libomp-dev pkg-config`). Rust execution requires
the Rust 1.97.1 toolchain whose cargo/rustc/rustdoc payload hashes are in config.
Training has its separate `requirements-training.txt`; the pinned LightGBM
wheel's 12 installed payloads are checked before training. Its library is **not**
substituted for DARTH's C++ library.

Archives are not part of the public payload. Retrieve only pinned public source:

```sh
python bootstrap_sources.py --download-public-sources
python run_native.py check
python -m unittest -v test_native.py
```

DiskANN commit `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475` plus the two original
instrumentation files reconstructs all 1,343 original source files and the
historical tree digest. Only then are the ordered-ID output patches applied.
Cargo.lock remains fixed; online locked fetch and offline build are separate.
The source archive retains its licenses and notices.

DARTH selected source is from commit
`0d9bafcf31d1d79668bc71139fe93fa5e70b5185`, with upstream LICENSE retained.
Three hardcoded LightGBM paths become mandatory CMake parameters. The IP variant
additionally uses the frozen two native IP fixes and standalone IP entry.
The legacy-L2 variant uses the unchanged upstream scientific source.
LightGBM's pinned 4.5.0 source distribution includes its licenses/dependencies.
Both libraries and **all** DARTH objects are built anew. This establishes a
separate full-source build, not bitwise identity with the historical executable;
the historical 315 reused object/source pairings remain unattested.

## Build-only CI (no scientific datasets)

```sh
python ci_native.py --component darth --output /new/ci-darth
python ci_native.py --component vamana --toolchain /rust/1.97.1 --output /new/ci-vamana
```

Each invocation uses one available CPU, one library thread, 8 GiB address space,
2 GiB per output file and a 90-minute wall/CPU ceiling; it requires 12 GiB free.
DARTH compiles LightGBM and both source variants, exercises signed-IP synthetic
controls and the authored LightGBM C-API transport model. The latter deliberately
checks native/reordered feature positions; it is not a scientific training run.
Vamana verifies source identity, fetches locked crates, compiles, and requires
both newly authored ordered-ID unit controls. CI has its **own build-only resource
contract**, not a bypass of production preflight. Local Windows validation does
not claim these Linux compiles succeeded; see `validation.json` and CI receipts.

## Explicit production phases

Every command below also requires `--authorize-new-execution`, a fresh `--output`,
and `--outstanding-growth-bytes` covering all outstanding project work. Linux
Python 3.11 preflight requires >=160 GiB available memory and >=200 GiB projected
free disk with aggregate outstanding growth <=128 GiB. Per-phase output cap is
32 GiB, address space 24 GiB, file size 8 GiB, wall/CPU 4 hours. Source/search
uses CPU 2; Arxiv model training alone uses CPUs 4–11 and n_jobs=8 (not eight OS
threads). SIFT training retains n_jobs=1 on CPU 2. No output is overwritten.

| Phase | Required inputs | Output / next step |
|---|---|---|
| `source` | downloaded DiskANN source | fully checked and patched source |
| `fetch` | `--prior source --toolchain ...` | isolated locked crate cache |
| `build` | `--prior fetch --toolchain ...` | new native binary and two controls |
| `prepare` source | `--dataset sift/arxiv --role source_design --bundle ... --truth ...` | frozen-order base/query/truth native files |
| `prepare` held-out | dataset, one target role, `--source-prepared ... --qbin ... --truth ...` | disjoint role files paired with base IDs |
| `source-search` | `--native-build build --prepared source-input` | one saved Vamana graph, source response |
| `heldout-search` | build, role input, `--graph source-search` | same graph/binary, fixed L64 search |
| `lightgbm-build` | downloaded LightGBM source | new installed C++ library |
| `darth-build` | `--prior lightgbm-build --flavor arxiv-ip/legacy-l2` | full-source DARTH build and controls |
| `darth-source` | `--native-build darth-build --prepared source-input` | graph and source observations |
| `darth-train` | build, `--prior darth-source` | 100-tree seed42 native-order model |
| `darth-heldout` | build, role input, `--graph darth-source --model darth-train` | same graph/model, frozen predictor action |

Repeat only the held-out phase for selection500, certification500 and evaluation1000
using their distinct registered inputs. Source is500. SIFT base is997420×128,
Arxiv1342143×768. Metrics are raw squared-L2 and genuine negative-dot/IP respectively;
no normalization or distance relabeling occurs. Vamana degree32/Lbuild64/alpha1.2,
k10/L64/reps1/task1; DARTH M16/efC100/efS200, source observations every5,
held-out target.95 and prediction intervals1000/100 remain frozen.

Config binds source-bundle/truth and each role query/truth hash. These are input
dependencies, not silently regenerated substitutes. Upstream bundle generation
and raw dataset acquisition belong to the separate shared input family.
Model training checks exact native feature order, tree count and finite structure.
Vamana exports ordered IDs and independently checks recall. Genuine-IP DARTH also
checks all exported scores against raw-vector float64 dot products. SIFT's legacy
DARTH executable supplies self-reported recall only; no independent returned-ID
audit is asserted. Native counters are not independently exact-distance counters,
and operational timing is not a benchmark rerun.

## Separate 100K Recall95 member-refresh family

Install the Faiss1.8.0.post1 wheel identified by `refresh_native_lock.json`,
NumPy1.26.4, h5py3.11.0 and SciPy1.14.1. This environment is distinct from
transfer100K's corrected Faiss1.15 replay. Read-only package inspection found
all frozen Faiss payload hashes match the historical DARTH Python environment.
The automatically selected historical SIMD path is not independently attested.

Use the same production opt-in/output/resource arguments above:

1. `refresh-prepare --refresh-dataset sift100k/arxiv_nomic_100k --hdf5 ...`
   reads only the pinned HDF5 `train` ranges. It constructs old and refreshed
   100K snapshots, three disjoint roles (500/500/1000), top100 native-L2 truths,
   and all ten insertion permutations. Every common query/truth file, permuted
   base and mapped truth must match the recovered historical input manifest.
2. `refresh-build --prepared ... --snapshot old/target_refresh05 --seed ...`
   builds one new Faiss HNSW M16/efC100 graph using the pinned Python payload.
3. `refresh-replay --prepared ... --graph ... --native-build ...`
   uses the new **legacy-l2** full-source DARTH build, one saved graph, three
   roles and ef10/20/40/80/120/160/200, no early stopping. Repeat for all40
   dataset/snapshot/seed cells; no completed response is skipped or overwritten.
4. `refresh-analyze --units <40 fresh response directories>` validates complete
   coverage and a common native build before the original function-only
   analysis computes target checks, four methods, bootstrap5000/seed991, LOBO,
   delete-largest and source-profile cost summaries into a new derived directory.

At 5%, the executed deletion seed is1491 (=991+500), matching the original
member-generation code and exact deleted-ID hash; the later preregistration's
short phrase “seed991 subset” is not used to change frozen membership. Arxiv
vectors are already normalized in the pinned input, but both native graph and
new role truth use squared L2 as actually executed. There is no raw-IP relabeling.
This interface covers the Recall95 primary5% family, not the older Recall90
1%/10% sensitivity runs. New graphs/executables are separately identified; it
does not claim historical graph or timing bitwise identity. Synthetic tests
exercise membership/permutation and source-pool logic; full40-cell science is
not executed during packaging or CI. No old science/auditor, old PID, saved
result or cached model is rerun here.
