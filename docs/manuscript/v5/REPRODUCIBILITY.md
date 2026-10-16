# Reproduction guide / 复现层级说明

## Version / 版本

This guide accompanies the **unpublished submission-review package**. Its outer `VERSION_BINDING.json` identifies the exact PDF, Overleaf ZIP, supplementary protocol, figure PDFs and fixed evidence releases. `PACKAGE_CHECKS.json` records document/package checks, not new scientific results. No new public release is claimed.

本说明对应待作者审核的本地提交包。当前稿件及更新后的协议不是公开 v4 快照，不能从旧快照寻找新版协议第7节的支持门槛明细。公开证据继续从 [artifact-manuscript-v4](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-manuscript-v4) 进入；旧版本不覆盖。本文科学记录未变，稿件、引用与图形展示晚于该快照。P12/v3 对 SIFT1M 并列评分的修正优先于 v2 中“尚未解决”的历史说明。

## Verification levels / 验证层级

| Level | Available material and existing verification | Boundary / 边界 |
|---|---|---|
| Document build / 文档构建 | Current PDF, source, bibliography and six figure PDFs; extracted-source local compilation checked in accompanying receipt | Document consistency, not numerical reproduction; no online Overleaf build / 不等于科学复现 |
| Saved-record reconstruction / 保存记录重建 | Original statistics/intervals, mechanism objectives, learning and qualification outputs; inputs, configurations, scripts and expected results in fixed releases | Recomputes from the declared saved-input level, not necessarily raw vectors or original timing trials / 不能把重建均值与区间称为重新测量 |
| Independent algorithmic checking / 独立实现核查 | P0–P11 Linux reconstruction/checking receipt; P12 fresh Windows environment receipt | Independence concerns implementations and stated environments, not a separate research team; P12 uses saved exhaustive truth / 未重新执行全局精确搜索 |
| Original-procedure execution / 原始程序执行 | Data-access instructions, configurations, dependency identities, staged execution interfaces and resource gates | Portable-entry and synthetic tests do not establish full-scale end-to-end execution; historical provenance gaps remain / 不宣称全文原始流水线均已独立重跑 |

## Result-to-entry map / 结果与入口

Figure numbers below refer to the current paper. Resolve older section/table numbers by the named result and input.

| Current result | Fixed entry | Input and output scope |
|---|---|---|
| Fig. 2: direct transfer | [paper-v2 paper runbook](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-paper-v2/artifact/paper/README.md) | Saved query-cluster records → means/intervals conditional on registered builds; not the full original action grid |
| Fig. 3; original summary-cost and qualification analysis | [response-v1 runbook](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-response-v1/artifact/RUNBOOK.md) | Saved response archive and decisions → nine analysis tables |
| Fig. 4: locked working points and paired intervals | paper-v2 paper runbook | Locked policy matrices → ten operating points and paired intervals; original timing acquisition is upstream |
| Fig. 5, cost-component table and alternative costs | paper-v2 paper/narrative runbooks; response-v1 | Saved ledger → breakdown, conditional curves, thresholds and comparisons; not end-to-end service measurement |
| Fig. 6: answer memory and lookup | paper-v2 paper runbook | Saved object sizes and batch timings → displayed values; not memory remeasurement on a new interpreter |
| Transfer/recovery/Deep1M narrative results | [paper-v2 evidence map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-paper-v2/artifact/EVIDENCE.md) | Saved narrative inputs, archive and per-family commands; preserve each stated scope |
| Added theory, mechanism, learning and P11 | [deepening-v2 map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-deepening-v2/artifact/deepening/EVIDENCE.md) | `ICDE_P0-P11_artifact.zip`: inputs, configurations, expected outputs, checkers; support detail in local protocol Section 7 uses existing P7 summary/decomposition records |
| SIFT1M boundary ties, P12 | [deepening-v3 runbook](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-deepening-v3/artifact/p12/README.md) | `P12_artifact_review.zip` plus original SIFT HDF5 → scoring and 384 objectives; no deployment qualification/relearning or ANN rerun |
| Original response generation | [delivery-v1 execution map](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-delivery-v1/artifact/original_execution/EXECUTION_MAP.md) | Ten family entries with staged input/build/truth/profile/decision/timing paths; this later map supersedes older inventories saying no portable command exists |

## Environments and commands / 环境与命令

These are reproduction instructions, **not commands executed for this packaging revision**. Use separate environments, read the chosen runbook and its resource gates, and write to new output directories. Do not overwrite historical outputs or conceal a failed run by retrying under the same key.

### Original paper statistics

In a fixed `artifact-paper-v2` checkout, use Python 3.12 and its pinned requirements:

```sh
python -m pip install -r artifact/requirements-analysis.txt
python artifact/reproduce_paper.py --check-inputs
python artifact/reproduce_paper.py --output paper-reconstruction
```

The paper runbook estimates below 512 MiB working memory for this bounded entry, not for original ANN execution. Figure 2/4 use 5,000 resamples, seed 991 and the documented shared-query recipe. Nine-table and narrative entries have their own archives and commands linked above.

### P0–P11

Download the scientific ZIP from [deepening-v2](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-deepening-v2), extract as `deepening-bundle`, and use a fresh Python 3.11 environment:

```sh
python -m pip install -r deepening-bundle/requirements.txt
python deepening-bundle/rebuild.py --bundle deepening-bundle --verify-only
python deepening-bundle/rebuild.py --bundle deepening-bundle --output rebuilt
```

Launch gates require 5 GiB available RAM and 10 GiB free disk, with one logical CPU/library thread and the documented sampled guards. The final published Linux receipt passed after a documented numeric-string comparison fix in the P8 checker. Earlier failures remain recorded; scientific inputs and expected outputs were unchanged.

### P12

Follow the P12 runbook to extract `P12_artifact_review.zip` and install its pinned requirements in a fresh Python 3.11 environment. Acquire and verify the exact SIFT HDF5 through the package's licensed source:

```sh
python p12-bundle/p12_rebuild.py --hdf5 /path/to/sift-128-euclidean.hdf5 --output new-p12-output
```

Use the package-specific resource gates. The fresh-environment receipt is Windows, not Linux. Original vectors are external; saved exhaustive truth remains an input.

### Original-procedure execution

Use the delivery-v1 map and each family README for native builds, data identities, roles, seeds and resource requirements. One environment or small memory threshold does not cover all families. Some historical resource gates are conservative operational limits, not algorithmic minima.

## Interpretation and remaining boundaries / 解释与尚存边界

- A PASS covers its stated level. Reconstructing means/intervals, checking algorithms and remeasuring a system are distinct.
- Some native implementation checks lack full returned IDs; old reused binary objects have different provenance from newly built sources. The Ada-ef supplement retains an unobserved historical exit and incomplete acquisition timing. These gaps remain in the family execution map.
- Main History-Max/TG comparisons use achieved quality–cost points, not a matched-failure-rate efficiency ranking. Qualification sensitivity does not change this estimand.
- Deep1M learned-policy results do not share the History-Max acquisition ledger. Do not join them into a demonstrated learned-policy break-even result.
- `U` is unmeasured policy-minus-baseline cost, not total service latency. Repayment numbers are conditional component-accounting results.
- Final submission requires author approval and public availability of the current protocol/guide through a fixed version. Existing evidence URLs do not publish this local package. CMT, ORCID and COI completion remain separate author checks.

本轮只闭合待审核文件的版本对应和复现说明，未追加实验、改图或发布。完整原始科学流程的独立执行与官方合规认证不由本次文档检查替代。
