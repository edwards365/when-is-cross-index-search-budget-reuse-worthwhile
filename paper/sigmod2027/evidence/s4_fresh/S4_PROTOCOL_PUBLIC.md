# S4 frozen protocol: fresh-query confirmation

S4 was registered after the previously analyzed 375-query S3 source-design role had frozen one action per source build and before any of the 1,000 future-query vectors or truths were accessed. The existing future-query list was split in registered order into 500 source-certification and 500 target-evaluation identifiers per dataset. Only these 500/500 roles are prospective. They are disjoint and do not overlap the earlier design or evaluation roles.

For each source build, the frozen source action is the lowest of six native grid actions whose one-sided Clopper-Pearson upper bound is at most 0.05 under a Bonferroni allocation of 0.05/6 on 375 source-role queries. If no action passes, the rule uses the endpoint. S4 evaluates three fixed candidate lanes at +0, +1, and +2 native grid levels, clipped at the endpoint.

On the 500 fresh source-certification queries, each candidate and endpoint receives alpha 0.025. The completed source decision executes the candidate only when both bounds are at most delta 0.05; otherwise it uses the certified endpoint. The separate 500-query target role evaluates this frozen candidate/fallback decision and cannot change its action, threshold, or fallback.

Primary intervals resample target-query identifiers with each query's complete 552-direction outcome vector. The experiment is conditional on the 24 registered builds per implementation and dataset. It does not treat directed pairs as independent builds or claim target-side deployment certification.

For each target direction, let `L_0.05` and `U_0.05` be one-sided Clopper-Pearson lower and upper bounds at per-direction alpha 0.05. Status B means `U_0.05 <= 0.05`, A means `L_0.05 > 0.05`, and U is the remaining interval-overlap case. No multiplicity correction is applied across the 552 directions. These statuses are descriptive target audits, not simultaneous certificates or deployment authorizations.
