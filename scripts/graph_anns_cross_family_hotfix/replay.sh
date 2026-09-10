#!/usr/bin/env bash
set -euo pipefail
repo="${1:-/home/wlk/projects/navigation-aware-resistance-hnsw}"
cd "$repo"
python3 scripts/graph_anns_cross_family_hotfix/run.py
python3 tests/graph_anns_cross_family_hotfix/test_hotfix.py
sha256sum -c results/graph_anns_cross_family_hotfix/checksums.sha256
