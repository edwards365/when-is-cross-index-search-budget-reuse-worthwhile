# Theory-to-experiment map

| Mathematical object or premise | Frozen experimental estimate | Code / test location | Validation purpose |
|---|---|---|---|
| \(\tau_e\) | local pseudoinverse leverage | `python/narhnsw/resistance.py`; `cpp/src/resistance.cpp` | structural nonredundancy |
| \(\sum_e\tau_e=N-1\) | projection trace residual | `theory/math_validation.py`; effective-resistance tests | algebra/solver audit |
| bridge iff \(\tau_e=1\) | bridge labels versus score tolerance | effective-resistance tests; mechanism edge log | local bridge certificate |
| random-tree marginal | exact enumeration / fixed-seed frequency | `spanning_tree_marginals`; test | probabilistic interpretation only |
| \(\Phi_H(A)\) | preregistered local cut estimator | graph analysis (pending) | distinguish bottleneck from pair score |
| local/global resistance bias | one-hop, two-hop, and wider-reference rank/error | counterexample test; pending radius ablation | test Rayleigh bias and ranking stability |
| direction log-det | regularized Gram marginal | `python/narhnsw/repair.py`; submodularity test | direction coverage and numerical audit |
| selection margin \(g_t\) | winner-minus-runner-up marginal | selector logging (pending) | test Theorem C across insertion orders |
| \(D_E\) | Jaccard edge difference across \((\pi,s)\) | stability analysis (pending) | raw graph sensitivity |
| \(D_\tau\) | symmetric-difference weight under one frozen reference | stability analysis (pending) | critical-edge sensitivity; not assumed superior |
| \(\delta\)-monotone premise | distance decrease along exact query traces | `python/narhnsw/search.py`; trace extension pending | test path mechanism and Theorem E premise |
| cross-cut premise | cluster/cut label crossings and signed progress | synthetic narrow-bridge experiment | test Theorem B on controlled data |
| \(ef^*(q;G,R)\) | minimum successful value on fixed `ef` grid | experiment pipeline | offline query difficulty; never an online feature |
| \(\operatorname{NDC}\) | exact wrapper distance-call counter | C++ instrumentation | search cost; upstream HNSW counter is not used as exact total |
| geometric hardness | LID, contrast, neighbor gap, density | analysis pipeline (pending) | separate query geometry from graph state |
| navigation hardness | stalls, frontier growth, missing high-score candidates | trace analysis (pending) | graph-conditional mechanism diagnosis |

For every claimed test, record whether the mathematical premise holds before evaluating the conclusion. Frozen diagnostic scores must be computed without held-out truth leakage when proposed as online signals. Truth-dependent quantities such as \(ef^*\) are explicitly offline diagnostics. A synthetic-only theorem remains useful as a mechanism certificate, but cannot be advertised as a real-data performance guarantee until premise prevalence and effect sizes are measured.
