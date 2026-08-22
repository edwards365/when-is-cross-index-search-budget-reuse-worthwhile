# External dependency lock record

The smoke phase vendors only hnswlib as a Git submodule. The other repositories are recorded to prevent ambiguous baselines; adding them is Tier- and experiment-gated.

| Component | Official URL | Pinned revision/release | Status | License note |
|---|---|---:|---|---|
| hnswlib | https://github.com/nmslib/hnswlib | `v0.8.0`, `3f3429661187e4c24a490a0f148fc6bc89042b3d` | submodule | Apache-2.0 upstream |
| Faiss | https://github.com/facebookresearch/faiss | v1.12.0 (subject to compatibility verification) | not vendored | MIT upstream |
| DiskANN | https://github.com/microsoft/DiskANN | release tag to be frozen before Vamana work | deferred | MIT upstream |
| VIBE | https://github.com/vector-index-bench/vibe | commit to be frozen before modern-data run | deferred | preserve dataset-specific licenses |
| ANN-Benchmarks | https://github.com/erikbern/ann-benchmarks | commit to be frozen before classic-data run | deferred | preserve dataset-specific licenses |
| Big-ANN-Benchmarks | https://github.com/harsha-simhadri/big-ann-benchmarks | commit to be frozen after Go gate | deferred | preserve dataset-specific licenses |

Do not use a “pending” row in a reported benchmark. Resolve it to a full commit hash first.
