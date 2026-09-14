# ICBA / Graph-ANNS Budget Portability — 项目交接文档（v2 终版）

> 文档用途：将全部研究进度、实验结果、理论状态、论文终稿和遗留工作完整移交给下一个 AI agent。
>
> 截止日期：2026-09-14（ICLR 2027 摘要截止 09-18，全文截止 09-25）。
>
> 证据原则：本文档严格区分"冻结事实""当前判断"和"待完成工作"。如聊天摘要与仓库结果冲突，以 Git commit 中的机器结果表为准。

---

## 1. 项目一句话定义

Graph-ANNS 索引在同一数据和名义超参下重建后，旧索引上校准的搜索预算策略（efSearch 等）能否安全迁移到新索引？答案是**不能盲迁移**（17–24% 增量风险），但**可以认证地部署**（Theorem 3 保形池化 ≤α 风险 @ 1.32–1.44× oracle），或者**消除环境**（确定性合同，零风险 @ 1.71–3.52× 构建开销）。

---

## 2. 权威锚点

- **仓库**：`github.com:edwards365/navigation-aware-resistance-hnsw`（SSH）
- **工作分支**：`exp/graph_anns_phase2_constructive_closure`
- **权威基线**：`ffe5798`（`exp/graph_anns_iclr_phase1_1_final_evidence_hotfix`）
- **论文终稿**：`results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v12_final.tex`
- **Rebuttal 信**：`docs/rebuttal_letter.md`
- **运行环境**：`LD_LIBRARY_PATH=/home/wlk/miniconda3/lib` + repo `.venv`（Python 3.11）
- **测试套件**：`tests/graph_anns_phase2_p{0..11}/test_*.py`（7 套，14–27 checks each）

---

## 3. 论文三个定理（终版状态）

### Theorem 1（transcript-limited 不可迁移下界）
- **内容**：max E[ℓᵢ] ≥ (Δ/2)(1−TV(P₀ᵀ, P₁ᵀ))
- **前提实测**：hit-count transcript TV ≤ 0.39（DKW 95% UCB）；joint runtime 特征 TV ≥ 0.44（该类下界弱化，如实报告）
- **损失下界**：0.305Δ（对 hit-count 类有效）
- **D-region**：21.9% 有向传输在 κ=0 下无共同安全动作（κ=1 仍 6.9%）；中位动作差 30/20
- **状态**：probe-class-conditional，前提有测量支撑

### Theorem 2（固定目标条件可恢复性）
- **内容**：五条件（可行、可辨、margin、独立角色、有效回退）满足时 screen-then-certify 以 ≥1−α 概率输出安全动作或有效弃权
- **实测审计**：48/48 目标通过 Theorem-2 筛选（ef=120/200）但零失败认证全败
- **γ 敏感性**：γ=0.005 时 16–21/24 目标存在 margin 动作；γ=0.02 时全无
- **CP 功效**：margin-band 2.5% 风险动作在 m=289 非零失败 CP 下通过率 70%
- **状态**：认证功效绑定（非 margin 缺失）；协议依赖性已量化

### Theorem 3（可交换构建保形池化）
- **内容**：部署源池 m 阶次统计量（m=⌈(1−α)(k+1)⌉），则 P[B_t(q)>a(q)] ≤ α
- **执行安全桥**：ν=0（4.4M+ 三元组穷举，全部 5 数据集）→ 执行失败 ≤ α+ν = α
- **验证矩阵**：3 尺度 × 3 实现 × 双数据集 + farm 深池 k=49（全非空转有效）
- **边界**：α ≥ 1/(k+1)；corr-weighted 选源使风险膨胀 3.3×；10M 未缓存池化退化
- **状态**：完整验证的认证可部署策略

---

## 4. 实验完备性矩阵（全部已提交）

| 维度 | 覆盖 | 关键数字 |
|---|---|---|
| 数据集族 | SIFT · Arxiv-Nomic · GloVe-100 · deep-image | 4 族 |
| 几何 | L2-128 · cosine-768 · angular-100 | 3 种 |
| 尺度 | 10K farm · 100K · 1M · 10M | 4 级 |
| 实现 | hnswlib · clean Faiss · Vamana | 3 族 |
| 种群农场 | SIFT-10K (200) + Arxiv-10K (200) | 双数据族 |
| 预测器 | ridge · kNN · HistGB | 全负 (R²≤0.02) |
| ν 执行安全 | hnswlib · Vamana · 1M · 10M · GloVe | **全部 ν=0** |
| Vamana 对齐 | target-min-safe 口径 | **0%**（reference-dependent） |

---

## 5. 论文文件位置

| 文件 | 路径 | 说明 |
|---|---|---|
| 终稿 v12 | `results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v12_final.tex` | 81KB，全部修复 |
| Rebuttal | `docs/rebuttal_letter.md` | 10 主题逐条回应 |
| 图 | `results/graph_anns_phase2_p7/media/fig{1..7}_*.png` | 7 张 |
| 交付 | `/home/wlk/Downloads/ICBA_ICLR_LaTeX/` | tex + 全部图 |
| ICLR 样式 | 需下载 `iclr2027_conference.sty` | Overleaf 用 |

