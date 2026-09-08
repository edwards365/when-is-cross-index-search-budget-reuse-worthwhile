# Final report

## Decision
`BLOCKED_BY_EVIDENCE_INTEGRITY`

## Scope and provenance
- Branch: `exp/graph_anns_paper_evidence_claim_lock`; HEAD/parent anchor: `0f5a2bec55cc62e9f9754358c1691eb965afe856`.
- Worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw` (the existing ANNS main worktree; no new Codex task or worktree was created).
- Anchor commits parsed: 8/8.
- Evidence levels: E0 unresolved historical claims, E1 exploratory historical, E2 conditionally reproduced; no E3/E4 result was created in this round.

## Numeric audit
- Actual auditable common budget grid: `{10,20,40,80,120,200}`.
- Recovery report: 1,458,000 physical rows and 486,000 unique query-budget units.
- Recovery manifest: 1,656,000 physical rows and 552,000 unique query-budget units.
- 972,000 twelve-level claim: not exactly recovered.
- 648,000 tournament-record claim and 648/324 pair claims: unresolved from local artifacts.
- Current fixed-target decision artifact reports 12 directed pairs, not 648.

## Gates
P0 FAIL; P1 PASS_WITH_SCOPE; P2 BLOCKED; P3 CONDITIONAL; P4 PASS. Therefore no confirmatory build matrix is authorized.

## Access firewall
`confirmatory_query` and `future_replication` were not accessed; validation-dev and formal-test are recorded as not accessed. Early Exit was not continued.

## Required next action
Repair the two row-count artifacts and locate or withdraw the unresolved 648,000/648/324 claims. Recompute `numeric_reconciliation.csv`, then rerun P0–P4 without touching sealed query roles.
