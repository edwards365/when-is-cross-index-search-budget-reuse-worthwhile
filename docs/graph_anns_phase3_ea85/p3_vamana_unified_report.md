# Phase 3 Vamana unified semantic bridge

Decision: **VAMANA_UNIFIED_SEMANTIC_BRIDGE_CONFIRMED_TWO_DATASETS**.

This is a protocol realignment of frozen Vamana Stage-I outputs, not a newly preregistered experiment. No graph was rebuilt and no new truth or sealed query role was accessed. The native action remains `l_value` with beam width 1; it is not equated numerically with HNSW `efSearch`.

| Dataset | Target builds | Transport risk | Build-bootstrap 95% CI | Cost tax | Cost 95% CI | Min LOTO risk | Delete-largest risk |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 6 | 0.1686 | [0.1588, 0.1793] | 0.0107 | [-0.0103, 0.0286] | 0.1644 | 0.1644 |
| Arxiv-Nomic-100K | 6 | 0.1137 | [0.1080, 0.1199] | 0.0117 | [-0.0083, 0.0303] | 0.1112 | 0.1112 |

The build-cluster intervals keep the safety-portability failure strictly positive on both datasets. LOTO and deleting the largest-risk target build preserve direction. Cost-tax intervals cross zero, so Phase 3 supports the cross-implementation safety phenomenon but not a Vamana cost-superiority claim.

Because this analysis reuses already observed frozen outputs, its contribution is semantic/statistical closure rather than independent replication. The original Stage-I query firewall, replay audit, index hashes, and negative/boundary evidence remain authoritative.
