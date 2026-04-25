#!/bin/bash
# Fases 1-4 — BO only (6 pipelines)

set -e

echo "==============================================="
echo "PHASES 1-4 — BO ONLY (6 pipelines)"
echo "==============================================="

cd /home/ubuntu/mogalef-systems-lab/mgf-control

# Array of (asset, tf, comb) tuples for BO
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

  LOG="logs/bo_${ASSET}_${TF}_${COMB}.log"
  mkdir -p logs

  (
    echo "[BO START] $ASSET $TF $COMB" | tee "$LOG"

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

    echo "[BO OK] $ASSET $TF $COMB" | tee -a "$LOG"
  ) &

  # Limit to 2 parallel jobs on BO (4 cores)
  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[BO] All 6 pipelines complete"
echo "[BO] Results: $(find phase*_results -name '*_top10.json' | wc -l) top-10 JSON files"
