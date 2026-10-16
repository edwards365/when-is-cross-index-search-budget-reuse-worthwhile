# 稿件配套协议与补充分析 / Supplementary protocol and analyses

状态：2026-10-15本地合稿配套版本，尚未发布；在artifact-manuscript-v4基础上补齐第7部分的支持门槛明细。正文III-C按文件名引用，IV/V按下列章节定位。实验协议、样本、权重和结果不变。这是配套说明，不是独立可执行的完整复现包。

This supplement accompanies the current unpublished local manuscript source ZIP and extends the supplement in artifact-manuscript-v4. Sections 4–7 preserve protocol and numerical details moved from the main text and existing theoretical examples. No experiments or statistical analyses were rerun for this revision.

## 1. 估计单位与重采样

| 实验 | 重采样及范围 |
|---|---|
| 新鲜查询主要比较 | 目标等权，各目标内查询等权。5,000次交叉bootstrap独立抽取目标ID和共享查询ID，各策略使用同一重采样索引。重复计时按下表规定先汇总。区间描述登记构图及查询所代表的变异。 |
| 十万级直接迁移 | 固定登记构图；每次抽取查询时，保留该查询在全部有向构图对上的结果。 |
| 十万级恢复、Deep1M一档上移恢复 | 交叉重采样目标构图与查询。Deep1M一档上移恢复另报告仅抽目标或仅抽查询的敏感性区间。该说明不适用于Deep1M学习分析。 |
| 百万级成员刷新 | 两种成员状态共同重采样构图对与共享查询。 |
| 机制、学习与资格敏感性 | 报告描述性逐目标结果，不新增bootstrap区间。 |
| 百万级Faiss记录权重 | 24条记录等权，保留13种序列化内容的重复次数；重复内容不是独立构图实现。此披露同时保留在III-C。 |

### English

Fresh-query paired estimates weight targets equally and queries equally within each target. We use 5,000 crossed bootstrap replicates, independently resampling target IDs and shared query IDs with the same resampled indices for every policy. Repeated measurements are summarized according to each timing protocol before resampling. The intervals describe variation over the registered builds and queries.

The 100K transfer intervals keep the registered builds fixed and retain all directed-pair results for each sampled query. Intervals for the 100K recovery study and the Deep1M one-rung recovery study use crossed target-build and query resampling. The latter also reports target-only and query-only sensitivities. Million-scale refresh jointly resamples build pairs and shared queries for both membership states. Mechanism, learning, and qualification sensitivities report descriptive target-level results without new bootstrap intervals.

Million-scale Faiss retains equal weights for its 24 records, including multiplicities of 13 serialized contents; repeated contents are not independent graph realizations.

## 2. 并列敏感性操作与比较集合

SIFT边界并列评分使用整数平方L2距离，只允许第k近邻距离处的等距返回项互换。遗漏的更近邻居仍计为遗漏，不能由边界项替代。

32图实验区分固定行动重评分和重新学习、资格检查，并分别检查保留源标签与重算源标签。百万级SIFT依据原始向量核验保存返回结果的距离。成本敏感性保留原端点达标子集，同时单独报告完整集合可行性。主部署比较仍使用原ID评分。

### English

SIFT boundary-tie scoring uses integer squared L2 distances and allows returned neighbors tied at the kth-neighbor distance to substitute for one another. Missing strictly closer neighbors still count as omissions and cannot be replaced by boundary ties.

The 32-graph study separates fixed-action rescoring from relearning and qualification, and tests both retained and recomputed source labels. Million-scale SIFT checks saved-return distances against original vectors. Cost sensitivities retain the original endpoint-passing subsets and separately report full-set feasibility. The principal deployment comparisons retain ID scoring.

## 3. 计时配置

共同设置：固定CPU亲和、单线程；搜索计时排除加载与预热。

| 实验 | 已记录环境或路径 | 重复与汇总 |
|---|---|---|
| 十万级Faiss恢复及基线比较 | Faiss 1.8.0 AVX2；AMD EPYC 7542 | 对每个数据集／目标构图／查询／行动单元，先取七次交错重复的算术均值，再关联锁定策略 |
| 新鲜查询 | hnswlib 0.8.0；原生墙钟计时 | 七次重复，均值 |
| 百万级Faiss补充 | AVX2；Python单查询API，包含派发与分配 | 每个构图／行动含5次重复×1,000条查询；合并这两个维度的5,000个计时，分别报告算术均值和中位数；不裁剪重复 |

