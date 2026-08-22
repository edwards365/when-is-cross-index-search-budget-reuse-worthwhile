# Local and global optimization models

## Directed Local Selection (DLS)

For one fixed base vertex \(u\), candidate set \(C_u\), reference graph \(H_u\), and frozen scores, solve
\(\max_{S_u\subseteq C_u,|S_u|\le M}F_u(S_u)\). Decisions for other vertices are absent. The result in K8 applies exactly here.

## Symmetric Local Repair (SLR)

Choosing \(u\to v\) requests a reciprocal adjacency. If \(v\) is full, its incident set is repruned, possibly deleting \(v\to u\) or a third edge. The state transition therefore changes another ground set and objective. SLR is a sequential coupled process, not one cardinality-constrained submodular problem.

## Global Degree-Constrained Rewiring (GDCR)

Choose a directed or undirected edge set subject to every vertex's degree capacity. In the undirected formulation each edge consumes capacity at two endpoints, giving a capacitated \(b\)-matching-style feasibility system. In a directed formulation separate outgoing partitions and incoming caps may appear. Even if a frozen global edge utility is submodular, the feasible family and approximation theorem must be identified afresh; the DLS \(1-1/e\) proof cannot be copied.

## Consequence for implementation claims

The current selector establishes a mechanism-level DLS result. Any HNSW integration must log reciprocal insertions, reverse-pruning losses, final degree violations, and the survival rate of edges favored by the local objective. Paper text must call this a local objective guarantee, not a construction-level approximation ratio.
