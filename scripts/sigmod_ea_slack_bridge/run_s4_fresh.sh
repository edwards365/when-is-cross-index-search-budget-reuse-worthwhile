#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/wlk/data500/navigation-aware-resistance-hnsw-main
OUT="$ROOT/results/sigmod_ea_slack_bridge"
INPUTS="$OUT/s4_inputs"
HRAW="$OUT/s4_raw_hnsw"
FRAW="$OUT/s4_raw_faiss"
BIN="$OUT/s4_hnsw_replay"
MANIFEST="$OUT/s4_fresh_preregistration.json"
mkdir -p "$INPUTS" "$HRAW" "$FRAW"
cd "$ROOT"

export OPENBLAS_NUM_THREADS=16
export OMP_NUM_THREADS=1

if [[ ! -f "$INPUTS/input_inventory.json" ]]; then
  .venv/bin/python scripts/sigmod_ea_slack_bridge/prepare_s4_inputs.py \
    --root "$ROOT" --manifest "$MANIFEST" --output "$INPUTS"
fi

g++ -O3 -std=c++17 -pthread -I third_party/hnswlib \
  scripts/sigmod_ea_slack_bridge/s4_hnsw_replay.cpp -o "$BIN"

.venv/bin/python - "$MANIFEST" <<'PY'
import hashlib,json,sys
d=json.load(open(sys.argv[1]))
for family in ('hnsw_indexes','faiss_indexes'):
  for r in d[family]:
    h=hashlib.sha256()
    with open(r['path'],'rb') as f:
      for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    if h.hexdigest()!=r['sha256']:
      raise SystemExit('HASH_MISMATCH '+r['path'])
print('index_hash_gate=PASS indexes=96')
PY

.venv/bin/python - "$MANIFEST" <<'PY' | while IFS=$'\t' read -r dataset build path; do
import json,sys
d=json.load(open(sys.argv[1]))
for r in d['hnsw_indexes']:
 print(r['dataset'],r['build_id'],r['path'],sep='\t')
PY
  out="$HRAW/$build.csv.gz"
  if [[ -f "$out" ]]; then continue; fi
  metric=l2
  if [[ "$dataset" == "arxiv_nomic_100k" ]]; then metric=ip; fi
  tmp="$HRAW/$build.csv"
  "$BIN" "$path" "$INPUTS/$dataset.queries.fvecs" "$INPUTS/$dataset.truth.ivecs" \
    "$metric" "10,20,40,80,120,200" "$build" "$tmp"
  gzip -9 "$tmp"
done

/home/wlk/data500/graph_anns_score8/envs/darth/bin/python \
  scripts/sigmod_ea_slack_bridge/s4_faiss_replay.py \
  --manifest "$MANIFEST" --inputs "$INPUTS" --output "$FRAW"

date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/S4_REPLAY_COMPLETE"
echo S4_REPLAY_COMPLETE