百万级Faiss补充实验未核验竞争任务排除和处理器频率控制；其GENERIC距离计数来自另一实现，不能与AVX2计时相除得到单位距离耗时。这些解释边界同时保留在III-C。

### English

Search timings use pinned single-thread execution and exclude loading and warmup. The 100K Faiss 1.8.0 AVX2 recovery and baseline studies on an AMD EPYC 7542 first average seven interleaved repetitions within each dataset/target-build/query/action cell, then attach locked policy decisions. Fresh-query hnswlib 0.8.0 uses means of seven native wall-clock repetitions. The million-scale Faiss AVX2 supplement records five Python single-query API repetitions for each of 1,000 queries, including dispatch and allocation. For each graph/action, it pools these 5,000 timings over the repetition and query axes and reports both their arithmetic mean and median, without trimming repetitions.

汇总依据：十万级恢复与基线比较的原分析脚本 `analyze_s9_3_runtime.py`、`analyze_s9_4_runtime.py` 中，`technical_cells()`均按上述单元取均值。百万级Faiss的 `latency_core.py` 保存形状为“行动×5×1,000”的计时数组，`mean_ns_by_action`与`median_ns_by_action`均对后两个维度归约；原身份核查脚本独立核验这两个字段。历史汇总表同时列出均值、中位数及p95/p99，属于补充描述统计，不是History-Max获取成本或生命周期核算的计时输入。

Aggregation provenance: `technical_cells()` in the original `analyze_s9_3_runtime.py` and `analyze_s9_4_runtime.py` averages the seven repetitions. For million-scale Faiss, `latency_core.py` stores an action-by-5-by-1,000 array; `mean_ns_by_action` and `median_ns_by_action` reduce its last two axes. The original identity checker independently verifies both fields. The historical summary table reports mean, median, and p95/p99 as supplementary descriptive statistics, not as timing inputs to History-Max acquisition or lifecycle accounting. These sources are accessible through the fixed delivery-v1 execution map under `recovery_100k` and `faiss_1m`.

Exclusion of competing host workloads and control of processor frequency were not verified for this supplement. Its GENERIC distance counter is a separate implementation, so these two paths do not support time-per-distance ratios.

## 4. 候选筛选与目标资格 / Candidate screening and qualification

所有下列主要检查使用召回阈值τ=0.95、容忍失败率ε=0.05及正文V-A的单侧Clopper–Pearson上界。筛选形成候选；独立角色的资格查询决定部署，不重新拟合候选。查询角色与共享关系由正文III-B说明。

The principal checks below use τ=0.95, ε=0.05, and the one-sided Clopper–Pearson upper bound in Section V-A. Screening constructs a candidate; held-out qualification selects deployment without refitting it. Query-role separation and sharing follow Section III-B.

| Study / 实验 | Candidate screening / 候选筛选 | Target qualification / 目标资格 |
|---|---|---|
| 100K one-rung recovery / 十万级一档上移 | Smallest source action passing the design check at α=0.05/J over J actions; endpoint if none passes. Raise by one grid position, capped at endpoint. / 源侧J行动筛选取最小通过行动，再上移一档；无通过行动或越过上限时用端点。 | Candidate and endpoint raw failures checked separately at α=0.025 each. / 候选与端点自身失败事件分别以0.025检查。 |
| Deep1M one-rung recovery / Deep1M一档上移 | Same smallest-action rule, but α=0.05 per source action. / 同一取最小行动规则，源侧每行动α=0.05。 | Separate raw checks at 0.025 each. / 同上。 |
| Fresh-query History-Max / 新鲜查询History-Max | Preset maximum of seven stable-tail labels; endpoint for any no-finite-tail label. No fitted target mapping. / 预设七源标签最大值；任一无有限尾则用端点，不拟合目标映射。 | Candidate-or-endpoint union failure at 0.05, and endpoint failure at 0.05. / 并集失败及端点失败各以0.05检查。 |
| Fresh-query TG500/TG1000 / 新鲜查询TG | Eleven selection-role actions screened at 0.05/11; minimum-mean-NDC eligible action, or endpoint if none passes. / 选择角色上十一行动作多重比较调整，在通过者中取平均NDC最少者；无通过者取端点。 | Disjoint qualification-role queries; separate raw checks at 0.025 each. / 独立资格角色，候选与端点自身失败事件各以0.025检查。 |
| Fixed-1600 | No screening. / 无筛选。 | Same separate raw checks as TG. / 与TG相同。 |
| Learned Vector, Maximum, Hierarchical / 学习映射 | Supported cells have at least five design observations; choose the minimum-mean-NDC action passing all observations, ties to lower action index. Query fallback follows V-A. / 支持门槛为五，单元内全部观测达标后优化平均NDC，成本并列取较小行动序号；回退见V-A。 | Separate raw checks at 0.025 each. / 候选与端点自身失败事件各以0.025检查。 |
| Learned-study target-calibrated comparator / 学习实验目标校准参照 | Six design-role actions screened at 0.05/6; minimum-mean-NDC eligible action, or endpoint. Deep1M comparator added after the learning results. / 六行动作多重比较调整，选最省NDC的通过者，否则端点；Deep1M参照为观察学习结果后追加。 | Separate raw checks at 0.025 each. / 同上。 |

