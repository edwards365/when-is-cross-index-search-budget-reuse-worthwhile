# 100K hardness-portability read-only audit

- Frozen parent verified: `exp/index_conditionality_ocgt_v3@0d490fecb655bf0345186a137f2ba2d5ee6287d6`; OCGT-v3 checksum verification passes.
- Isolated worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw-hardness-100k`, branch `exp/hardness_portability_100k`; clean at creation.
- The source OCGT-v3 worktree contains only a known untracked `Testing/` directory created by the prior CTest audit; it was not modified.
- Source HDF5 files exist locally: SIFT 525,128,288 bytes, GloVe 485,413,888 bytes, Arxiv-Nomic 4,135,431,488 bytes. Frozen manifests define train sizes 1,000,000×128, 1,183,514×100, and 1,344,643×768 with squared-L2 or normalized inner-product semantics.
- Only the train member is authorized. Formal `test`, `neighbors`, and `distances` members remain sealed and unread.
- Existing OCGT-v3 tooling provides exact top-10 generation, native HNSW search, a per-row native-versus-instrumented equality check, graph/query/truth hashing and complete raw schema.
- The current tracer does not serialize or restore a live candidate/result/visited prefix; Phase I therefore requires a separately frozen implementation and exact equivalence test if authorized.
- Resources: 128 CPU threads, 251 GiB RAM (about 239 GiB available), four RTX 3090 GPUs. Free disk is 11,324,923,904 bytes (10.55 GiB), only 0.55 GiB above the mandatory 10 GiB stop threshold.
- The 100K base can be read directly from each frozen HDF5 train prefix, avoiding a persistent duplicate. Queries/truth are small, but every build must delete its exact temporary point/index files immediately after hashes and raw records are durable.

Audit decision: `PASS_TO_100K_DATA_FREEZE_WITH_CRITICAL_DISK_MARGIN`. No graph construction or performance query is authorized before data/query/truth manifests and preregistration are committed.
