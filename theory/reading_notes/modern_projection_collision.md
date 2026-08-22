# Reading cards: modern projection and collision methods

## MCGI

1. **Object:** manifold-consistent graph indexing. 2. **Assumptions:** paper's learned/estimated local geometry and datasets. 3. **Result:** adaptive graph construction informed by local intrinsic dimension. 4. **Mechanism:** manifold-consistency and LID-aware indexing. 5. **Complexity:** empirical/preprint claims only. 6. **HNSW relation:** contemporary graph-construction alternative. 7. **Transfer:** motivates LID-stratified analysis. 8. **Missing:** peer-reviewed theorem and a connection to resistance. 9. **Verified:** full primary arXiv preprint, submitted 2026-01-05. 10. **Action:** do not import guarantees; add LID slices when data support them.

## pHNSW

1. **Object:** projection-filtered hardware/software HNSW. 2. **Assumptions:** PCA projection quality and the evaluated hardware/workloads. 3. **Result:** candidate filtering reduces expensive full-distance work empirically. 4. **Mechanism:** low-dimensional PCA screening. 5. **Complexity:** systems measurements/preprint. 6. **HNSW relation:** direct query acceleration. 7. **Transfer:** projection screening is orthogonal to edge repair. 8. **Missing:** a recall-safe projection error bound for our data. 9. **Verified:** full primary arXiv preprint. 10. **Action:** keep separate from graph-theory claims.

## Projection-Augmented Graphs

1. **Object:** graph ANN augmented by projection information. 2. **Assumptions:** paper projection/data model and construction. 3. **Result:** improved ANN trade-offs in the stated method; current arXiv metadata reports ICML 2026 poster acceptance. 4. **Mechanism:** projection-assisted graph traversal/construction. 5. **Complexity:** paper-specific. 6. **HNSW relation:** contemporary alternative. 7. **Transfer:** possible fast direction proxy. 8. **Missing:** exact equivalence to our regularized log-det and local score margins. 9. **Verified:** full primary arXiv PDF, current v2 metadata. 10. **Action:** any projected direction approximation must receive a Gram/log-det perturbation bound.

## Collision/overlap lesson

Projection, directional diversity, graph hubs, and electrical leverage are different observables. A collision or projection filter can reduce distance computations without preserving a particular adjacency, while leverage measures redundancy in a weighted undirected reference. The project will combine them only through an explicitly declared objective or tested proxy, never by naming analogy.
