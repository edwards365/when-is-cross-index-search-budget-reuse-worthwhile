# Reading card: submodular greedy and sensor placement

**Sources.** Nemhauser, Wolsey, and Fisher (1978), DOI 10.1007/BF01588971; Krause, Singh, and Guestrin, JMLR 9 (2008), `krause08a`.

1. **Problem.** Maximize a monotone submodular utility under a cardinality budget; place sensors to maximize Gaussian-process information utility.
2. **Graph model.** None required for the generic theorem; the sensor paper uses covariance/information structure.
3. **Distance assumptions.** Not an ANN-distance result.
4. **Algorithm.** Add the element of maximum current marginal gain; lazy evaluation exploits diminishing returns.
5. **Theorem.** Normalized monotone submodular cardinality greedy achieves the finite-step factor \(1-(1-1/M)^M\ge1-1/e\). Krause et al. establish submodularity for their declared information objective and apply the guarantee.
6. **Assumptions.** Fixed ground set and set function, nonnegative/normalized monotone submodularity, exact cardinality constraint, and exact greedy unless an approximate variant is separately analyzed.
7. **Proof method.** Residual optimality gap shrinks by at least a \(1/M\) fraction per step; log-det/information diminishing returns follow from covariance order.
8. **HNSW relation.** Supports only the frozen one-node selector.
9. **Directly usable.** Greedy factor, lazy evaluation idea, and matrix determinant lemma/Cholesky implementation pattern.
10. **Not transferable.** Dynamic leverages, changing candidates, reciprocal pruning, and global degrees violate the fixed local setup.
11. **Innovation collision.** Log-det diversity is established mathematics; novelty cannot be claimed for submodularity itself.
12. **Metrics.** Objective value versus exhaustive optimum on small sets, marginal gaps, lazy recomputations, and numerical condition.
