# SIGMOD E&A 重组版（W6）：修改记录与交付边界

日期：2026-09-17。对象：W5.5 论文及两份投稿前审稿报告。

## 1. 本轮完成了什么

本轮不是新算法搜索，也没有启动 ANN 搜索矩阵或构建新索引。完成了论文重组、现有冻结响应的派生统计、认证组合与成本修复、六张图重绘、短附录和源码包。旧实验结果不覆盖，W5.5 保留。

新标题为 **Auditing Search-Budget Portability Across Graph-ANNS Rebuilds: [Experiments & Analysis]**。它不再把“所有来源策略已被认证安全”作为标题前提。

保留 TCP，但把它放在 **ICBA 审计下的恢复案例**位置，而不是以算法竞赛或绝对 SOTA 作为全文主张。本文用 Target-calibrated pooling 解释实际执行的历史查询预算池与目标 shift；同时明确历史项目中的 Tiered Conformal Pooling 命名及另一 stable-tail 变体，避免把它们偷换成同一算法/保证。代码、动作和原始实验没有因命名而改变。

### 分阶段组织

| 阶段 | 完成内容 | 验收依据 |
|---|---|---|
| 证据和主张对齐 | 分开 graph-only 回顾性响应、refresh 后可执行策略、外部方法资格 | 标题、摘要、定义、协议与结论一致 |
| 结构与理论 | 现象优先；ICBA 为审计规程；TCP 为恢复案例；理论明确经典工具及适用条件 | 正文保留关键命题与证明，独立短附录补充推导 |
| 统计和认证修复 | 共享 query 权重的交叉 bootstrap；逐目标 CP；联合错误预算敏感性 | 5000 次重采样，seed 991；20 个目标明细；244 项算术与来源校验 |
| 成本修复 | cached 与 cold 两种历史场景；补全现有记录中可计价的信息成本 | 分项 CSV、逐目标 break-even、非摊销目标与生命周期曲线 |
| 图表与排版 | 六张真实数据/流程图、统一图表单位与 95% 区间、去无意义 seed 连线 | 矢量 PDF/SVG 与生成代码；双栏 PDF 逐页检查 |
| 交付 | 完整 LaTeX、正文 PDF、独立附录 PDF、数据与复核脚本 | README、来源映射、SHA256 清单 |

### 新正文顺序

Introduction → Related Work → Portability/Risk/Guarantees → ICBA/TCP → Experimental Design → RQ1 graph-only → RQ2 matched refresh → RQ3 audit → RQ4 recovery → RQ5 tails → RQ6 build sensitivity → RQ7 methods/family/scale → RQ8 economics → RQ9 reproducibility → implications/conclusion。

## 2. 有实质影响的结果修正

| 事项 | 本轮核查结果 | 论文如何表达 |
|---|---|---|
| 独立于 TCP 的现象 | hnswlib/Faiss、两数据集、每组 24 builds / 552 directions / 750 queries，增量风险 17.17–23.60 个百分点 | 作为 RQ1；回顾性 first-passing 响应迁移，不称可部署 Oracle 算法 |
| 真正的同策略 old→new | SIFT 3.77%→6.69%，增量 2.92 [1.75,4.07] pp；Arxiv 3.19%→7.24%，增量 4.05 [2.86,5.31] pp | 同策略配对，现有响应派生分析；refresh 与 graph change 的因果作用仍不能分开 |
| 来源侧资格 | 单策略 α=.05 下，SIFT 6/10、Arxiv 5/10 old policies 合格；这 11 个在目标检查均不合格 | 事后单策略诊断，不是 11 次转移的联合保证，不用它恢复旧标题的普遍语气 |
| 原始 TCP 决策 | 原 .05/.05 两检查共接受 19/20；SIFT/Arxiv 收益 44.39%/44.79% | 保留历史事实，但不把它叫 95% 联合程序 |
| 联合错误预算 | 候选、endpoint 各 .025，冻结 shift 不动，接受 16/20；所有 endpoint 合格，无弃权 | 新增 post-hoc sensitivity；每个固定 target 的总错误预算 .05，不跨 20 targets 联合 |
| 联合程序表现 | 风险 SIFT 1.79 [1.25,2.40]%，Arxiv 1.68 [1.10,2.35]%；相对 mean-NDC 收益 44.39 [42.76,46.01]% / 29.86 [14.75,45.00]% | 正文与摘要采用更严格程序的恢复收益，不把原 44.79% 贴到新认证规则上 |
| p95 / p99 | 联合程序的 pooled 与每个目标 p95/p99 均未高于 endpoint | 描述性观测，不冒充正式 quantile noninferiority test；NDC 不等于 latency |
| 完整冷历史成本 | SIFT/Arxiv break-even 约 396,000/457,000 次；cached 约 129,000/148,000 次 | 两种场景分开，成本单位 NDC；cold 指对保留旧图获取 profile，不含重新建整个历史图档案 |
| 不摊销目标 | 新联合程序 Arxiv 4 个 fallback targets 没有 serving saving | 不被 dataset mean 掩盖；正开销无法靠零 serving saving 摊销 |
| 生命周期 | cold 在 N=10^5 两数据集均负；N=10^6 平均净节省约 490/389 million NDC | 删除/修正过早经济性结论；不推广到无限新 query 流 |
| Deep1M | 20.04 [17.29,22.77] pp；target reference 本身约 8.82% 风险 | 单独列参照；核对源码后标为 target-build bootstrap，不写 query-cluster bootstrap |
| Vamana | 风险是阶段特定事件；cost-tax 区间含 0 | 保留方向性佐证，不与 HNSW 定量合并，不宣称正成本惩罚已成立 |

