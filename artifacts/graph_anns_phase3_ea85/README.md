# ICBA/TCP SIGMOD E&A artifact

This directory is the reviewer-facing entry point for the Phase 1--5 evidence
seal. It reproduces committed tables without downloading datasets and documents
the separate full replay path for raw experiments.

## Lightweight smoke (about one minute, under 100 MiB)

From a clean repository checkout:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[test]'
bash artifacts/graph_anns_phase3_ea85/reproduce_smoke.sh
```

The smoke verifies the sealed input checksums, parses every Phase decision,
checks query-role firewall evidence, reruns the Phase 5 integration, and runs
the focused test suite. It does not access raw queries or truth.

## Regenerate paper-facing tables

```bash
bash artifacts/graph_anns_phase3_ea85/reproduce_tables.sh
```

Tables are written under `results/graph_anns_phase3_ea85/phase5_seal/`; figures
are written under `figures/graph_anns_phase3_ea85/`. Inputs are checked against
the committed evidence before regeneration.

## Full replay

Run `bash artifacts/graph_anns_phase3_ea85/run_artifact.sh full-check` after
setting the roots listed by its help. The expensive `full` mode additionally
requires `ICBA_FULL_REPLAY_ACK=YES`. See `full_replay.md`; raw datasets and
indexes are not committed. The path requires the checksummed external inputs
and approximately 5 GiB for Deep1M, plus the earlier SIFT/Arxiv stores. No GPU
is required.

## Claim boundary

The artifact supports a stratified rebuild-portability phenomenon, the utility
of ICBA as a safety/value audit, and conditional search-distance value for
target-selection TCP recalibration. It does not claim universal failure,
absolute SOTA, or full-lifecycle TCP economic superiority.
