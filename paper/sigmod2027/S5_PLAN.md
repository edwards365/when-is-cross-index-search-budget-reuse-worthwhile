# S5 Pre-Submission Closure Plan

Status: `FROZEN_BEFORE_MANUSCRIPT_UPDATE`

Canonical manuscript root: `paper/sigmod2027/`. Work remains in the current main worktree and branch. No new Codex task, worktree, graph construction, model search, or scientific threshold change is authorized.

## Official submission boundary

The target is SIGMOD 2027 Experiment & Analysis (E&A). The official research call was checked on 2026-09-17: the paper must use the ACM two-column proceedings format, remain within 12 content pages plus unlimited references, be double anonymous, use a PDF no larger than 10 MB, and append the exact title suffix `: [Experiments & Analysis]`. A short appendix may be submitted only as a separate PDF; the main paper must remain self-contained. Anonymous artifacts are supplied through the submission form rather than a personal link in the PDF.

## S5.0 — Freeze story, title, and claim map

Inputs are W6 at `b019951` plus the sealed S1–S4 evidence. Freeze the title decision, central claim, section roles, evidence level, and disposition of every old/new number before prose edits. Pass condition: every abstract/introduction/conclusion claim maps to a committed result or theorem, and S4 is labeled fresh-query confirmation rather than folded into the post-hoc TCP experiment.

## S5.1 — Clean-environment replay

Export the anonymous package to a task-specific directory on `data500`, then validate it from a newly created clean environment that has no repository-relative imports or external result paths. The clean replay must:

1. regenerate all manuscript tables and figures from packaged compact evidence;
2. execute evidence and numerical consistency checks;
3. rebuild main and appendix PDFs from the exported source;
4. compare regenerated tables and figure data against the committed claim map;
5. record interpreter, package, LaTeX engine, command, runtime, and hashes.

Native ANN reruns are not part of the anonymous compact replay. They remain a separately documented full-reproduction tier.

## S5.2 — Anonymous package

Build one canonical package, not iteration copies. Remove Git history, absolute paths, usernames, machine names, author metadata, acknowledgements, personal URLs, hidden PDF metadata, shell history, caches, and superseded W1–W6 previews. Retain source, ACM licensing files, bibliography, active figures, compact evidence, regeneration scripts, environment lock, README, provenance map, main PDF, and short appendix PDF. Run content and binary-string scans before sealing the archive.

## S5.3 — Evidence/result mapping

Update `PROVENANCE.md` and the machine-readable ledger with four evidence classes:

- graph-only portability response evidence;
- refreshed-workload TCP evidence and certification sensitivity;
- external-method, scale, and graph-family scope evidence;
- S4 fresh-query source-certified slack evidence.

Every row records dataset, implementation, build unit, query role, event, estimator, uncertainty unit, evidence level, artifact path, and permitted manuscript claim. Conflicting historical numbers are removed from active macros rather than explained in prose.

## S5.4 — Compact main manuscript

Target 11.3–11.7 content pages to leave float and template headroom. Keep the evidence-first E&A structure:

1. Introduction and findings preview;
2. Related work and experimental gap;
3. portability estimands and certification semantics;
4. ICBA audit contract and recovery policies;
5. experimental design and inference;
6. graph-only and refresh portability failures;
7. recovery, source-slack confirmation, tails, and robustness;
8. cross-method/scale/family scope;
9. lifecycle economics and operational implications;
10. conclusion.

TCP remains a recovery case inside ICBA rather than a second paper competing with the E&A contribution. S4 appears as a prospective boundary test: Faiss +1 is supported on registered builds; hnswlib does not show cross-dataset economic value. Repeated disclaimers are consolidated into estimand definitions and one limitations paragraph.

## S5.5 — Short appendix and final gates

Keep only material useful for verifying main-paper claims: proof details, the 20-target certificate table, crossed-bootstrap definition, S4 source-certification details, and clean-replay contract. Do not move a result required for the central argument out of the main paper. Final gates cover page count, file size, fonts, unresolved references, float clipping, terminology, numerical consistency, anonymity, PDF metadata, archive hashes, and clean-room replay.

## Stop conditions

Stop on a changed frozen result, a claim without committed evidence, a clean replay that imports the main repository, anonymous-package identity leakage, a main body over 12 pages, or an appendix carrying evidence required to understand the central claim.
