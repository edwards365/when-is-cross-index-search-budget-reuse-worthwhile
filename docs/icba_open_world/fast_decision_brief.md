# ICBA open-world Fast Decision

Status: **FAST DECISION, not final confirmatory seal**.

Frozen-input reproduction passed. After excluding right-censored and no-safe-endpoint graphs, open-world under-budget risk remains above 0.05 for hnswlib, Faiss HNSW, and Vamana on SIFT and Arxiv. Removing the top 1% NDC-saving queries does not change that verdict.

At labeled-target sentinel k={32,64,128,256}, all six dataset-by-implementation risks remain above 0.05 and do not trend toward safety. The evidence therefore rejects finite sentinel variance as the dominant explanation. Endpoint infeasibility explains GloVe and part of the all-graph problem, but not feasible-only SIFT/Arxiv failure. Environment exclusion is the largest identified contrast. Source-Oracle dependence and target-label dependence are necessary limitations of the successful frozen lane, but their separate numerical contributions are not identifiable because no frozen deployable-policy or unlabeled-target counterfactual exists.

Across 648 frozen directed build pairs, the preregistered Z0-near/response-far rule yields 94 empirical collision candidates. Z0 metadata does not qualify for structured recovery. A common deployable Z1 runtime fingerprint is absent, so Z1 is NOT_ESTIMABLE rather than failed by imputation. Z2 is labeled target information and is not a deployable unlabeled channel.

Fast Decision label: **OPEN_WORLD_IMPOSSIBILITY_SUPPORTED_STRUCTURE_UNRESOLVED**. The next theory priority is the no-structure open-world safety-versus-conservatism lower bound, with support/OOD recovery retained only as a future conditional route. Do not begin algorithm design from this evidence.

Theorem priority status: T-OW0 FORMAL_PROOF_COMPLETE; T-OW1 RESTRICTED_PROPOSITION/PROOF_SKETCH (two environments, finite grid); T-OW2 FORMAL_PROOF_COMPLETE by counterexample; T-OW3 PROOF_SKETCH; T-OW4 CONJECTURE; T-OW5 NOT_ESTIMABLE pending build-level power completion.
