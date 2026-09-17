# W2 citation and claim audit

Checked 2026-09-17. This is a bounded search for Introduction and Related Work, not a systematic review or a complete novelty certificate. No private manuscript passages or result tables were used as search queries. The bibliography contains 13 cited entries; no new experiments were run.

## Primary-source support

|BibTeX key|Primary source and checked passage|Permitted use in this draft|
|---|---|---|
|malkov2020hnsw|[IEEE article](https://doi.org/10.1109/TPAMI.2018.2889473), abstract and publication metadata|Hierarchical graph search; TPAMI 42(4), 824–836, 2020, not the 2018 online date as issue year.|
|subramanya2019diskann|[NeurIPS proceedings](https://papers.nips.cc/paper_files/paper/2019/hash/09853c7fb1d3f8ee67a61b6bf4a7f8e6-Abstract.html), abstract|DiskANN introduces Vamana; no imported speedup numbers or assertion of a rebuild-transfer guarantee. Author spelling normalized to Krishnaswamy, consistent with the author's FreshDiskANN record.|
|singh2021freshdiskann|[Author preprint](https://arxiv.org/abs/2105.09613), abstract|Dynamic insertion/deletion maintenance; cited as a 2021 preprint, not an invented conference publication.|
|elliott2024ordering|[Author preprint](https://arxiv.org/abs/2405.17813), abstract; publisher DOI [10.1145/3664190.3672512](https://doi.org/10.1145/3664190.3672512)|Insertion-order/intrinsic-dimensionality sensitivity; ICTIR 2024, 25–33. Does not directly establish our calibrated-budget transfer effect.|
|azizi2025evaluation|[Author preprint](https://arxiv.org/abs/2502.05575), abstract; publisher DOI [10.1145/3709693](https://doi.org/10.1145/3709693)|Graph-family construction/search evaluation. PACMMOD 3(1), 2025. Not conflated with a later four-author workshop variant.|
|li2020laet|[Author-hosted paper](https://www.pdl.cmu.edu/PDL-FTP/BigLearning/mod0246-liA.pdf), pp.1–2|Static and intermediate-search features, learned query-specific termination; SIGMOD 2020, DOI 10.1145/3318464.3380600.|
|chatzakis2025darth|[Author full text](https://arxiv.org/html/2505.19001v2), §3.1–3.2|GBDT recall prediction, search-integrated termination, adaptive prediction intervals, HNSW/IVF. PACMMOD 3(4), **2025**; presented at SIGMOD 2026. DOI 10.1145/3749160.|
|zhang2026adaef|[Author full text](https://arxiv.org/html/2512.06636v1), model description, §6.3 and update experiments|Similarity-distribution-based ef selection; explicitly credit stale/incremental/recomputed comparisons after updates. Published PACMMOD 4(1), 2026, DOI 10.1145/3786639.|
|wang2026annie|[PVLDB paper](https://www.vldb.org/pvldb/vol19/p3820-wang.pdf), pp.3820–3822, §5.1 and §6.8|Graph-derived cost features, optional recall-target guarantee, quantile-loss premise, OOD query analysis. PVLDB 19(11), 3820–3833, 2026; DOI 10.14778/3836663.3836728. Do not reduce it to a predictor without guarantees.|
|horchidan2025conann|[PVLDB paper](https://www.vldb.org/pvldb/vol19/p29-horchidan.pdf), §3.1–3.2|Expected FNR objective, IVF cluster probing, exchangeability, calibration aligned with construction. PVLDB 19(1), 29–42, **2025**; conference cycle 2026. DOI 10.14778/3772181.3772184.|
|chatzakis2026darthplus|[HAL v1 record](https://hal.science/hal-05566027v1), abstract and authors obtained from [HAL API](https://api.hal.science/search/?q=halId_s:hal-05566027&fl=title_s,authFullName_s,producedDateY_i,abstract_s,uri_s&wt=json)|**Abstract-level verification only.** HAL web/PDF access returned a browser challenge; API returned the primary deposited record. Text states only optional probabilistic quality guarantees on HNSW/IVF. Preprint 2026; no invented theorem assumptions, venue, or direct comparison result.|
|angelopoulos2024crc|[ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html), abstract and paper §1|Expected monotone-loss control; not automatically a high-probability guarantee over every selected action.|
|angelopoulos2021ltt|[Author preprint](https://arxiv.org/abs/2110.01052), abstract; [author PDF](https://people.eecs.berkeley.edu/~angelopoulos/publications/downloads/ltt.pdf), §2.1–2.3|Risk control as multiple testing; cited as arXiv 2021, not assigned an unverified publication venue.|

Publication metadata for DARTH, Ada-ef, ICTIR ordering, and the graph-search evaluation were additionally checked against publisher-deposited Crossref records. BibTeX preserves full author lists. Sources support the associated mechanisms; their own headline speedups are not copied into our comparison.

## Corrections that affect the argument

1. **Primary TCP setting:** `docs/graph_anns_phase3_ea85/p2_refresh95_protocol.md` identifies a 5% mixed delete/insert refresh followed by rebuilding. W2 adds this qualifier to the abstract, Introduction, and Methodology. It does not relabel the frozen scientific results or attribute the combined effect to graph changes alone.
2. **Recall estimand:** at k=10, `Recall@10 < .95` means at least one miss. A 5% probability of this event is different from 5% expected FNR. The text no longer treats their thresholds as interchangeable.
3. **DARTH bridge:** the frozen bridge report contains high average recall together with elevated query-level failure. That alone neither contradicts a different published quality objective nor identifies a source-to-target increment. W2 avoids claiming it does.
4. **Closest prior guarantees:** ANNiE's RTG and DARTH+'s stated optional guarantee are credited. ConANN's index family and expected-FNR estimand are explicit. We do not claim the first recall guarantee or absence of prior data-update experiments.
5. **TCP scope:** Introduction connects the recovery values to old-build profiles of the corresponding queries. It does not promote the replay to an unseen-query deployment result or a joint candidate/fallback certificate.

## Empirical headline links (unchanged W0 macros)

|Headline|Frozen linkage|Writing status|
|---|---|---|
|Direct reuse failure 6.69% / 7.24%|`WZeroSiftSourceRisk`, `WZeroArxivSourceRisk`|Empirical target failure in the refresh replay; not a confidence bound.|
|Target recalibration failure 1.79% / 2.04%|`WZeroSiftTargetRisk`, `WZeroArxivTargetRisk`|Empirical recovery in the query-profile population.|
|Mean NDC gain 44.39% / 44.79%|`WZeroSiftTargetGain`, `WZeroArxivTargetGain`|Relative to registered endpoint; not latency or full-cost SOTA.|
|Cross-family/scale evidence|W0 Vamana and Deep1M blocks|Their local references/estimands retained, not merged into one leaderboard.|

## W3 theoretical references and verification (2026-09-17)

The W2 entries remain unchanged. Three references were added for the theory section, using public title searches only:

- `yu1997assouad`: Springer chapter, 1997, pp. 423–435, DOI `10.1007/978-1-4612-1880-7_29`. Publisher metadata and abstract verified. Publisher preview was available intermittently, not the full chapter. The two-point reduction in the manuscript is proved explicitly; no empirical TV value is borrowed from this source. Primary record: https://link.springer.com/chapter/10.1007/978-1-4612-1880-7_29.
- `clopper1934confidence`: Biometrika 26(4), 404–413, 1934, DOI `10.1093/biomet/26.4.404`. Oxford's indexed publisher record verifies metadata; full paper remains paywalled. The one-sided formula is also checked against the frozen analysis implementation and direct binomial inversion in `check_w3_math.py`. Primary record: https://academic.oup.com/biomet/article-abstract/26/4/404/291538.
- `angelopoulos2023conformal`: Foundations and Trends in Machine Learning 16(4), 494–591, 2023, DOI `10.1561/2200000101`. Publisher summary verifies publication metadata (https://www.nowpublishers.com/article/DownloadSummary/MAL-101). Inspected the author preprint v6, Section 1.1 and Appendix D, for finite-sample rank coverage, exchangeability, the unsupported-rank case and ties (https://arxiv.org/html/2107.07511v6). W3 supplies the discrete-label proof with random tie-breaking for analysis only. It does not implement randomization of budget actions.

The existing LTT citation supports simultaneous risk testing. The mathematical primitives are credited as classical; the manuscript does not present them as new distribution-free inequalities. No numerical farm result or TV upper bound was added to W0.

## Remaining work after W3

Full-text theorem-level comparison with DARTH+ remains pending. W3 states conditional theory and clarifies the implementation boundary; it does not resolve the W0 empirical holds on source-profile acquisition, joint certification of the refresh lane, source-truth cost, shared-query bootstrap dependence, or empirical TV premises.
