#!/usr/bin/env bash
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${ICBA_PYTHON:-${PYTHON:-python}}"
mode="${1:-help}"

usage() {
  cat <<'EOF'
Usage: run_artifact.sh {smoke|tables|full-check|full}

smoke       Verify committed evidence and run focused tests.
tables      Regenerate Phase 5 tables and Phase 6 figures.
full-check  Validate external roots and binaries without running experiments.
full        Replay expensive registered cells from existing datasets/indexes.

full/full-check require ICBA_DATA500_ROOT, ICBA_EA85_ROOT, ICBA_SCORE8_ROOT,
ICBA_DARTH_ROOT, ICBA_DARTH_BINARY, and ICBA_PYTHON. full additionally requires
ICBA_FULL_REPLAY_ACK=YES. It never downloads data or deletes prior outputs.
EOF
}

check_full() {
  : "${ICBA_DATA500_ROOT:?set ICBA_DATA500_ROOT}"
  : "${ICBA_EA85_ROOT:?set ICBA_EA85_ROOT}"
  : "${ICBA_SCORE8_ROOT:?set ICBA_SCORE8_ROOT}"
  : "${ICBA_DARTH_ROOT:?set ICBA_DARTH_ROOT}"
  : "${ICBA_DARTH_BINARY:?set ICBA_DARTH_BINARY}"
  : "${ICBA_PYTHON:?set ICBA_PYTHON}"
  [[ -d "$ICBA_DATA500_ROOT" ]]
  [[ -d "$ICBA_SCORE8_ROOT" ]]
  [[ -d "$ICBA_DARTH_ROOT/.git" ]]
  [[ -x "$ICBA_DARTH_BINARY" ]]
  [[ -x "$ICBA_PYTHON" ]]
  "$ICBA_PYTHON" --version
  printf 'FULL_REPLAY_INPUT_CHECK_PASS\n'
}

case "$mode" in
  smoke)
    PYTHON="$python_bin" bash "$repo/artifacts/graph_anns_phase3_ea85/reproduce_smoke.sh"
    ;;
  tables)
    PYTHON="$python_bin" bash "$repo/artifacts/graph_anns_phase3_ea85/reproduce_tables.sh"
    ;;
  full-check)
    check_full
    ;;
  full)
    check_full
    [[ "${ICBA_FULL_REPLAY_ACK:-}" == "YES" ]] || {
      echo "Refusing expensive replay: set ICBA_FULL_REPLAY_ACK=YES" >&2
      exit 2
    }
    export ICBA_REPO_ROOT="$repo"
    bash "$repo/scripts/graph_anns_phase3_ea85/run_darth95_bridge.sh"
    "$python_bin" "$repo/scripts/graph_anns_phase3_ea85/analyze_darth95_bridge.py" \
      --repo-root "$repo" --data-root "$ICBA_EA85_ROOT" \
      --darth-comparison-root "$ICBA_SCORE8_ROOT/darth_comparison"
    bash "$repo/scripts/graph_anns_phase3_ea85/adaef_bridge/run_adaef_extension.sh"
    bash "$repo/scripts/graph_anns_phase3_ea85/run_phase2_refresh95_replay.sh"
    "$python_bin" "$repo/scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py" \
      --replay-root "$ICBA_EA85_ROOT/refresh95_replay" --repo-root "$repo"
    "$python_bin" "$repo/scripts/graph_anns_phase3_ea85/analyze_phase3_vamana_unified.py" \
      --repo-root "$repo" --data500-root "$ICBA_DATA500_ROOT"
    "$python_bin" "$repo/scripts/graph_anns_phase3_ea85/run_phase4_deep1m.py" \
      --repo-root "$repo" --data-root "$ICBA_EA85_ROOT"
    "$python_bin" "$repo/scripts/graph_anns_phase3_ea85/analyze_phase4_deep1m.py" \
      --repo-root "$repo" --data-root "$ICBA_EA85_ROOT"
    PYTHON="$python_bin" bash "$repo/artifacts/graph_anns_phase3_ea85/reproduce_tables.sh"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
