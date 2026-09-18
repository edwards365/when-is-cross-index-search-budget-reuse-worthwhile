# Compact Manuscript Structure

## Storyline

Graph rebuilds alter the execution environment of a search-budget decision. The paper follows one closed operational loop: diagnose portability, qualify a target decision, recover useful work, and price the information used by that recovery. ICBA is the organizing contract. TCP covers recurring profiled queries through target selection and certification. The fixed-slack route instead freezes a source-derived candidate and asks whether target certification alone is sufficient. Faiss on two 100K datasets and hnswlib on Deep1M provide target-certified recovery evidence; hnswlib on the 100K grids supplies the implementation boundary. The central claim is conditional recovery under explicit target qualification, not one universally transferable policy.

## Main-paper order and page budget

| Section | Role | Target pages |
|---|---|---:|
| Abstract + 1 Introduction | problem, key findings, contributions | 1.25 |
| 2 Related Work | construction sensitivity, adaptive policies, risk control | 0.75 |
| 3 Estimands and Guarantees | risk, first/stable labels, information limit, fixed-target certificate | 1.20 |
| 4 ICBA and Recovery Policies | audit contract, TCP, source-slack bridge | 1.15 |
| 5 Experimental Design | roles, implementations, statistics, evidence levels | 0.85 |
| 6 Portability Failures | graph-only and refresh evidence | 1.20 |
| 7 Recovery and Prospective Boundary | TCP, target-certified Faiss and Deep1M, tails, robustness | 2.10 |
| 8 Scope Across Methods and Graph Family | DARTH, Ada-ef, graph-only Deep1M transport, Vamana | 0.80 |
| 9 Economics and Operational Implications | break-even, deployment decision tree, limitations | 1.20 |
| 10 Conclusion | community takeaway | 0.25 |
| Float headroom | placement variance | 0.70 |

Target: 11.3–11.7 content pages, leaving references outside the 12-page limit.

## Evidence order

1. Establish graph-only non-portability without TCP.
2. Show deterioration of one executable policy under data refresh.
3. Use ICBA to explain which observations, query roles, and confidence allocations authorize a decision.
4. Quantify TCP recovery, fallback, tails, build robustness, and amortization on the recurring-profile workload.
5. Test fixed-slack recovery on fresh queries: establish the source-only implementation boundary, then report independent target qualification on Faiss and preregistered hnswlib Deep1M.
6. Use DARTH, Ada-ef, graph-only Deep1M transport, and Vamana to delimit external scope rather than form a leaderboard.

## Main vs appendix

The main paper retains all central point estimates, 95% intervals, certification decisions, and the cross-implementation recovery contrast. The separate appendix holds proof expansions, per-target rows, bootstrap formulas, complete source-certification rows, and clean-replay details. No central result may be introduced only in the appendix.

## Compression rules

- Define each limitation once, where it changes interpretation.
- Replace repeated `not a universal claim` sentences with implementation/dataset qualifiers in the claim itself.
- Keep one terminology table only if it saves more space than in-line definitions after S4 integration.
- Keep TCP and fixed-slack results in separate tables because they use different information contracts; connect them in prose through the common ICBA decision flow.
- Move per-target rows and alternative bootstrap variants to the appendix.
- Keep result sentences in observation–interpretation form; remove process narration and reviewer-facing reassurance.
