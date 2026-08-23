# Replay Gate R0 final report

Decision: **PASS_TO_GRAPH_E0**.

Labels: **LOCAL_NAVIGATION_SUPPORTED** at the offline local-diagnostic level and **PROXY_DISTRIBUTION_MISMATCH** for absolute calibration. Neither label establishes final-graph or search-performance improvement.

## Evidence matrix

| dataset | Jaccard(A4) | dStrict vs A4 | dStrict vs Geometry | dStrict vs GGR | dBeam vs A4 | proxy-real rho | calibration MAE | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arxiv_nomic_10k | 0.883124 | 0.017298 | 0.04717 | 0.074476 | 0.020484 | 0.316638 | 0.430458 | True |
| glove100_10k | 0.701934 | 0.043478 | 0.041729 | 0.052764 | 0.038454 | 0.195705 | 0.55994 | True |
| sift_10k | 0.966066 | 0.006004 | -0.016182 | 0.005629 | 0.000343 | 0.285945 | 0.502106 | False |

Passing datasets: arxiv_nomic_10k, glove100_10k (2/3; required 2).

- The full selector matrix contains 2,304 frozen insertion events and 20,736 selector rows; selections are nonempty.
- GloVe and Arxiv are non-equivalent to Algorithm 4 at the frozen 0.95 mean-Jaccard threshold and beat every registered strong comparator on strict-progress and beam-admissible route labels in a majority of seeds.
- Length-adjusted coverage intercepts remain positive; the signal is not fully explained by choosing shorter edges.
- LengthAware-Angle exactly reproduces Algorithm 4 on all recorded events; GB-MPCC therefore also exceeds this explicit equivalence baseline on the two passing datasets.
- SIFT does not pass because mean GB-MPCC/Algorithm-4 Jaccard exceeds 0.95 and route gains over Geometry/GGR are seed-inconsistent.
- The proxy strongly overestimates absolute real-route coverage and has only modest event-level rank correlation. This is retained as a central risk, not hidden by the relative-ranking result.

## Scope and authorization

R0 used only frozen train-prefix candidates and existing design-dev queries/truth. Existing Original 100K indexes were loaded read-only; no index was constructed or mutated. Formal test was not accessed.

This committed PASS authorizes only Graph Gate E0 under a separate frozen E0 protocol. It does not authorize E1, formal test, or any performance claim.
