# 100K recovery: S9-3 prospective fixed-slack and S9-4 paired arms

This entry provides new, separately receipted executions of input preparation,
graph construction, role responses, decision locking, evaluation and timing.
It preserves the original six budgets (16–512), eight permutation seeds per
dataset, and three disjoint 500-query roles. S9-4 uses the same sixteen S9-3 graphs.
Do not rebuild them for S9-4.

## Metric and evidence identity

Both physical indexes are **Faiss METRIC_L2**, M16/efConstruction100, one thread.
SIFT truth is L2. The historical Arxiv input path normalizes base/query float32
vectors and computes IP truth; the search index remains L2. This historical
normalized experiment is distinct from the later genuine native-IP experiment.
No metric conversion, new tie handling, or normalization change is introduced.

`roles.json` preserves all registered training-row IDs and original raw HDF5
SHA values. Only `train[:100000]` and those external training rows are accessed.
`config.json` pins all twelve prepared files, sixteen graph identities, source
functions and S9-3 source decisions. Paths in public records are portable;
original manifest hashes remain available for provenance. A mismatch stops
dependent work rather than changing frozen hashes or trying other seeds.

Faiss uses the pinned `portable_truth` public-wheel payload. The original gate
hashed the AVX2 library; it did not attest which SIMD module was actually loaded.
This adapter records actual dispatch but does not retroactively fill that gap.
The `n3` field is the original Faiss HNSW diagnostic, not an independently counted
exact-distance counter. New timing observations never replace the paper's timings.

## Environment

Linux x86-64, Python 3.11, CPU 2 available. Install `requirements.txt`, then the
wheel specified by sibling `portable_truth/requirements.txt` (including its hash).
Sibling `portable_fresh_inputs/prepare_inputs.py` supplies the already-published
RAM/disk gates. Each explicit stage has expected RSS 8 GiB, AS 16 GiB, file cap
1 GiB, CPU/wall cap 7,200 seconds, growth cap 2 GiB, projected disk floor 200 GiB
and total outstanding project-growth ceiling 128 GiB. Numerical libraries use
one thread. Run stages serially; timing additionally requires an exclusive-host
assertion. That assertion is not an independently monitored whole-host guarantee.

The commands below describe a new reproduction in fresh output directories.
They are not permission to rerun sealed experiments. `--outstanding-growth-bytes`
must cover the whole project's remaining peak growth, not merely this stage.

## Ordered execution

Use these common arguments with every command:

```sh
--input-adapter artifact/original_execution/portable_fresh_inputs \
--outstanding-growth-bytes 2147483648 --authorize-new-stage
```

1. **Prepare both role panels separately.** For `P=3` and `P=4`:

```sh
python artifact/original_execution/portable_recovery_100k/run_recovery.py prepare \
  --family P --sift-hdf5 /path/to/sift-128-euclidean.hdf5 \
  --arxiv-hdf5 /path/to/arxiv-nomic-768-normalized.hdf5 \
  --output /path/to/new-prepared-P COMMON_ARGUMENTS
```

Preparation retains the original float32/block-25 truth implementation and `.npy`
serialization for vectors and truth. It requires
frozen file SHA matches. Newly exported `base.f32bin` must match the original graph
registry. Neither raw data nor original indexes are bundled; obtain the registered
datasets according to their upstream access and license conditions.

2. **Build each S9-3 graph once.** For each registered dataset and ordinal 0–7:

```sh
python artifact/original_execution/portable_recovery_100k/run_recovery.py build \
  --family 3 --dataset sift_100k --ordinal 0 \
  --prepared /path/to/new-prepared-3 --prepared-sha256 SHA_OF_COMPLETED_JSON \
  --truth-adapter artifact/original_execution/portable_truth \
  --output /path/to/new-graph-sift-0 COMMON_ARGUMENTS
```

3. **Profile one role and graph per stage.** Use family 3 roles `source_design`,
`target_certification`, `target_evaluation`; family 4 roles `baseline_selection`,
`baseline_certification`, `baseline_evaluation`. Generate the first two role
responses, lock decisions, then generate evaluation responses for a clean staged
reproduction. Each role produces 3,000 rows in original action/query order.

