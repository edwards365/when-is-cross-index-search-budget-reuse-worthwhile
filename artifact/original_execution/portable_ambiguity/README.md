# G1: 100K cross-index ambiguity — new execution interface

This package covers the separate G1 diagnostic family: three datasets, three implementations, three construction labels and three insertion orders (81 registered units; 9 labels per dataset/implementation). It does not run or repair the later native-million-vector chain. Local validation used synthetic inputs only; no paper experiment was rerun.

## Preserved conditions

- Frozen train-only membership: 250 design and 750 confirm queries, separate from the first 100,000 base vectors. SIFT uses unnormalized L2; GloVe/Arxiv use the original float32 normalization without epsilon clamping. Exact ground truth preserves the original float64 squared-L2 routine for all three datasets. This is not a new metric substitution.
- Budget grid: 10, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512. The legacy analysis uses recall threshold 0.9 and the original 1024 marker for no finite stable tail inside this grid. Its historical endpoint clipping is preserved as a diagnostic computation, not a claim that the endpoint is safe.
- Seeds/labels 43, 59, 71 and orders random, natural_source_order, cluster_block_order. The three exact cluster-order payloads are included. Random insertion order uses seed 20260915. HNSW uses M16/efConstruction100.
- G1 Vamana is DiskANN commit `158126e64129d3c39f9df02199c2dcc06d4f9e7f`, diskann-inmem 0.56.0 integration-test, the four included patches, R32/alpha1.2/Lbuild50, and cosine for normalized datasets. Its three seed labels were **not** passed as RNG seeds by the original driver; they remain repetition labels. They must not be represented as three independently randomized constructions.
- Faiss uses the pinned 1.15.0 public wheel and its 33 payload hashes, not the separate 1.8.0 recovery environment. The public payload lock matches the inspected installation; it does not retrospectively attest the historical CPU-dispatch path.

## Dependencies and stages

Use Linux x86-64, Python 3.11 without optimization, and `requirements.txt`. Install Faiss into a dedicated environment with `python -m pip install --no-deps --require-hashes -r requirements-faiss.txt`. Install the three Python requirements first. Every native library payload and the actually loaded Faiss extension are checked before Faiss execution.

All stage commands require a new, nonexistent output directory, the sibling `portable_fresh_inputs` adapter, `--authorize-new-stage`, and an explicit outstanding project growth budget. They enforce CPU2, library threads1, a 200 GiB projected disk floor, 128 GiB aggregate outstanding-growth ceiling, 16 GiB address space, 4 GiB per-file cap and four-hour stage wall/CPU cap. The 8 GiB aggregate stage-output limit is a postcondition, not a kernel aggregate quota. Preflight checks current RAM/RSS/iowait. A failure is retained and must stop dependent execution; do not overwrite/retry a failed key.

Set shell variables to newly allocated paths; the following are templates, not permission to run paper workloads automatically:

```sh
python run_ambiguity.py prepare --dataset sift_100k --source "$RAW_HDF5" \
  --output "$NEW_INPUTS" --input-adapter ../portable_fresh_inputs \
  --outstanding-growth-bytes 8589934592 --authorize-new-stage
```

`prepare` hashes the supplied raw HDF5 against membership.json before reading **only** train. It emits base, queries, truth, source IDs and the three orders. All four frozen query/truth serialization hashes must match. No automatic source download or formal test access occurs.

For HNSW, first use the sibling `portable_transfer_100k/run_transfer.py compile` entry and preserve its completion receipt. This package verifies the benchmark C++ source, include pins, compile receipt and new binary. For G1 Vamana, obtain the exact archive from `config.json → native_inputs.diskann.url` and validate its declared SHA:

```sh
python run_ambiguity.py compile-vamana --source-archive "$PINNED_DISKANN_ARCHIVE" \
  --output "$NEW_BUILD" --input-adapter ../portable_fresh_inputs \
  --outstanding-growth-bytes 8589934592 --authorize-new-stage
```

This safely extracts the source, verifies Cargo.lock, installs exactly four source patches, verifies the recorded Rust 1.97.1 toolchain and executes `cargo build --locked --release -p diskann-inmem --features integration-test --bin integration-test`. Cargo dependencies are acquired in the new output's cargo-home using the pinned lock; the package does not supply every dependency archive offline. The pre-R0 binary hash in diskann_provenance.json is historical provenance, **not** the expected patched binary hash. No final patched historical source/binary equivalence is claimed.

Each native unit builds its one graph and then replays all 12 budgets against 1,000 queries, preserving the original combined build/search driver boundary:

```sh
python run_ambiguity.py unit --implementation faiss --dataset sift_100k \
  --seed 43 --history random --prepared "$NEW_INPUTS" \
  --prepared-sha256 "$INPUT_COMPLETED_SHA256" --output "$NEW_UNIT" \
  --input-adapter ../portable_fresh_inputs \
  --outstanding-growth-bytes 8589934592 --authorize-new-stage
```

For HNSW add `--transfer-adapter ../portable_transfer_100k --native-build "$NEW_BUILD" --native-build-sha256 "$BUILD_COMPLETED_SHA256"`. For Vamana add the two native-build arguments referring to its compile-vamana receipt. No arbitrary binary is accepted. A standalone reload/replay stage for Vamana is not provided: the original integration-test unit combines construction and search, so calling a new unit is a new construction, not a replay of a saved Vamana graph.

`unit` retains native output, independently reconstructs ID recall, checks all 12,000 query-budget identities, and compares the graph hash with exactly one registered historical record. A mismatch is a failure, not silently replaced evidence. Exact graph matching under a new compiler/runtime is not presumed. Distance counters retain implementation-specific original meanings.

Create a JSON array of 81 records, each `{"directory": "new-unit-directory", "completed_sha256": "receipt SHA256"}`. Then:

```sh
python run_ambiguity.py analyze --unit-manifest "$NEW_UNIT_MANIFEST" \
  --output "$NEW_ANALYSIS" --input-adapter ../portable_fresh_inputs \
  --outstanding-growth-bytes 8589934592 --authorize-new-stage
```

The adapter requires every registered dataset/implementation/seed/order exactly once and verifies each receipt/payload before invoking the guarded frozen G1 analysis. It produces effort, headroom, rank, transfer and index-blindness CSVs plus a decision JSON and 5,000-draw query bootstrap. The historical optional Parquet branch remains optional and writes NOT_ESTIMABLE if its dependencies are absent. This is the original G1 analysis, **not** the later same-condition summary-cost decomposition.

## Validation and limits

For the separate bounded Linux-native qualification entries and complete dependency-version map, see `NATIVE_CI.md`. A definition is not a successful native run; each implementation requires its actual CI completion receipt.

`python -m unittest discover -s . -p test_ambiguity.py -v` checks source pins, all 81 identities, split membership, native configuration, safe archive extraction, parent receipt corruption, 12,000-row synthetic schema/recall and no top-level archived-driver execution. These checks do not certify full data regeneration, native builds, original graph reproduction, bootstrap results or formal timing. Those stages require the declared Linux environment, source data and resources. Public source archives/URLs and locks are delivered; native-build success and complete offline Cargo availability are not claimed. Original scripts and evidence remain unchanged.
