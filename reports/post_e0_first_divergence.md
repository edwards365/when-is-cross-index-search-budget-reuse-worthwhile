# Post-E0 D0-D first-divergence attribution

Rows: 3127 harmed query-ef pairs across 9 frozen graph pairs.

| Diagnostic class | Count | Fraction |
|---|---:|---:|
| NEAR_TARGET_DAMAGE | 1968 | 0.6294 |
| RECIPROCAL_PRUNING_DAMAGE | 801 | 0.2562 |
| QUEUE_ORDER_EFFECT | 194 | 0.0620 |
| PROXY_TAIL_FAILURE | 97 | 0.0310 |
| REDUNDANCY_LOSS | 67 | 0.0214 |

Classification follows the preregistered exclusive precedence and is a diagnostic partition, not a causal proof. Counterfactual D0-E and add-back D0-F are still required.

Only 5.15% of the first absent edges were strict-progress edges, while 58.78% were admissible under the contemporaneous beam threshold. The edge-origin audit found 2326 source-selection changes, 339 reciprocal edges lost because the originating selection changed, and 462 reverse-pruning losses.

No new ef point, validation-dev member, or formal-test member was accessed. Temporary indexes used for exact trace reconstruction were deleted before this analysis.