Fresh-query and learned-policy comparisons require an eligible endpoint. Both checks passing selects the candidate; only the endpoint passing selects the endpoint; endpoint failure prevents deployment on that target. Source-screening levels are not target-deployment guarantees. The per-check bounds are not a simultaneous guarantee over every target and method.

新鲜查询与学习比较均要求端点合格：两项通过选候选，仅端点通过选端点，端点不通过则不在该目标部署。源侧筛选水平不是目标部署保证；逐检查上界也不构成覆盖全部目标和方法的联合保证。

## 5. 迁移扩展的事件与结果 / Transfer-extension events and results

| Setting / 条件 | Policy and event / 策略与事件 | Saved result / 保存结果 |
|---|---|---|
| Million-scale fixed membership, hnswlib / 百万级固定成员 | Source-calibrated fixed action; candidate-or-endpoint union failure / 源校准固定行动，候选或端点失败并集 | SIFT 1.72%, Arxiv 0.90%; none of 56 directions exceeds 5% empirically / 56方向经验值均不超过5% |
| 100K membership refresh / 十万级成员刷新 | Replay unchanged policy; change in actual failure / 重放不变策略，实际失败率变化 | SIFT +2.92 pp, Arxiv +4.05 pp; both paired intervals positive / 配对区间均为正 |
| Million-scale membership refresh / 百万级成员刷新 | Candidate-or-endpoint union before fallback / 回退前候选或端点并集失败变化 | SIFT +0.425 pp, Arxiv +0.050 pp; both paired intervals include zero / 两个区间均跨零 |

These are different policies, grids, query-role designs, and events, not a common scale-effect estimate. Refresh also changes reference answers. The fixed-membership extension does not transfer the 100K query-specific first-passing labels.

以上不是同一规模效应的估计：策略、网格、查询角色及事件均有区别。成员刷新还会改变参考答案。百万级固定成员扩展迁移的不是十万级逐查询首个达标标签。

## 6. 压缩与保序的有限例子 / Finite examples for compression and order

These are existing mathematical examples, not ANN measurements. Queries have equal positive weights. Costs below follow the displayed action order; safe sets are specified explicitly. Fine cells are individual queries unless stated otherwise. All compared optima are feasible and finite. Compression gap means coarse minus fine optimum; order gap means ordered-coarse minus unordered-coarse optimum.

以下为已有数学例子，不是ANN测量。查询正权重且等权，成本数组按行动顺序排列；未特别说明时细单元为单条查询。各比较均可行且最优值有限。压缩差是粗摘要减细摘要最优值，保序差是粗摘要保序最优减无保序最优。

