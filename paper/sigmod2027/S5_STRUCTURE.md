# S5 Compact Manuscript Structure

## Storyline

Graph rebuilds alter the execution environment of a search-budget decision. The paper first measures when retained budgets stop meeting their target, then separates response portability, statistical qualification, and lifecycle value. ICBA is the organizing audit contract. TCP and the source-slack replay are two recovery cases with different information requirements: TCP uses target selection, while the latter tests whether a source-certified fixed margin can avoid target selection. The evidence shows conditional recovery rather than one universally transferable policy.

## Main-paper order and page budget

| Section | Role | Target pages |
|---|---|---:|
| Abstract + 1 Introduction | problem, key findings, contributions | 1.25 |
| 2 Related Work | construction sensitivity, adaptive policies, risk control | 0.75 |
| 3 Estimands and Guarantees | risk, first/stable labels, information limit, fixed-target certificate | 1.20 |
| 4 ICBA and Recovery Policies | audit contract, TCP, source-slack bridge | 1.15 |
| 5 Experimental Design | roles, implementations, statistics, evidence levels | 0.85 |
| 6 Portability Failures | graph-only and refresh evidence | 1.20 |
| 7 Recovery and Prospective Boundary | TCP, tails, robustness, fresh S4 Faiss/hnswlib result | 2.05 |
| 8 Scope Across Methods and Scale | DARTH, Ada-ef, Deep1M, Vamana | 0.85 |
| 9 Economics and Operational Implications | break-even, deployment decision tree, limitations | 1.20 |
| 10 Conclusion | community takeaway | 0.25 |
| Float headroom | placement variance | 0.70 |

Target: 11.3–11.7 content pages, leaving references outside the 12-page limit.

## Evidence order

1. Establish graph-only non-portability without TCP.
2. Show deterioration of one executable policy under data refresh.
3. Use ICBA to explain which observations, query roles, and confidence allocations authorize a decision.
4. Quantify TCP recovery, fallback, tails, build robustness, and amortization.
5. Add the S4 fresh-query boundary test: source +1 is safe and economical for registered Faiss builds, while the same bridge collapses to endpoint or negligible value for hnswlib.
6. Use external methods and scale/family bridges to delimit scope rather than form a leaderboard.

## Main vs appendix

The main paper retains all central point estimates, 95% intervals, certification decisions, and the S4 cross-implementation contrast. The separate appendix holds proof expansions, twenty-target rows, bootstrap formulas, complete S4 source-certification rows, and clean-replay details. No central result may be introduced only in the appendix.

## Compression rules

- Define each limitation once, where it changes interpretation.
- Replace repeated `not a universal claim` sentences with implementation/dataset qualifiers in the claim itself.
- Keep one terminology table only if it saves more space than in-line definitions after S4 integration.
- Use one combined recovery table for TCP and S4; retain distinct evidence-level columns.
- Move per-target rows and alternative bootstrap variants to the appendix.
- Keep result sentences in observation–interpretation form; remove process narration and reviewer-facing reassurance.
