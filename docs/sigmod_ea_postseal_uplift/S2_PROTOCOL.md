# SIGMOD E&A post-seal uplift — S2 query-role gate

## Decision

`S2_PASS_FRESH_POOL_FROZEN`

S2 is complete. It is a metadata-only preregistration gate: no ANN search, query
vector read, exact-neighbor truth read, index build, policy change, or sealed
S5R3 paper modification occurred. The work remains in the existing ANNS main
worktree on branch `exp/sigmod_ea_target_cert_uplift`.

## Why the initial gate stopped

The first audit correctly established that E4's only named
`future_replication_ids` pool had been fully consumed by S4. In each dataset its
1,000 IDs were partitioned into 500 source-certification and 500
target-evaluation queries, with zero within-dataset overlap. Reusing those IDs or
relabeling S3's historically inspected outcomes would not constitute prospective
evidence. Commit `7c51328b0cf7ffb5e5d2bd1337f769d710c7e702` therefore stopped safely.

## Resolution

The immutable source files contain substantially larger `train` members than the
100K index: 1,000,000 rows for SIFT and 1,344,643 for Arxiv-Nomic. Source hashes
and shapes were already sealed in the project registry. S2 defined a new query-ID
candidate window `[500000, 600000)`, which is outside the E4/S4 ranges, and
audited every repository role/preregistration/access manifest plus the complete
Faiss external-validity role tables.

The audit found no repository JSON role ID in that window. The Faiss tables had
121 SIFT IDs and 86 Arxiv IDs in the window; all were excluded. Deterministic
sampling then used seed 991 for SIFT and 992 for Arxiv to freeze 1,000 eligible
IDs per dataset. The first 500 are `target_certification`; the remaining 500 are
`target_evaluation`. Both within-dataset and known-registry overlap are zero.

Here, **fresh** means never previously assigned or accessed as a query or truth
role. It does not mean the underlying bytes were never read: some rows may have
appeared as index data in separate scale experiments. This distinction is frozen
before outcomes are observed.

## Frozen S3 contract

- Candidate policy: S4-frozen Faiss `source_selected_plus_1`; no retuning.
- Scope: SIFT-100K and Arxiv-Nomic-100K, 24 registered builds per dataset and
  552 directed source-to-target pairs.
- Roles: 500 target-certification and 500 target-evaluation queries per dataset,
  mutually exclusive and frozen before content access.
- Risk event: `Recall@10 < 0.95`; threshold 5%.
- Certification: one-sided Clopper--Pearson bound; candidate/endpoint allocation
  is 0.025 + 0.025 when both are checked.
- Evaluation cannot change policy, action, threshold, grid, or endpoint.
- Statistics: 5,000 bootstrap replicates, seed 991; leave-one-build-out and
  delete-largest-contributing-build checks.
- Execution: fixed hardware, threads, affinity, warm-up, and randomized or
  interleaved candidate/endpoint order; record NDC and wall-clock separately.

Primary admission requires both datasets to satisfy certification UCB <= 5%,
evaluation risk <= 5%, positive mean work or latency savings with a confidence
lower bound above zero, p95 non-inferiority, and build-robust direction.

## Firewall and handoff

- New vector reads: 0.
- New truth reads: 0.
- ANN searches: 0.
- Index builds: 0.
- `validation-dev`, `formal-test`, and reserved truth access: 0.

Exact IDs, hashes, exclusions, source provenance, and the fixed downstream
contract are stored in
`manifests/sigmod_ea_postseal_uplift_s2_query_roles.json`. S3 is authorized but
has not started.
