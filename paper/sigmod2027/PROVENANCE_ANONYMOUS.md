# Anonymous Evidence Provenance

This package contains compact records sufficient to regenerate manuscript tables, figures, certification arithmetic, and reported uncertainty summaries. It does not contain full vector collections, serialized ANN indexes, or native raw-search replay assets.

| Evidence block | Packaged source | Unit and interpretation |
|---|---|---|
| Graph-only hnswlib/Faiss increments | `evidence/w6_audit/graph_only_registry.csv` | 24 builds, 552 overlapping directions, shared-query inference conditional on registered builds |
| Graph-only marginal risk intervals | `evidence/graph_only_query_clusters.csv` and `evidence/replay_graph_only_intervals.py` | 3,000 compact per-query cluster means; 5,000 seed-991 query-cluster bootstrap draws reproduce absolute, reference, and incremental intervals |
| Refreshed-workload TCP decisions | `evidence/w6_audit/certification_per_build.csv` and paired arrays | ten targets per dataset; target selection, certification, and evaluation roles are distinct |
| Joint candidate/endpoint sensitivity | `evidence/w6_audit/certification_per_build.csv` and `evidence/reanalyze_review.py` (SHA-256 `ab012e376fa73686fe07bad7498aa6ec928d89d06fef28842ccebd8732dab471`) | fixed policies with `.025 + .025` confidence-error allocation per target; native-response reanalysis requires external frozen replay assets |
| Crossed uncertainty and tails | `evidence/w6_audit/crossed_summary.csv` and paired arrays | 5,000 seed-991 product-bootstrap draws over target build and shared query |
| Lifecycle accounting | `evidence/w6_audit/cost_components.csv`, `cost_horizons.csv` | cached/cold history scenarios; NDC accounting, not wall-clock or monetary cost |
| External method and scale/family scope | `evidence/extensions/` | estimator-specific bridges, not a common leaderboard |
| Fresh source-slack confirmation | `evidence/s4_fresh/s4_summary.csv`, `s4_source_certification.csv`, and `s4_pair_results.csv` | 24 registered builds per implementation and dataset; source certification and 552 held-out target directions are distinct |
| Fresh-stage registration | `evidence/s4_fresh/s4_preregistration_public.json`, `s4_source_policy.csv`, and `S4_PROTOCOL_PUBLIC.md` | previously analyzed 375-query S3 source-action role, 96 frozen source actions, disjoint prospective 500/500 S4 roles, and registration digests |
| Post-seal target certification | `evidence/target_certified/s3_pair_results.csv`, `s3_target_build_results.csv`, and `s3_summary.csv` | fixed Faiss `+1` candidate; 500 target-certification and 500 disjoint target-evaluation queries over 24 targets and 552 directions per dataset |
| Target-stage lifecycle | `evidence/target_certified/s4_pairwise_cost_ledger.csv`, `s4_shared_target_cost_ledger.csv`, and `s4_dataset_summary.csv` | exact target truth plus measured certification searches; pairwise and 23-source shared-target scenarios; historical source acquisition remains not estimable |

The clean replay regenerates compact evidence only. Full native reproduction requires separately provisioned public datasets, graph indexes, native libraries, and the registered query-role manifests. The manuscript distinguishes this compact replay from independent native-search replication.
