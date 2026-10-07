# Fresh-query roles, effective base and query-vector preparation

This input-only entry implements the frozen train-only protocol behind the
fresh-query panels. It prepares membership and query vectors, not an ANN index,
exact truth or search responses. Scientific roles, seed, raw-vector metric
conventions and exclusions are unchanged. `provenance.json` identifies the
original source/configuration and the two unchanged selection/scan functions.

## Install and validate without original datasets

Use a new environment with Python 3.11 for production preparation:

```sh
python -m pip install -r requirements.txt
python -m unittest -v test_prepare_inputs
python prepare_inputs.py check-registry
```

`check-registry` recomputes the frozen IDs from the old/E1b role registries and
seed, compares every ID with the saved membership, and derives the retained raw
base order. It opens no HDF5 file or experimental result. Expected per dataset:
2,500 fresh queries, 7,500 total query IDs removed, SIFT base 992,295 with 205
content exclusions, Arxiv base 1,337,142 with one content exclusion. The small
test HDF5 is synthetic; no original full-data content scan is claimed by tests.

## Raw input acquisition

Use the provider links, sizes and SHA256 in
[`../datasets.json`](../datasets.json) in the repository, or `datasets.json` in
the `artifact-sources-v1` archive. Do not reuse the normalized S9 panel or the
100K Faiss L2 preparation. Here SIFT uses stored float32 vectors and squared L2;
Arxiv uses the stored float32 vectors with native IP and **no extra normalization**.
The full HDF5 SHA is checked before opening `train`. The code never opens
`test`, `neighbors` or `distances`. Source vectors are not redistributed here.

## Explicit new preparation (not executed for the original datasets in this release)

```sh
python prepare_inputs.py prepare \
  --sift /path/to/sift-128-euclidean.hdf5 \
  --arxiv /path/to/arxiv-nomic-768-normalized.hdf5 \
  --output /path/to/new-fresh-inputs \
  --authorize-input-preparation --outstanding-growth-bytes 16777216
```

The final number is the stage's 16 MiB growth; declare larger total outstanding
project growth if other stages are planned. The original CPU 2/single-library-
thread, 8 GiB address-space, 16 MiB per-file, 1800s CPU/wall conditions remain.
The project preflight preserves its RAM/RSS reserve checks, I/O-wait limit,
200 GiB projected disk floor and 128 GiB outstanding-growth ceiling. Stricter
inherited process limits are retained. A new output directory is mandatory;
failure evidence remains and there is no automatic retry or replacement draw.
These conservative historical resource conditions are not algorithmic minimums.

The full train-only content scan recomputes and compares exclusions, rejecting
query-query duplicates or changed exclusion sets. It then writes:

- `tcp_fresh_roles_v1/membership.npz`, with the frozen membership SHA;
- eight `tcp_fresh_profiles_v1/<dataset>_<role>/queries.qbin` files;
- start/completion or failure receipts, including ordered-base-ID digest.

Query files preserve raw ID order and original little-endian float32 bits. The
two evaluation qbins must match their frozen SHA/size. All NPZ array ordering
is preserved. Linux serialization is checked against the original membership
SHA; Windows writes a different ZIP host-OS marker and is not a production
preparation environment. There is no silent fallback to a newly pinned hash.

## Connection to cache and remaining upstream work

The outputs provide three of the seven inputs required by
[`../portable_cache`](../portable_cache/README.md): membership and the two
evaluation query files. Exact-truth NPZs and audited profile arrays are still
produced by separate stages. This preparation does not issue the old truth or
ANN audit's PASS receipt, nor claim that a new run was historically prospective.

The recorded base counts and ordered raw IDs are the interface for both the
truth builder and graph builder. `TRUTH_HANDOFF.md` specifies the next exact-
truth stage and its unresolved native dependency. No new paper values, cache
timings, graph builds, model training or bootstrap results are generated here.
