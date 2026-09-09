# Final report

## Decision
`BLOCKED_BY_BUILD_LEVEL_POWER_OR_RESOURCES`

## Scope and provenance
- Branch: `exp/graph_anns_paper_evidence_claim_lock`; HEAD/parent anchor: `208129dce0a322678f34147b110959b418ddab14`.
- Worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw` (the existing ANNS main worktree; no new Codex task or worktree was created).
- Anchor commits parsed: 8/8.
- Evidence levels: E0=0, E1=exploratory historical, E2=conditionally reproduced/design variance; no E3/E4 result was created in this round.

## Numeric audit
- Gate-A actual common budget grid: `{10,20,40,80,120,200}`.
- Raw Gate-A main files: 1656000 physical rows and 552000 unique query-budget units (arxiv_nomic_100k: files=27, rows=486000, units=162000; glove100_100k: files=27, rows=486000, units=162000; sift_100k: files=27, rows=684000, units=228000).
- 1,458,000/486,000: superseded six-budget projection from the recovery report.
- 972,000: separate Cross-Index protocol, 81 graphs × 1,000 queries × 12 budgets.
- 648,000: separate Tournament protocol, 27 graphs × 2,000 queries × 12 budgets.
- 648 directed / 324 undirected pairs: dependent cross-index build contrasts, not independent environments.
- Fixed-target retrospective subset: 12 directed pairs.

## P2 repair
The prior P2 diagnosis incorrectly treated the three-build fixed-target audit as the only variance source. The pinned historical hnswlib matrix provides nine target-build units per primary dataset. At the preregistered minimum effect 0.05, two-sided alpha 0.05, and 5,000 residual-bootstrap studies, power at 18 builds is 91.5% on SIFT and 89.1% on Arxiv; leave-one-build-out minima are 85.7% and 84.9%. P2 passes as a prospective design Gate.

## Gates
P0 PASS_WITH_CONTEXT; P1 PASS_WITH_SCOPE; P2 PASS; P3 CONDITIONAL; P4 PASS. No confirmatory build matrix is authorized until P3 is sealed.

## Access firewall
`confirmatory_query` and `future_replication` were not accessed; validation-dev and formal-test are recorded as not accessed. Early Exit was not continued.

## Required next action
Seal the execution resource envelope on `/home/wlk/data500`, including build, search, truth, storage, and full wall-clock estimates, then rerun P3/P4 before any confirmatory query access.
