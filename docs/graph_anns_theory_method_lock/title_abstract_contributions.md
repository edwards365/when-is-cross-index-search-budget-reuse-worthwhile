# Title, abstract, and contributions

## Candidate titles

1. **When Safe Search Budgets Do Not Transfer: Build-Reconfiguration Risk in Graph ANNS**
2. **Hidden Build Environments in Graph ANNS: Theory and Evidence for Budget Non-Portability**
3. **Rebuilding the Same Index, Changing the Safe Budget: A Cross-System Study of Graph ANNS**

Recommended title: **When Safe Search Budgets Do Not Transfer: Build-Reconfiguration Risk in Graph ANNS**. “Graph ANNS” is justified by evidence spanning registered HNSW and Vamana-style implementations, provided the scope qualifier appears in the abstract and limitations.

## Abstract (231 words)

Graph approximate nearest-neighbor search systems routinely rebuild an index after data refreshes, maintenance, or randomized construction, while downstream search-budget policies are often treated as portable across builds. We study whether that assumption is justified. We model an index build as a hidden algorithmic environment and define the query-level safe budget using an implementation-native finite action set and an endpoint-aware failure event. A two-environment reduction to classical hypothesis testing shows that, when observable transcripts cannot distinguish builds requiring conflicting useful actions, any environment-blind policy must incur under-budget risk, conservative computation, fallback, or abstention in at least one environment. We complement this limitation with a fixed-target recovery theorem: a finite frozen candidate family can be safely screened and independently certified when endpoint feasibility, identifiability, positive risk margin, target evidence, and a valid fallback or abstention mechanism are available. We operationalize these results through ICBA, a certified diagnostic procedure for budget portability rather than a new search algorithm. Across SIFT-100K and Arxiv-Nomic-100K, and registered builds of hnswlib HNSW, Faiss HNSW, and DiskANN3/Vamana-style search, 48.27%–89.47% of queries change budget category across builds, while source-to-target transport-violation effects remain positive in all six data–operator cells. Conservative-cost penalties are statistically resolved for both HNSW implementations but not for the Vamana-style implementation, revealing operator-dependent consequences. A preregistered falsification ladder further shows why recalibration, build selection, structural stabilization, multi-lane rescue, and conservative auditing can fail despite partial mechanism evidence. Our results establish build reconfiguration as a missing condition for safe budget control and delineate what additional evidence is required for recovery.

## Contributions

- A finite environment–action formulation of build-reconfiguration portability with explicit unresolved endpoints, implementation-native actions, and risk/cost semantics.
- A domain-specific hidden-environment lower bound connecting classical testing error to unsafe search, conservative computation, fallback, and abstention.
- A fixed-target conditional recovery theorem and classical certification/economic corollaries with explicit scope boundaries.
- Cross-system evidence from six registered data × operator cells spanning HNSW and Vamana-style construction.
- ICBA, a certified audit procedure and theory-driven falsification ladder that separates safety, action attainability, observability, tail cost, and deployment economics.

## Introduction opening

Graph-based approximate nearest-neighbor search is commonly tuned as if an index were a stable substrate: once a search budget meets a recall target, the same policy is reused after rebuilding the index with unchanged data and nominal hyperparameters. Yet graph construction depends on input order, random choices, pruning, and implementation-specific state. A rebuild can therefore preserve aggregate recall while changing which queries require more search. This creates a portability problem that ordinary query-adaptive tuning does not address: the policy is transferred not only across queries, but across independently realized algorithmic environments.

## Theory contribution paragraph

Our theory separates limitation from recovery. The negative result is a Graph-ANNS loss instantiation of classical two-point testing: indistinguishable builds with conflicting useful action regions impose a non-portability lower bound. The positive result is deliberately conditional and fixed-target: endpoint feasibility, action-relevant identifiability, margin, independent target evidence, and a valid fallback or abstention suffice for finite-family screening and certification. Concentration and break-even statements are classical corollaries, not new universal statistical theory.

## Experimental contribution paragraph

We evaluate registered build families rather than treating queries as the only random unit. Across two datasets and three implementations, build reconfiguration repeatedly changes query-level safe budgets and induces directional transport violations. Effect sizes differ by data and operator, and conservative cost is not universally resolved. Method attempts are reported as a falsification ladder: they supply mechanism evidence and expose why safe selection, stable construction, rescue lanes, or conservative fallback may fail to create deployable value.

## Conclusion paragraph

Safe query-budget control depends on the realized graph, not only on dataset and nominal hyperparameters. Hidden build environments create a statistical barrier to environment-blind portability, while fixed-target recovery remains possible only under explicit feasibility, information, evidence, and fallback conditions. The cross-system evidence makes the risk-side phenomenon paper-ready within the registered scope; the absence of a deployable recovery algorithm is itself explained by the falsification ladder rather than concealed. Future work should target observable build descriptors with validated sufficiency, prospective environment-level certification, and cost-realizable recovery actions.
