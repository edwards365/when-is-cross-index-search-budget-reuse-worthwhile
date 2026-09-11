# ICBA Graph-ANNS Phase 1.1a final evidence hotfix

Parent commit: `39a8b6d41f9fa0561660100856e2e98f330d0a4a`. Branch: `exp/graph_anns_iclr_phase1_1_final_evidence_hotfix`. Worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw`. Parent tracked results were not modified.

Gate A=PASS; Gate B=PASS; Gate D=PASS; Gate E=PASS; Gate F=PASS.

### sift_100k
- 24 builds, 552 directed pairs, 750 clean queries; action grid 16/32/64/128/256/512.
- finite variation=0.910666667, endpoint variation=0.005333333, inclusive variation=0.910666667, unresolved=0.000722222.
- absolute/reference/incremental risk=0.236714975845/0.000722222222/0.235992753623; bootstrap CI=[0.227801690821,0.243872403382]; top-1% deletion=0.234269405055; LOBO=[0.235343873518,0.236598155468].

### arxiv_nomic_100k
- 24 builds, 552 directed pairs, 750 clean queries; action grid 16/32/64/128/256/512.
- finite variation=0.758666667, endpoint variation=0.018666667, inclusive variation=0.758666667, unresolved=0.001666667.
- absolute/reference/incremental risk=0.179323671498/0.001666666667/0.177657004831; bootstrap CI=[0.168569927536,0.186756219807]; top-1% deletion=0.175348646432; LOBO=[0.177140974967,0.178210803689].

## D3/D0
- sift_100k: Recall delta 0.000266667; mean budget ratio 0.976290009; p95 ratio 1.000000000; p99 ratio 1.000000000; build-time ratio 3.517991618.
- arxiv_nomic_100k: Recall delta -0.000400000; mean budget ratio 0.998529638; p95 ratio 1.000000000; p99 ratio 1.000000000; build-time ratio 1.709469143.

## Decision
`HNSW_CROSS_IMPLEMENTATION_CONFIRMED_VAMANA_ESTIMAND_NOT_HARMONIZED`.
