# Auditable counterexamples

`python -m theory.search_counterexamples` emits the exact numerical examples C1, C2, and C6. Tests verify C1--C4. Conductances are positive and graphs are undirected for resistance; navigation uses the stated unweighted adjacency.

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
