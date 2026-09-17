# SIGMOD E&A · W3 Theory、ICBA与TCP

前四节已写成正文：Introduction、Related Work、Theory、ICBA/TCP。当前PDF为8页（含参考文献），第5–10节仍是结构草稿，不是完整论文或投稿包。实验、分析代码和W0冻结结果均未修改。

## 使用

1. 将源码ZIP上传Overleaf，入口选择 `main.tex`。
2. 编译器选择 **XeLaTeX**，使用可用的新版本TeX Live。Overleaf自动调用BibTeX；必要时选择“从头重新编译”以解析新引用。
3. 本地可使用 `latexmk -xelatex -outdir=build main.tex`；也可用 `tectonic -X compile main.tex --outdir build --keep-logs`。
4. `references.bib`现有16条引用。`LITERATURE_NOTES.md`记录原始来源、支持的主张与核验深度；DARTH+仅经HAL原始记录的摘要核验，未声称已读其完整证明。
5. `sections/`中的10个文件是后续正文唯一编辑入口；数值使用 `evidence/results_macros.tex`，不得手工覆写宏中的实验值。

## 本轮产物

- Introduction：维护动机、迁移问题、离散风险口径、ICBA审计、TCP恢复证据与四项贡献。
- Related Work：构图与维护、预算自适应、质量保证、校准与选择四组文献。
- 必要的连带修正：摘要和Methodology明确主TCP结果是5%数据刷新后重建，而非纯重建归因。
- Theory：观测受限下界、margin条件选择、同时认证、exchangeable-build覆盖，含4个短证明。明确有限池分辨率、ties、无限标签和固定target/随机build的概率单位。
- ICBA/TCP：对齐冻结refresh代码的first-safe标签、历史最大池化、全局shift、候选/endpoint检查、未通过时的回放标记和成本接口；区分历史stable-tail版本。
- 10节主文、5个figure（其中Fig.2为文字流程，另外4个为图位）、4张表（其中1张为报告字段框架）。
- 风险、迁移风险差、单固定策略CP上界、搜索收益、总成本和break-even公式。
- W0冻结宏与证据账本；旧结果与旧ICLR稿保留原状。
- `WRITING_PLAN.md`给出每节目标、正式稿页数预算、图表证据需求及后续衔接。
- `check_w1.py`保留原文件名便于兼容，已扩展到W3的16项引用、4命题/证明与正文检查；`check_w3_math.py`提供10项无实验数据的数学回归检查。这些检查不是实验复现或独立理论评审。

## 模板与投稿边界

采用用户提供的acmart-primary包：类文件声明 `2026/08/16 v2.20`，未改动类文件、字体大小、页边距或行距。`template-source/`保留上游源码与说明，`ACM-LICENSE`保留许可证。

该包README将其描述为development snapshot，且版本日期与类声明存在差异。因此本轮将其作为W1预览模板，不能把它的打包来源等同于最终投稿官方production版本审核通过。最终稿前须对照ACM生产模板。

按2026-09-17核对的SIGMOD 2027 Research CFP，E&A标题需含 `: [Experiments & Analysis]`，正文最多12页（参考文献不计），双栏、匿名，附录作为独立短PDF。当前 `anonymous,nonacm` 设置用于内部无出版元数据预览；正式提交前须按最新CFP复核选项。

规则来源：https://2027.sigmod.org/calls_papers_sigmod_research.shtml

源码包包含内部写作计划、证据账本和模板说明，**不是匿名提交ZIP**。PDF预览不显示作者、服务器和仓库地址。内部草稿提示与Section purpose、Planned exhibit、Writing Completion Map应在完成正文后移除，而不是直接隐藏未解决的证据问题。

## 证据冻结

W0提交：`79f0024011f67b7f40f2a75d55cfa6a27a159861`。
W0源输入快照：`d0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5`。
完整仓库中的检查命令：`.venv/bin/python paper/sigmod2027/evidence/freeze_w0.py --check`。
独立源码包中的检查命令：`python check_w1.py`。

W3保留W0的H1–H6条件：query-indexed历史档案、refresh candidate/fallback联合认证、源truth与重复查询的成本归属、共享query依赖、TV实证前提与理论机制一致性。正确的条件证明不等于这些经验前提通过。结论只采用当前可支持的经验与条件性表述。评分、未来接收概率和“所有Gate已通过”不进入论文。

## W1归档检查

- 2026-09-17，Tectonic 0.17.0 / XeTeX编译完成，Letter双栏，共 **5页**。W1骨架长度不代表12页完整稿已完成。
- 5页全部渲染并目视检查；公式符号、4张表和图位可读，页码正常。最终日志没有overfull box、缺失字符、未定义引用。
- 字体逐字形渲染正常。运行时存在fontconfig配置提示与字体请求诊断、少量underfull排版警告，不将其误报为零警告编译。
- 57个W0宏与账本完全一致，正文引用34个；10节、5图位、4表及标签检查通过。
- 仓库W0检查再次通过；本轮未运行ANN实验、未调整阈值、未写入实验结果目录。
- 人工检查了自动文风扫描的4类提示；骨架要求的四发现枚举和必要的协议边界予以保留。未把文风检查解释为科学有效性验证。

## 历史W2交付检查

记录见 `W2_VALIDATION.md`；W1/W2预览保留为历史交付。排版使用原模板的字号与边距，仅采用自然页底留白，没有用缩字号或负间距压篇幅。

## W3交付检查

见 `W3_VALIDATION.md`，包含理论到代码的对应表、证明修正理由及检查覆盖范围。当前源码对应W3预览；可运行 `python check_w1.py` 和 `python check_w3_math.py`。论文读者应区分：条件证明已写全、经验结果已冻结、部分强部署主张仍未得到支持。
