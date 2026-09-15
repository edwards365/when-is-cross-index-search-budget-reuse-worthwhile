#!/usr/bin/env bash
set -euo pipefail

repo=${TCP_REPO:-/home/wlk/projects/navigation-aware-resistance-hnsw}
root=${TCP_PHASE5_ROOT:-/home/wlk/data500/tcp_sigmod_regular_closure/phase5_prospective_v1}
python=${TCP_DARTH_PYTHON:-/home/wlk/data500/graph_anns_score8/envs/darth/bin/python}
binary=${TCP_DARTH_BINARY:-/home/wlk/data500/graph_anns_score8/build/darth/hnsw-test/hnsw_test}
dataset=${1:?usage: phase5_run.sh sift|arxiv build|grid}
stage=${2:?usage: phase5_run.sh sift|arxiv build|grid|darth}
source_seeds=(1103 1229 1361 1499 1621 1747 1877 1999 2131)
read -r -a target_seeds <<< "${TCP_TARGET_SEEDS:-2381 2503 2633}"
grid=(10 20 40 80 120 160 200)

case "$dataset" in
  sift)
    source_indexes=/home/wlk/data500/graph_anns_score8/darth_comparison/multibuild/indexes
    source_prefix=sift100k
    darth_model=/home/wlk/data500/graph_anns_score8/darth_comparison/multibuild/m1/seed_1103/model_11feat.txt
    ;;
  arxiv)
    source_indexes=/home/wlk/data500/graph_anns_score8/darth_comparison/arxiv/indexes/multibuild
    source_prefix=arxiv100k
    darth_model=/home/wlk/data500/graph_anns_score8/darth_comparison/arxiv/runs/m1/seed_1103/model_11feat.txt
    ;;
  *) echo "invalid dataset: $dataset" >&2; exit 2 ;;
esac

out="$root/$dataset"
mkdir -p "$out/indexes" "$out/logs" "$out/grid"

build_targets() {
  for seed in "${target_seeds[@]}"; do
    index="$out/indexes/${dataset}_seed_${seed}.faiss"
    metadata="$out/indexes/${dataset}_seed_${seed}.json"
    if [[ -e "$index" || -e "$metadata" ]]; then
      echo "refusing to overwrite target index for seed $seed" >&2; exit 3
    fi
    "$python" "$repo/scripts/graph_anns_score8/darth_build_faiss_hnsw.py" \
      --base "$out/builds/seed_${seed}/SIFT100M/base.100M.fvecs" \
      --output "$index" --metadata "$metadata" \
      >"$out/logs/build_${seed}.stdout" 2>"$out/logs/build_${seed}.stderr"
    sha256sum "$index" >"$out/indexes/${dataset}_seed_${seed}.sha256"
  done
}

run_grid() {
  sha256sum "$binary" >"$out/grid/executable.sha256"
  git -C "$repo" rev-parse HEAD >"$out/grid/repo_head.txt"
  for seed in "${source_seeds[@]}" "${target_seeds[@]}"; do
    build_dir="$out/builds/seed_${seed}"
    if [[ " ${source_seeds[*]} " == *" $seed "* ]]; then
      index="$source_indexes/${source_prefix}_seed_${seed}.faiss"
    else
      index="$out/indexes/${dataset}_seed_${seed}.faiss"
    fi
    seed_out="$out/grid/seed_${seed}"
    mkdir -p "$seed_out"
    sha256sum "$index" >"$seed_out/index.sha256"
    for split in cert eval; do
      count=500; query_type=validation
      if [[ "$split" == eval ]]; then count=1000; query_type=testing; fi
      for ef in "${grid[@]}"; do
        log="$seed_out/${split}_ef${ef}"
        if [[ -e "${log}.txt" ]]; then
          echo "refusing to overwrite $log.txt" >&2; exit 4
        fi
        command=("$binary" --dataset SIFT100M --M 16 --efConstruction 100
          --efSearch "$ef" --k 10 --index-filepath "$index"
          --dataset-dir-prefix "$build_dir/" --query-num "$count"
          --output "${log}.txt" --mode no-early-stop --query-type "$query_type")
        printf '%q ' "${command[@]}" >"${log}.command"; printf '\n' >>"${log}.command"
        "${command[@]}" >"${log}.stdout" 2>"${log}.stderr"
      done
    done
  done
}

run_darth() {
  darth_out="$out/darth_source_1103"
  mkdir -p "$darth_out"
  sha256sum "$darth_model" >"$darth_out/model.sha256"
  for seed in "${target_seeds[@]}"; do
    index="$out/indexes/${dataset}_seed_${seed}.faiss"
    build_dir="$out/builds/seed_${seed}"
    seed_out="$darth_out/seed_${seed}"
    mkdir -p "$seed_out"
    for split in cert eval; do
      count=500; query_type=validation
      if [[ "$split" == eval ]]; then count=1000; query_type=testing; fi
      log="$seed_out/darth_${split}_${count}"
      if [[ -e "${log}.txt" ]]; then
        echo "refusing to overwrite $log.txt" >&2; exit 5
      fi
      command=("$binary" --dataset SIFT100M --M 16 --efConstruction 100
        --efSearch 200 --k 10 --index-filepath "$index"
        --dataset-dir-prefix "$build_dir/" --query-num "$count"
        --output "${log}.txt" --mode early-stop-testing --query-type "$query_type"
        --target-recall .90 --initial-prediction-interval 20
        --min-prediction-interval 5 --logging-interval 5
        --predictor-model-path "$darth_model")
      printf '%q ' "${command[@]}" >"${log}.command"; printf '\n' >>"${log}.command"
      "${command[@]}" >"${log}.stdout" 2>"${log}.stderr"
    done
  done
}

case "$stage" in
  build) build_targets ;;
  grid) run_grid ;;
  darth) run_darth ;;
  *) echo "invalid stage: $stage" >&2; exit 2 ;;
esac
