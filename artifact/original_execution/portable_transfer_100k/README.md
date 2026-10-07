# Transfer at 100K: original execution entries

Two distinct protocols are retained. This adapter does not collapse them into a
shared grid, normalization rule, query set, counter, or native dependency.
Packaging and tests have not rerun either original scientific panel.

| Component | E4 HNSW | Corrected Faiss-100K |
|---|---|---|
| Base | First 100,000 train vectors | First 100,000 train vectors |
| Arxiv | Unit normalization, native inner product; original float32 L2 truth on normalized vectors | Raw stored vectors, L2 for native search and exact truth |
| Source implementation | `e4_run_matrix.py` and `hnsw_gate_a_benchmark.cpp` | `phase1_1_runner.py:faiss100k`, corrected roles/replay from `graph_anns_iclr_phase1_1_repair/run_all.py` |
| Builds | Eight seeds times random/LID-ascending/LID-descending | 24 insertion-permutation seeds |
| Grid | 10, 20, 40, 80, 120, 200 | 16, 32, 64, 128, 256, 512 |
| Queries | Frozen 1,000 confirmatory train IDs; paper keeps local IDs 0–749, latency round 0 | Frozen 750 train IDs, excluded base and historical query-role IDs |
| Native work | Original tracer and upstream-search agreement check | Per-query NDC remains `NOT_ESTIMABLE_BATCH_CUMULATIVE` |

The HNSW paper filter is exactly the historical repaired `load_h` rule. It does
not take the last 750 queries or invent a new random subset. Faiss corrected
replay does not export its historical cumulative batch counter as per-query NDC.
It uses all 24 registered graph records. The recovered 100K Faiss registries
contain 24 distinct graph hashes per dataset; this is not the repeated-identity
supplement from a different panel.

## Dependencies and checks

Use Linux x86-64, Python 3.11, a C++17 compiler, and an isolated environment:

```sh
python -m pip install -r requirements.txt
python -m pip install --no-deps -r requirements-faiss-native.txt
python run_transfer.py check
python -m unittest -v test_transfer
```

The 1.15.0 public wheel archive and 33 installed payload files are SHA-256
bound. Before import, the adapter verifies the distribution, every recorded
payload, and the import origin; afterwards it records the loaded native module.
The payload matches the inspected original installation. Historical SIMD
dispatch is not attested. HNSW headers are pinned to upstream commit
`3f3429661187e4c24a490a0f148fc6bc89042b3d`; the tracer and runner are frozen
project sources. The explicit `-O3` compilation is a new build recipe, not an
attestation of the old executable or a bitwise timing reproduction.

`check` reads only code, configuration, role IDs, and small order files. Tests
use synthetic vectors only. Linux native tests compile the original HNSW runner
on tiny inputs and compare its endpoint IDs with independent truth. The Faiss
test checks pinned import, save/reload, exact ranking, and endpoint IDs on tiny
inputs. Windows skips these two native tests and must not report them as passed.

## Explicit new-execution phases

Every production phase requires `--authorize-new-execution`, a new absent output
directory, and `--outstanding-growth-bytes` covering all remaining project
growth, not just the current phase. Existing successful or failed output roots
cannot be reused. These commands describe an independently authorized future
execution; they are not instructions to rerun sealed experiments during delivery.

Resource preflight retains CPU 2, one library thread, at least 160 GiB available
RAM, a 200 GiB projected-free disk floor and a 128 GiB project growth ceiling.
The new per-phase caps are 16 GiB address space, 4 GiB per file, 16 GiB output
growth, and 14,400 seconds CPU/wall. Output growth is checked, not a kernel disk
quota. RAM and I/O checks are snapshots. Retaining new native index and trace
files differs from historical cleanup but does not alter search actions.

HNSW example (replace paths and budget with actual authorized values):

```sh
python run_transfer.py prepare --dataset sift_100k --source /data/sift-128-euclidean.hdf5 --lid-order sift_100k_order.npy --output /data/new-transfer/sift-input --outstanding-growth-bytes 17179869184 --authorize-new-execution
python run_transfer.py compile --output /data/new-transfer/hnsw-build --outstanding-growth-bytes 17179869184 --authorize-new-execution
python run_transfer.py unit --dataset sift_100k --seed 83 --history random --prepared /data/new-transfer/sift-input --native-build /data/new-transfer/hnsw-build --output /data/new-transfer/sift-83-random --outstanding-growth-bytes 17179869184 --authorize-new-execution
```

Each unit performs one native build and all six actions, with 100 warmup queries
and five timing rounds as in the original source. It preserves all native output
and exports `paper_rows.csv`. Run each of the 24 seed/order units once; then
`analyze --dataset sift_100k --units <all 24 unit directories>` with the same
explicit output/resource flags invokes the unchanged extracted historical
`action_summary` at hit threshold 10. Arxiv has its own preparation and 24 units.
All newly measured timings retain a new-run identity, not historical values.

Corrected Faiss example:

```sh
python run_transfer.py faiss-prepare --dataset sift_100k --source /data/sift-128-euclidean.hdf5 --output /data/new-transfer/faiss-sift-input --outstanding-growth-bytes 17179869184 --authorize-new-execution
python run_transfer.py faiss-build --dataset sift_100k --build-number 0 --prepared /data/new-transfer/faiss-sift-input --output /data/new-transfer/faiss-sift-build00 --outstanding-growth-bytes 17179869184 --authorize-new-execution
python run_transfer.py faiss-replay --dataset sift_100k --prepared /data/new-transfer/faiss-sift-input --graph /data/new-transfer/faiss-sift-build00 --output /data/new-transfer/faiss-sift-replay00 --outstanding-growth-bytes 17179869184 --authorize-new-execution
```

Preparation verifies the raw HDF5 hash, reproduces the frozen role-ID ledger and
FlatL2 truth. Build uses the original IDMap2/HNSW construction and must match the
frozen graph SHA before replay can proceed; a mismatch leaves failure evidence
and stops. It never substitutes an index that merely has the same parameters.
`faiss-analyze --dataset sift_100k --units <all 24 replay directories>` uses the
same explicit output/resource flags and the original extracted summary and
leave-one-build-out functions, for hit thresholds 8, 9 and 10. Each phase checks
the preceding receipt, config identity, output hashes and dataset pairing.

## Evidence limits

`config.json` binds the original source/protocol, raw input identities, both LID
orders, corrected role records, 48 Faiss graph identities, and packaged source.
Small orders and IDs contain no raw vectors. No source script with top-level
execution is imported; extraction is AST based. Full-panel equivalence remains
unexecuted here. Full original vectors/graphs are not bundled. A future graph
identity mismatch must be diagnosed, not bypassed by changing the pin or seed.
Public saved-response analysis remains the route to reproducing the paper now
without rerunning its costly scientific collection.
