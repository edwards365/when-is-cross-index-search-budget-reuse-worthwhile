# W5.5：图示、术语与语义修订核查

日期：2026-09-17。基于 W5 提交 `b55a57ffcb635842cf958d4ef975cef0f211773e`。
本轮仅论文修订、从冻结汇总表生成图和描述性统计；未启动 ANN 搜索、重构索引、调参或新实验。

## 对评审意见的批判性处理

| 意见 | 判断及处理 |
|---|---|
| ICBA/TCP 未展开 | 成立。摘要、Introduction 首次出现及半栏术语表均展开。旧稿未确立 ICBA 英文全称，因此本版明确将本文工作流命名为 **Index-Conditioned Budget Audit**，而非伪称查到了历史全称。 |
| TCP 全称 | 采用 **Tiered Conformal Pooling**；历史依据为 `results/graph_anns_phase2_p11/glove_preregistration.json` 的原词及 `docs/graph_anns_phase2_p11/theorem3_and_policy.md` 的 tiered policy。名称对应政策家族，不把九历史、first-passing refresh 实现冒充已经满足构建可交换的保形保证。该区别保留在 §4.2。 |
| 零图/计划框 | W5 的确没有图，但“仍有计划框”与实际 W5 不符（框已移除）。“零图必然初筛失败”不是已核实的会议规则。可读性意见成立，本版新增三张真实可追溯图。 |
| 至少两张 | 三张均已入正文：Figure 1 概念总览+冻结风险/成本散点；Figure 2 实现工作流；Figure 3 20格决策矩阵+逐build风险图。概念图明确不是测量到的图结构。 |
| 机制分析去留 | 增补“失败集中度”描述性诊断：两数据集全部10个目标直接复用风险超过5%；删失败最多目标后仍为6.61%/7.13%。明确图拓扑因果归因不在此 replay 范围内，不能把分布诊断当机制证明。 |
| 三处缺空格 | 意见未给出原句或页码，不能声称精准定位了所指三处。对当前源码和全PDF检查词边界、宏展开与缩写邻接，未见残余粘连；数字后文字使用显式TeX空格。 |
| “ICBA…” | 定位到实际问题：ACM段落标题自动句号与大写ICBA后的手动句号产生 `ICBA..`。去掉手动句号，重新渲染核查。 |
| 千分位/label语义 | 使用 siunitx 统一成本和尾部数字千分位；将两个 `unresolved endpoint(s)` 改为 `unresolved label(s)`。没有改动冻结值。 |
| Transport risk | §3.1 显式定义为源策略在目标上的绝对失败概率，并给出经验估计含义，区分源风险与reference-relative增量；不同实验块的事件仍各自保留。 |
| 数据集名 | 正文统一 Arxiv-Nomic-100K、SIFT-100K；术语表说明表内缩写。证据文件的原始机器键不重命名。 |
| Table 5 / 三处正文区间 | Table 5 写明 estimate [95% interval]，三处正文为 recovery gain、Ada-ef risk、Deep1M increment；Table 3 写法保留。区分百分比与百分点，未把不同实验块区间合并。 |
| 两个“非错误疑点” | 原意见未具体指出哪两个，不能替它虚构。补充两个已核实且容易误读的解释：尾部分位数的小数来自插值；Table 3 两个敏感性列相同，是因为最低LOTO确实对应删除最大相对收益目标。SIFT seed2267、Arxiv seed1499，均按逐build均值重算验证。 |
| small caps | 检查定理/证明标题与数学体，保留模板默认small caps；字体含图中Times New Roman全部嵌入，无缺字或强制大写替换。 |

## 图与证据

制图源：`make_figures.py`。输出 `figures/{overview,workflow,target_decisions}.{pdf,svg,png}`。
数值输入仅 `evidence/refresh95_summary.csv` 与 `refresh95_per_build.csv`，均来自原冻结基线
`d0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5`。
新描述性汇总为 `evidence/w55_diagnostics.json`，八个显示宏为 `w55_macros.tex`。

- SIFT-100K：源复用10个目标风险5.70%–7.40%；669次失败；最大目标占11.06%；删该目标后6.61%。
- Arxiv-Nomic-100K：风险6.40%–8.20%；724次失败；最大目标占11.33%；删该目标后7.13%。
- target recalibration 候选接受19/20；回退为 Arxiv-Nomic-100K seed1229，候选CP UCB=5.056404%，严格超过5%而回退。图中没有调整阈值。
- 图里的每点/格保留实际目标，回退记录不删除。风险点为经验率，不伪加置信区间。

## 编译与检查

- ACM `acmart` 2.20，`sigconf,anonymous,nonacm`；模板和参考文献样式未修改。
- Letter双栏；10页总计，正文结束及参考文献起始于第9页，正文不超过12页。
- 三幅矢量图、五张编号表、一张不编号术语表、四个命题及证明、16篇引用。
- PDF约0.32MB；正文、图形、公式字体全部嵌入；没有缺失交叉引用、缺图、overfull框或作者身份metadata。
- 逐页视觉检查完成；未发现图表截断、重叠、small caps缺字或边界溢出。
- 57个W0宏、10个W5宏、80条逐build记录通过核查；W3数学检查10/10通过。
- 新增检查覆盖八个描述性宏、20个决策、全部目标风险、fallback seed、LOTO等价说明、图文件、术语、区间标注、页数和嵌入字体。
- 保留原始参考文献的五项可选字段警告（无页码的会议条目等），不为消除警告编造页码/出版地；现有underfull排版提示不影响阅读。

## 保留的实质边界

1. 主实验是相同query历史profile的refresh/rebuild replay，不是未见query预测，也不识别纯图重建因果效应。
2. 19/20是独立候选CP检查的经验接受数，不是联合95%决策链证书；candidate+endpoint两个0.05误差预算没有被写成总0.05。
3. 图和文字保留经验尾部比较与统计非劣认证的区别；NDC收益不是wall-clock加速比。
4. 成本模型缺项时break-even仍为条件性/optimistic估计；Vamana成本区间包含0的结论保留。
5. 构建外层、query内层原有bootstrap对跨build共享query依赖的限制没有被图形包装掩盖。
6. 匿名artifact链接尚未验证，因此未把可识别作者身份的开发仓库放进匿名PDF。正式投稿前仍须提供并检查匿名artifact入口。

本版是完整W5.5写作交付，不等同于新实验完成、理论保证升级或录用概率承诺。
