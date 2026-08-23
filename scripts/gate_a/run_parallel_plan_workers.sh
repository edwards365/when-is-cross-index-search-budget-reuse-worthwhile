#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 DATASET BUILD_SEED OUTPUT WORKER_COUNT" >&2
  exit 2
fi

dataset=$1
build_seed=$2
output=$3
worker_count=$4
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
python="$repo/.venv/bin/python"
config="$repo/configs/gate_a/gate_a_100k.yaml"
log_root="$repo/logs/gate_a/$(basename "$output")-workers"
minimum_disk_bytes=$((10 * 1024 * 1024 * 1024))

if [[ ! "$worker_count" =~ ^[1-9][0-9]*$ ]]; then
  echo "worker count must be a positive integer" >&2
  exit 2
fi

mkdir -p "$log_root"
cd "$repo"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

pids=()
cleanup() {
  for pid in "${pids[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup INT TERM

for ((worker = 0; worker < worker_count; worker++)); do
  "$python" -u scripts/gate_a/generate_plans.py \
    --config "$config" \
    --dataset "$dataset" \
    --build-seed "$build_seed" \
    --output "$output" \
    --selection-worker-index "$worker" \
    --selection-worker-count "$worker_count" \
    >"$log_root/worker-$worker.log" 2>&1 &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    failed=1
  fi
done
trap - INT TERM
if ((failed)); then
  echo "at least one selection worker failed; finalization withheld" >&2
  exit 10
fi

available_disk_bytes=$(df --output=avail -B1 "$repo" | tail -1 | tr -d ' ')
if ((available_disk_bytes < minimum_disk_bytes)); then
  echo "available disk is below the 10 GiB finalization gate" >&2
  exit 11
fi

"$python" -u scripts/gate_a/generate_plans.py \
  --config "$config" \
  --dataset "$dataset" \
  --build-seed "$build_seed" \
  --output "$output" \
  >"$log_root/finalize.log" 2>&1

echo "parallel plan generation and finalization completed"
