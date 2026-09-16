#!/usr/bin/env bash
set -euo pipefail

repo="${ICBA_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
data500="${ICBA_DATA500_ROOT:-/home/wlk/data500}"
score8="${ICBA_SCORE8_ROOT:-$data500/graph_anns_score8}"
external="${ICBA_DARTH_ROOT:-$score8/external/DARTH}"
binary="${ICBA_DARTH_BINARY:-$score8/build/darth/hnsw-test/hnsw_test}"
output_root="${ICBA_EA85_ROOT:-$data500/graph_anns_phase3_ea85}/darth95_bridge"
expected_darth=0d9bafcf31d1d79668bc71139fe93fa5e70b5185
seeds=(1103 1229 1361 1499 1621 1747 1877 1999 2131 2267)

[[ "$(git -C "$external" rev-parse HEAD)" == "$expected_darth" ]]
[[ -x "$binary" ]]
mkdir -p "$output_root"

run_one() {
  local dataset=$1
  local seed=$2
  local dataset_dir index model out
  if [[ "$dataset" == sift_100k ]]; then
    dataset_dir="$score8/darth_comparison/multibuild/datasets/seed_${seed}"
    index="$score8/darth_comparison/multibuild/indexes/sift100k_seed_${seed}.faiss"
    model="$score8/darth_comparison/multibuild/m1/seed_${seed}/model_11feat.txt"
  else
    dataset_dir="$score8/darth_comparison/arxiv/builds/seed_${seed}"
    index="$score8/darth_comparison/arxiv/indexes/multibuild/arxiv100k_seed_${seed}.faiss"
    model="$score8/darth_comparison/arxiv/runs/m1/seed_${seed}/model_11feat.txt"
  fi
  out=$output_root/$dataset/seed_${seed}
  [[ -d "$dataset_dir" ]]
  [[ -s "$index" ]]
  [[ -s "$model" ]]
  mkdir -p "$out"
  local common=(
    --dataset SIFT100M
    --M 16
    --efConstruction 100
    --efSearch 200
    --k 10
    --index-filepath "$index"
    --dataset-dir-prefix "$dataset_dir/"
    --mode early-stop-testing
    --target-recall .95
    --initial-prediction-interval 20
    --min-prediction-interval 5
    --logging-interval 5
    --predictor-model-path "$model"
  )
  if [[ ! -s "$out/cert_500.csv" ]]; then
    "$binary" "${common[@]}" --query-num 500 --query-type validation \
      --output "$out/cert_500.csv" >"$out/cert.stdout.log" 2>"$out/cert.stderr.log"
  fi
  if [[ ! -s "$out/eval_1000.csv" ]]; then
    "$binary" "${common[@]}" --query-num 1000 --query-type testing \
      --output "$out/eval_1000.csv" >"$out/eval.stdout.log" 2>"$out/eval.stderr.log"
  fi
  printf '%s,%s,complete\n' "$dataset" "$seed" >>"$output_root/progress.csv"
}

if [[ ! -s "$output_root/input_sha256.txt" ]]; then
  {
    sha256sum "$repo/manifests/graph_anns_phase3_ea85/unified_protocol.yaml"
    sha256sum "$repo/manifests/graph_anns_phase3_ea85/p1_darth95_amendment.yaml"
    sha256sum "$binary"
    git -C "$external" rev-parse HEAD
  } >"$output_root/input_sha256.txt"
fi

printf 'dataset,seed,status\n' >"$output_root/progress.csv"
for dataset in sift_100k arxiv_nomic_100k; do
  for seed in "${seeds[@]}"; do
    run_one "$dataset" "$seed"
  done
done

find "$output_root" -type f \( -name '*.csv' -o -name '*.log' -o -name '*.txt' \) -print0 \
  | sort -z | xargs -0 sha256sum >"$output_root/output_sha256.txt"
printf 'COMPLETE\n' >"$output_root/STATUS"
