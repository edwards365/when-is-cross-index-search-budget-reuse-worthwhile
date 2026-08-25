# OCGT-v3 read-only audit

- Frozen parent: `exp/index_conditionality_ocgt@664f2bb0c7dcf35fca19866a651b4ef8e48d41d2`.
- Isolated worktree/branch: `/home/wlk/projects/navigation-aware-resistance-hnsw-ocgt-v3`, `exp/index_conditionality_ocgt_v3`.
- The parent worktree contains untracked user/generated files; none were overwritten or removed.
- OCGT-v2 remains frozen and is not an input to confirmatory statistics.
- Python tests: 80/80 passed. The historical build directory exposes no registered CTest tests; this must be resolved or documented before preregistration.
- Frozen construction assets are the first 10,000 rows of each train member: SIFT (1,000,000×128), GloVe (1,183,514×100), Arxiv-Nomic (1,344,643×768).
- Source SHA256 values match the frozen manifests: SIFT `dd6f0a6e...`, GloVe `544af1d5...`, Arxiv `8be0993b...`.
- Existing design queries use 1,000 unique train source IDs per dataset, all in `[100000,200000)`; none overlaps the 10K base.
- No previously frozen validation-dev artifact was found. OCGT-v3 must therefore use the preregistered fallback from the train member only, with seed 20260901, excluding `[0,10000)` and all prior design source IDs.
- Formal members are named `test`, `neighbors`, and `distances` (plus `avg_distances` for Arxiv); their contents were not read.
- The fallback can provide at least 500 independent source IDs per dataset without touching formal-test. Exact membership, vector hashes, non-overlap proof, and exact top-10 truth must be frozen before any HNSW query.
- OCGT-v2 raw rows omit several OCGT-v3-required fields; the v3 recorder/schema must be implemented and tested before Gate R.
- Available resources at audit: 128 CPU threads, 251 GiB RAM (239 GiB available), four RTX 3090 GPUs, approximately 11 GiB free disk. The disk margin is only about 1 GiB above the mandatory stop gate and must be monitored closely.

Audit conclusion: `PASS_TO_QUERY_MEMBERSHIP_PREPARATION`, conditional on using only the documented train-member fallback and completing schema/recorder tests before performance work.