| Example / 例子 | Safe sets, costs and cells / 安全集、成本及单元 | Implication / 结论 |
|---|---|---|
| Different tail demands, no loss / 需求不同但无损 | Actions 0<1<2; S₁={0,1,2}, c₁=(5,1,3); S₂={1,2}, c₂=(9,1,3); merge the two singleton cells. | Both cells minimize at action 1; compression gap 0. / 共同最优为行动1，压缩无损。 |
| Equal tail demands, positive loss / 需求相同但有损 | Same three actions; both safe sets complete; c₁=(1,5,6), c₂=(5,1,6); merge both cells. | Fine mean cost 1, coarse mean cost 3; gap 2. / 需求相同不能保证成本最优选择兼容。 |
| Compression dominates / 压缩代价较大 | Same three actions, all safe; c₁=(0,10,20), c₂=c₃=(20,10,0); coarse cells {1,2}<{3}. | Fine optimum 0; coarse optimum 20/3, attained in order by (2,2); compression gap 20/3, order gap 0. |
| Order dominates / 保序代价较大 | Actions 0<1, both safe; two singleton cells ordered 1<2; c₁=(10,0), c₂=(0,10); no merging. | Unordered optimum 0 uses (1,0); best ordered mean cost 5; compression gap 0, order gap 5. |

The examples rule out a universal ordering of the two penalties. They do not predict which penalty will dominate a new ANN condition. Complete minimizing sets matter when costs tie; selecting one arbitrary minimizer can conceal a compatible ordered sequence.

例子排除了两类代价的普遍排序，但不能预测新的ANN条件中哪种更大。成本并列时必须考虑完整最优集合，任意选一个最优行动可能掩盖兼容的保序序列。

## 7. 学习归属与工作点明细 / Learning attribution and operating-point details

### Deep1M ID-scoring learning comparison

There are 4,000 evaluation query–target cells (eight equally weighted targets, 500 shared queries). Vector falls back on 586 cells: 424 unseen, 157 below the support threshold, and 5 without a common safe training action. Maximum falls back on 128 cells, all without a common safe training action. These are query-level fallbacks; both policies pass target qualification on all eight targets.

4,000个评估单元由八个等权目标和500条共享查询组成。Vector回退586个：未见424、支持不足157、训练无共同安全行动5；Maximum回退128个，全部由于训练无共同安全行动。这些是查询级回退，两策略在全部目标上均通过资格检查。

| Locked deployment / 锁定部署 | Failures / 失败数 | Mean NDC / 平均NDC |
|---|---:|---:|
| Vector | 33 | 5820.348 |
| Maximum | 40 | 5228.836 |
| Target-calibrated (post hoc) / 目标校准（事后） | 69 | 7227.518 |
| Endpoint / 端点 | 23 | 11362.814 |

| Vector / Maximum branch / 执行分支 | Cells / 单元数 | Contribution to full-sample NDC difference / 全样本差额贡献 | Failure-count difference / 失败数差 |
|---|---:|---:|---:|
| Both learned / 均学习 | 3406 | −70.775 | +4 |
| Vector fallback, Maximum learned / 向量回退、最大标签学习 | 466 | +683.396 | −11 |
| Both fallback / 均回退 | 120 | 0 | 0 |
| Vector learned, Maximum fallback / 向量学习、最大标签回退 | 8 | −21.108 | 0 |
| Total / 合计 | 4000 | +591.512 | −7 |

Contributions fix the original actions and full-sample weights, without subgroup retraining or reoptimization. Displayed components are rounded to three decimals; the total is computed before rounding. The main-text integer difference 592 is rounded from 591.512, not obtained by subtracting the displayed integer means 5820 and 5229. The decomposition identifies where the observed difference occurs, not the effect of removing fallback.

贡献固定原行动及全样本权重，不对子集重训练或重优化。分项显示到三位小数，总计在取整前计算。正文592来自591.512取整，不是显示均值5820与5229之差。归属说明差额集中在哪里，不表示取消回退的因果效果。

### Fresh-query comparison and qualification sensitivity

| Quantity / 量 | SIFT | Arxiv |
|---|---:|---:|
| History-Max failure reduction versus TG1000, pp, paired 95% interval / 相对TG1000的失败率降低及配对区间 | 1.0375 [0.4375, 1.7750] | 0.6625 [0.1500, 1.1750] |
| TG1000 evaluation failure / 评估失败率 | 2.0125% | 1.0125% |
| SIFT TG1000 under union/0.025 / 并集0.025条件下SIFT TG1000 | 1.8125%; mean NDC 8,342 | Not applicable / 不适用 |

