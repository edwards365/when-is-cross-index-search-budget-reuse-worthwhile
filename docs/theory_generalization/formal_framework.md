# Information-Constrained Budget Adaptation framework

## Budgeted search system

A system is (S=(\mathcal Q,\mathcal I,\mathcal E,R,C)), with query (q\), index/environment (I\), totally ordered frozen budget grid (\mathcal E\), quality (R_I(q,e)), cost (C_I(q,e)), quality target (\tau), and allowed marginal failure probability (\delta). Define

\[
B_I(q;\tau)=\min\{e\in\mathcal E:R_I(q,e')\ge\tau\ \forall e'\ge e\}.
\]

If the set is empty, (B_I(q;\tau)>e_{\max}) is right-censored. This stable definition remains meaningful when empirical recall is non-monotone over the grid.

## Information classes

- (\mathcal G_{fixed}): no query or index observation; fixed budget only.
- (\mathcal G_{source}): a source-side summary (X_s(q)).
- (\mathcal G_{monotone}): (B_s(q)) with a nondecreasing decision rule.
- (\mathcal G_{target-static}): target-index and query static features.
- (\mathcal F_t): target-native sequential search filtration and stopping times.
- (\mathcal G_{oracle}): target sufficient budget (B_t(q)).

For a policy class measurable with respect to information (\mathcal G),

\[
V_\delta(\mathcal G)=\inf_\pi \mathbb E[C_I(q,\pi)]\quad\text{s.t.}\quad
\Pr\{R_I(q,\pi)<\tau\}\le\delta.
\]

An information inclusion yields a value inequality only when the richer class contains every feasible policy of the poorer class under the same distribution, cost, risk and action space. There is no general ordering between target-static summaries and a sequential filtration unless one measurably contains the other. The oracle is a lower benchmark when its action is admissible; fixed is an upper benchmark only when fixed policies belong to the adaptive class.

## Safety notions

Pointwise deterministic safety, marginal population risk, conditional risk, empirical design risk and certified population risk are distinct predicates. AUROC/AUPRC describe ranking, not any one of these safety predicates. A full sequential policy—including fallback—is the certification unit, not an isolated checkpoint.

## Empirical boundary

The mathematics applies to any ordered-budget decision problem satisfying its assumptions. Direct empirical evidence currently covers three datasets and three graph-index implementations; actionable positive transfer cost is strongest for hnswlib and is not asserted as universal across indexes.
