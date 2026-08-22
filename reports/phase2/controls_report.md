# Phase II resistance-specificity control audit

Status: **implemented and validated for Gate-A entry**. This is a 10K
construction-only audit; it contains no query-performance result and reads only the
public HDF5 `train` member.

Geometry-safe Random receives the same Geometry baseline, epsilon-zero guard,
candidate pool, budget, source, and layer as GGR. It sees no leverage, query, trace,
or ground truth and uses independent seed 313 plus a deterministic dataset/center
offset. It samples from unvisited Geometry-feasible one-for-one exchanges until it
matches the number of GGR exchange steps. Shuffled-Resistance uses independent seed
991, permutes leverage identities inside each local candidate pool, and then calls the
unchanged GGR selection procedure.

| Dataset | Method | Changed centers | Requested/actual steps | Budget match | Terminal changed edges | Geometry total delta | True leverage total |
|---|---|---:|---:|---:|---:|---:|---:|
| SIFT | GGR | 73 | 163/163 | 100% | 158 | +1.628146 | 327.176968 |
| SIFT | Geo-safe Random | 73 | 163/163 | 100% | 130 | +2.353474 | 322.061553 |
| SIFT | Shuffled Resistance | 62 | 163/135 | 50.0% centers | 135 | +1.282026 | 320.423986 |
| GloVe | GGR | 57 | 106/106 | 100% | 105 | +0.661461 | 830.034914 |
| GloVe | Geo-safe Random | 57 | 106/106 | 100% | 96 | +0.760157 | 815.240184 |
| GloVe | Shuffled Resistance | 52 | 106/96 | 66.4% centers | 95 | +0.416580 | 812.678602 |
| Arxiv | GGR | 50 | 110/110 | 100% | 108 | +0.362605 | 427.923162 |
| Arxiv | Geo-safe Random | 50 | 110/110 | 100% | 90 | +0.693127 | 422.638128 |
| Arxiv | Shuffled Resistance | 35 | 110/80 | 64.8% centers | 79 | +0.268973 | 419.979130 |

All methods have minimum final-minus-baseline Geometry delta zero, never negative.
Random exactly matches GGR step budget on every center, including zero-step centers;
therefore source count, candidate size, and layer distribution are also exact. The
shuffled control is intentionally not forced to take non-improving shuffled-score
steps: its lower natural count is part of executing the same selector after score
identity destruction.

GGR's larger true frozen-leverage total is a mechanical self-check because GGR selects
on that score. It cannot establish resistance-specific navigation value; only Gate A
paired query results against both controls can do so. Full rows and fixed seeds are in
`results/raw/phase2_controls_10k_s7_v1` at commit `bf9bc86`.