Holding candidates and queries fixed, the 2×2 raw/union and α=0.05/0.025 check changes only SIFT TG1000, which sends one target to the endpoint under union/0.025. History-Max, TG500, and Fixed-1600 retain their decisions; all settings cover eight targets. These comparisons retain achieved, not matched, failure rates. Higher History-Max NDC point estimates have difference intervals crossing zero on both datasets; its API-time difference has a positive interval on SIFT and crosses zero on Arxiv, as reported in V-D.

2×2检查固定候选与查询，只改变SIFT TG1000：并集0.025下一个目标改用端点。History-Max、TG500和Fixed-1600决策不变，所有设置覆盖八个目标。实际失败率并未匹配；两个数据集NDC差区间均跨零，API时间差仅SIFT区间为正，Arxiv跨零，正文V-D保留该披露。

### 支持门槛与资格选择 / Support thresholds and qualification

#### 中文说明

支持门槛是一个摘要单元学习预算所需的最少设计观测数。主分析使用预先规定的门槛 5；敏感性分析检查 1、2、5、10、20，不根据评估结果重新选择主门槛。以下完整列出 Hierarchical 相对 Maximum 的三个条件、五档门槛。Vector 比较保留在同一 `summary.csv` 中。

每个条件包含八个目标与每目标 500 条共享评估查询，总分母为 4,000。平均 NDC 差采用目标等权、目标内查询等权。失败差为次数，不是百分点。负数表示 Hierarchical 更低；零值也保留。所有结果使用原始 ID 评分，是保存响应上的描述性比较，没有新增置信区间。

“选择调整”是 Hierarchical 从候选到部署的变化，减去 Maximum 对应的变化。候选差加净选择调整等于部署差。该恒等式追踪资格选择实际改变的执行行动，不是总体因果效应估计。

#### English text

The support threshold is the minimum number of design observations required to learn an action for a summary cell. The main analysis uses the prespecified threshold of five. Sensitivity results cover thresholds one, two, five, ten, and twenty without selecting a new main threshold from evaluation outcomes. The table includes every condition and threshold for Hierarchical minus Maximum; comparisons with Vector remain in the same source CSV.

Each condition contains eight equally weighted targets and 500 shared evaluation queries per target, giving a denominator of 4,000. NDC differences are per-query means; failure differences are counts, not percentage points. Negative values favor Hierarchical, and zero differences are retained. These saved-response comparisons use original ID scoring and are descriptive, without new confidence intervals.

The net selection adjustment subtracts Maximum's candidate-to-deployment change from Hierarchical's change. Candidate difference plus net selection adjustment equals deployed difference. This identity attributes changes to the actions selected by qualification; it does not estimate a population causal effect.

#### 完整对照 / Complete Hierarchical-minus-Maximum comparison

SIFT100K 的两个条件均使用 `efConstruction=200`，分别为 `M=16` 和 `M=32`，不应与下方 `M=16, efConstruction=100` 的另一例子混用。Both SIFT100K conditions below use `efConstruction=200`; the `efConstruction=100` example below is separate.

数值按保存 CSV 精度列出，不将小数位数视为统计精度。Values retain the saved CSV precision, not a claim of statistical precision.

| Condition / 条件 | Support / 门槛 | Candidate mean NDC gap / 候选差 | Net selection adjustment / 净选择调整 | Deployed mean NDC gap / 部署差 | Candidate failure gap / 候选失败差 | Selection failure adjustment / 选择失败调整 | Deployed failure gap / 部署失败差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Deep1M | 1 | -220.04 | 1355.7825 | 1135.7425 | 25 | -23 | 2 |
| Deep1M | 2 | -179.071 | 0 | -179.071 | 16 | 0 | 16 |
| Deep1M | 5 | -91.8835 | 0 | -91.8835 | 4 | 0 | 4 |
| Deep1M | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| Deep1M | 20 | 0 | 0 | 0 | 0 | 0 | 0 |
| SIFT100K-M16 | 1 | -223.922 | 630.6665 | 406.7445 | 177 | -166 | 11 |
| SIFT100K-M16 | 2 | -133.10625 | 386.50475 | 253.3985 | 69 | -75 | -6 |
| SIFT100K-M16 | 5 | -39.9515 | 0 | -39.9515 | 11 | 0 | 11 |
| SIFT100K-M16 | 10 | -12.79725 | 0 | -12.79725 | 0 | 0 | 0 |
| SIFT100K-M16 | 20 | 0 | 0 | 0 | 0 | 0 | 0 |
| SIFT100K-M32 | 1 | -301.78 | 979.16725 | 677.38725 | 201 | -189 | 12 |
| SIFT100K-M32 | 2 | -170.237 | 631.2985 | 461.0615 | 63 | -70 | -7 |
| SIFT100K-M32 | 5 | -73.8 | 0 | -73.8 | 24 | 0 | 24 |
| SIFT100K-M32 | 10 | -16.33875 | 0 | -16.33875 | 1 | 0 | 1 |
| SIFT100K-M32 | 20 | -10.55325 | 0 | -10.55325 | 0 | 0 | 0 |

