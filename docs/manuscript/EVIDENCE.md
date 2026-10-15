# Current manuscript → fixed evidence

**Manuscript binding:** [artifact-manuscript-v4](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-manuscript-v4), October 15, 2026.

This release updates the paper's organization, analysis-and-evaluation framework exposition, protocol supplement, and approved overview. It adds no scientific measurements and changes no saved experimental inputs, decisions, statistics, or preceding release assets. The paper has 12 body pages plus one page of AI disclosure and references; this is a measured layout property, not a certification of submission compliance.

## Read or build this version

- Download `manuscript.pdf` and `manuscript-source.zip` from the release. The ZIP includes all six figure PDFs, bibliography, template, and compilation instructions. Upload its contents to Overleaf and use `main.tex` as the root.
- `study_design_protocol.md` is the separately readable supplementary protocol, also included in the source ZIP and [here](study_design_protocol.md).
- `overview.pptx`, `overview.pdf`, and `overview.png` are the approved Figure 1 in editable, vector, and preview formats. Unchanged Figures 2–6 editing sources remain in [artifact-delivery-v1](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-delivery-v1).
- `release-manifest.json` and `CHECKSUMS.sha256` bind the release files; `verification.json` records the actual packaging checks. `LICENSE`, `LUCIDE_LICENSE`, and `figure_asset_licenses.md` state the license scope. External datasets and third-party software retain their own terms.

## Follow the scientific evidence

Use the fixed tags below, not a moving `main` branch, when reproducing a result. The linked maps provide the inputs, commands, expected outputs, verification receipts, and remaining provenance gaps.

| Paper content | Fixed evidence entry | Verification boundary |
|---|---|---|
| Figures 2 and 4–6: transfer, deployed operating points, costs, answer lookup | [Original paper evidence map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-delivery-v1/artifact/EVIDENCE.md); [paper statistics](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-paper-v2/artifact/paper/README.md) | Saved-record aggregation and stated bootstrap routes, not new search/timing measurements |
| Figure 3: common-set summary cost and coverage | [Nine-table reconstruction](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-response-v1/artifact/RUNBOOK.md) | Saved-response analysis with declared numerical tolerances |
| Sections IV–V: construction conditions, cost decompositions, finite-support learning, qualification, boundary ties (P0–P11) | [Unified P0–P11 map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-deepening-v2/artifact/deepening/EVIDENCE.md); [runbook](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-deepening-v2/artifact/deepening/README.md) | Fixed claims and saved-response reconstruction; actual fresh-environment receipts specify the checks |
| SIFT1M boundary-tie supplement (P12) | [P0–P12 map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-deepening-v3/artifact/p12/EVIDENCE.md); [P12 runbook](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-deepening-v3/artifact/p12/README.md) | Fresh-environment Windows distance, scoring, and objective checks on saved material |
| New execution under original protocols | [Execution map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-delivery-v1/artifact/original_execution/EXECUTION_MAP.md) | Data acquisition and staged execution interfaces; tiny native CI is not a full-data rerun |

Theoretical optima use known target responses and do not supply a deployable decision rule. Deployment comparisons retain their own query roles, quality events, and actual risks. The History-Max acquisition ledger is not assigned to newly learned policies. These distinctions remain in the main paper.

## What v4 checks, and what it does not

The extracted source ZIP was compiled locally with Tectonic 0.17.0; every page's extracted text and size matched the delivered PDF. References, citations, figure identities, embedded fonts, and internal link destinations were checked. The bilingual section sources were checked for structural consistency. The current checks do not rerun ANN search, exact search, timing, bootstrap, or P0–P12 analyses, and do not replace the independently implemented scientific checks in the preceding releases.

Older releases retain their original paper snapshots. They are not silently replaced by this paper. `release-manifest.json` records the predecessor tag/asset identities observed when preparing v4.
