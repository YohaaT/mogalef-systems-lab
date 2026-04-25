#!/bin/bash
# TANK FULL OPTIMIZATION — Phases 1-5 con VEC + POOL (12 pipelines)
# Ejecución optimizada: todas las fases paralelizadas con POOL(6)

set -e

echo "==============================================="
echo "TANK FULL OPTIMIZATION — Phases 1-5 VEC+POOL"
echo "==============================================="

cd ~/mogalef-systems-lab/mgf-control

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

for PIPELINE in "${PIPELINES[@]}"; do
  IFS=':' read ASSET TF COMB <<< "$PIPELINE"

  LOG="logs/tank_${ASSET}_${TF}_${COMB}.log"
  mkdir -p logs

  (
    echo "[TANK] Starting $ASSET $TF $COMB (Phases 1-5 optimized)" | tee "$LOG"

    # Phase 1
    echo "[Phase 1] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase1_signal_independent_pool.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase1_results --workers 6 >> "$LOG" 2>&1

    # Phase 2a
    echo "[Phase 2a] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase2a_horaire_independent_pool.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase2a_results --workers 6 >> "$LOG" 2>&1

    # Phase 2b
    echo "[Phase 2b] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase2b_regime_independent_pool.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase2b_results --workers 6 >> "$LOG" 2>&1

    # Phase 3
    echo "[Phase 3] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase3_exits_independent_pool.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase3_results --workers 6 >> "$LOG" 2>&1

    # Phase 4
    echo "[Phase 4] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase4_stops_independent_pool.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --out ./phase4_results --workers 6 >> "$LOG" 2>&1

    # Phase 5 VEC+POOL
    echo "[Phase 5-VEC] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase5_combine_filters_vectorized.py \
      --asset "$ASSET" --timeframe "$TF" --comb "$COMB" \
      --phase1-dir ./phase1_results --phase2a-dir ./phase2a_results \
      --phase2b-dir ./phase2b_results --phase3-dir ./phase3_results \
      --phase4-dir ./phase4_results --out ./phase5_results \
      --workers 6 >> "$LOG" 2>&1

    echo "[TANK OK] $ASSET $TF $COMB" | tee -a "$LOG"
  ) &

  # Limit to 2 parallel jobs on TANK (8 cores, POOL(6) each = ~12-14 cores needed)
  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[TANK] All 12 pipelines complete (Phases 1-5 optimized)"
echo "[TANK] Phase 1-4 results: $(find phase*_results -name '*_top10.json' 2>/dev/null | wc -l) JSONs"
echo "[TANK] Phase 5 results: $(find phase5_results -name '*_top5.json' 2>/dev/null | wc -l) JSONs"
echo "==============================================="
