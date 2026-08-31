# NeurIPS and database red-team review

## NeurIPS/ICLR objection

The safety theorem is a one-line consequence of simultaneous coverage; the exact instance is Bonferroni plus Clopper–Pearson; the cost result is uniform concentration; and the lower bound is classical testing/BAI. CIBS-Race overlaps strongly with SafeBAI, LUCB, Track-and-Stop, successive elimination, and confidence sequences. Without a genuinely new information model theorem or optimal rate, this is not a credible top-ML theory contribution.

## Database/ANN objection

The current evidence is a budget proxy from exploratory offline simulation. Reviewers can reasonably reject unless real mean NDC, p95/p99, candidate-search cost, build time, memory, truth acquisition, and break-even are measured on independent portfolios. A fixed (K=3) Best-of-R comparison is insufficient unless the certificate, endpoint semantics, and full service accounting materially change deployability.

## Strongest failure modes

- selection is driven by one lucky build/seed;
- exact-binomial multiplicity rejects nearly everything;
- proxy benefit vanishes in actual NDC or worsens p95;
- offline build/candidate-search costs eliminate break-even;
- query roles are contaminated;
- endpoint infeasibility is silently imputed;
- results do not replay from serialized builds;
- direct ANN autotuning prior subsumes the practical contribution after full-text verification.

## Minimum defensible database story

Show a preregistered hnswlib build portfolio on two datasets, exact simultaneous risk certification, one-build/one-`ef` deployment, genuine mean-NDC gain with p95 non-inferiority, finite service break-even, top-1% robustness, independent evaluation, and a second portfolio confirmation. Position theory as safety plumbing and semantic discipline, not as the main novelty.

## Decision

Proceed with the narrow Stage-I pilot. Do not pursue a NeurIPS-level theory story on current results. If the pilot passes, target a database/ANN systems venue; if it fails, preserve the protocol and negative evidence without overstating a method contribution.