---

## 6. 剩余工作（按优先级）

### 立即需要（投稿前）
1. **Overleaf 编译 v12_final**：确认正文 ≤9 页 + 公式/表格/图渲染正常
2. **如果超页**：从 §7.6 经济段和 Limitations 第三段可再挤 ~0.5 页

### Rebuttal 阶段（如果有审稿）
3. 根据 reviewer 具体问题引用 `docs/rebuttal_letter.md` 对应段落
4. 补充审稿人可能要求的 build-level bootstrap CI（纯代码，30 min）

### Camera-ready 或后续论文
5. 三个 origin-unlocated 历史聚合数（recal %、protected-edge cost、matched-lane ratio）需重推导或永久移除
6. 外部方法对照（ConANN/DARTH/ANNiE 跨重建测试）需新基础设施
7. 数据刷新场景（insert/delete→rebuild）需新实验设计
8. Vamana estimand 完全对齐需 DiskANN 构建管线重跑

### 明确不做
- 1B 规模（资源不足）
- GPU byte-identity（超出注册配置范围）
- 生产 trace 验证（无访问权限）

---

## 7. 关键 JSON/CSV 产物索引

```
results/graph_anns_phase2_p2/
  max_over_source_summary.csv          # 池化 22 源风险 0.09–0.92%
  six_method_table_{sift,arxiv}.csv   # 六方法构造表
  five_condition_instances.csv         # Thm2 五条件 48 目标审计
results/graph_anns_phase2_p3/
  contract_ablation.csv                # 合同四级消融
results/graph_anns_phase2_p4/
  economics_matrix.csv                 # 36 格经济矩阵
  grid_sensitivity.csv                 # 网格敏感性
results/graph_anns_phase2_p6/
  sift1m_summary.json                  # 1M 21.87%
results/graph_anns_phase2_p8/
  h_sensitivity_incremental.csv        # h=8/9/10 增量口径
  gamma_sensitivity.csv                # γ 功效敏感性
  rich_probe_distinguishability.csv    # 探针特征矩阵
results/graph_anns_phase2_p10/
  deep10m_summary.json                 # 10M 22.16%
  deep10m_verdict.json
results/graph_anns_phase2_p11/
  conformal_pooling_validity.csv       # Thm3 验证矩阵
  conformal_faiss_validity.csv         # Faiss 第二实现
  conformal_multiscale.csv             # 1M/10M/farm 多尺度
  conformal_vamana_validity.csv        # Vamana 第三实现
  execution_safety_verdict.json        # ν=0 全覆盖
  glove_execution_safety.json          # GloVe ν=0
  build_farm_summary.json              # SIFT farm
  arxiv_farm_summary.json              # Arxiv farm
  d_region_kappa.json                  # D-region 21.9%
  theory_fixes_verdict.json            # TV-UCB 0.39
  cp_power_real_data.json              # CP 功效实测
  vamana_aligned_estimand.json         # Vamana 对齐=0%
  glove_summary.json                   # GloVe 17.54%
  predictor_baselines.json             # ridge/kNN/HistGB
  tcp_method_figure.png                # TCP 方法图
```

---

## 8. 禁止事项（继承自原交接文档）

- 不修改冻结结果或封存数据
- 不将 Vamana 提升为 harmonized estimand
- 不声称所有 Graph-ANNS、open-world 或普遍成本税
- 不访问 future-replication、validation-dev 或 formal-test 角色
- 不把未通过 Gate 的探索结果包装为 positive method
- 不为迎合审稿而更改已冻结主 estimand

---

## 9. 下一个 agent 的启动步骤

1. `git checkout exp/graph_anns_phase2_constructive_closure && git pull`
2. 阅读 `docs/rebuttal_letter.md` + 本文档
3. 确认 `results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v12_final.tex` 存在且清洁
4. 如果用户已有 Overleaf 编译结果 → 处理页数/渲染问题
5. 如果进入 rebuttal → 从 §6 的 rebuttal 阶段任务开始
6. 如果投稿被拒 → 按 §6 的 camera-ready/后续论文方向规划下一轮

---

## 10. 项目完整提交历史（关键节点）

```
e3d395d  GloVe ν=0 → 执行安全矩阵全闭合
c065369  M2/M5' 去重 + 决策规则 5 路对齐
033ea62  跨数据集扩展段 + Vamana 对齐披露
0b898a6  Vamana 对齐估计量（0%，reference-dependent）
6dd34c6  CP 功效 margin-band 实测
f28c5e1  Arxiv-10K farm（可交换性 KS 0.113-0.120）
68d2a03  v13 写作修复
70daecc  v12 全部 P0 修复
b1debcd  行终止符验证
1ec00de  abstract end 去重
f22674d  M5' 行终止符修复
99c8bfe  v11（R_E 14 项修复）
...（更早提交见 git log）
```
