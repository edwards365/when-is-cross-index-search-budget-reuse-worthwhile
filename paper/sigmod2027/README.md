# SIGMOD E&A · W1 LaTeX论文骨架

这是一份可编译、可继续写作的内部骨架，不是完整论文或投稿包。实验和W0冻结结果均未修改。

## 使用

1. 将源码ZIP上传Overleaf，入口选择 `main.tex`。
2. 编译器选择 **XeLaTeX**，使用可用的新版本TeX Live。两次编译解析交叉引用。
3. 本地可使用 `latexmk -xelatex -outdir=build main.tex`；也可用 `tectonic -X compile main.tex --outdir build --keep-logs`。
4. 当前W1尚未加入经逐源核实的参考文献。`references.bib`是明确标注的待填骨架；不存在用虚构条目消除问号的情况。
5. `sections/`中的10个文件是后续正文唯一编辑入口；数值使用 `evidence/results_macros.tex`，不得手工覆写宏中的实验值。

## 本轮产物

- 标题、摘要草案、一句话主线、四项贡献和四项发现。
- 10节主文、5个有明确科学问题的图位、4张表（其中1张为报告字段框架）。
- 风险、迁移风险差、单固定策略CP上界、搜索收益、总成本和break-even公式。
- W0冻结宏与证据账本；旧结果与旧ICLR稿保留原状。
- `WRITING_PLAN.md`给出每节目标、正式稿页数预算、图表证据需求及W2衔接。
- `check_w1.py`检查源文件结构、宏与账本对应、标签引用和模板身份。此检查不是实验复现或统计有效性证明。

## 模板与投稿边界

采用用户提供的acmart-primary包：类文件声明 `2026/08/16 v2.20`，未改动类文件、字体大小、页边距或行距。`template-source/`保留上游源码与说明，`ACM-LICENSE`保留许可证。

该包README将其描述为development snapshot，且版本日期与类声明存在差异。因此本轮将其作为W1预览模板，不能把它的打包来源等同于最终投稿官方production版本审核通过。最终稿前须对照ACM生产模板。

按2026-09-17核对的SIGMOD 2027 Research CFP，E&A标题需含 `: [Experiments & Analysis]`，正文最多12页（参考文献不计），双栏、匿名，附录作为独立短PDF。当前 `anonymous,nonacm` 设置用于内部无出版元数据预览；正式提交前须按最新CFP复核选项。

规则来源：https://2027.sigmod.org/calls_papers_sigmod_research.shtml

源码包包含内部写作计划、证据账本和模板说明，**不是匿名提交ZIP**。PDF预览不显示作者、服务器和仓库地址。内部骨架提示与Section purpose、Planned exhibit、W1 Completion Map应在完成正文后移除，而不是直接隐藏未解决的证据问题。

## 证据冻结

W0提交：`79f0024011f67b7f40f2a75d55cfa6a27a159861`。
W0源输入快照：`d0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5`。
完整仓库中的检查命令：`.venv/bin/python paper/sigmod2027/evidence/freeze_w0.py --check`。
独立源码包中的检查命令：`python check_w1.py`。

W1保留W0的H1–H6条件：query-indexed历史档案、candidate/fallback联合认证、源truth与重复查询的成本归属、共享query依赖、TV前提与理论机制一致性。结论只采用当前可支持的经验与条件性表述。评分、未来接收概率和“所有Gate已通过”不进入论文。

## 本次交付检查

- 2026-09-17，Tectonic 0.17.0 / XeTeX编译完成，Letter双栏，共 **5页**。W1骨架长度不代表12页完整稿已完成。
- 5页全部渲染并目视检查；公式符号、4张表和图位可读，页码正常。最终日志没有overfull box、缺失字符、未定义引用。
- 字体逐字形渲染正常。运行时存在fontconfig配置提示与字体请求诊断、少量underfull排版警告，不将其误报为零警告编译。
- 57个W0宏与账本完全一致，正文引用34个；10节、5图位、4表及标签检查通过。
- 仓库W0检查再次通过；本轮未运行ANN实验、未调整阈值、未写入实验结果目录。
- 人工检查了自动文风扫描的4类提示；骨架要求的四发现枚举和必要的协议边界予以保留。未把文风检查解释为科学有效性验证。
