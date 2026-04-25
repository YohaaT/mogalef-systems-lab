#!/bin/bash
# Phase 5 — Combinación vectorizada + POOL (BO / TANK)
# Distribución: BO 6 pipelines, TANK 12 pipelines
#
# Uso:
#   bash run_phase5_vec_parallel.sh

set -e

ASSETS=("ES" "FDAX" "MNQ")
TIMEFRAMES=("5m" "10m" "15m")
COMBS=("001" "002")

BO_HOST="ubuntu@79.72.62.202"
BO_KEY="$HOME/.ssh/B_O.key"
BO_PATH="/home/ubuntu/mogalef-systems-lab/mgf-control"

TANK_HOST="ytambo@192.168.1.162"
TANK_KEY="$HOME/.ssh/id_ed25519"
TANK_PATH="~/mogalef-systems-lab/mgf-control"

echo "==============================================="
echo "PHASE 5 — Vectorizado + POOL (BO/TANK paralelo)"
echo "==============================================="

# BO distribution: 6 pipelines
echo "[BO] Launching 6 pipelines..."
ssh -i "$BO_KEY" "$BO_HOST" << 'SSH_BO'
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
      --workers 0 \
      >> "$LOG" 2>&1

    if [ $? -eq 0 ]; then
      echo "[BO OK] $ASSET $TF $COMB" | tee -a "$LOG"
    else
      echo "[BO ERROR] $ASSET $TF $COMB" | tee -a "$LOG"
    fi
  ) &

  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[BO] All pipelines complete"
SSH_BO

echo ""
echo "[BO] Results:"
ssh -i "$BO_KEY" "$BO_HOST" "cd /home/ubuntu/mogalef-systems-lab/mgf-control && find phase5_results -name '*_top5.json' 2>/dev/null | wc -l"

# TANK distribution: 12 pipelines
echo "[TANK] Launching 12 pipelines..."
ssh -i "$TANK_KEY" "$TANK_HOST" << 'SSH_TANK'
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
    echo "[TANK Phase5] $ASSET $TF $COMB" | tee "$LOG"

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
      --workers 0 \
      >> "$LOG" 2>&1

    if [ $? -eq 0 ]; then
      echo "[TANK OK] $ASSET $TF $COMB" | tee -a "$LOG"
    else
      echo "[TANK ERROR] $ASSET $TF $COMB" | tee -a "$LOG"
    fi
  ) &

  if (( $(jobs -r -p | wc -l) >= 2 )); then
    wait -n
  fi
done

wait
echo "[TANK] All pipelines complete"
SSH_TANK

echo ""
echo "[TANK] Results:"
ssh -i "$TANK_KEY" "$TANK_HOST" "cd ~/mogalef-systems-lab/mgf-control && find phase5_results -name '*_top5.json' 2>/dev/null | wc -l"

echo ""
echo "==============================================="
echo "[SUCCESS] Phase 5 vectorized complete on BO + TANK"
echo "Results in: phase5_results/phase5_combine_*.json"
echo "==============================================="
