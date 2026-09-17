# Evidence provenance and claim map

This revision changes the paper and adds derived analyses. Existing native
response records, scientific result tables, query roles and selected shifts
are not changed. Original manuscript/repository baseline:
`e3d1cf9227c42858cb2a4e0d56dad2ff54451a12`.

| Claim | Frozen source or new derived source | Unit and interpretation |
|---|---|---|
| Graph-only hnswlib/Faiss increments | `results/graph_anns_iclr_phase1_1_hotfix/cross_family_evidence_table_final.csv`; copied to `evidence/w6_audit/graph_only_registry.csv` | 24 builds, 552 overlapping directions, 750 shared queries per setting; query-cluster intervals conditional on builds |
| Original TCP refresh decisions | `results/graph_anns_phase3_ea85/refresh95/per_build.csv` and corresponding old/target response tensors | 10 matched targets per dataset; original shifts and outcomes reproduced before any sensitivity |
| Matched old/new source risk | `evidence/w6_audit/*_paired_arrays.npz`, `audit_status.json` | Same policy on matched snapshots; refresh and graph changes remain confounded |
| Old-side qualification | `certification_per_build.csv`, columns `old_source_cp`, `target_source_cp` | Single-policy CP at .05, separate query role; post-hoc diagnostic, not campaign-wide certification |
| Joint candidate/endpoint decisions | `certification_per_build.csv` | Same selected policies; .025+.025 confidence-error allocation, at fixed target |
| Risk/gain/quantiles/sensitivity | `crossed_summary.csv`, paired NPZ arrays | 5000 product-bootstrap draws, target weights and shared query weights, seed 991; conditional histories and decisions |
| Per-target p95/p99 | `certification_per_build.csv` | Includes endpoint fallback; descriptive observed tail ratios, not a formal quantile noninferiority test |
| Complete NDC acquisition accounting | `cost_components.csv`, `cost_horizons.csv` | Cached/cold history; old truth counted once across graphs sharing the old base; full acquisition work conservatively charged |
| DARTH | `results/graph_anns_phase3_ea85/darth95_bridge/dataset_summary.csv`, copied to `evidence/extensions/darth_dataset_summary.csv` | Adapter target qualification at Recall@10<.95, not a matched transfer increment |
| Ada-ef | `results/graph_anns_phase3_ea85/adaef_bridge/arxiv_10build/aggregate.json`, copied to `evidence/extensions/adaef_aggregate.json` | 10 Arxiv target builds; native cosine/IP estimator does not provide an equivalent SIFT L2 path |
| Deep1M | `scripts/graph_anns_phase3_ea85/analyze_phase4_deep1m.py`; `results/graph_anns_phase3_ea85/deep1m/summary.csv` copied to `evidence/extensions/deep1m_summary.csv` | Eight target-build resampling units; 1000 queries and source histories conditioned on; no query-cluster claim |
| Vamana-style | `results/graph_anns_phase3_ea85/vamana_unified/summary.csv`, copied to `evidence/extensions/vamana_summary.csv` | Six target builds; stage-specific event, not the HNSW execution estimand; cost is mean per-target ratio and intervals include zero |

## Audit contract

Every experimental setting must identify: vector snapshot, implementation,
build IDs, query population and roles, native action grid, allowed policy
observations, truth definition, failure event, reference, policy selection,
certification allocation, fallback/abstention, executed cost, censoring, and
statistical unit. A missing field limits comparability; it is not filled by
borrowing another setting's certificate or endpoint assumption.

## Important semantic checks

1. At k=10, Recall@10<.95 counts any missing neighbor; it is not expected
   missed-neighbor fraction or mean recall.
2. First-passing and stable-tail labels differ on nonmonotone response curves.
3. Unresolved labels are retained; largest-grid execution is not assumed safe.
4. Original per-policy .05+.05 checks are not a .05 family-wise procedure.
5. Reanalysis does not reselect shifts after examining evaluation outcomes.
6. Shared query IDs imply crossed dependence; query weights are common across
   every sampled target in a bootstrap replicate.
7. Ratio-of-means gain differs from the mean of build-wise ratios.
8. Target deletions overlap: the largest-gain deletion is one LOTO member.
9. The one-million-vector result is response evidence, not TCP recovery there.
10. No fresh-query, structural causal mechanism, wall-clock, universal SOTA,
    or independently reproduced native-search claim is added.

## Verification

`independent_validation.json` records 244 arithmetic/provenance checks.
The four extension snapshots match frozen Git content after LF normalization;
the Vamana/Deep1M working-tree CSV copies use CRLF, a byte-level difference
without changed cells. Historical native-replay tests are reported as historical evidence,
not rerun or counted as new tests. Figure regeneration uses the compact
tables/arrays, not values inferred from figures. Full raw replay is outside
the self-contained LaTeX package and requires provisioned experiment assets.
