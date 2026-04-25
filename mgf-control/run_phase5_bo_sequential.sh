#!/bin/bash
# Phase 5 — BO ONLY secuencial (6 pipelines)
# Ejecución simple: sin VEC/POOL optimización

set -e

echo "==============================================="
echo "PHASE 5 — BO SEQUENTIAL (6 pipelines)"
echo "==============================================="

cd /home/ubuntu/mogalef-systems-lab/mgf-control

PIPELINES=(
  "ES:15m:001"
  "ES:15m:002"
  "FDAX:15m:001"
  "FDAX:15m:002"
  "ES:10m:001"
  "MNQ:10m:002"
)

for PIPELINE in "${PIPELINES[@]}"; do
  IFS=':' read ASSET TF COMB <<< "$PIPELINE"

  LOG="logs/phase5_${ASSET}_${TF}_${COMB}.log"
  mkdir -p logs

  (
    echo "[BO Phase5] $ASSET $TF $COMB" | tee "$LOG"

    python3 phase5_combine_filters.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --phase1-dir ./phase1_results \
      --phase2a-dir ./phase2a_results \
      --phase2b-dir ./phase2b_results \
      --phase3-dir ./phase3_results \
      --phase4-dir ./phase4_results \
      --out ./phase5_results \
      >> "$LOG" 2>&1

    if [ $? -eq 0 ]; then
      echo "[BO OK] $ASSET $TF $COMB" | tee -a "$LOG"
    else
      echo "[BO ERROR] $ASSET $TF $COMB" | tee -a "$LOG"
    fi
  ) &

  # Limit to 2 parallel jobs on BO (4 cores)
  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[BO] All 6 pipelines complete"
echo "[BO] Results: $(find phase5_results -name '*_top5.json' 2>/dev/null | wc -l) top-5 JSON files"
echo "==============================================="
