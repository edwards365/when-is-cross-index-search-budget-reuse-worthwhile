#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${PYTHON:-python}"
cd "$repo"
"$python_bin" scripts/graph_anns_phase3_ea85/seal_phase5_statistical_economic.py --repo-root "$repo"
"$python_bin" scripts/graph_anns_phase3_ea85/regenerate_phase6_figures.py --repo-root "$repo"
"$python_bin" scripts/graph_anns_phase3_ea85/artifact_smoke.py --repo-root "$repo"
