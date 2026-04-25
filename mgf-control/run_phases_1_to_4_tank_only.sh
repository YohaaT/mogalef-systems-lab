#!/bin/bash
# Fases 1-4 — TANK only (12 pipelines)

set -e

echo "==============================================="
echo "PHASES 1-4 — TANK ONLY (12 pipelines)"
echo "==============================================="

cd ~/mogalef-systems-lab/mgf-control

# Array of (asset, tf, comb) tuples for TANK
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
    echo "[TANK START] $ASSET $TF $COMB" | tee "$LOG"

    # Phase 1
    echo "[Phase 1] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase1_signal_independent.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --out ./phase1_results >> "$LOG" 2>&1

    # Phase 2a
    echo "[Phase 2a] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase2a_horaire_independent.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --out ./phase2a_results >> "$LOG" 2>&1

    # Phase 2b
    echo "[Phase 2b] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase2b_regime_independent.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --out ./phase2b_results >> "$LOG" 2>&1

    # Phase 3
    echo "[Phase 3] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase3_exits_independent.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --out ./phase3_results >> "$LOG" 2>&1

    # Phase 4
    echo "[Phase 4] $ASSET $TF $COMB..." >> "$LOG"
    python3 phase4_stops_independent.py \
      --asset "$ASSET" \
      --timeframe "$TF" \
      --comb "$COMB" \
      --out ./phase4_results >> "$LOG" 2>&1

    echo "[TANK OK] $ASSET $TF $COMB" | tee -a "$LOG"
  ) &

  # Limit to 2 parallel jobs on TANK (8 cores)
  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[TANK] All 12 pipelines complete"
echo "[TANK] Results: $(find phase*_results -name '*_top10.json' | wc -l) top-10 JSON files"