区间均为 95%，但重采样单位随 setting 明确区分。refresh 的 crossed 区间条件于历史库、已选 shift 和决策，不重新训练，也不证明新 build 分布下的安全。

## 3. 第一份审稿报告逐项处理

编号按 `ICBA_SIGMOD_2027_EA_strict_review.md`。

| ID | 意见 | 处理与状态 |
|---|---|---|
| C001 | Safe 标题超出来源侧证据 | 已改题并补 old/new 配对；来源资格仍按单策略、事后诊断界定 |
| C002 | graph-only 与 refresh、已建档与新 query 混淆 | 已分为 RQ1/RQ2；TCP recurring-profile 范围在方法、协议和经济性处明确 |
| C003 | shared queries 的 crossed dependence | 已重算共用 query 权重的 target×query bootstrap，保留 build-only/query-only 敏感性 |
| C004 | 生命周期成本遗漏 | 已补 target endpoint cert、全角色 old profiling、共享 old truth；未计价的 elapsed/control/storage/历史建图不伪填为零 |
| C005 | 理论未实例化、方法定位过强 | 经典信息界和 rank 保证写清边界；联合候选/fallback 命题由新敏感性在相应条件下接触；TCP 为案例 |
| C006 | empirical / individually certified / jointly controlled 混用 | 已统一术语与对象，保留 query-sampling 条件 |
| C007 | RQ 跳序 | 已按阅读顺序重排 RQ1–RQ9 |
| C008 | HNSW 未展开 | 引言首段展开 Hierarchical Navigable Small World |
| C009 | TCP 名称引入 conformal 暗示 | 本文实际规则命名、历史家族名及非 5% build-conformal 保证已区分 |
| C010 | 机械 Q/P/O/C 段落 | 删除重复标签，保留问题、协议、观察、推论的自然论证 |
| C011 | 总览图均值无区间 | 已重画双面板并给相应条件区间，未添加未经测量的连续趋势 |
| C012 | seed 连线暗示趋势 | 决策点阵与无连接线逐目标点图代替 |
| C013 | 表格单位/n 不足 | 每表明确百分比/百分点/NDC/千次、样本量和区间单位 |
| C014 | 仅 pooled tails | 补每目标 p95/p99 点图与 CSV，fallback 等于 endpoint 的含义明确 |
| C015 | 成本虚假精度 | 正文采用千次和合理舍入，原精度保留机器表 |
| C016 | Vamana estimand 混合 | 专门 scope 表列事件、参照、单位；风险和成本不跨引擎合并 |
| C017 | 审计术语密度过高 | 减少工程状态标签、宏缩写与重复防御措辞；保留必要定义 |
| C018 | 摘要跨家族过强 | 摘要核心是 graph-only 与双数据集 recurring-workload；不声称全家族同一保证 |
| C019 | LOTO 和删最大 build 像独立证据 | 明说后者是前者中一个指定成员，相同最小值不计两份稳健性证据 |
| Related Work | 动态维护近邻不全 | 补 IP-DiskANN、Wolverine；说明改变索引与审计预算的比较轴 |
| Artifact | 未独立复现/未提供匿名入口 | 本轮补可编译源码与数值复核包；匿名托管、独立 native replay 仍待完成，不标为已解决 |

## 4. 第二份审稿报告逐项处理

编号按第二份《SIGMOD 2027 Experiments & Analysis 投稿前审查报告》。

