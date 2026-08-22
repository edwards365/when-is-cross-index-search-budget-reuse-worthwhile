# Mechanism report

Status: numerical smoke check completed. No H1 conclusion is currently supported.

On the first 256 base nodes of the deterministic narrow-bridge dataset, an 8-NN graph was union-symmetrized and weighted with `exp(-d²/rho²)`, where `rho=1.773496389389038` was the median observed k-NN distance. Exact component-wise Moore--Penrose calculations scored 1,532 present undirected edges. Leverage ranged from 0.072678587495142 to 1.0000000000000133; there were no values above `1+1e-8`.

This validates the numerical bound on this sample only. It does not test missing insertion candidates, query bottlenecks, controls, or intervention outcomes.
