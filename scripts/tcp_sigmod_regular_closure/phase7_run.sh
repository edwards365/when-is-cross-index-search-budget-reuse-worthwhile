#!/usr/bin/env bash
set -euo pipefail

export TCP_PHASE5_ROOT=/home/wlk/data500/tcp_sigmod_regular_closure/phase7_high_recall_v1
export TCP_TARGET_SEEDS="2791 2903 3011"

repo=${TCP_REPO:-/home/wlk/projects/navigation-aware-resistance-hnsw}
cd "$repo"

dataset=${1:?usage: phase7_run.sh sift|arxiv build|grid|darth}
stage=${2:?usage: phase7_run.sh sift|arxiv build|grid|darth}
exec scripts/tcp_sigmod_regular_closure/phase5_run.sh "$dataset" "$stage"
