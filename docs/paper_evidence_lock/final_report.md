# Final report

## Decision
`BLOCKED_BY_BUILD_LEVEL_POWER_OR_RESOURCES`

## Scope and provenance
- Branch: `exp/graph_anns_paper_evidence_claim_lock`; HEAD/parent anchor: `9fe44938561d47ce3688549e51f7217fe4940840`.
- Worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw` (the existing ANNS main worktree; no new Codex task or worktree was created).
- Anchor commits parsed: 8/8.
- Evidence levels: E0=unresolved historical rows before repair, E1=exploratory historical, E2=conditionally reproduced; no E3/E4 result was created in this round.

## Numeric audit
- Gate-A actual common budget grid: `{10,20,40,80,120,200}`.
- Raw Gate-A main files: 1656000 physical rows and 552000 unique query-budget units (arxiv_nomic_100k: files=27, rows=486000, units=162000; glove100_100k: files=27, rows=486000, units=162000; sift_100k: files=27, rows=684000, units=228000).
- 1,458,000/486,000: superseded six-budget projection from the recovery report.
- 972,000: separate Cross-Index protocol, 81 graphs × 1,000 queries × 12 budgets.
- 648,000: separate Tournament protocol, 27 graphs × 2,000 queries × 12 budgets.
- 648 directed / 324 undirected pairs: dependent cross-index build contrasts, not independent environments.
- Fixed-target retrospective subset: 12 directed pairs.

## Gates
P0 PASS_WITH_CONTEXT; P1 PASS_WITH_SCOPE; P2 BLOCKED_BY_BUILD_LEVEL_POWER_OR_RESOURCES; P3 CONDITIONAL; P4 PASS. Therefore no confirmatory build matrix is authorized yet.

## Access firewall
`confirmatory_query` and `future_replication` were not accessed; validation-dev and formal-test are recorded as not accessed. Early Exit was not continued.

## Required next action
Use the repaired numeric contexts as the sole basis for a build-level power calculation. Before any confirmatory query access, justify 18–24 same-protocol builds per primary dataset and measure the pilot resource envelope on `/home/wlk/data500`; then rerun P2–P4.
