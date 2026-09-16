#!/usr/bin/env bash
set -euo pipefail

repo="${ICBA_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
data500="${ICBA_DATA500_ROOT:-/home/wlk/data500}"
score8="${ICBA_SCORE8_ROOT:-$data500/graph_anns_score8}"
root="${ICBA_EA85_ROOT:-$data500/graph_anns_phase3_ea85}"
binary="${ICBA_DARTH_BINARY:-$score8/build/darth/hnsw-test/hnsw_test}"
inputs="$root/refresh95_inputs"
outputs="$root/refresh95_replay"
seeds=(1103 1229 1361 1499 1621 1747 1877 1999 2131 2267)
grid=(10 20 40 80 120 160 200)

[[ -x "$binary" ]]
mkdir -p "$outputs"

index_path() {
  local dataset=$1 snapshot=$2 seed=$3
  if [[ "$dataset" == sift100k && "$snapshot" == old ]]; then
    printf '%s/darth_comparison/multibuild/indexes/sift100k_seed_%s.faiss' "$score8" "$seed"
  elif [[ "$dataset" == sift100k ]]; then
    printf '%s/darth_comparison/refresh/indexes/refresh_05/sift100k_refresh05_seed_%s.faiss' "$score8" "$seed"
  elif [[ "$snapshot" == old ]]; then
    printf '%s/darth_comparison/arxiv/indexes/multibuild/arxiv100k_seed_%s.faiss' "$score8" "$seed"
  else
    printf '%s/darth_comparison/arxiv/refresh/indexes/refresh_05/arxiv100k_refresh05_seed_%s.faiss' "$score8" "$seed"
  fi
}

role_type() {
  case "$1" in
    selection) printf training ;;
    certification) printf validation ;;
    cold_evaluation) printf testing ;;
  esac
}

role_count() {
  case "$1" in
    selection|certification) printf 500 ;;
    cold_evaluation) printf 1000 ;;
  esac
}

validate_rows() {
  local path=$1 expected=$2
  [[ -s "$path" ]] || return 1
  local lines
  lines=$(wc -l < "$path")
  [[ "$lines" -eq $((expected + 1)) ]]
}

for dataset in sift100k arxiv_nomic_100k; do
  [[ -s "$inputs/$dataset/input_manifest.json" ]]
  for snapshot in old target_refresh05; do
    for seed in "${seeds[@]}"; do
      index=$(index_path "$dataset" "$snapshot" "$seed")
      [[ -s "$index" ]]
      prefix="$inputs/$dataset/$snapshot/seed_${seed}/"
      [[ -s "${prefix}SIFT100M/base.100M.fvecs" ]]
      for role in selection certification cold_evaluation; do
        qtype=$(role_type "$role")
        count=$(role_count "$role")
        outdir="$outputs/$dataset/$snapshot/seed_${seed}/$role"
        mkdir -p "$outdir"
        for ef in "${grid[@]}"; do
          output="$outdir/ef_${ef}.csv"
          if validate_rows "$output" "$count"; then
            continue
          fi
          rm -f "$output"
          "$binary" \
            --dataset SIFT100M \
            --query-num "$count" \
            --k 10 \
            --output "$output" \
            --M 16 \
            --efConstruction 100 \
            --efSearch "$ef" \
            --index-filepath "$index" \
            --mode no-early-stop \
            --query-type "$qtype" \
            --dataset-dir-prefix "$prefix" \
            >"$outdir/ef_${ef}.stdout.log" 2>"$outdir/ef_${ef}.stderr.log"
          validate_rows "$output" "$count"
        done
      done
      printf '%s,%s,%s,complete\n' "$dataset" "$snapshot" "$seed" >>"$outputs/progress.csv"
    done
  done
done

find "$outputs" -type f -name 'ef_*.csv' -print0 | sort -z | xargs -0 sha256sum >"$outputs/output_sha256.txt"
printf 'COMPLETE\n' >"$outputs/STATUS"
