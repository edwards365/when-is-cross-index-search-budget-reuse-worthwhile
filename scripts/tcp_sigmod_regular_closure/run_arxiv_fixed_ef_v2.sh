#!/usr/bin/env bash
set -euo pipefail

repo=${TCP_REPO:-/home/wlk/projects/navigation-aware-resistance-hnsw}
input_root=${TCP_ARXIV_INPUT_ROOT:-/home/wlk/data500/graph_anns_score8/darth_comparison/arxiv}
output_root=${TCP_ARXIV_OUTPUT_ROOT:-/home/wlk/data500/tcp_sigmod_regular_closure/arxiv_fixed_ef_v2}
bin=${TCP_DARTH_BIN:-/home/wlk/data500/graph_anns_score8/build/darth/hnsw-test/hnsw_test}
dry_run=${TCP_DRY_RUN:-0}
seeds=(1103 1229 1361 1499 1621 1747 1877 1999 2131 2267)
grid=(10 20 40 80 120 160 200)

run_one() {
  local log=$1
  shift
  printf '%q ' "$@" >"${log}.command"
  printf '\n' >>"${log}.command"
  if [[ "$dry_run" == 1 ]]; then cat "${log}.command"; return 0; fi
  "$@" >"${log}.stdout" 2>"${log}.stderr"
}

mkdir -p "$output_root"
if [[ "$dry_run" != 1 ]]; then
  sha256sum "$bin" >"$output_root/executable.sha256"
  git -C "$repo" rev-parse HEAD >"$output_root/repo_head.txt"
fi
for seed in "${seeds[@]}"; do
  dataset_dir="$input_root/builds/seed_${seed}/"
  index="$input_root/indexes/multibuild/arxiv100k_seed_${seed}.faiss"
  out="$output_root/seed_${seed}"
  mkdir -p "$out"
  if [[ "$dry_run" != 1 ]]; then sha256sum "$index" >"$out/index.sha256"; fi
  for split in cert eval; do
    n=500; query_type=validation
    if [[ "$split" == eval ]]; then n=1000; query_type=testing; fi
    for ef in "${grid[@]}"; do
      run_one "$out/${split}_ef${ef}" "$bin" \
        --dataset SIFT100M --M 16 --efConstruction 100 --efSearch "$ef" --k 10 \
        --index-filepath "$index" --dataset-dir-prefix "$dataset_dir" \
        --query-num "$n" --output "$out/${split}_ef${ef}.txt" \
        --mode no-early-stop --query-type "$query_type"
    done
  done
done
