# Phase II Gate 0 numerical amendment

Status: frozen before the Gate 0 precision run; formal test firewall remains sealed.

This amendment corrects terminology and numerical semantics without changing the
research hypothesis, datasets, methods, epsilon candidates, or decision thresholds.
The original hashed `phase2_v1` files remain unchanged.

1. The deterministic greedy Geometry value is named
   `F_geo_base = F_geo(S_geo)`. It is not denoted by a star and is not claimed to be
   the global cardinality-constrained optimum.
2. Geometry feasibility uses float64 and the explicit mixed allowance
   `eta_geo = tau_num * (1 + abs(F_geo_base))`.
3. Frozen-leverage strict improvement uses a separate absolute tolerance `eta_tau`;
   it is not conflated with the Geometry allowance.
4. Gate 0 sweeps `tau_num in {0, 1e-15, 1e-12, 1e-9}` with `eta_tau=1e-12` on the
   three existing 10K construction-only datasets, 128 deterministic centers per
   dataset, and a 32-center-per-dataset stratified Decimal-60 recomputation.
5. Epsilon remains zero for Gate 0. No epsilon is selected for formal evaluation.
6. Gate 0 cannot pass until proposed changes are measured after actual reciprocal
   insertion and reverse pruning in the final HNSW graph. An external selector result
   alone is insufficient treatment-strength evidence.
