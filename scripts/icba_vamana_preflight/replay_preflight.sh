#!/usr/bin/env bash
set -euo pipefail
ROOT=/home/wlk/data500/icba_vamana_preflight
export RUSTUP_HOME="$ROOT/toolchain" CARGO_HOME="$ROOT/cargo" CARGO_TARGET_DIR="$ROOT/target"
"$ROOT/target/release/diskann-benchmark" --quiet run --input-file "$ROOT/perm_run1_patched.json" --output-file "$ROOT/permutation_output/replay_registered.json"
