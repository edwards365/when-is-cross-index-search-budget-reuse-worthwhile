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

Validation currently completed: targeted GGR/repair tests 17/17, full project Python
58/58, scoped Ruff clean, CTest 2/2, and all 16 frozen Phase I artifact hashes still
valid.

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
