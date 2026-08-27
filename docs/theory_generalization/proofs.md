# ICBA proofs and proof obligations

## T1 — information ordering

Let policy classes \(\Pi_1\subseteq\Pi_2\) have the same action space, law, cost and risk constraint. The feasible set of \(\Pi_1\) is contained in that of \(\Pi_2\); taking an infimum gives \(V_\delta(\Pi_2)\le V_\delta(\Pi_1)\). This is a feasible-set argument, not a claim that every named information object forms a total order. In particular, target-static features and a sequential filtration need not contain one another. The comparison to fixed policies requires fixed actions to belong to the richer class. **FORMALLY_PROVED.**

## T2 — source-summary safe envelope

For summary \(X=x\), define \(g^*(x)=\operatorname{ess\,sup}(B_t\mid X=x)\). By the defining property of essential supremum, \(B_t\le g^*(X)\) almost surely, so \(g^*\) is safe. Any safe \(g\) satisfies \(B_t\le g(x)\) almost surely within each conditional cell, hence \(g(x)\ge g^*(x)\) almost everywhere. With nondecreasing cost, \(g^*\) minimizes expected cost. The information-coarsening tax is zero exactly when the chosen cost is almost surely equal to oracle cost; under strictly increasing cost this is equivalent to \(B_t=g^*(X)\) almost surely, i.e. target budget is summary-measurable. **FORMALLY_PROVED.**

## T3 — least safe monotone majorant

On ordered source cells \(x_1<\cdots<x_m\), let \(a_i=\max\{B_t:X=x_i\}\). Any safe nondecreasing \(g\) obeys \(g_i\ge a_i\) and therefore \(g_i\ge\max_{j\le i}a_j\). With the convention that larger source difficulty must not receive smaller target budget, the least majorant is \(g_i^*=\max_{j\le i}a_j\). If the implementation orders cells in the reverse direction, the equivalent formula is a suffix maximum; code and theorem must use the same convention. Pointwise order makes the least majorant unique on the budget lattice; equal-cost plateaus can make the cost-minimizing action non-unique without changing the least budget majorant. Unlike ordinary isotonic regression, no squared-error compromise is allowed: every observation is an upper constraint. Population form replaces maxima by conditional essential suprema. **FORMALLY_PROVED, ORIENTATION AUDIT REQUIRED.**

## T4 — inversion matching bound

For two source cells whose source ordering conflicts with target-required ordering, monotonicity forces at least one cell away from its oracle action. A pair penalty is the minimum excess cost over the two admissible monotone repairs. Summing penalties over vertex-disjoint inversion pairs avoids charging one query twice and therefore lower-bounds total monotone excess cost. A maximum-weight matching yields the strongest bound in this family. Inversion count alone cannot determine cost: penalties can be zero on cost plateaus or arbitrarily heterogeneous. Tight two-query examples exist; chains with heavily overlapping inversions make matching loose. The proof currently depends on additive per-query cost, uncensored finite budgets and the exact pair-repair penalty. **PROOF_SKETCH_ONLY pending exhaustive verification.**

## T5 — risk-matched finite optimization

Partition queries by observed information cell. Each candidate action in a cell has an expected cost and an integer failure count. Selecting one action per cell with total failures at most \(\lfloor\delta n\rfloor\) is a multiple-choice knapsack. Dynamic programming over cells and failure budget enumerates every feasible selection exactly, hence returns the minimum. At \(\delta=0\) only safe-envelope actions remain; with singleton oracle cells it becomes risk-matched oracle selection; with one information cell it becomes global fixed-budget selection. A common global failure budget can be allocated unevenly across cells, so independent conditional quantiles need not be globally optimal. **FORMALLY_PROVED for finite observed data.**

## T6 — certification power

For \(M\) prespecified policies and family error \(\alpha\), certify policy \(h\) only if its one-sided Clopper–Pearson upper bound \(U_{\alpha/M}(X_h,n)\le\delta\). Bonferroni gives simultaneous coverage without independence between policies. Define \(k^*=\max\{k:U_{\alpha/M}(k,n)\le\delta\}\). If true failures are iid Bernoulli(\(p\)), certification probability is \(P\{\mathrm{Binomial}(n,p)\le k^*\}\). For \(n=256,M=16,\alpha=\delta=.05\), \(k^*=3\). **FORMALLY_PROVED under iid calibration.**

## T7 — signal–certificate separation

AUC is invariant under strictly increasing score transformations, while a deployed threshold's selected-set risk depends on score calibration and threshold location. Thus two scorers can have identical rankings and AUC yet different threshold decisions after using the same numerical cutoff. More strongly, a rare unsafe tail can contribute little to pairwise ranking error but dominate \(P(unsafe\mid stop)\). Therefore high AUROC/AUPRC is neither necessary nor sufficient for a finite-sample risk certificate. It remains useful for candidate ordering and efficiency. **FORMALLY_PROVED by counterexamples.**

## T8 — sequential escape

A target-native state \(S_t\in\mathcal F_t\) that is not measurable with respect to source summary \(X_s\) permits stopping rules outside \(\sigma(X_s)\)-measurable policies; T2/T3 therefore do not lower-bound that larger class. Filtration growth gives nested stopping-policy classes only when earlier policies and fallback are retained. Prefix resumability determines whether observing state adds only incremental cost or forces duplicated work. Certification applies to the complete stopping/fallback policy. The 500-query equality test is computational evidence for one implementation, not a universal resumability theorem. **FORMALLY_PROVED for class separation; EMPIRICAL_ONLY for hnswlib resumability.**
