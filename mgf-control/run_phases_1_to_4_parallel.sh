#!/bin/bash
# Fases 1-4 — Optimización INDEPENDIENTE en paralelo (BO / TANK)
# Distribución: BO 80% de carga (6 pipelines), TANK 20% (12 pipelines)
# Cada pipeline: Fase 1 → 2a → 2b → 3 → 4
#
# Uso:
#   bash run_phases_1_to_4_parallel.sh

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
echo "PHASES 1-4 — Optimización independiente (BO/TANK paralelo)"
echo "==============================================="

# BO distribution: 6 pipelines (80% = lighter TF, faster execution)
# Strategy: TF 15m + TF 10m (faster) first on BO
echo "[BO] Launching 6 pipelines (15m + 10m)..."
ssh -i "$BO_KEY" "$BO_HOST" << 'SSH_BO'
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
SSH_BO

echo ""
echo "[BO] Results:"
ssh -i "$BO_KEY" "$BO_HOST" "cd /home/ubuntu/mogalef-systems-lab/mgf-control && find phase*_results -name '*_top10.json' | wc -l"

# TANK distribution: 12 pipelines (remaining: 5m + 10m TF 001 + MNQ combinations)
echo "[TANK] Launching 12 pipelines (5m + 10m + remaining)..."
ssh -i "$TANK_KEY" "$TANK_HOST" << 'SSH_TANK'
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
SSH_TANK

echo ""
echo "[TANK] Results:"
ssh -i "$TANK_KEY" "$TANK_HOST" "cd ~/mogalef-systems-lab/mgf-control && find phase*_results -name '*_top10.json' | wc -l"

echo ""
echo "==============================================="
echo "[SUCCESS] Phases 1-4 complete on BO + TANK"
echo "Results in: phase1/2a/2b/3/4_results/phase*_top10.json"
echo "==============================================="
