#!/usr/bin/env bash
set -euo pipefail

REPO="${ICBA_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
ROOT="${ICBA_EA85_ROOT:-/home/wlk/data500/graph_anns_phase3_ea85}"
BUNDLE="$ROOT/adaef_arxiv100k_frozen/arxiv_nomic_100k__adaef_input_bundle_v2.hdf5"
BRIDGE="$ROOT/build/adaef/adaef_arxiv_bridge"
PYTHON="${ICBA_PYTHON:-python}"
ANALYZE="$REPO/scripts/graph_anns_phase3_ea85/adaef_bridge/analyze_adaef_smoke.py"

for seed in 1031 1049 1061 1069 1087 1097 1103; do
  run_dir="$ROOT/adaef_arxiv_extension/seed${seed}"
  mkdir -p "$run_dir"
  "$BRIDGE" design "$BUNDLE" "$run_dir/index.hnsw" "$run_dir/adapter.bin" \
    "$run_dir/design_summary.json" "$seed" >"$run_dir/design.log" 2>&1
  "$BRIDGE" run-role "$BUNDLE" certification "$run_dir/index.hnsw" \
    "$run_dir/adapter.bin" "$run_dir/certification.csv" >"$run_dir/certification.log" 2>&1

  "$PYTHON" - "$run_dir/certification.csv" "$run_dir/certification_decision.json" <<'PY'
import csv, json, sys
from scipy.stats import beta
source, output = sys.argv[1:]
rows = list(csv.DictReader(open(source)))
result = {}
for lane in ("raw", "fixed_safe"):
    failures = sum(float(row[f"{lane}_recall"]) < .95 for row in rows)
    n = len(rows)
    upper = 1.0 if failures == n else float(beta.ppf(.95, failures + 1, n - failures))
    result[lane] = {"failures": failures, "n": n, "risk": failures/n, "cp95_upper": upper}
result["deployment"] = "RAW_ADA_EF" if result["raw"]["cp95_upper"] <= .05 else (
    "FIXED_SAFE_EF200" if result["fixed_safe"]["cp95_upper"] <= .05 else "NO_CERTIFIED_ACTION")
open(output, "w").write(json.dumps(result, indent=2, sort_keys=True) + "\n")
if result["deployment"] == "NO_CERTIFIED_ACTION":
    raise SystemExit(3)
PY

  "$BRIDGE" run-role "$BUNDLE" evaluation "$run_dir/index.hnsw" \
    "$run_dir/adapter.bin" "$run_dir/evaluation.csv" >"$run_dir/evaluation.log" 2>&1
  (cd "$REPO" && "$PYTHON" "$ANALYZE" --run-dir "$run_dir" \
    --output "$run_dir/summary.json" >"$run_dir/analysis.log")
  sha256sum "$run_dir/index.hnsw" "$run_dir/adapter.bin" "$run_dir/certification.csv" \
    "$run_dir/evaluation.csv" "$run_dir/summary.json" >"$run_dir/SHA256SUMS"
done
