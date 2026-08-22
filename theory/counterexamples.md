# Auditable counterexamples

`python -m theory.search_counterexamples` emits exact numerical examples for C1, C2, and C6. Tests verify the finite constructions. Conductances are positive and graphs are undirected for resistance unless a directed navigation graph is explicitly stated.

## C1. Unit leverage without navigation value

Coordinates are \(u=(0,0)\), appendage \(v=(-1,0)\), progress node \(a=(1,0)\), target \(t=q=(2,0)\). Unit edges are \((u,v),(u,a),(a,t)\). Edge \((u,v)\) is a bridge, so \(\tau_{uv}=1\), but following it changes query distance from 2 to 3. It points away and enters a dead appendage. **Disproves:** high leverage implies query usefulness.

## C2. Low leverage as the only greedy shortcut

Let \(u=(0,0)\), \(v=(2,0)\), and four auxiliary nodes \(a_i=(0,10+i)\). Add a unit direct edge \((u,v)\) and four unit two-hop paths \(u-a_i-v\). Then \(R(u,v)=1/(1+4/2)=1/3\), so the direct edge's leverage is \(1/3\). For \(q=(2.1,0)\), every \(a_i\) is farther from \(q\) than \(u\); without the direct edge pure greedy stops at \(u\), while with it the path is \(u,v\). Adding more parallel paths drives the leverage arbitrarily close to zero. **Disproves:** discarding low-leverage edges preserves greedy navigation.

## C3. Spectral closeness does not preserve greedy navigation

Take any connected weighted base graph containing a local greedy trap at \(u\), and add a shortcut \((u,v)\) of conductance \(\eta>0\) to a vertex closer to \(q\). Since \(L'=L+\eta b_{uv}b_{uv}^\top\) and \((b_{uv}^\top x)^2\le R_L(u,v)x^\top Lx\),
\[
L\preceq L'\preceq(1+\eta R_L(u,v))L\quad\text{on }\mathbf1^\perp.
\]
The spectral error tends to zero with \(\eta\), yet an adjacency-based navigator treats every positive-conductance edge as present and may escape immediately. Chaining such gadgets makes the path/recall difference large. The test supplies a three-node trap. **Disproves:** arbitrarily accurate spectral approximation alone preserves greedy traces or recall.

## C4. Local overestimation

The local reference contains only unit edge \((u,v)\), giving \(R_{\rm local}=1\). The global graph adds two unit two-hop paths through vertices outside the local set, giving \(R_{\rm global}=1/(1+2/2)=1/2\). With \(m\) hidden paths the global value is \(1/(1+m/2)\), while the local value stays one. **Disproves:** a fixed local radius gives a uniform global score/rank approximation without further structure.

## C5. Direction diversity can displace accurate neighbors

At \(u=(0,0)\) with budget two, put near useful candidates \(a=(1,0)\), \(b=(1,\epsilon)\) and far candidates \(c=(0,R)\), \(d=(-R,0)\). For sufficiently large \(R\), locality satisfies \(\ell_a,\ell_b\gg\ell_c,\ell_d\), but the direction log-det marginal of \(b\) after \(a\) tends to its redundant-direction minimum, whereas an orthogonal far direction has a fixed positive advantage. Choosing \(\beta/\gamma\) large enough selects a far direction and displaces \(b\). A query distribution concentrated near the positive x-axis loses its useful local edge. **Disproves:** maximizing direction volume alone preserves local precision. This parametric example will receive a dedicated coordinate-grid enumerator in the next theory batch.

## C6. Dynamic leverage is not generally submodular

Define the otherwise ambiguous dynamic set function explicitly: \(F_{\rm dyn}(S)=\sum_{e\in S}\tau_e^{H_0+S}\). The smallest unweighted violation found by the current exhaustive search has five vertices, base tree \((0,1),(0,2),(0,3),(1,4)\), and candidates \(e_0=(0,4),e_1=(1,2),e_2=(3,4)\). For \(A=\{e_0\}\subset B=\{e_0,e_1\}\),
\[
\Delta(e_2\mid A)=11/24\approx0.45833<13/28\approx0.46429=\Delta(e_2\mid B).
\]
**Disproves:** this recomputed-leverage sum has diminishing returns. Other dynamic scoring procedures may not even integrate to a path-independent set function; each must be defined before a submodularity claim is meaningful.

## C7. A bridge can be irrelevant to the query support

Join two dense clusters by their unique edge (a-b), so \(\tau_{ab}=1\). Put all database queries and their true neighbors in the first cluster, and start every search there. The bridge is maximally nonredundant yet is never needed by this query distribution. **Disproves:** topological necessity alone implies positive expected ANN utility.

## C8. Two bridges need not help the same direction

Let a central component attach to two leaf components by bridges \(e_L,e_R\), hence both scores are one. Embed the leaves so that each helps only its own query region. **Disproves:** equal resistance makes edges interchangeable for query navigation.

## C9. A long bridge can displace a necessary local edge

At a vertex with budget one, let \(e_b\) be a long bridge into a query-irrelevant appendage and \(e_g\) the sole strict-improvement move toward the target. Parallel alternate paths can make \(\tau(e_g)<1\), so pure resistance selects \(e_b\). **Disproves:** leverage maximization under a degree budget preserves the best monotone move.

## C10. Symmetrization can invent a nonexistent directed escape

Take directed arc \(a\to u\) but no arc \(u\to a\). Union symmetrization inserts \(\{u,a\}\), whereas intersection symmetrization omits it. **Disproves:** a score on an unspecified symmetrization is automatically a valid directed HNSW edge-utility score.

## C11. Candidate coverage dominates any scoring theorem

Let \(u\to v\to t\) be the unique metric-decreasing route, but exclude \(v\) from \(C_u\). Every selector over \(C_u\) fails to add \(u\to v\). **Disproves:** an approximation guarantee over the available ground set implies navigation.

## C12. Pure resistance is uninformative on a tree candidate star

Under scheme A, join center \(u\) to candidate leaves \(v_i\), with no alternate routes. Every candidate has \(\tau_i=1\), regardless of direction or distance. **Disproves:** candidate leverage necessarily discriminates candidates under the project's own augmented-star construction.

## C13. High-dimensional direction gains concentrate

Draw normalized candidate directions independently and uniformly from a high-dimensional sphere. Pairwise inner products concentrate near zero, so at early prefixes most candidates have nearly the same log-det marginal. In a deterministic (d=512,c=64) seeded sample, the coefficient of variation of first-step marginals is exactly zero (all unit directions give \(\log(1+\sigma^{-2})\)); at a small random prefix it becomes small rather than encoding query relevance. **Disproves:** the direction term necessarily offers strong candidate discrimination in high dimension. An anisotropic/query-aligned distribution or learned projection is an additional premise, not a consequence of dimension.

## Requested failure-mode coverage

| Failure mode | Witness |
|---|---|
| high resistance but wrong query direction | C1 |
| low resistance but only useful shortcut | C2 |
| spectral closeness but different navigation | C3 |
| local/global rank distortion | C4 |
| diversity displaces local accuracy | C5 |
| dynamic score lacks submodularity | C6 |
| query-irrelevant bridge | C7 |
| equal bridges help incompatible regions | C8 |
| degree-budget displacement | C9 |
| directed/symmetrized mismatch | C10 |
| missing useful candidate | C11 |
| constant scores on augmented tree/star | C12 |
| high-dimensional direction concentration | C13 |
