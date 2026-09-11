# P1 definitions patch (for P5 application to the anonymous DOCX)

These blocks are paper-ready text. They add no new claim; they make existing quantities formal.

## D1. Minimum safe action and unresolved state (Section 3, after Eq. 2)

For each registered build environment E and query q, the minimum observed safe action is
B_E(q) = min{ a in A_E : Z_E(q,a) = 0 }, with B_E(q) = BOT when no registered action
succeeds; BOT is categorical and is never imputed as a numeric budget.

## D2. Incremental transport risk (Section 3 / Section 6, primary estimand)

Delta_{s->t} = Pr_{q~P_Q}[ Z_t(q, B_s(q)) = 1 ] - r_t^ref,
where r_t^ref is the registered reference risk on the target (the target-bottom event rate
under the stage-registered reference construction; for the four HNSW cells this is the
reference event of the repaired h=10 common estimand). Intervals are 95% query-bootstrap
over 5,000 resamples (seed 991) retaining each sampled query's full vector of directed-pair
observations; they are conditional on the registered build family.

## D3. Variation families (Section 7.1 / Appendix F)

- Finite-action variation: V_fin = Pr_q[ |{ B_E(q) : E in E_reg, B_E(q) != BOT }| > 1 ].
- Endpoint-state variation: V_end = Pr_q[ the multiset { 1{B_E(q)=BOT} : E in E_reg } is
  non-constant ].
- Inclusive variation: V_inc = Pr_q[ the tuple (B_E(q))_E is non-constant treating BOT as a
  state ].
Reported separately; V_fin is the headline heterogeneity number (75.87%-91.07%).

## D4. Cost naming (global rename in P5)

"ROM-NDC" is renamed **DistComp** throughout: DistComp(x vs y) = (mean distance computations
of x) / (mean distance computations of y), i.e. ratio of mean numbers of distance
computations, computed only within one implementation. "NDC" alone is avoided to prevent
confusion with NDCG. Per-action cost C_E(q,a) is implementation-internal and raw values are
never equated across implementations.

## D5. Certification parameters (Section 4.3 / Section 5)

delta = 0.05 (risk tolerance), alpha = 0.05 (familywise certification level), materiality
gate = 0.02 (preregistered scientific threshold, not a utility function), safety margin
gamma > 0 with the registered value stated per experiment, candidate family size M frozen
before certification; simultaneous control is Bonferroni over M when selection precedes
certification. Zero-failure Clopper-Pearson threshold m_min = ceil(log(alpha_l)/log(1-delta))
(= 59 for a single frozen action at alpha_l = 0.05, delta = 0.05; larger after Bonferroni).

## D6. Preregistration binding (Section 6 / Appendix I)

"Preregistered" in this paper means frozen in a versioned manifest with commit hash and
timestamp before the corresponding evaluation role was accessed (artifacts list the commit
per stage); it does not refer to an external OSF registration.

## D7. D3 regime naming (Section 7.3)

The deterministic contract (D3) is a hnswlib deterministic construction control: fixed input
order, seed, single thread, toolchain; it is an environment-elimination contract for the
registered same-data setting, not a recovery algorithm and not an implementation-independent
guarantee.

## D8. Auxiliaries used by Section 8

- Threshold rescue: a primary-lane failure whose quality event becomes a pass after union
  with the registered auxiliary lane outputs under the same tie rule.
- Search-only regret: per-query difference in distance computations between the deployed
  action and the target-safe per-query oracle, aggregated as mean with 95% query-bootstrap CI.
- Resident vs all-in cost: resident = in-process measurement after warm-up; all-in adds cold
  load, truth, and control costs; missing components remain NOT_ESTIMABLE rather than proxied.
- Reference action: the stage-registered reference construction used by r_t^ref in D2.

## Application notes for P5

- D2/D3 go where the first unexplained percentages appear (abstract keeps numbers only).
- D4 rename touches Table 3/4 headers, Section 7.2, and Appendix F/G text.
- D5 constants must match every experiment section that currently omits them.
- D6 replaces every bare "preregistered" claim.
