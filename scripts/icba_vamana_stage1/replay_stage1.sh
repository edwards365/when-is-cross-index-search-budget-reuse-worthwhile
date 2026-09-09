#!/usr/bin/env bash
set -euo pipefail
PY=/home/wlk/projects/navigation-aware-resistance-hnsw/.venv/bin/python
$PY scripts/icba_vamana_stage1/run_vamana_stage1.py
$PY scripts/icba_vamana_stage1/analyze_vamana_stage1.py /home/wlk/data500/icba_vamana_stage1 SIFT-100K
$PY scripts/icba_vamana_stage1/run_vamana_arxiv.py
$PY scripts/icba_vamana_stage1/analyze_vamana_stage1.py /home/wlk/data500/icba_vamana_stage1_arxiv Arxiv-Nomic-100K
$PY scripts/icba_vamana_stage1/seal_vamana_stage1.py
