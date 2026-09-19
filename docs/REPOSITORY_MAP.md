# Repository map

This repository preserves the full research path. Use this map to distinguish canonical deliverables from historical stage records.

## Canonical entry points

| Path | Purpose |
|---|---|
| `README.md` | Public project overview and quickest route to the paper/artifact |
| `paper/sigmod2027/` | Current SIGMOD E&A manuscript, appendix, figures, compact evidence, and checks |
| `artifacts/graph_anns_phase3_ea85/` | Reviewer-facing smoke, table regeneration, and full-replay instructions |
| `docs/RESULTS_GUIDE.md` | Claim, estimand, scope, and evidence map |
| `docs/QUICKSTART.md` | Environment and replay commands |
| `reports/STATUS.md` | Current project state and validated boundaries |
| `CITATION.cff` | Repository citation metadata |

## Implementation and validation

| Path | Contents |
|---|---|
| `python/narhnsw/` | Reusable Python modules |
| `cpp/` | Native instrumentation and validation code |
| `scripts/` | Data, experiment, audit, replay, and analysis programs |
| `configs/` | Dataset and experiment configurations |
| `tests/python/` | Python regression and protocol tests |
| `theory/` | Formal definitions, proof sketches, counterexamples, and tests |
| `third_party/` | Pinned or documented external dependencies |

## Evidence and generated products

| Path | Contents |
|---|---|
| `results/` | Committed compact results and sealed derived outputs |
| `figures/` | Project-level generated figures |
| `paper/sigmod2027/evidence/` | Submission-facing compact evidence and independent checks |
| `paper/sigmod2027/figures_v3/` | Current manuscript figures in PNG/PDF/SVG |
| `manifests/` | Frozen protocols, decisions, checksums, and registrations |
| `reports/` | Phase reports, gate outcomes, and current status |

Large datasets, indexes, raw traces, build directories, and machine-local logs are not source artifacts and are excluded from Git.

## Historical research trail

Stage-specific directories under `docs/`, `results/`, `figures/`, `tests/`, `scripts/`, and `manifests/` record preregistered branches of the investigation. They are intentionally retained because negative results and stop decisions are evidence.

Notable boundaries:

- tag `phase1-local-resistance-null-v1` freezes the early navigation-aware resistance result;
- later certification/fallback audits explain why several apparent improvements were not deployable;
- stable-build, CIBS, CALS/BN-APD, and related folders are mechanism investigations, not the current headline algorithm;
- S9 folders contain the final prospective robustness, runtime, and strong-baseline sprint used by Final V3 Prime.

Do not infer project status from the newest-looking stage directory. Use `reports/STATUS.md` and the final manuscript.

## Naming and compatibility

The public research name is now **ICBA: Auditing Search-Budget Portability Across Graph-ANNS Rebuilds**. The GitHub slug `navigation-aware-resistance-hnsw` and Python package name `narhnsw` are preserved to avoid breaking clones, imports, citations, and historical manifests.
