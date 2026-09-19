# Project status

Last updated: 2026-09-19

## Current state

The active research deliverable is the SIGMOD Experiments & Analysis manuscript **Auditing Search-Budget Portability Across Graph-ANNS Rebuilds** and its ICBA/TCP evidence package. The canonical review build is `paper/sigmod2027/ICBA_SIGMOD_EA_FINAL_V3_PRIME.pdf`.

The project has moved beyond its original resistance-rewiring hypothesis. That early path is frozen at tag `phase1-local-resistance-null-v1`; it remains part of the provenance and negative-results record but is not the current headline contribution.

## Completed evidence blocks

- Graph-only portability matrices across hnswlib/Faiss and SIFT-100K/Arxiv-Nomic-100K.
- Controlled 5% refresh replay with mutually separated roles.
- ICBA decision contract: construction, target certification, fallback, held-out evaluation, and cost accounting.
- TCP endpoint-relative recovery and a same-target-label-budget strong-baseline audit.
- Cross-method/family/scale evidence including DARTH/Ada-ef bridges, Vamana, and Deep1M.
- Prospective insertion-permutation panel with 112 separately certified target decisions.
- Fixed-machine, fixed-thread, interleaved runtime measurement.
- Lifecycle and break-even ledgers with explicit cost currencies and boundaries.
- LOTO, crossed bootstrap, tail, deletion, and fallback sensitivity checks.
- Compact anonymous manuscript replay, checksums, and claim-to-source provenance.

## Current scientific conclusion

Search-budget portability is an index-conditioned property, not reusable state that should be assumed safe after rebuild. ICBA provides the central contribution: deploy the least complex target-qualified policy whose information cost is justified by held-out value.

TCP is useful for recurring profiled queries when query conditioning adds incremental value. It is not universally superior. On the registered evidence, its incremental advantage over target calibration with the same target-label budget is resolved on SIFT but not Arxiv-Nomic; certified fixed and target-global policies remain important alternatives.

## Validated claim boundaries

- Results are conditional on registered builds, grids, query populations, and measurement settings.
- Per-decision certificates are not simultaneous campaign certificates.
- NDC and wall time are reported as different endpoints.
- Serving-work savings and lifecycle economic value use separate ledgers.
- External extensions retain their native estimands and are not pooled as independent replications.
- Evaluation roles never select actions, thresholds, shifts, or fallback rules.

## Reproduction status

- Lightweight artifact smoke: available at `artifacts/graph_anns_phase3_ea85/reproduce_smoke.sh`.
- Paper table/figure replay: available under `paper/sigmod2027/`.
- Full native replay: documented and gated; raw datasets and indexes are external.
- Final V3 Prime readiness/checksum records: committed under `paper/sigmod2027/qa/` and the delivery SHA files.

## Remaining work

The scientific core is sealed. Remaining submission work is repository/artifact presentation, independent clean-run validation, anonymous hosting, final metadata checks, and any venue-mandated packaging. Further experimental expansion should be preregistered as a new claim rather than retrofitted into the sealed evidence.

## Navigation

- [Project overview](../README.md)
- [Results guide](../docs/RESULTS_GUIDE.md)
- [Quickstart](../docs/QUICKSTART.md)
- [Repository map](../docs/REPOSITORY_MAP.md)
- [Paper provenance](../paper/sigmod2027/PROVENANCE.md)

Historical status text remains available through Git history and the frozen Phase I tag.
