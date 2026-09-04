# GSC theory-delta input audit

## Scope and isolation

This audit starts from frozen commit `736c3799a92bf31f503c37e8eaaf680f84398aa5` and targets branch `exp/icba_gsc_theory_prior_delta_lock`. The requested server worktree was not mounted in this environment, so an isolated staging directory is used; no server-side worktree state is inferred. The audit creates no graph, trains no model, and does not modify frozen experiment directories.

## Commit verification

The following full commit IDs were resolved through the repository history/API before writing this delta:

| Role | Commit | Resolved status |
|---|---|---|
| GSC starting point | `736c3799a92bf31f503c37e8eaaf680f84398aa5` | verified |
| Open-World Final Seal | `a9f88bbcfd9b2c2f3e8a27e1471e16628b60cdb0` | verified |
| Oracle–Observable Theory | `4e728d437038816a7706e9cb802d19274aa691b9` | verified |
| Certification–Fallback Theory | `41a44bd930679b5e933034a1496d2fe42e1ae018` | verified |
| Ordered Rung Semantic Reaudit | `904de537f16798eac9f68da549f2741d92e2b1c2` | verified |
| Stable-Build Theory Forensics | `dca81b23ce3cfe7ca95e3b3362fb3129cf24f937` | verified |
| Stable-Build Semantic Gate | `f7f08ce1f82e23eb4b14cdc08db1190301dc82af` | verified |
| CFSR-Lite Pilot | `7417147e9ce2e526973cd47b3b390c0ae2bb7c65` | verified |
| CIBS Theory/Semantic Lock | `b0190169cdb758aa5311c7d13fbfd4fd724020f0` | verified |
| Active Observation Gate | `97ca42a120fff015885bba509e8aa90178aabfa2` | verified |
| Decision-Regret Closure | `a3db1c0a0dcb23826389ffa958759063a6163ef2` | verified |

## Evidence hierarchy applied

The latest formal semantic reaudits and closure reports supersede earlier drafts. Query-disjoint evidence supersedes reused-query comparisons; build-cluster bootstrap is required for build-level statements; fixed-target statements are not promoted to open-world statements; and all claims based on final GSC evaluation remain prohibited in this task.

## Frozen limitations retained

The historical 123-item SHA256 baseline remains limited to 111 matches, 8 mismatches, and 4 untracked `__pycache__` entries. A later local checksum passing does not repair that historical reproducibility defect. The audit treats CIBS Joint Feasibility Closure as the latest frozen route: no two-dataset CI-supported joint-feasible action, QNI/Race not authorized, and prior proxy or oracle values as non-deployable.

## Access controls

The following are explicitly not accessed: `gsc_safety_certification`, `gsc_final_evaluation`, `gsc_future_confirm`, validation-dev, formal-test, and any sealed truth not already present in the approved frozen summaries. No theorem, operator, or claim is conditioned on those results.

## Source-to-output map

- inherited semantics and theorem references: prior commits listed above and `docs/icba_cibs_theory_delta/theory_inheritance_report.md`;
- conflict decisions: `results/icba_gsc_theory_delta/conflict_ledger.csv`;
- new theorem status: `results/icba_gsc_theory_delta/theorem_status.csv`;
- operator prior-art: `docs/icba_gsc_theory_delta/operator_prior_art_delta.md` and `results/icba_gsc_theory_delta/operator_overlap_matrix.csv`;
- experiment handoff assumptions: `results/icba_gsc_theory_delta/assumption_observability.csv`.

The branch is a documentation/theory delta only. It must not be represented as a fresh experimental result.

