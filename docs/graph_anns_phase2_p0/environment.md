# P0 environment record

- Worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw`
- Branch: `exp/graph_anns_phase2_constructive_closure` (from `ffe5798738cb1bf505e724c3b91982420065d280`,
  tip of `exp/graph_anns_iclr_phase1_1_final_evidence_hotfix`, verified equal to `github` remote)
- Interpreter: repo `.venv` Python 3.11.16 (numpy/pandas/scipy/matplotlib import OK)
- Required prefix for every run:
  `LD_LIBRARY_PATH=/home/wlk/miniconda3/lib` — system `/lib/x86_64-linux-gnu/libstdc++.so.6`
  lacks `GLIBCXX_3.4.29` required by the venv pandas binary; miniconda's libstdc++ provides it.
- System python3 is 3.14.6 and must NOT be used for analysis (dependency set differs).
- Frozen trees are strictly read-only for P0–P5; new outputs only under
  `results/graph_anns_phase2_*`, `docs/graph_anns_phase2_*`, `scripts/graph_anns_phase2/`,
  `tests/graph_anns_phase2_*`.
- No ANN search, no index build, no query/truth role access in P0.