门槛 1 时，Hierarchical 在 Deep1M、M16、M32 上分别有 2、5、5 个目标回退，Maximum 候选全部通过。门槛 5 时，两种策略在所有目标均通过。较低候选计算量与较低部署计算量因此不能互相替代；同时，各工作点的实际失败次数不同，不能视为同风险效率排序。

At support one, Hierarchical falls back on two, five, and five targets in Deep1M, M16, and M32, respectively, while all Maximum candidates pass. At support five, both policies pass on every target. Lower candidate work therefore need not mean lower deployed work. The operating points also have different failure counts, so the table is not an equal-risk efficiency ranking.

#### 另一构图条件的资格反转 / Qualification reversal in another construction condition

以下 SIFT100K `M=16, efConstruction=100` 例子及完整算术，不与上表 `efConstruction=200` 的支持门槛扫描混用。该例采用已报告的保存结果。

在该条件中，Maximum 在全部八个目标通过资格检查，行动保持不变。Hierarchical 候选相对 Maximum 的平均 NDC 低 48.17，但失败多 25 次。一个目标回退到端点后，Hierarchical 全样本平均 NDC 增加 65.32，失败减少八次。因此部署后的差额变为 NDC 高 17.15、失败多 17 次。差额均使用全部 4,000 个评估查询--目标单元。此例说明目标级资格选择如何改变实际执行策略及成本排序。

In the SIFT100K condition with `M=16` and `efConstruction=100`, Maximum passes qualification on all eight targets, leaving its actions unchanged. The Hierarchical candidate uses 48.17 fewer mean NDC but has 25 more failures than Maximum. Fallback on one target adds 65.32 NDC to Hierarchical's full-sample mean and removes eight failures. Its deployed difference is consequently 17.15 more NDC and 17 more failures. All differences use the full 4,000 evaluation query–target cells. This existing construction example shows how target qualification changes the executed policy and its cost ordering; it is separate from the support sweep above.

## 8. 合稿承接位置与来源 / Locations and provenance

- III-C保留主要估计方法、配对原则、记录权重和计量含义；本文件第1、3部分承接分流的协议细节。
- 对应的IV/V敏感性结果必须承接第2部分的比较集合与操作身份。尤其不能省去“固定原端点达标集合、另报全体可行性”，或把重评分与重学写成同一实验。
- 本轮正文明确引用源码包内的study_design_protocol.md，随本地更新代码包交付；公开artifact-manuscript-v4与artifact-deepening-v3保持不变，未纳入本轮新增的支持门槛说明。
- V-A的筛选细则移至第4部分；IV-A迁移扩展的原数值移至第5部分；IV-C有限例子见第6部分；V-C/V-D的计数、取整与原始精度见第7部分。正文仍保留事件差别、风险、集合与事后参照等解释条件。
- 第7部分的门槛表对应固定证据包内P7的`hierarchy_path_transfer_20261011_v1/summary.csv`与`decomposition.csv`；Vector对照亦保留在同一summary.csv。
- 新增说明依据已有`theory_conditions.md`、`p3_results_analysis.md`、`p7_results_analysis.md`及分流前正文；没有生成新测量或事后修改协议。
- 公开定位：源码包的 `sections/study_design.tex`、`sections/quality_recovery.tex`；P0—P12输入、分析代码和实际验证路径见[固定证据导航](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/blob/artifact-manuscript-v4/docs/manuscript/EVIDENCE.md)。上述报告名是原研究记录的来源标识，不是要求读者访问本地写作目录。沿用已完成的核对，本轮没有重跑统计或实验。
