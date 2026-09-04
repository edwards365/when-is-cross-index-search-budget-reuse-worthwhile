# CALS semantic repair reaudit

Evidence level: EXPLORATORY_FIXED_TARGET_CALS_SEMANTIC_REPAIR. The prior zero-rescue result is withdrawn because portal IDs were internal tableint values rather than external labels. This reaudit resolves and records build-specific external/internal mappings, preserves query-role isolation, and evaluates all 256 registered portal subsets.

Corrected SIFT and Arxiv outputs show positive hit gains at every tested ef (8,16,32,64); gains are largest at low ef and remain nonzero at ef64. The per-query and all-subset Oracle are explicitly NON_DEPLOYABLE upper bounds. NDC is a proxy because the frozen source does not expose full native expansion counts; p95 NDC therefore remains NOT_ESTIMABLE for this audit.

Safety is not established: best fixed subsets retain risk above 5% on both datasets at ef64 and substantially higher at lower ef. Thus no deployment authorization follows. The corrected conclusion is that rescue is real but requires portal complementarity and an independently instrumented, costed deployment policy.
