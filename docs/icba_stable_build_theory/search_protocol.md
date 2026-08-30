# Stable-by-Construction literature-forensics protocol

## Frozen scope and audit boundary

Cutoff: **2026-08-30**. Remote base commit: `904de537f16798eac9f68da549f2741d92e2b1c2`; theory reference: `41a44bd930679b5e933034a1496d2fe42e1ae018`. The server checkout named in the task was not mounted in this execution environment. Work was staged in an isolated directory and committed atomically to `exp/icba_stable_build_theory_forensics`. No merge from the theory reference was performed.

The audit did not read `validation-dev`, `formal-test`, or GloVe experimental records, did not build an index, and did not change any frozen result. The legacy baseline remains `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123`: it is a limitation, not repaired evidence. The remote base commit was resolved before writing; local disk had about 55 GB free. No active experiment owned by this task was started.

## Search families

Queries combined the following concepts and exact-title searches:

1. HNSW, NSG, MRNG/RNG, DiskANN/Vamana, FreshDiskANN, graph repair, entry points, pruning, batch/parallel construction;
2. insertion order, random seed, concurrent nondeterminism, deterministic/reproducible HNSW, build variance, Steiner-Hardness;
3. robust/dynamic ANN, graph maintenance, deletion/insertion stability, drift and rebuild;
4. graph perturbation, greedy-routing robustness, spanners, fault tolerance, consensus/majority graphs and concentration;
5. Learn-Then-Test, RCPS, CRC, DKW, selective classification, active testing and safe fallback;
6. ANNiE, QBAT, Ada-ef, ConANN, DARTH/DARTH+, per-query budgets and autotuning;
7. exact phrases: “budget response stability”, “recall-budget curve”, “cross-build HNSW”, “rebuild policy transfer”, “critical path ANNS”, and “consensus ANN graph”.

Primary sources were official proceedings, publisher pages, OpenReview, PMLR/PVLDB and arXiv PDFs. Search-engine snippets and secondary pages were used only for discovery. A title that could not be tied to a formal source is marked `UNVERIFIED_REFERENCE` and cannot support novelty.

## Reading levels

- **A — full text plus theorem/method verification.** All sections relevant to the information model, construction, theorem statements and proofs (when any exist) were inspected. “No numbered theorem” is recorded rather than inventing one.
- **B — body read, proof audit incomplete.** Methods/theory/experiments were read, but the complete proof chain or supplementary material was not independently closed.
- **C — discovery only.** Metadata, abstract, or public fragment only; excluded from theorem-level novelty decisions.

Final registry: **23 A, 25 B, 15 C**. The seven new stable-build A items are HNSW, NSG, DiskANN, FreshDiskANN, HNSW ordering sensitivity, Revisiting PG Construction, and MonaVec. Fifteen previously audited A items were reused only where the local full-text audit trail identified exact theorems/sections.

## Direct-prior trigger

`DIRECT_PRIOR_ART_FOUND_REDEFINE` requires one work to satisfy all four predicates: it actively modifies Graph-ANNS construction; explicitly optimizes cross-build query-budget response; proves a safety-risk or certification-complexity guarantee; and evaluates multiple rebuilds. No verified A-level paper satisfied all four. Similarity of vocabulary, deterministic replay, stable recall during updates, or a search-path lemma alone is insufficient.

## Citation tracing

For the 15 highest-risk papers, backward references were traced to NSW/RNG/MRNG, classical greedy routing, prediction-risk control and query-adaptive search; forward/author traces covered FreshDiskANN, dynamic-update work, learned query-cost methods, deterministic embedded indexes, and the 2024/2025 graph-construction analyses. The trace is summarized in `direct_prior_art_report.md`; exact source URLs and reuse decisions are in the literature matrix.

## Reproducibility

`scripts/icba_stable_build_theory/finite_graph_checks.py` contains deterministic finite witnesses and a seeded random small-graph search. `tests/icba_stable_build_theory/test_finite_graph_checks.py` runs without external test packages. These checks support bookkeeping and counterexamples; they do not replace the proofs in `proof_appendix.md`.
