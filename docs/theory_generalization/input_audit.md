# Theory generalization input audit

Phase 0 audits objects at their frozen Git commits rather than the later working-tree copies. This avoids treating expected downstream recomputation as corruption.

| Experiment | Frozen commit | Tree files | Selected evidence | Frozen checksum OK | Problems |
|---|---:|---:|---:|---:|---:|
| cross_index | `b82abf6bab8a` | 1107 | 269 | 17 | 0 |
| tournament | `80c505dcc3ec` | 926 | 261 | 20 | 0 |
| rcrs_fast | `01c491f71270` | 1133 | 281 | 18 | 0 |
| rcrs_signal | `07ffc3818718` | 1164 | 294 | 21 | 0 |

## Frozen decisions

- Cross-Index: `SHRINK_TO_HNSWLIB_IMPLEMENTATION_BOUNDARY`; 81 graphs and 972,000 rows.
- Rebuild Algorithm Tournament: `NO_DEPLOYABLE_CANDIDATE_KEEP_BOUNDARY_STUDY`; exploratory design simulation.
- RCRS fast feasibility: positive pointwise monotone tax and 500-query prefix equivalence; not a completed algorithm.
- RCRS Signal Pilot: `STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL`; 0/16 GloVe policies certified.

## Definition and comparability findings

- **quality_target:** Recall@10 threshold tau=0.9 in RCRS signal; other frozen experiments must be read from their own manifests.
- **budget:** Frozen ordered ef/search-list grid; no interpolation is treated as an observed budget.
- **minimal_sufficient_budget:** Smallest observed budget attaining target at that point.
- **minimal_stable_sufficient_budget:** Smallest budget after which every larger frozen budget attains target.
- **right_censoring:** No stable sufficient budget exists on the frozen grid; record B>e_max.
- **ndc:** Native distance-computation count; implementation-local and not automatically cross-implementation comparable.
- **split_rule:** Cross-Index, Tournament, RCRS-fast and RCRS-signal query splits are distinct evidence units; Global/GCC/Oracle numbers are not pooled across splits.
- **risk_rule:** Pointwise safety, empirical marginal risk and certified population risk remain separate.

## Data firewall

No validation-dev or formal-test member was opened by this audit. No graph was built. Existing untracked `logs/` were preserved.

## Open audit items

Exact source-specific `e0`, budget grids and split membership hashes will be transcribed from each frozen manifest before unified empirical calculations. A missing or mismatched frozen-commit checksum blocks reuse of that artifact but does not justify modifying it.
