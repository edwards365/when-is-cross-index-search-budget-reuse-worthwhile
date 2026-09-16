# Independent SIGMOD 2027 route audit after Phase 6

## Applicable official standard

SIGMOD 2027 treats regular papers, Experiments & Analysis (E&A) studies, and
DI&DS papers as research-track submissions reviewed by the same committee. An
E&A contribution should provide new insights into strengths and weaknesses of
existing methods through an experimental survey, phenomenon analysis,
benchmark/dataset, reproducibility study, or user study. The title must end in
`: [Experiments & Analysis]`. The main paper limit is 12 pages excluding
references. Code, data, scripts, and notebooks are expected through an
anonymous link; a clean, executable artifact materially helps review even
though artifact availability is not an absolute acceptance condition.

Official sources consulted on 2026-09-17:

- https://2027.sigmod.org/calls_papers_sigmod_research.shtml
- https://reproducibility.sigmod.org/

## Current evidence state

The package now covers two external adaptive policies (DARTH and Ada-ef), two
100K datasets under seed rebuild and mixed 5% refresh, a Vamana-style native
action family, and an eight-build Deep1M scale check. The event is consistently
`Recall@10 < .95`; target build is the primary statistical unit; negative and
null results remain visible. Phase 2 shows that target-selection TCP
recalibration is safe and search-efficient on both refresh datasets, while raw
source reuse is unsafe. Phase 5 prevents the search-only result from being
misstated as full-lifecycle economics. Phase 6 supplies an anonymous smoke,
tables, figures, checksums, source commits, and claim boundaries.

## Evidence-based scores

### E&A route: 8.10 / 10

| Dimension | Score | Evidence and deduction |
|---|---:|---|
| E&A fit and relevance | 1.40/1.50 | Clear data-management phenomenon and strengths/weaknesses analysis across methods; title/paper still needs explicit E&A framing. |
| Insight and significance | 1.25/1.50 | Safety transfer failure is stable across methods, implementations, datasets, refresh, and scale; production consequences remain partly economic rather than measured end-to-end. |
| Statistical/semantic soundness | 1.45/1.50 | Fixed event, target-build inference, 5,000 bootstrap, LOTO/deletion, tails, censoring, and negative results; Vamana alignment is post-hoc and must stay labeled. |
| Breadth and baseline fairness | 1.30/1.50 | DARTH, Ada-ef, HNSW, Vamana-style, SIFT, Arxiv, and Deep1M; not a comprehensive survey of all adaptive ANN methods. |
| Reproducibility | 1.15/1.50 | Clean-clone smoke, 24 tests, tables/figures and ledgers pass; historical full replay still contains machine-specific paths and lacks one master installer/runner. |
| Economics/applicability | 0.75/1.00 | Search-only break-even is measured; truth/rebuild/control costs are not harmonized. |
| Presentation/claim discipline | 0.80/1.00 | Machine claim matrix and limitations are strong; final 12-page E&A paper-facing rewrite is not yet sealed. |

This is a credible E&A package, but not yet an 8.5+ package because a reviewer
cannot execute the complete historical matrix from one portable interface and
because the positive TCP result lacks a harmonized lifecycle cost denominator.

### Regular route: 7.05 / 10

| Dimension | Score | Evidence and deduction |
|---|---:|---|
| Method novelty | 0.95/1.50 | ICBA is a useful audit framework and TCP is a conditional recovery mechanism, but the strongest current contribution is empirical diagnosis. |
| Technical soundness | 1.35/1.50 | Safety semantics and inference are strong. |
| Empirical breadth | 1.30/1.50 | Multiple methods/families/datasets/refresh/scale. |
| Method effectiveness | 0.75/1.50 | Target recalibration is positive on two refresh datasets; raw transfer and audited source fallback have no deployable gain. |
| Significance | 0.90/1.50 | Important failure mode, but no broad end-to-end method superiority. |
| Reproducibility | 1.15/1.50 | Same portable-full-replay gap as above. |
| Presentation | 0.65/1.00 | Current evidence is not yet reorganized into a concise regular-paper method story. |

Regular is possible only with a deliberately scoped claim, but E&A is the
better-supported route. No score is raised by relaxing safety or tail gates.

## Hard blockers and high-value loop

1. **Portable full replay (hard blocker for 8.5+ artifact confidence).** Replace
   the eight historical hard-coded launch/analysis path contracts with CLI or
   environment data-root parameters, add a master setup/run/check interface,
   and test it from a neutral path without touching sealed raw inputs.
2. **Lifecycle cost closure (hard blocker for a strong TCP systems claim).**
   Audit existing logs for build, truth, profiling, certification, control,
   fallback, and serving time/counts. If components are unavailable, perform a
   preregistered timing-only replay on frozen inputs; never infer missing costs.
3. **Paper-facing E&A compliance.** Use the required title suffix, fit the main
   text in 12 pages, make phenomenon insights primary, keep TCP conditional,
   and map every headline table/figure to the artifact.
4. **Optional breadth.** Add another external method only if official code and
   matching action/risk semantics are available without extensive
   reimplementation. This is lower value than blockers 1--3.

Projected E&A score after items 1--3, assuming they pass without changing the
scientific claims: 8.65--8.90. A fourth external method can improve confidence
but is not required to cross 8.5.
