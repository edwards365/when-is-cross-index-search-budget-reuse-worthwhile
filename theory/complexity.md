# Complexity

For a local candidate graph of size `c`, dense symmetric eigendecomposition/pseudoinversion costs `O(c^3)` time and `O(c^2)` memory. Scoring present edges after the inverse is `O(c^2)`. The reference greedy implementation recomputes small log determinants and is intentionally not optimized; a production implementation should use determinant-lemma or Cholesky rank-one updates. Exact local inversion at every node is not claimed to be scalable.

