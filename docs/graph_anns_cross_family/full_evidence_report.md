# Cross-family evidence report

## Answers to the registered evidence questions

1. Provenance: direct frozen commits, machine table in `source_provenance.csv`.
2. Mutation: none to source branches or result trees.
3. New computation: integration/bootstrap/figures only; zero ANN runs and indexes.
4. Data: SIFT-100K and Arxiv-Nomic-100K.
5. Families: two HNSW implementations plus Vamana-style.
6. Threshold: Recall@10 >= .95.
7. Category variation: 48.27%–89.47%, all above 10%.
8. Transport risk: 11.37%–21.57%, all above 2%.
9. Uncertainty: every registered risk CI lower bound is >10%.
10. Robustness: registered deletion/LOBO tables preserve positive direction; no single-build dominance reported.
11. Censoring: mixed rates range 0.27%–2.67%; retained explicitly.
12. Reference risk: nonzero evaluation reference for HNSW stages; definitionally zero target-own-safe reference for Vamana.
13. Cost: resolved positive for hnswlib/Faiss; unresolved for Vamana.
14. Cross-family magnitude: not claimed because native budgets/counters differ.
15. Safety conclusion: strong recurrence across every cell.
16. Method conclusion: none; this is evidence integration, not method validation.
17. Legacy scope: 111/123 conditional reproduction limitation retained.
18. Decision: `CROSS_FAMILY_EVIDENCE_SUFFICIENT_FOR_PAPER`; no future replication authorized.
