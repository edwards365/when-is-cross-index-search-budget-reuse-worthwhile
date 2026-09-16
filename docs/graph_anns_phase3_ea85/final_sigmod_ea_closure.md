# Final SIGMOD E&A closure audit

## Final decision

`SIGMOD_EA_8_5_CLOSURE_COMPLETE`

The evidence package closes at **8.70/10 for SIGMOD Experiments & Analysis** and **7.55/10 for Regular**. The E&A route has no remaining critical scientific, statistical, reproducibility, or known format blocker. The Regular route remains credible but would need stronger method novelty and controlled system-level performance evidence; this does not block the E&A submission.

## What is closed

- Rebuild portability failure is reproduced across registered hnswlib evidence, external adaptive policies, post-hoc Vamana alignment, and a first-1M eight-build check.
- ICBA separates unsafe raw efficiency from certified deployable value using target builds as the statistical unit, query-role isolation, endpoint-aware events, build-cluster bootstrap, LOTO, and deletion robustness.
- Raw source TCP reuse is unsafe on both mixed-refresh datasets; independently selected target recalibration is safe, mean-distance efficient, and p95 non-inferior.
- The lifecycle native-distance ledger includes source profiling, target selection, certification, control, fallback, and serving. It is positive at `N=1e6` on both datasets while disclosing one nonamortizing Arxiv build.
- Artifact smoke, table regeneration, portable path interfaces, external-source ledger, query/truth checks, guarded full replay, checksums, and tests are committed.
- The paper-facing title marker, 12-page budget, headline-number ledger, claim boundaries, reviewer risks, limitations, and anonymous artifact text are sealed.

## Manuscript integration order

1. Change the title to the sealed E&A title and replace the abstract with the scoped E&A abstract.
2. Reframe the introduction around three questions: whether safe budgets transfer, how to audit failures, and when target recalibration amortizes.
3. Replace universal or SOTA-adjacent language with registered-family conditional language.
4. Put raw TCP failure and target-selection TCP recovery in the same main-text result panel.
5. Promote the lifecycle native-distance result and its one-build Arxiv exception to the main text.
6. Label Vamana as post-hoc supporting evidence and Deep1M as first-1M/eight-build evidence at first mention.
7. Use the sealed 11.3-page allocation and move secondary theory/protocol detail to the appendix.
8. Insert the anonymous artifact placeholder and external-data/full-replay boundary.

## Remaining work by priority

- **P0 editorial:** integrate the sealed language and compile the SIGMOD-formatted manuscript within 12 pages excluding references.
- **P0 verification:** run a final table-to-manuscript numeric diff and anonymity scan after integration.
- **P1 optional:** controlled wall-clock benchmarking on pinned hardware/threads may strengthen Regular positioning, but must remain secondary to native-distance evidence.
- **P2 optional:** broaden to more implementations or refresh operators only under a new preregistered protocol; current evidence is sufficient for the E&A closure.

No additional experiment is authorized solely to increase a numeric score. A new experiment should start only if manuscript integration or an external review reveals a concrete hard blocker not covered by the committed evidence.
