# Rebuild Tax source audit

The frozen source commit `4f49c02121b0321e5ed0b2d4a0846a22e1bad910` exists and its committed checksum manifest verifies. The new branch `exp/rebuild_tax_cross_mechanism` was created at that commit in the existing worktree to avoid duplicating roughly 100 MB of tracked evidence while disk space is close to the mandatory 10 GiB stop line. No frozen file was overwritten.

The confirmatory source contains exactly 45 primary graph configurations and 540,000 rows: 27 core graphs/324,000 rows plus 18 natural or cluster-block graphs/216,000 rows. Every graph has 1,000 queries at all 12 frozen ef values; dataset, seed, history and query-ef coverage are complete. All rows record successful native/tracer agreement. `exact_ndc` is the instrumented distance-function count and is the primary cost. Latency is a single native `searchKnn` timing per cell without a dedicated 100K warmup and is therefore secondary.

The query split remains 250 train-design and 750 confirmatory-audit queries. Only manifests and committed hashes were inspected for data-firewall status; validation-dev and formal-test members were not read. Full per-query search traces and deleted graph indexes are not available. Graph-global metadata is limited to hashes, entrypoint, maximum layer, construction time and peak memory, so M3 and M4 must report identifiability limits rather than invent topology or trace features. Exact frozen LID is replayable; the SHEAF-like and single-prefix outputs are replayable only to their already frozen scope.

Decision: `PASS_SOURCE_AUDIT`. Gate M may proceed using only deterministic derivations of the frozen 540,000 rows. No new HNSW query is authorized.
