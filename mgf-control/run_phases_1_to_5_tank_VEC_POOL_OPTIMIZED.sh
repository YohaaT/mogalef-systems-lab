#!/bin/bash
# TANK VEC+POOL OPTIMIZED - all five phases with optimized strategy entrypoints.
set -euo pipefail

echo "==============================================="
echo "TANK VEC+POOL OPTIMIZED - Phases 1-5"
echo "==============================================="

cd "$(dirname "$0")"
mkdir -p logs phase1_results phase2a_results phase2b_results phase3_results phase4_results phase5_results

WORKERS="${WORKERS:-6}"
MAX_PARALLEL="${MAX_PARALLEL:-2}"

PIPELINES=(
  "MNQ:15m:001"
  "MNQ:15m:002"
  "ES:5m:001"
  "ES:5m:002"
  "FDAX:5m:001"
  "FDAX:5m:002"
  "FDAX:10m:001"
  "FDAX:10m:002"
  "MNQ:5m:001"
  "MNQ:5m:002"
  "ES:10m:002"
  "MNQ:10m:001"
)

run_pipeline() {
  local asset="$1"
  local tf="$2"
  local comb="$3"
  local log="logs/tank_VEC_OPT_${asset}_${tf}_${comb}.log"

  {
    echo "[TANK VEC-OPT] START ${asset} ${tf} COMB_${comb}"

    python3 phase1_signal_independent_pool_vec_opt.py \
      --asset "$asset" --timeframe "$tf" --comb "$comb" \
      --out ./phase1_results --workers "$WORKERS"

    python3 phase2a_horaire_independent_pool_vec_opt.py \
      --asset "$asset" --timeframe "$tf" --comb "$comb" \
      --out ./phase2a_results --workers "$WORKERS"

    python3 phase2b_regime_independent_pool_vec_opt.py \
      --asset "$asset" --timeframe "$tf" --comb "$comb" \
      --out ./phase2b_results --workers "$WORKERS"

    python3 phase3_exits_independent_pool_vec_opt.py \
      --asset "$asset" --timeframe "$tf" --comb "$comb" \
      --out ./phase3_results --workers "$WORKERS"

    python3 phase4_stops_independent_pool_vec_opt.py \
      --asset "$asset" --timeframe "$tf" --comb "$comb" \
      --out ./phase4_results --workers "$WORKERS"

    python3 phase5_combine_filters_vec_opt.py \
      --asset "$asset" --timeframe "$tf" --comb "$comb" \
      --phase1-dir ./phase1_results --phase2a-dir ./phase2a_results \
      --phase2b-dir ./phase2b_results --phase3-dir ./phase3_results \
      --phase4-dir ./phase4_results --out ./phase5_results \
      --workers "$WORKERS"

    echo "[TANK VEC-OPT] OK ${asset} ${tf} COMB_${comb}"
  } > "$log" 2>&1
}

for pipeline in "${PIPELINES[@]}"; do
  IFS=':' read -r asset tf comb <<< "$pipeline"
  run_pipeline "$asset" "$tf" "$comb" &

  while (( $(jobs -r -p | wc -l) >= MAX_PARALLEL )); do
    wait -n
  done
done

wait
echo "[TANK] All pipelines complete (VEC+POOL OPTIMIZED)"

