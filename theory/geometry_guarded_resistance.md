# Geometry-Guarded Resistance Selection

## Frozen local problem

For a center `u`, finite candidate set `C_u`, and budget `M`, let the frozen Geometry
objective be

`F_geo(S)=beta log det(I + sigma^-2 sum_(e in S) z_e z_e^T)
          + gamma sum_(e in S) exp(-(d_e/rho_u)^2)`.

The Phase II implementation fixes `beta=gamma=1`, `sigma=0.5`, and `rho_u` to the
median center-candidate distance, exactly matching the Phase I Geometry control. Its
deterministic greedy output is `S_geo`, and `F_base=F_geo(S_geo)`. This is a greedy
baseline value, not a claim of exact combinatorial optimality.

Scheme-A scores `tau_e=w_e R_eff(e)` are computed once on the explicitly augmented,
connected, union-symmetrized local graph. They are frozen during selection.

## GGR exchange algorithm

Initialize `S=S_geo`. Among all one-for-one proposals, deterministically accept a
proposal only when

- `F_geo(S') + eta_geo >= (1-epsilon) F_base`, and
- `sum_(e in S') tau_e > sum_(e in S) tau_e + eta`,

where `eta_geo=tau_num(1+|F_base|)` is the registered mixed float64 tolerance. Frozen
leverage improvement uses a separate `eta_tau`. Select the feasible proposal with
largest leverage gain, then geometry value, then deterministic candidate indices.
Stop at local optimality or the registered accepted-swap cap.

## Construction guarantees

Every accepted operation removes and adds exactly one distinct edge. Induction gives
`|S|=|S_geo|<=M`, so the per-node and global directed-edge budgets are preserved when
applied independently to all outgoing lists. The acceptance predicate gives
`F_geo(S) >= (1-epsilon)F_base-eta_geo` after every swap. The leverage sum increases by
more than `eta_tau`; with a finite candidate set and the explicit cap, termination is
unconditional. Without the cap, strict improvement and finitely many fixed-cardinality
subsets also imply termination in exact arithmetic.

These are algorithm-by-construction properties, not statements about the globally
best constrained set. The final set is only a one-swap local optimum if the cap does
not bind.

## What is not proved

The guard applies to the stated local undirected-reference Geometry objective. It
does not show nondecreasing Recall, NDC, latency, reachability, or stability of the
directed HNSW search. Independent per-node reselection can change incoming degrees,
reciprocity, reverse pruning, components, and long paths. Scheme-A leverage is also a
local augmented-graph quantity, not the final graph's dynamic edge marginal. These
effects require paired multi-build experiments.
