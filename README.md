<div align="center">

# When Is Cross-Index Search Budget Reuse Worthwhile?

**Information limits · Quality recovery · Conditional reuse costs**

An experimental and analytical study of historical search-budget reuse across ANN indexes.

[![Artifact checks](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/actions/workflows/artifact.yml/badge.svg?branch=main)](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/actions/workflows/artifact.yml)
[![Response-analysis release](https://img.shields.io/badge/release-artifact--response--v1-087F99)](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-response-v1)
[![MIT license](https://img.shields.io/badge/license-MIT-64748B)](LICENSE)

[Overview](#research-overview) · [Quick start](#quick-start) · [Artifact](artifact/README.md) · [Runbook](artifact/RUNBOOK.md) · [中文](README.zh-CN.md)

</div>

## Research overview

**Rebuilding an index can change the budget a query needs—even when its exact answer does not change.** We study what historical information can support, how target-side evidence changes deployment, and when reuse is worth its acquisition cost.

[![Research overview: information limits, quality recovery, and conditional value](docs/assets/research-overview.png)](docs/assets/research-overview.png)

*Three distinct questions, not three automatic guarantees. Click the figure to enlarge; see the [figure guide](docs/OVERVIEW.md) for its scope and notation.*

| Research question | What the study examines | Explore the evidence |
|---|---|---|
| **What can history distinguish?** | Common safe actions, summary compression, and additional order restrictions | [Same-target summary diagnostics](artifact/data/summary_information_bridge/) |
| **What does target evidence change?** | Candidate qualification, locked fallback, and target-calibrated fixed budgets | [Operating points and paired comparisons](artifact/EVIDENCE.md) |
| **When is reuse worth its cost?** | Acquisition, sharing, repeated service, and valid-answer reuse | [Cost ledgers and conditional boundaries](artifact/EVIDENCE.md) |

The study includes 100K and roughly million-vector panels. These panels differ in more than scale; they are not a controlled measurement of scale alone. Target-informed empirical cost optima are diagnostic references, not deployed policies. Quality recovery and savings against a conservative endpoint do not establish a same-risk cost advantage over simpler alternatives.

## Quick start

### 1. Check the released results

Use **Python 3.11+**. This check needs only the standard library and writes no outputs.

```sh
git clone --branch artifact-paper-v2 https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile.git budget-reuse
cd budget-reuse
python artifact/check_saved_results.py
```

The command checks file identity and selected aggregation arithmetic. It does not rerun ANN search or recompute confidence intervals. The tag pins this paper-statistics supplement; the earlier `artifact-response-v1` release remains unchanged.

### 2. Reconstruct nine analysis tables

Download `summary-analysis-inputs.zip` (**9.45 MB**) from the [versioned release](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-response-v1). Follow the [runbook](artifact/RUNBOOK.md) to create an isolated environment with the pinned dependencies, then run:

```sh
python artifact/reproduce_summary.py --archive summary-analysis-inputs.zip --output reproduction-output
```

This reconstructs selected summary-cost, qualification-sensitivity, and cost-component tables from saved responses. The recorded portability check used Python 3.12.14, NumPy 1.26.4, and SciPy 1.13.1: **eight tables matched byte-for-byte; one matched within declared numerical tolerances, with decisions unchanged**. See the [verification report](artifact/receipts/portability_verification.json).

## Release scope

### 3. Reconstruct numerical-figure statistics

With the pinned analysis environment, run:

```sh
python artifact/reproduce_paper.py --output paper-reconstruction
```

The [paper supplement](artifact/paper/README.md) supplies small saved-record inputs directly in Git. Its clean-export check reconstructs 36 migration/paired intervals, ten operating points, 320 cost-curve points and 80 batch-lookup means. Figure 3 uses the nine-table route above. See the [recorded check](artifact/receipts/paper_reconstruction.json) and the [whole-paper coverage map](artifact/EVIDENCE.md).

### 4. Reconstruct narrative panels

The [narrative runbook](artifact/narrative/README.md) adds 96 original grid CSVs, 100K/Deep1M recovery records, demand labels, refresh arrays and alternative-cost reconstruction. It recomputes ten additional reported intervals and verifies the raw-to-Figure-2-cluster path. Historical native inclusion/measurement records are [separately documented](artifact/native_evidence/README.md).

**`artifact-paper-v2` supplements the immutable `artifact-paper-v1` and `artifact-response-v1` releases. It is saved-record reconstruction, not complete original-experiment reproduction.**

| Material | Public status |
|---|---|
| Selected result tables, paired intervals, and cost records | Available in [`artifact/`](artifact/README.md) |
| Saved-response archive and portable nine-table reconstruction | Available in the [release and runbook](artifact/RUNBOOK.md) |
| Conceptual overview | Available above, in the approved manuscript visual style |
| Submission-version TeX, editable figures, and complete PDF build | Not yet curated into this release |
| Numerical-figure saved-record statistics, including Figure 2/4 intervals | Supplied by the paper supplement |
| Narrative-panel reconstruction | Supplied for the listed panels; remaining diagnostic/native upstream gaps are explicit |
| Full original ANN execution | Incomplete; input/source/configuration dependencies are listed in the evidence map |

The [coverage table](artifact/README.md#coverage) distinguishes supplied materials from remaining work. Single-index native DARTH/Vamana checks do not substitute for multi-build transfer evidence. No publication acceptance, artifact badge, or complete independent reproduction is claimed.

## Repository guide

```text
artifact/          Released results, manifests, checks, and analysis runbook
docs/              Documentation index, overview guide, and historical context
.github/           Continuous checks and contribution templates
CITATION.cff       Repository citation metadata
CONTRIBUTING.md    Contribution and evidence-preservation guidelines
CHANGELOG.md       Public release and presentation history
```

Start with the [documentation index](docs/README.md) or [paper-to-evidence map](artifact/EVIDENCE.md). Earlier code under `python/`, `cpp/`, `configs/`, and `scripts/` remains in place; those directories are not all current artifact entry points. The [repository status](artifact/REPOSITORY_STATUS.md) explains the branch reconciliation, and the [historical README](docs/history/README_before_icde_artifact.md) preserves the preceding research agenda.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before changing experiments or frozen evidence. For reproduction problems, [open a reproducibility issue](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/issues/new?template=reproducibility.yml) with the release, environment, command, and sanitized output.

## Citation and license

Use [CITATION.cff](CITATION.cff) for repository metadata and record the release or commit used. This metadata does not describe an accepted publication. Code and project-generated materials use the existing [MIT license](LICENSE); third-party components retain their licenses, and external vector datasets are not redistributed by this release.
