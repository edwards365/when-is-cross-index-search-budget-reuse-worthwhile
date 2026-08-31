# CIBS semantic contract

## Deployment object

CIBS deploys one immutable serialized Graph-ANNS build and one raw global fixed-`ef`. The action is (a=(G_k,e_\ell)); it is not a per-query policy, model, online ensemble, or dynamic router.

## Raw fixed-`ef`

`ef` is an implementation search-control parameter, not a cap on expansions or NDC. Each raw fixed-`ef` run is independent. Raw recall is not assumed monotone in `ef`; no monotone envelope may certify the original action. Budget order organizes the grid but does not reduce the first-version multiplicity (M=KL).

## Risk and endpoints

(Z_i(a)=1\) whenever raw Recall@10 is below \(\tau\). If the maximum tested budget cannot attain \(\tau\), the observation is a failure or a separately preregistered abstention—never “success at max `ef`.” Right-censoring is not success evidence. The certificate controls target-query failure probability for the named action and portfolio only.

## Cost fields

Report requested `ef`, actual expansions, NDC, wall-clock, mean, p95, and p99 separately. Primary selection cost is mean NDC. Tail gates are not weighted into the mean. Offline accounting separates build, exact truth, candidate searches, selection, certification, artifact serialization, memory, and index size.

## Shared truth

One exact truth object per query may be reused for all candidate actions, so truth acquisition need not scale with (K). Candidate searches do scale with the number of evaluated actions. Build identities are not independent query replicates, and a query bootstrap does not quantify portfolio/build uncertainty.

## Query roles

The pilot must create immutable, pairwise-disjoint roles:

- `cibs_sentinel`: selection and certification only;
- `cibs_evaluation`: independent descriptive/confirmatory pilot evaluation, never selection;
- `cibs_future_confirm`: sealed for later independent confirmation;
- optional `cibs_design`: method-development only, if later needed.

Before any access, publish query IDs, SHA256 hashes, a pairwise-overlap matrix, master seed, truth-access policy, and a future-confirm sealing declaration. If only 250 eligible sentinel queries exist, use (n=250) and its exact threshold; do not borrow six evaluation queries. Validation-dev and formal-test remain sealed.

## Build generation

Pre-register seeds, insertion orders, dataset, graph degree `M`, `efConstruction`, metric, compiler, thread count, SIMD mode, and build IDs. Do not use sentinel/evaluation truth to generate builds, choose promising seeds, or drop failures. Serialize every candidate and hash it. The first version varies only legal seed and insertion order, not graph hyperparameters or implementation.

## Observable versus oracle

The deployed action depends only on preregistered artifacts and allowed sentinel observations. Oracle Portfolio may use full outcome information only as a nondeployable upper bound. Evaluation and future-confirm truth cannot influence action choice, tie-breaking, candidate generation, or threshold selection.

