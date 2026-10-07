# 跨索引搜索预算复用：何时值得？

**When Is Cross-Index Search Budget Reuse Worthwhile?**

信息限制 · 质量恢复 · 条件成本收益

[English](README.md) · [复现入口](artifact/README.md) · [运行指南](artifact/RUNBOOK.md) · [证据导航](artifact/EVIDENCE.md) · [版本记录](CHANGELOG.md)

## 研究主线

**数据、查询和检索语义不变时，精确答案可以保持不变，但索引重建可能改变查询所需的搜索预算。** 本项目研究历史预算信息能够支持什么决策、目标侧证据如何改变部署，以及获取这些信息是否值得。

[![研究总览：信息限制、质量恢复与条件成本收益](docs/assets/research-overview.png)](docs/assets/research-overview.png)

*沿用论文已确定的总览图风格。点击查看原图；三个部分对应不同的研究判断，不表示自动成立的保证。具体范围见[图示说明](docs/OVERVIEW.md)。*

| 主线 | 研究内容 | 结果入口 |
|---|---|---|
| 信息限制 | 同一摘要合并不同需求；共同安全行动与额外保序约束 | [同条件摘要诊断](artifact/data/summary_information_bridge/) |
| 质量恢复 | 目标资格检查、锁定回退，以及目标校准固定预算对照 | [工作点与配对比较](artifact/EVIDENCE.md) |
| 条件收益 | 获取、共享、重复服务，以及有效精确答案的替代用途 | [成本账本与开销边界](artifact/EVIDENCE.md) |

实验覆盖十万级与近百万／百万级面板，但面板之间不只改变规模，不能据此隔离纯粹的规模效应。同条件经验最优成本是使用目标响应得到的诊断参照，不是可直接部署的算法。恢复质量、相对保守端点节省和历史信息的同风险增量优势，是不同判断。

## 快速开始

### 检查已发布结果

使用 Python 3.11 或更新版本，仅需标准库。以下命令固定到保存结果重建版本；后续执行入口另行版本化。

```sh
git clone --branch artifact-paper-v2 https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile.git budget-reuse
cd budget-reuse
python artifact/check_saved_results.py
```

检查文件身份及部分汇总算术，不写输出、不运行 ANN，也不重新生成置信区间。

### 从保存响应重建分析表

在[版本发布页](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-response-v1)下载 `summary-analysis-inputs.zip`（9.45 MB），依照[运行指南](artifact/RUNBOOK.md)建立固定依赖的隔离环境，然后运行：

```sh
python artifact/reproduce_summary.py --archive summary-analysis-inputs.zip --output reproduction-output
```

该入口重建九张摘要成本、资格敏感性与成本分项分析表。已记录的可移植性验证使用 Python 3.12.14、NumPy 1.26.4、SciPy 1.13.1：八张表字节一致，一张表在声明的数值容差内一致，决策不变。完整比较见[验证报告](artifact/receipts/portability_verification.json)。

### 重建论文统计与叙述面板

按[论文统计指南](artifact/paper/README.md)运行 `reproduce_paper.py`，重建图 2、4、5、6 的保存记录统计；图 3 使用上述九表入口。[叙述面板指南](artifact/narrative/README.md)说明原始网格记录、100K／Deep1M 恢复、摘要歧义、刷新与替代成本的重建命令和所需发布附件。这些路径重算所声明的统计及区间，不重新测量历史搜索时间。

## 当前交付的三个层次

| 层次 | 固定入口 | 能够确认什么 |
|---|---|---|
| 保存结果重建 | [`artifact-paper-v2`](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-paper-v2)；九表输入仍取自不可变的 `artifact-response-v1` | 按证据导航重建论文已交付的点估计、区间和成本算术，不等于重新执行 ANN |
| 当前论文与图形 | [`artifact-delivery-v1`](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-delivery-v1) | Overleaf 源码、当前 PDF、六图可编辑包及其数据／生成入口；作者个人信息仍按要求暂缓 |
| 原协议的新执行入口 | 同一交付版本中的[十类实验执行导航](artifact/original_execution/EXECUTION_MAP.md) | 数据获取、依赖身份、分阶段命令、独占新输出与收据；实际检查范围由 `DELIVERY.json` 和对应 CI 记录说明 |

保存统计重建、合成／微型原生测试和全规模新实验是不同验证层次。新入口提供响应、锁定决策及测量记录的生产路径；只有明确列出的新分析入口才进一步汇总新输出，不能把保存结果重建程序当作任意新测量的自动导入器。本次交付没有独立重测全部原始 ANN 或计时面板，也没有补造历史缺失的来源、退出状态或获取成本。

详细范围见[工件覆盖表](artifact/README.md#coverage)、[证据导航](artifact/EVIDENCE.md)和[执行范围](artifact/EXECUTION_SCOPE.md)。获取执行入口时应使用其固定交付版本，不要假定较早的 `artifact-paper-v2` 已包含后续新增命令。第三方数据与依赖仍须按各自许可获取；此处不宣称论文录用、工件徽章或全部独立复现。

## 目录与协作

| 入口 | 用途 |
|---|---|
| [`artifact/`](artifact/README.md) | 已发布证据、校验、输入清单与复现入口 |
| [`docs/`](docs/README.md) | 按阅读目的组织的导航与研究图示说明 |
| [仓库整合状态](artifact/REPOSITORY_STATUS.md) | 公开内容与研究分支的关系 |
| [贡献指南](CONTRIBUTING.md) | 提交问题、验证变更、保护冻结证据 |
| [历史项目介绍](docs/history/README_before_icde_artifact.md) | 保留旧研究方向，不作为当前论文主张 |

旧的 `python/`、`cpp/`、`configs/`、`scripts/` 等目录保持原位，不应将其中所有历史入口视为当前工件流程。请勿为检查发布包而重跑冻结实验或覆盖其原始输出。

引用信息见 [CITATION.cff](CITATION.cff)，使用时注明版本或提交。项目代码和自产材料采用既有 [MIT 许可证](LICENSE)；第三方组件及外部数据的许可不因此改变。
