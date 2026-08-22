# Phase I claim table

| 结论 | 类型 | 状态 | 证据 | 可否用于论文 |
|---|---|---|---|---|
| 有效电阻恒等式 | 数学 | 已证明 | `theory/known_results.md`, `theory/project_theorems.md`, exact tests | 可以，但仅限声明的连通无向正权图 |
| 局部次模性 | 数学 | 已证明 | `theory/lemmas.md`, greedy optimum tests | 可以，但仅限冻结局部目标与单节点基数约束 |
| 冻结局部贪心具有 `1-1/e` 近似 | 数学 | 已证明/经典推论 | 单调次模目标和基数约束 | 可以，不得推广为HNSW全局保证 |
| 高电阻保证导航 | 数学 | 已反驳 | `theory/counterexamples.md` | 不可以 |
| 低杠杆边可安全删除 | 数学 | 已反驳 | 唯一导航捷径反例 | 不可以 |
| 谱近似保证搜索路径稳定 | 数学 | 已反驳 | 邻接导航不连续反例 | 不可以 |
| 动态杠杆目标仍为次模 | 数学 | 已反驳 | 五节点穷举反例 | 不可以 |
| HNSW插入与查询可被精确重放 | 工程 | 已验证 | C++重放、CTest、3,072次标签/NDC一致性 | 可以，按实现范围陈述 |
| Scheme A/B/C可计算 | 工程 | 已验证 | 46,150条layer-0候选评分 | 可以，必须保留三种语义 |
| Trace+Resistance提升Recall | 实验 | 未获支持 | 独立留出；差值及区间跨零 | 不可以 |
| 电阻独特降低NDC | 实验 | 未获支持 | Geometry对照点估计更优 | 不可以 |
| 查询轨迹能在选择夹具上识别失败相关边 | 实验 | 有限支持 | 46条渐进方向覆盖8个选择侧失败查询 | 只能作为离线诊断，不可作为查询无关算法收益 |
| 插入顺序稳定性 | 实验 | 未决 | Phase I尚未测试 | 不可以 |
| 构建种子稳定性 | 实验 | 未决 | Phase I只有正式图种子7 | 不可以 |
| 公共数据外部有效性 | 实验 | 未决 | Phase I仅合成夹具 | 不可以 |

The controlling paper statement is: **Phase I established local mathematical and engineering feasibility, but the performance algorithm did not pass the resistance-specific benefit gate.**