| ID | 处理 |
|---|---|
| C001 | 同第一份 C001：改题、补 matched-source 诊断、保留边界 |
| C002 | 实际 TCP 规则与历史名称分开，说明 pooling/shift，不以名称获取保证 |
| C003 | gain 明确定义为 1−ratio of pooled means；等查询数时等价于 relative total-NDC reduction |
| C004 | 不是补一句“optimistic”，而是重算 cached/cold 成本并报告改变后的回本点 |
| C005 | 成本表以 10^3 query executions 为单位，区间与不摊销数量完整 |
| C006 | 补 risk 95% crossed intervals；未采用把所有 query×build 当独立二项试验的简化 |
| C007 | RQ 顺序重组，无跳号 |
| C008 | HNSW degree 用 M，池规模用 m，网格大小用 J，成本 C(N)；避免同符号跨义 |
| C009 | observed/qualified/joint-error/build-marginal 语言分开 |
| C010 | Ada-ef 缺 SIFT 的原因明确为现有 cosine/IP 估计器缺等价 L2 路径，不写成 SIFT 负结果 |
| C011 | 991 在 membership 和统计中的角色分开，不能把它当 graph seed；协议明确 |
| C012 | 解释 SIFT 两认证程序完全重合与 LOTO/最大删除重合 |
| C013 | 删除机械重复免责声明；保留在会改变读者解释之处的实质边界，不为“去防御性”删除事实 |
| C014 | 未伪造匿名 artifact URL；源码包先交付，正式匿名托管仍是提交前步骤 |

## 5. 没有照单全收的意见

- “还没有 graph-only 证据”不等于仓库没有这类结果：本轮找回并核对了冻结 hnswlib/Faiss 四组表，用作主文 RQ1；但它们仍是 retrospective response，不冒充部署型来源认证。
- “必须新实验才能获得 source baseline”并不完全成立：冻结 old/target 响应足够重放同策略。补出的诊断仍明确事后性质，不能伪装为新预注册验证。
- 不能仅用每个数据集 10,000 条 evaluation outcomes 套独立 binomial CI，忽略跨 build 共享 query；本轮用 crossed resampling。
- 不能因为审稿评分较高就把可复现性记满分；材料未由外部独立 native replay 复现。
- 不能只把旧成本表换名为 optimistic 并保留过早回本点；已能计算的遗漏项应实际计入。
- 不能用两份个体 95% CP 检查拼成同一 95% 程序，也不能把 CP 叫成 conformal coverage。
- E&A 不要求 TCP 每个维度优于所有现有方法；本稿也没有由此获得相对全部方法的 SOTA 资格。主要比较是同目标 endpoint 下的恢复和成本。

## 6. 仍不能靠文字修复的边界

1. 新 query / cache-miss 条件下的预算预测与经济性未由该主 replay 证明。
2. refresh 中数据变化与重建路径的因果效应未分离；graph-only 另有独立诊断，但不是同一因果分解。
3. 行为差异、截尾比例与删极值可定位现象，不构成导航边/路径层面的因果机制证明。
4. NDC 收益不等于 wall-clock、能耗、内存或完整货币收益；这些需要新测量。
5. 跨 build 置信区间条件于现有历史/选择，不等于开放环境的新 build 认证；非联合 20-target 保证。
6. 匿名托管入口和外部独立重放仍待提交前完成。

这些项在正文中缩小相应主张，并没有用“未来工作”掩盖一项已经宣称获得的结果。本轮不承诺录用、不把稿件评为已达 8.5/10；应让下一轮审稿基于这版新的主张和证据判断，而不是继承旧稿分数。

## 7. 图表和交付检查

六图：双证据总览、ICBA/TCP 工作流、20 目标决策点阵、risk–NDC tradeoff、逐目标 p95/p99 比率、生命周期净收益。所有实测图来自机器数据；流程图不冒充测量。

正文保持 ACM 双栏、Letter 页面；正文和参考文献总计 10 页，正文低于 12 页；独立短附录 2 页。公式、矢量图和表格保留。最终字节大小、metadata、引用与版面检查记录见交付清单。没有未解析引用、缺字或 Overfull box；字体请求/Underfull 的编译提示已结合页面视觉检查，而不是隐瞒为“零警告”。

匿名 artifact 的入口应在正式投稿表单中按官方要求提供。正文不放作者个人 GitHub 地址。当前官方要求参考：https://2027.sigmod.org/calls_papers_sigmod_research.shtml 。具体投稿前仍需复核当轮实时规则。

本轮采用 `ccf-paper-writer` 的主张—证据组织与 prose-quality 检查、`ccf-visual-composer` 的图形证据和渲染核验，以及 PDF 技能的编译后逐页检查；技能没有替代科学证据或补造实验。