```sh
python artifact/original_execution/portable_recovery_100k/run_recovery.py profile \
  --family 3 --dataset sift_100k --role source_design \
  --prepared /path/to/new-prepared-3 --prepared-sha256 PREPARED_RECEIPT_SHA \
  --graph /path/to/new-graph-sift-0 --graph-sha256 GRAPH_RECEIPT_SHA \
  --truth-adapter artifact/original_execution/portable_truth \
  --output /path/to/new-source-profile-sift-0 COMMON_ARGUMENTS
```

4. **Lock decisions from calibration roles only.** A response manifest is a JSON
array of records `{"directory":"/path/to/new-role-profile",
"completed_sha256":"SHA"}`. Supply all 16 builds × two calibration roles,
and no evaluation roles. For family 4 also supply `--source-lock` and its
`--source-lock-sha256` from the new family 3 lock.

```sh
python artifact/original_execution/portable_recovery_100k/run_recovery.py lock \
  --family 3 --response-manifest /path/to/calibration-profile-map.json \
  --output /path/to/new-lock-3 COMMON_ARGUMENTS
```

S9-3 picks the first source-design budget meeting CP risk 0.05 with error 0.05/6,
moves one rung up, then checks candidate and endpoint with error 0.025 each on
target certification. S9-4 B3/B4 select the **first eligible budget**, unlike the
million-scale minimum-NDC baseline. B3 uses the first 250 selection + first 250
certification queries; B4 uses 500 + 500. All five deployable and three diagnostic
arms are locked. The evaluation oracle is absent from this lock.

5. **Evaluate without changing the lock.** The response manifest now contains
exactly 16 evaluation-role directories. The prior lock is validated before
evaluation responses are opened.

```sh
python artifact/original_execution/portable_recovery_100k/run_recovery.py evaluate \
  --family 3 --response-manifest /path/to/evaluation-profile-map.json \
  --lock /path/to/new-lock-3 --lock-sha256 LOCK_RECEIPT_SHA \
  --output /path/to/new-evaluation-3 COMMON_ARGUMENTS
```

Family 4 computes its original oracle only after the locked decisions, marking
it nondeployable. `evaluation_cells.csv` connects to the separately published
saved-output statistics; this entry does not rerun bootstrap analyses.

6. **Measure isolated API timing per graph.** Requires matching prepared, graph
and lock receipts, `--truth-adapter`, `--dataset`, and `--exclusive-timing`:

```sh
python artifact/original_execution/portable_recovery_100k/run_recovery.py timing \
  --family 3 --dataset sift_100k \
  --prepared /path/to/new-prepared-3 --prepared-sha256 PREPARED_RECEIPT_SHA \
  --graph /path/to/new-graph-sift-0 --graph-sha256 GRAPH_RECEIPT_SHA \
  --lock /path/to/new-lock-3 --lock-sha256 LOCK_RECEIPT_SHA \
  --truth-adapter artifact/original_execution/portable_truth --exclusive-timing \
  --output /path/to/new-runtime-sift-0 COMMON_ARGUMENTS
```

Timing retains 50 warmups/action, seven repetitions, seed 991 + permutation seed,
and query/action interleaving. Actions are deployed actions plus endpoint 512.
Wall and process-CPU clocks surround the original one-query API call. CSV records
also carry `n3` and returned-ID hashes; new timing values are not frozen historical
outputs or evidence of historical measurement equivalence.

## Verification and remaining scope

Synthetic tests validate role separation, frozen pin coverage, normalization,
truth kernels, source/target decision branches, nested B3 roles, lock-oracle
separation and tiny L2 native serialization/search. No old dataset, graph,
response, decision run, timing or bootstrap has been rerun during packaging.

The first local test run caught an unused evaluation helper in the lock-only
module. The builder now excludes that helper; calibration logic is unchanged.
Linux native CI and production-stage execution are separate verification levels.
This delivery does not claim all sixteen full-size graphs have been regenerated
on a different host, nor that historical SIMD selection is known.
