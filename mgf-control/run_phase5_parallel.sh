#!/bin/bash
# Phase 5 — Combinar filtros en paralelo (BO 80% / TANK 20%)
#
# Uso:
#   bash run_phase5_parallel.sh
#
# Distribución:
#   BO (4 cores): ES (3TF) + FDAX (3TF) = 6 pipelines (80%)
#   TANK (8 cores): MNQ (3TF) = 3 pipelines (20%)

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
echo "PHASE 5 — Combinación de filtros (BO/TANK paralelo)"
echo "==============================================="

# BO distribution: ES, FDAX (6 pipelines)
echo "[BO] Launching ES + FDAX pipelines..."
ssh -i "$BO_KEY" "$BO_HOST" << 'SSH_BO'
cd /home/ubuntu/mogalef-systems-lab/mgf-control

# Run sequentially but log in parallel
for ASSET in ES FDAX; do
  for TF in 5m 10m 15m; do
    for COMB in 001 002; do
      LOG="logs/phase5_${ASSET}_${TF}_${COMB}.log"
      mkdir -p logs

      echo "[BO] Starting ${ASSET} ${TF} ${COMB}..."
      (
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
          echo "[BO OK] ${ASSET} ${TF} ${COMB}" | tee -a "$LOG"
        else
          echo "[BO ERROR] ${ASSET} ${TF} ${COMB}" | tee -a "$LOG"
        fi
      ) &

      # Limit to 2 parallel jobs on BO (4 cores, leave 2 free)
      if (( $(jobs -r -p | wc -l) >= 2 )); then
        wait -n
      fi
    done
  done
done

wait
echo "[BO] All pipelines complete"
SSH_BO

# TANK distribution: MNQ (3 pipelines)
echo "[TANK] Launching MNQ pipelines..."
ssh -i "$TANK_KEY" "$TANK_HOST" << 'SSH_TANK'
cd ~/mogalef-systems-lab/mgf-control

# Run sequentially but log in parallel
for TF in 5m 10m 15m; do
  for COMB in 001 002; do
    LOG="logs/phase5_MNQ_${TF}_${COMB}.log"
    mkdir -p logs

    echo "[TANK] Starting MNQ ${TF} ${COMB}..."
    (
      python3 phase5_combine_filters.py \
        --asset "MNQ" \
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
        echo "[TANK OK] MNQ ${TF} ${COMB}" | tee -a "$LOG"
      else
        echo "[TANK ERROR] MNQ ${TF} ${COMB}" | tee -a "$LOG"
      fi
    ) &

    # Limit to 2 parallel jobs on TANK (8 cores, leave 2 free)
    if (( $(jobs -r -p | wc -l) >= 2 )); then
      wait -n
    fi
  done
done

wait
echo "[TANK] All pipelines complete"
SSH_TANK

echo "==============================================="
echo "[SUCCESS] Phase 5 complete on BO + TANK"
echo "Results in: phase5_results/phase5_combine_*.json"
echo "==============================================="
