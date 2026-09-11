# D3 full recalculation

D3 index bytes, top-k, hit counts, minimum-safe actions and endpoint states were separately recomputed from raw D3 rows. Both datasets pass 3/3 identity checks and have zero incremental and post-top-1 deletion transport risk. D3/D0 quality and build overhead are in `d3_vs_d0_quality.csv`; D3 NDC is not estimable because its rows have no NDC field and D0 NDC is a zero placeholder.
