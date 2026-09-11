# P2 literature audit + theory derivation + conclusion optimization

## Theory derivation: why max-over-source works, and where it must stop

**Proposition (pooling risk as an order statistic).** Let B_1(q),...,B_k(q) be the
source-pool minimum safe actions and B_t(q) the target's, over a common grid, and let the
robust policy deploy a_rob(q) = max_{s<=k} B_s(q) and abstain when any source has
B_s(q) = BOT. Then the target unsafe-execution probability satisfies

  r_t(a_rob) = Pr_q[ a_rob(q) < B_t(q) ]  =  Pr_q[ max_s B_s(q) < B_t(q) ],

which is the CDF of the maximum evaluated at the target: an order-statistic of the pooled
source response. Two consequences.

1. *Monotone k-decay with an outlier floor.* If, conditional on q, the events
   {B_s(q) < B_t(q)} were independent across sources with per-source probability
   p(q) = Pr[B_s(q) < B_t(q) | q], then r_t(a_rob) = E_q[p(q)^k]: geometric decay in k,
   matching the measured curve (hnswlib SIFT: 0.218 -> 0.116 -> 0.076 -> 0.033 -> 0.012 ->
   0.0096 for k = 1,2,3,5,10,22). The decay stalls at the mass of queries where the target
   build is an outlier (p(q) ~ 1 for most sources) - the same tail that LOBO isolates.
   Conditional independence is not assumed by the policy, only used to read the curve;
   the measured curve is the artifact of record.

2. *Cost floor.* On queries where the target is a response outlier, a_rob(q) > B_t(q),
   so the conservative rate converges up to Pr_q[B_(k)(q) > B_t(q)] - measured 0.39-0.68 at
   k = 22 - and the DistComp floor 1.34-1.45x oracle is exactly the price of covering the
   inter-build response diameter. Pooling cannot beat this floor; only environment
   elimination (deterministic contract) or target evidence can.

**Corollary (certification margin, why m=59 misleads).** The zero-failure CP bound at
m = 59 certifies risk <= 0.05 only when the true risk is near zero: P(pass | r) =
(1-r)^59, so r = 0.008 (SIFT max-action) passes with probability 0.62, r = 0.0126 (Arxiv)
with 0.47 - exactly the measured certify rates. Reviewer E1's "59 queries" premise holds
only for M = 1 with a genuine margin; the registered grid provides useful actions whose
risk sits inside the thin band (0.008, 0.05), where Theorem 2's condition (iii)
(positive margin) fails - measured as 48/48 first-failure at c3_margin.

## Literature audit (claims vs. cited work)

- Pooling-as-quantile: a_rob is the order-1 upper quantile of the source response; formal
  relatives are conformal quantile aggregation and split-conformal risk control
  (Bates et al. 2021; Angelopoulos et al. 2024/2025 - all already cited). The k-source
  ladder is an empirical quantile ladder; no new theory is claimed.
- Multi-environment pooling: Duchi et al. 2025 treats environments as the sampling unit;
  our pooling baseline is the deterministic best-case for the practitioner, and its
  k-decay gives a measurable analogue of their "environment diversity".
- Budget autotuning: Bae et al. 2026 (QBAT) tunes budgets per index; our result says any
  such tuner must be re-run per build, and gives the pooling baseline its robustness
  ceiling. ANCHOR SUGGESTION for P5 (currently unanchored reference).
- Rebuild variability empirics: Elliott & Clark 2024 study data-order effects on recall -
  ANCHOR SUGGESTION for Section 2.1 (currently unanchored).
- Certification sample complexity: Garivier & Kaufmann 2016 (fixed-confidence BAI) is the
  natural anchor for the m_min derivation - ANCHOR SUGGESTION for Section 4.3.
- Le Cam reduction attribution: Yu 1997 - ANCHOR SUGGESTION for Section 4.1.
- Graph-ANNS theory context: Prokhorenkova & Shekhovtsov 2020 - ANCHOR for Related Work 2.1.
- Adaptive HNSW: Zhang & Miller 2026 - ANCHOR for Related Work 2.2.

All six unanchored references from P0 now have a designated anchor site; no new citations
are invented.

## Conclusion optimization (fed to P5)

1. Section 5 decision rule is upgraded from two branches to a four-way, cost-ordered
   prescription: deterministic contract (risk 0, build-time 1.71-3.52x) > robust source
   pooling when >= 10 prior builds exist (risk < 2.4%, DistComp 1.34-1.45x, uncertified) >
   fixed-action certification only with declared margin (m=59 per action, Bonferroni
   inflation for selection; fails on the registered grid) > abstain. This is the paper's
   constructive core and answers E1 + max-over-source in one table.
2. Theorem 2 discussion gains its honest empirical verdict: conditions (i),(ii),(iv),(v)
   are satisfiable on the registered grid; (iii) is not, for any non-maximal action -
   turning the theorem from template to measured boundary.
3. Three-layer evidence framing (response vs global policy vs learned predictor): the
   six-method table now gives the *policy layer* a constructive answer, so the paper can
   state precisely that layer 1 is confirmed, layer 2 now has a bounded positive answer
   (pooling), and layer 3 remains future work.
