#!/bin/bash
# Phase 5 — TANK ONLY con VEC + POOL (12 pipelines)
# Ejecución optimizada: vectorización + multiprocessing.Pool(6)

set -e

echo "==============================================="
echo "PHASE 5 — TANK VEC + POOL (12 pipelines)"
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

  LOG="logs/phase5_${ASSET}_${TF}_${COMB}.log"
  mkdir -p logs

  (
    echo "[TANK Phase5-VEC] $ASSET $TF $COMB" | tee "$LOG"

    python3 phase5_combine_filters_vectorized.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --phase1-dir ./phase1_results \
      --phase2a-dir ./phase2a_results \
      --phase2b-dir ./phase2b_results \
      --phase3-dir ./phase3_results \
      --phase4-dir ./phase4_results \
      --out ./phase5_results \
      --workers 6 \
      >> "$LOG" 2>&1

    if [ $? -eq 0 ]; then
      echo "[TANK OK] $ASSET $TF $COMB" | tee -a "$LOG"
    else
      echo "[TANK ERROR] $ASSET $TF $COMB" | tee -a "$LOG"
    fi
  ) &

  # Limit to 2 parallel jobs on TANK (8 cores, POOL(6) each)
  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[TANK] All 12 pipelines complete"
echo "[TANK] Results: $(find phase5_results -name '*_top5.json' 2>/dev/null | wc -l) top-5 JSON files"
echo "==============================================="
