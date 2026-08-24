# SGDR three-day environment and evidence audit

- Repository: `/home/wlk/projects/navigation-aware-resistance-hnsw`
- Parent branch/commit: `research/post-e0-diagnostics` at `476eea8da83e9a34651acd739cbaabc5ed7454b2`
- SGDR branch: `exp/sgdr_3day_feasibility`
- Remote: local immutable bundle at `/home/wlk/projects/navigation-aware-resistance-hnsw.bundle`
- Existing untracked build, log, and result directories were preserved.
- CPU: AMD EPYC 7542, 128 logical CPUs.
- Memory: 251 GiB total, 239 GiB available at audit.
- GPU: four RTX 3090 cards, 24 GiB each; Gate O does not require them.
- Free disk: 12,031,283,200 bytes (11.20 GiB), above but close to the frozen 10 GiB stop threshold.
- No SGDR or HNSW experimental process was active at audit.

Frozen decision hashes checked before starting:

- `manifests/post_e0_total_d0_decision.json`: `9a649fbbe618f75f2c39eba728d4593e255a68943e4e274b8955d35812599bb8`
- `manifests/post_e0_d0f_decision.json`: `ff77b408de8dbbddb5188009c5d0b4ec35213ea4f42b8c46aee70bd0113da5a8`

The E0/D0 result directories remain untracked frozen evidence and will be read only. The SGDR study uses a new namespace and must stop before creating large transient artifacts if free disk drops below 10 GiB.
