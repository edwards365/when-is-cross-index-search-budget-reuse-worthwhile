# SIGMOD E&A post-seal uplift — S2 query-role gate

## Decision

`BLOCKED_MISSING_EXPLICIT_UNUSED_QUERY_POOL`

S2 is a metadata-only preregistration gate. It does not run ANN search, read query
vectors, read exact-neighbor truth, choose a new policy, or modify the sealed S5R3
paper. The parent is `49bd2910b122293f43c1a9063364a038fa4417b8` and the
work remains in the existing ANNS main worktree.

## Audit result

The E4 role manifest contains one explicitly reserved pool per dataset:
`future_replication_ids` with 1,000 unique IDs. S4 already consumed that pool in
its entirety, in the frozen list order: entries 0--499 became
`fresh_source_certification_ids` and entries 500--999 became
`fresh_target_evaluation_ids`. For both SIFT-100K and Arxiv-Nomic-100K, the S4
union equals the E4 future-replication set and the two S4 roles have zero
within-dataset overlap.

No second role is labelled unused, reserved, or future in the audited manifests.
The 750 E4 confirmatory-evaluation IDs are a subset of the 1,000 confirmatory IDs,
and the 250 target-sentinel IDs occupy the remainder. The S3 local-ID roles were
all historically inspected and are explicitly `POST_HOC_ROLE_LIMITED`.

## Firewall

- New vector reads: 0.
- New truth reads: 0.
- ANN searches: 0.
- Index builds: 0.
- Policy changes: 0.
- `validation-dev`, `formal-test`, and reserved truth access: 0.

The presence of larger query files is not evidence of an admissible unused role.
S2 therefore does not sample IDs from those files and does not infer provenance
from numeric ranges.

## Frozen S3 design, not yet authorized

Once a provenance-bearing untouched pool of at least 1,000 IDs per dataset is
created and frozen before content access, allocate 500 target-certification and
500 target-evaluation IDs deterministically with seed 991. The candidate remains
the S4-frozen Faiss `source_selected_plus_1` policy over the registered 24 builds
per dataset and 552 directed source-to-target pairs. Certification and evaluation
must be disjoint; evaluation may not alter the action, threshold, or endpoint.

Certification uses the one-sided Clopper--Pearson upper bound at 5%. If candidate
and endpoint are both tested, the preregistered split is 0.025 + 0.025. Primary
admission requires both datasets to satisfy risk UCB <= 5%, evaluation risk <=
5%, positive mean work or latency savings with a lower confidence bound above
zero, non-inferior p95, and stability under leave-one-build-out and deletion of
the largest contributing build. Candidate and endpoint runs must be interleaved
under fixed hardware, threads, affinity, warm-up, and order logging.

S3 remains unauthorized until a new role manifest records provenance, IDs,
hashes, pairwise overlaps, and a truth-access log with pre-access status.
