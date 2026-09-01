# CIBS joint-closure artifact and site audit

- Audit UTC: `2026-09-01T06:43:52.023143+00:00`
- Branch: `exp/icba_cibs_joint_feasibility_closure`
- Frozen HEAD: `10363a3a8a9abe0170af02b0b7ba29ffbf8f4621`
- Stage-I decision manifest SHA256 before correction: `29c8803980eabc59a62e9b97595169e72981d672a1744509cce560d71157c505`
- Persistent free bytes: `9506189312`
- Inventoried files: `20`; total bytes: `1527225528`
- Reliable independent copy of large untracked artifacts: `NOT_VERIFIED`.
- Deletion performed: `NO`.
- Git ignore added: `NO`; no broad pattern may hide unknown evidence.

## Classification

- `PERSISTENT_REPLAY_ARTIFACT`: 6 files
- `REGENERABLE_COMPILED_TOOL`: 3 files
- `REGENERABLE_DATA_CONVERSION_CACHE`: 2 files
- `REGENERABLE_PREREGISTERED_ORDER_CACHE`: 3 files
- `REGENERABLE_ROLE_MATERIALIZATION_CACHE`: 6 files

The six serialized index files are replay artifacts and remain preserved outside Git. Runtime base conversions, role materializations, insertion orders, and compiled runners are reproducible caches, but they also remain preserved because this closure has no deletion authorization. Their exact paths, sizes, mtimes, and SHA256 values are in `results/icba_cibs_joint_closure/artifact_inventory.csv`.

## Worktree status at audit

```text
## exp/icba_cibs_joint_feasibility_closure
?? artifacts/icba_cibs_stage1/
?? manifests/icba_cibs_stage1_corrected_decision.json
?? results/icba_cibs_joint_closure/
?? results/icba_cibs_stage1/runtime/base/
?? results/icba_cibs_stage1/runtime/orders/
?? results/icba_cibs_stage1/runtime/queries/
?? results/icba_cibs_stage1/runtime/tools/
?? scripts/icba_cibs_joint_closure/
```

## Relevant process snapshot

```text
1425872       00:02 62.5  0.0 S    python3 scripts/icba_cibs_joint_closure/phase0_joint_closure.py
1027643 16-04:37:42  0.0  0.0 Ssl  /home/wlk/.vscode-server/code-a5b500951314efd502d07465bd138dfbd714a960 --cli-data-dir /home/wlk/.vscode-server/cli agent host
1425870       00:02  0.0  0.0 S    sshd: wlk@notty
1425871       00:02  0.0  0.0 Ss   bash -c cd /home/wlk/projects/navigation-aware-resistance-hnsw-cibs-stage1 && python3 scripts/icba_cibs_joint_closure/phase0_joint_closure.py && git status --short --branch && wc -l results/icba_cibs_joint_closure/artifact_inventory.csv && sed -n '1,80p' docs/icba_cibs_joint_closure/artifact_audit.md
1425882       00:00  0.0  0.0 S    bash -lc ps -u "$USER" -o pid=,etime=,%cpu=,%mem=,stat=,cmd= --sort=-%cpu | head -20
1425884       00:00  0.0  0.0 R    ps -u wlk -o pid=,etime=,%cpu=,%mem=,stat=,cmd= --sort=-%cpu
1425885       00:00  0.0  0.0 S    head -20
2525603 50-04:42:51  0.0  0.0 Ssl  /home/wlk/.vscode-server/code-fc3def6774c76082adf699d366f31a557ce5573f --cli-data-dir /home/wlk/.vscode-server/cli agent host
2527377 50-04:30:49  0.0  0.0 Ssl  /home/wlk/.vscode-server/code-fc3def6774c76082adf699d366f31a557ce5573f --cli-data-dir /home/wlk/.vscode-server/cli agent host
```

## Label-only correction

The frozen Stage-I manifest is unchanged. Its out-of-dictionary label is mapped in a new manifest to `CIBS_RECALL_OR_TAIL_GATE_FAILED`. The correction changes no metrics, action selection, bootstrap sample, gate threshold, or scientific conclusion.
