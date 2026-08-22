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

Validation currently completed: targeted GGR/repair tests 16/16, full project Python
57/57, scoped Ruff clean, and CTest 2/2. Public-data development results and the main
epsilon are pending; no performance conclusion is available.
