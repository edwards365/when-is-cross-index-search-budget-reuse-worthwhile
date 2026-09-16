# Recommended SIGMOD E&A language

## Title

**When Safe Search Budgets Do Not Transfer Across Graph-ANNS Rebuilds: [Experiments & Analysis]**

## Abstract

Graph approximate-nearest-neighbor indexes are routinely rebuilt after refreshes, replica creation, and implementation changes, yet search-budget policies are often reused without auditing whether their safety transfers. We present ICBA, an audit framework that treats each build as an experimental environment and separates unsafe efficiency, certification, fallback, and deployable value. Across registered hnswlib rebuilds, external adaptive policies, a post-hoc Vamana semantic bridge, and an eight-build first-1M scale check, source-native actions repeatedly fail to transport safely. The first-1M experiment estimates 20.04% incremental transport risk (95% build-cluster interval 17.29–22.77%). Raw source TCP reuse is likewise unsafe on SIFT and Arxiv, whereas independently selected target recalibration attains risks of 1.79% and 2.04% and reduces mean distance evaluations by 44.39% and 44.79%, with non-inferior p95 tails. A harmonized lifecycle ledger shows that this target-selection route amortizes after approximately 138.8k SIFT or 107.4k Arxiv query sets and has positive native-distance value at one million queries, while one Arxiv build does not amortize. These results characterize when rebuild reuse fails, which recovery mechanisms remain deployable, and where evidence is only supportive. We release an anonymous, path-portable artifact for smoke validation, table regeneration, and guarded full replay.

## Contributions

1. **A rebuild-portability estimand and audit.** ICBA makes the target build the statistical unit, preserves endpoint censoring, and distinguishes raw efficiency from certified deployability.
2. **A stratified empirical boundary.** Registered evidence spans hnswlib mixed-refresh rebuilds, external adaptive policies, post-hoc Vamana alignment, and an eight-build first-1M check; conclusions remain scoped to the registered actions, builds, and datasets.
3. **A conditional mitigation result.** Target-selection TCP recalibration, not raw source reuse, is safe and distance-efficient on both registered mixed-refresh datasets, with positive build-cluster intervals and non-inferior p95 tails.
4. **Lifecycle and reproducibility closure.** A common native-distance ledger includes selection, certification, source profiling, control, fallback, and serving costs; an anonymous artifact regenerates the reported evidence with explicit external-data boundaries.

## Limitations

The study is conditional on registered build families, action grids, endpoints, and query roles; it does not establish universal non-transfer or algorithmic SOTA. Vamana is a post-hoc semantic alignment rather than a primary harmonized estimand. Deep1M is limited to the first one million vectors, eight builds, and 1,000 fresh queries. Lifecycle conclusions use implementation-native distance evaluations; wall-clock measurements are exploratory because hardware isolation is not controlled. One Arxiv target build does not amortize, and raw full replay requires external datasets and prebuilt-index setup that cannot be bundled anonymously. These boundaries are part of the result rather than exceptions to it.

## Reproducibility and artifact statement

The anonymous artifact at **[ANONYMOUS_ARTIFACT_URL]** includes an environment lock, external-source ledger, data and query checksums, truth-access log, portable smoke validation, table and figure regeneration, guarded full-replay instructions, runtime/storage estimates, and claim-to-evidence mappings. Smoke and table regeneration do not contain private host paths. Full raw replay intentionally stops with an actionable message when external data or indexes are absent.
