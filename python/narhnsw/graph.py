"""Graph validation utilities shared by repair experiments."""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


def validate_adjacency(adjacency: np.ndarray, max_degree: int | None = None) -> dict[str, int]:
    graph = np.asarray(adjacency, dtype=bool)
    if graph.ndim != 2 or graph.shape[0] != graph.shape[1]:
        raise ValueError("adjacency must be square")
    if np.any(np.diag(graph)):
        raise ValueError("self-loops are forbidden")
    degree = graph.sum(axis=1)
    if max_degree is not None and np.any(degree > max_degree):
        raise ValueError("maximum degree exceeded")
    union = graph | graph.T
    components, _ = connected_components(csr_matrix(union), directed=False)
    return {
        "nodes": len(graph),
        "directed_edges": int(graph.sum()),
        "max_out_degree": int(degree.max(initial=0)),
        "components_union": int(components),
        "reciprocal_directed_edges": int((graph & graph.T).sum()),
    }
