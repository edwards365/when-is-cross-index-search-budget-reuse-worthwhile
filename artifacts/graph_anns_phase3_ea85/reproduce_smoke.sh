#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${PYTHON:-python}"
cd "$repo"
"$python_bin" scripts/graph_anns_phase3_ea85/artifact_smoke.py --repo-root "$repo"
"$python_bin" -m pytest -q tests/graph_anns_phase3_ea85
