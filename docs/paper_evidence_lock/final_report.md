# Final report

## Decision
`READY_FOR_CONFIRMATORY_HNSWLIB_REBUILD_MATRIX`

## Scope and provenance
- Branch: `exp/graph_anns_paper_evidence_claim_lock`; HEAD/parent anchor: `cb34f88518590c1ff38897307b24225b2e4be09b`.
- Worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw`; no new Codex task or worktree was created.
- Anchor commits parsed: 8/8.
- No E4 result was created in this round.

## Numeric and power closure
- Gate-A: 1656000 physical rows and 552000 unique query-budget units on `{10,20,40,80,120,200}`.
- Cross-Index: 972,000 rows; Tournament: 648,000 rows; 648 directed/324 undirected dependent build contrasts.
- P2 power at 18 builds: SIFT 91.5%, Arxiv 89.1%; leave-one-build-out minima 85.7% and 84.9%.

## P3 resource closure
The preferred 48-build matrix uses `/home/wlk/data500/graph_anns_paper_evidence_lock` only. Historical per-dataset maximum build/search timings plus truth generation give 1.279 hours; the registered 4x operational envelope is 5.114 hours. The 100x storage stress envelope plus reserve is 651.672 GiB, leaving 250.987 GiB. P3 passes as an E2 resource-planning Gate, not an E4 result.

## Gates
P0 PASS_WITH_CONTEXT; P1 PASS_WITH_SCOPE; P2 PASS; P3 PASS; P4 PASS. The contract is ready; this evidence-lock round does not automatically start the confirmatory build matrix.

## Access firewall
`confirmatory_query` and `future_replication` were not accessed; validation-dev and formal-test are recorded as not accessed. Early Exit was not continued.

## Required next action
Start the separately authorized E4 matrix exactly as frozen, using new mutually exclusive confirmatory queries and 18–24 builds per dataset. Any protocol change requires a new preregistration before query access.
