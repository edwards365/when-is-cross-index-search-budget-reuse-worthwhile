# Complexity ledger

Let \(c=|V_u|\) be local reference size, \(m_u=|E_u|\), ambient dimension \(d\), and selection budget \(M\le c\).

## Exact local resistance

Building a dense Laplacian is \(O(m_u+c^2)\) time including initialization and \(O(c^2)\) storage. A dense symmetric eigendecomposition/pseudoinverse is \(O(c^3)\) time and \(O(c^2)\) storage. Once \(L^+\) is available, a particular pair resistance costs \(O(c^2)\) as a generic quadratic form but only four indexed entries via \(R(a,b)=L^+_{aa}+L^+_{bb}-2L^+_{ab}\); all declared terminal pairs are therefore \(O(c^2+|C_u|)\) after inversion.

As a scale indicator, \(c^3\) is 32,768, 262,144, and 2,097,152 scalar cube units for \(c=32,64,128\). A Cholesky-like \(c^3/3\) leading count is about 10,923, 87,381, and 699,051 multiply-add units. One dense double matrix occupies 8 KiB, 32 KiB, and 128 KiB, respectively; eigensolvers need several such work arrays. Constants and memory traffic, not these counts alone, must be benchmarked.

Doing this independently for every data point costs \(O(nc^3)\), so the exact version is a mechanism-validation oracle rather than a claimed scalable constructor. Candidate routes for later work are hard-region gating, candidate subsampling, randomized resistance embeddings, nearly-linear Laplacian solves, terminal Schur complements, common-neighbor proxies, spanning-tree samples, and periodic offline repair.

## Direction log determinant

Recomputing a \(d\times d\) determinant for every candidate at every step is at least \(O(cMd^3)\) and is unacceptable. Maintaining a \(d\times d\) Cholesky factor gives each quadratic-form marginal and rank-one update \(O(d^2)\), hence \(O(cMd^2)\) scoring time and \(O(d^2)\) storage.

Sylvester's identity permits the selected-row Gram form. If all \(c^2\) direction inner products are precomputed in \(O(c^2d)\) time and \(O(c^2)\) storage, at greedy size \(t\) a candidate marginal needs an \(O(t^2)\) triangular solve. Summing over candidates and \(t<M\) is \(O(cM^3)\), plus \(O(M^3)\) factor updates. Without the full Gram cache, forming correlations adds \(O(cdM^2)\). The implementation should use Cholesky solves and `log1p`, symmetrize Gram matrices numerically, and reject zero directions; it should not form \(A_S^{-1}\) or `det(A_S)` explicitly.

## Combined selector

Frozen resistance/locality terms add \(O(cM)\). With a precomputed direction Gram matrix, the total exact local pipeline is
\[
O(c^3+c^2d+cM^3)
\]
time and \(O(c^2)\) storage (assuming \(M\le c\)). Lazy greedy may reduce evaluated candidates empirically but has the same worst-case order. Dynamic leverage adds up to \(M\) new resistance solves, \(O(Mc^3)\), and loses the frozen submodular proof.
