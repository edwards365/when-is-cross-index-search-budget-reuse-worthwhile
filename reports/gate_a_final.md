# Gate A final frozen result

Final label: **RESISTANCE_SPECIFICITY_NOT_ESTABLISHED**.

All 81 preregistered main runs completed without failure. SIFT used five
triggered midpoint supplements and Arxiv used 27 uniform midpoint supplements;
GloVe triggered none. Every audited artifact records only the `train` HDF5
member and `formal_test_members_accessed=false`; formal test data remain sealed.

| Dataset | Frozen endpoint status | GGR improvement vs Geometry by build seed |
| --- | --- | --- |
| sift_100k | PRIMARY_ENDPOINT_REACHABLE | b7 -1.121%, b17 +0.098%, b29 -0.279% |
| glove100_100k | PRIMARY_ENDPOINT_UNREACHABLE_WITHIN_PREREGISTERED_GRID | undefined (Recall 0.95 unreachable) |
| arxiv_nomic_100k | PRIMARY_ENDPOINT_REACHABLE | b7 -0.746%, b17 -0.744%, b29 -1.613% |

Positive improvement is favorable. SIFT is weakly negative but seed directions are
inconsistent and the result is not specific to resistance. Arxiv is consistently
unfavorable to GGR versus Geometry and both matched negative controls. GloVe's
primary endpoint is right-censored by the frozen efSearch grid and is neither a
success nor a zero-effect result.

The preregistered requirement—stable superiority over Geometry, matched random,
and shuffled-resistance controls on at least two datasets and most seeds—is not
met. The GGR development direction is frozen and receives no further tuning.
Effective-resistance mathematics and engineering feasibility remain valid, but
resistance-specific HNSW navigation or performance benefit is not established.

Detailed p50/p95/p99 NDC, latency, Recall, build cost, run identities, and SHA-256
evidence hashes are in `manifests/gate_a/gate_a_final.json`,
`completed_run_matrix.json`, and `result_checksums.json`.
