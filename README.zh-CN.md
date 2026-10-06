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

使用 Python 3.11 或更新版本，仅需标准库。以下命令固定到分析发布版本；`main` 还包含后续文档改进。

```sh
git clone --branch artifact-response-v1 https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile.git budget-reuse
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

## 目前公开到哪一步

**当前是 `artifact-response-v1` 分析工件预发布版，不是完整论文工件。**

- 已提供：部分结果、配对区间、成本记录、文件清单、保存响应输入包和九表重建入口。
- 已提供：论文总览图及文档导航；不改变既有实验结果。
- 尚未纳入此发布：投稿版 TeX、可编辑完整图集及完整 PDF 构建环境。
- 尚未完整交付：全部原始 ANN 面板执行与 bootstrap 重建。

详细范围见[工件覆盖表](artifact/README.md#coverage)。原生 DARTH/Vamana 单图检查与多图迁移实验的证据用途不同；此处不宣称论文已录用、已获工件徽章或已完成全部独立复现。

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
