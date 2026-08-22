# Phase II status

Phase II branch: `exp/geometry-first-resistance-second`.

The design preregistration and test firewall were SHA-256 hashed and frozen at commit
`73934e5`. The formal test firewall remains **SEALED**. No Phase II public test vector,
ground-truth neighbor, query trace, or formal outcome has been read.

Implemented locally after the preregistration commit:

- exact reuse of the existing Geometry objective;
- deterministic query-free GGR one-for-one selection;
- frozen Scheme-A leverage integration in exported graph repair;
- per-node degree and total directed-edge preservation;
- swap, geometry-loss, leverage-gain, tolerance, and termination metadata;
- first theory files and proof-status registry;
- public dataset manifests for SIFT1M, GloVe-100, and VIBE Arxiv-Nomic.

Validation currently completed: full project Python 60/60, scoped Ruff clean, CTest
3/3, and all frozen Phase I artifact hashes still valid.

The first construction-only public-data audit is complete on the first 10,000 SIFT1M
training vectors at code commit `83c4cfd` (128 fixed centers, 32 candidates, `M=16`,
seed 7). At epsilon 0, 73/128 centers admitted 163 leverage-improving swaps with no
positive Geometry loss; mean frozen-leverage gain was 0.047327. At epsilon 0.005 and
0.01, all centers swapped, while mean Geometry loss was 0.003802 and 0.008642 and mean
leverage gain was 0.125747 and 0.161331, respectively. A negative mean "loss" at
epsilon 0 means the one-swap search sometimes improved the greedy Geometry set itself.

This is a selector-mechanics result, not an ANNS performance or stability result: it
used no development query and cannot select the main epsilon. The formal test remains
sealed. The next required experiment is development-query search on independently
derived queries, followed by the hashed epsilon amendment; no performance conclusion
is currently available.

The same sealed audit was repeated on 10,000 L2-normalized GloVe-100 training vectors.
At epsilon 0, 57/128 centers admitted 106 swaps with max Geometry loss 0 and mean
frozen-leverage gain 0.151332. At epsilon 0.005 and 0.01, mean Geometry loss was
0.004250 and 0.008712 and mean leverage gain was 0.657232 and 0.836533. The two public
datasets therefore agree that strict secondary optimization is mechanically nonempty;
they still provide no query-performance or stability evidence.

Arxiv-Nomic completes the three-dataset construction audit. At epsilon 0, 50/128
centers admitted 110 swaps with max Geometry loss 0 and mean frozen-leverage gain
0.073967. Epsilon 0.005 and 0.01 yielded mean Geometry loss 0.004403 and 0.009100 and
mean leverage gain 0.290561 and 0.364347. Thus all three preregistered public data
families show a nonempty lexicographic (`epsilon=0`) resistance action space. This is
the strongest conclusion permitted by these construction-only audits.

Gate 0 is complete. Its numerical audit found identical selections from zero through
`1e-9` mixed tolerance, deterministic repeats, and strictly positive Decimal-60
final-minus-Geometry deltas for every sampled changed center. The paired independent
final-graph audit at commit `150a0fe` then applied Geometry and GGR selections through
hnswlib reciprocal insertion and reverse pruning. Across SIFT/GloVe/Arxiv, 73/57/50
of 128 centers changed; 158/105/108 terminal GGR edges were proposed, every source
edge survived, and 157/99/106 reciprocal edges survived (99.37%/94.29%/98.15%). Gate
0 therefore passes and epsilon zero is frozen as the main Phase-II setting. Gate A is
not yet running: Geometry-safe Random and Shuffled-Resistance must first be implemented
on the identical feasible-swap path. All formal test access remains unauthorized.
