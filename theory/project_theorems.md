# Project theorem candidates: audited versions

## Theorem A: score-gap bridge retention

At greedy prefix \(S\), candidate \(e\) is selected next if for every \(f\ne e\),
\[
\alpha(r_e-r_f)+\beta[\Delta_{\rm dir}(e\mid S)-\Delta_{\rm dir}(f\mid S)]
+\gamma(\ell_e-\ell_f)>0.
\]
This follows directly from exact greedy maximization. A conservative sufficient condition is
\[
\alpha(r_e-\max_{f\ne e}r_f)>
\beta\max_{f\ne e}|\Delta_{\rm dir}(f\mid S)-\Delta_{\rm dir}(e\mid S)|+
\gamma\max_{f\ne e}|\ell_f-\ell_e|.
\]
If \(e\) is a bridge of \(H_u\), then \(r_e=1\), but bridge status alone does not make either inequality true. To guarantee selection sometime within budget \(M\), the dominance condition must hold at a step before the budget is exhausted (or uniformly at all prefixes not containing \(e\)). **Status:** `project_proved`, deliberately weak.

## Theorem B: monotone cross-cut concatenation

Let \(A,B\) partition the graph. If a \(\delta\)-monotone path joins the entry to \(a\in A\), edge \((a,b)\) is retained with \(b\in B\) and \(d_X(b,q)\le d_X(a,q)-\delta\), and a \(\delta\)-monotone path joins \(b\) to the target region, concatenation is a \(\delta\)-monotone path of length at most \(L_A+1+L_B\). If \((a,b)\) is the unique graph edge crossing \((A,B)\), deleting it removes every graph path across the cut. **Status:** `project_proved`.

This is an existence theorem. Pure greedy follows the path only under a policy-compatible condition, such as every greedy choice at each path vertex staying in a basin with the same progress property.

## Theorem C: greedy selection stability

Let \(F,\widetilde F\) share a finite ground set, budget, deterministic tie rule, and initial empty set. Assume for every candidate \(v\) and every prefix that can occur in the common induction,
\(|\Delta_F(v\mid S)-\Delta_{\widetilde F}(v\mid S)|\le\varepsilon\). If the winner-to-runner-up gap under \(F\) is strictly greater than \(2\varepsilon\) at each of its first \(M\) steps, both greedy sequences are identical.

**Proof.** At a common prefix, perturbing the winner down and any competitor up changes their difference by at most \(2\varepsilon\), so the winner is unchanged. Induction preserves the common prefix. **Status:** `project_proved`.

The statement fails to compare different candidate ground sets without a matching rule, and says nothing about later reciprocal pruning.

## Theorem D: spectral perturbation

The common-kernel resistance bound and leverage-ranking margin are proved in K5. **Status:** `project_proved`. A local reference graph must approximate the relevant global terminal Schur complement spectrally for this result to control local scores; mere radius or hop count is insufficient.

## Theorem E: pure-greedy query bound

Fix target region \(\mathcal T(q)=\{x:d_X(x,q)\le r_q\}\). If every non-target vertex reachable by pure greedy has a neighbor with distance at most \(d_X(x,q)-\delta\), then pure greedy, which chooses the closest neighbor, enters \(\mathcal T(q)\) within
\(\lceil(d_X(x_0,q)-r_q)/\delta\rceil\) steps.

**Proof.** The chosen neighbor is at least as good as the assumed one. Sum the decrease until the nonnegative threshold gap is exhausted. **Status:** `project_proved` for pure greedy and `partial` for HNSW beam search. `efSearch` cannot be inferred without explicit queue-retention and termination assumptions.
