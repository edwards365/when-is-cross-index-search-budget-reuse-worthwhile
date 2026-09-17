# W0：SIGMOD E&A写作证据冻结

状态：**数字与代码来源已冻结；存在明确的主张限制，不能认定论文已经投稿就绪。**

冻结基线：`d0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5`。
本目录的`evidence_ledger.json`是写作数字来源；`results_macros.tex`由生成器直接产生。
检查：在仓库根目录运行`.venv/bin/python paper/sigmod2027/evidence/freeze_w0.py --check`。
生成器读取冻结提交中的CSV、JSON和代码，检查工作树输入未漂移、唯一行选择、逐build失败数与汇总风险、mean gain、Deep风险差和生命周期净收益的算术一致性。
本次没有重新读取大型原始query表，也没有运行新实验；因此不宣称独立完成原始数据复现。

## 写作术语

| 术语 | 冻结含义 |
|---|---|
| ICBA | build-conditioned measurement、selection、certification和部署决策的审计框架 |
| Source TCP pool reuse | 针对同一query读取其他九个旧build上的最小通过动作，取最大动作后应用于target |
| Target-selection TCP recalibration | 对上述query-indexed动作进行全局grid shift；selection选择shift，certification检验候选；失败时按现有实现检查endpoint |
| Fixed-safe endpoint | ef=200这一注册动作；不是先验零风险保证 |
| Evaluation risk | 此轮代码计算的`Recall@10 < .95`经验失败比例；不能改称证书上界 |
| Incremental risk | transport risk减reference risk，数值展示单位为百分点（pp） |
| p95 distance | query-pooled距离计算次数的样本分位数；不等同wall-clock p95 |
| Break-even queries | 生命周期模型中的查询执行次数；不同于Phase2的repeated-query-set次数 |
| Net saving at N=1e6 | 数据集内每target平均的建模距离计算节省；不是所有target之和 |

TCP全称和早期conformal pooling定理的同一性在核对原始定义前不新增扩写；当前使用精确实现名称。

## 已确定的语义修正

1. Loop3建议摘要将138.8k/107.4k写为query sets，应改为query executions。Phase2约11/9的search-only重复集合摊销不能替代生命周期结果。
2. Deep1M增量为20.04 **个百分点**，不是相对风险提升20.04%；其28.86% transport risk和8.83% reference risk均须保留。
3. Phase2主事件按代码是Recall@10<.95。k=10的离散Recall使通过阈值要求10/10命中。旧计划中的`under-budget OR endpoint-censored`不能直接作为所有结果的共同定义，需逐实验标注。
4. `tail_p95_noninferior`是样本p95比较得到的0/1字段。写作可说“样本p95较低”，不能说“统计非劣已认证”。
5. control=0只表示模型没有额外距离调用；CPU调度、控制时间和内存并未因此为零。rebuild=0来自同target graph的差分抵消，不代表构建免费。

## 主张限制和后续核对

| ID | 发现及证据位置 | 本轮处理 | 解锁条件 |
|---|---|---|---|
| H1 | `analyze_phase2_refresh95.py`中对cold_evaluation也调用old-build minimum和source_pool_indices | 允许写“拥有对应旧build查询档案的回放/复用”；禁止任意新query零标签部署表述 | 核对旧query档案实际获得方式、源侧truth成本和新query调用路径 |
| H2 | endpoint和candidate均在同一certification角色上计算CP，再按通过情况选择 | 保留实测风险及现有通过状态；暂缓全流程严格95%安全保证措辞 | 证明此选择组合有效，或明确同时校正/独立fallback证书；不能仅凭单项CP推导联合保证 |
| H3 | 生命周期模型按100K×1000计算target truth；source_profile采用search次数，未显式计入旧build truth；对评估查询档案只计一次 | 数字以CONDITIONAL_MODEL_OUTPUT冻结；不称无条件端到端生命周期优势 | 明确源truth为共享已付成本及基线对称性，明确重复query工作负载/新query增量profile |
| H4 | gain bootstrap每个抽到的build内部独立重采query；原查询ID可能跨build共享 | 标注现有nested bootstrap定义；不宣称已覆盖所有query/build依赖 | 核对目标estimand和共享query相关性是否需要联合query重采样 |
| H5 | 旧v12摘要称TV<=.25，正文写plugin .25+界.14；classifier准确率不能提供TV上界 | 下界公式可保留为条件性理论；实证TV headline暂不冻结 | 核实有限支持TV上界证明及完整(q,T)观测条件；不能用CDF DKW界直接替代一般TV界 |
| H6 | 旧v12贡献称margin失败，与前文certification power binds表述不一致 | 理论机制结论暂缓；不把历史诊断混入新摘要 | 对照最终theory和target矩阵逐命题核对 |
| H7 | Loop3以11.3页预算和字符串检查推断无格式阻塞；实际SIGMOD正文尚未编译 | 标为planned/not compiled | 完成正式正文、编译、数字与匿名性扫描 |

上述发现不推翻已登记的实测数值，但收窄可支持的部署和认证结论。此前8.70/10等分数为内部主观评估，没有外部审稿校准，也不是由测试通过数推出的测量值；不进入论文或作为投稿保证。

## 与旧稿的衔接

- v12只作历史文字与理论候选来源；不覆盖原文件。
- 主文新增数字只使用本目录宏，避免手工复制舍入值。
- Faiss、GloVe、10M、200-build farm、deterministic contract、conformal pooling旧数字本轮未逐源复核，暂不进入新的headline数字清单。将来使用时须扩充本清单并核对估计量。
- 文献新颖性、来源元数据、完整理论证明不属于本次数字冻结已通过范围。
- W1可以基于已核实的迁移现象与经验恢复结果起草骨架；H1–H6涉及的强主张必须保持待核实状态。

## 稳定写作规则

不通过编辑旧CSV消除冲突。若源代码、估计量或数字改变，先生成明确的修订证据并更新冻结基线；在此之前，生成器的`--check`应拒绝输入漂移。统计风险与认证置信度、native distance与真实时延、回放经验结论与未来部署保证分别命名。
