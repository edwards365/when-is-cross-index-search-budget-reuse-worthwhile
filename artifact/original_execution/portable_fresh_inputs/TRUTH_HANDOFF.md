# Exact-truth dependency: fixed semantics, open native build integration

The next original stage is
`scripts/icde2027_1m/materialize_tcp_fresh_truth_v1.py`, pinned in the
`artifact-sources-v1` source supplement with
`manifests/icde2027_1m/tcp_fresh_truth_v1.json`.

Its required semantics are already determined:

| Item | Recorded behavior |
|---|---|
| Source | Original SHA-pinned HDF5 `train` only |
| Base | Remove all 7,500 query IDs and frozen content exclusions; ascending raw-ID order |
| Metrics | SIFT `IndexFlatL2`; Arxiv `IndexFlatIP`; no normalization |
| Roles | source_design 500, target_selection 500, target_certification 500, target_evaluation 1000 |
| Stream/search | Add retained base in 8,192-row source blocks; top-10 search per complete role |
| Returned IDs | Map Faiss positions through ordered retained raw IDs |
| Checks | Position bounds, self exclusion, unique neighbor IDs, finite scores and direction-appropriate score order |
| Output | NPZ with query_ids, neighbor_raw_ids, scores; cost receipts separate base acquisition and role reads/search |
| Recorded environment | Python 3.11, NumPy 1.26.4, h5py 3.11.0, project Faiss 1.8.0; 16 threads, CPU affinity 4–19 |

The current truth config pins a version and an original module location, not a
portable build recipe. A generic `pip install faiss==1.8.0` is **not** a verified
substitute for that native build, including tie behavior and binary provenance.
This release does not invent a dependency lock or supply a bypass of identity
checks. Build/source provenance and the relocation of dependent receipts must
be integrated before publishing a verified truth execution command.

The portable input producer's `completed.json` is a new preparation receipt,
not the old `PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME` file with its
historical hash. Downstream integration must validate the new receipt and the
unchanged membership/data identities explicitly; it must not rewrite the old
receipt or disable its checks. The cache entry continues to require the frozen
truth/profile bytes, so the whole raw-data-to-cache chain remains open.
