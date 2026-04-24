#!/bin/bash
# Phase 2 Parallel Execution - VPS Server Script
#
# VPS responsibilities:
# 1. Execute Phase 2a Block 2 (90 combos)
# 2. Execute Phase 2c (Volatility - 5 bands)
#
# TANK will run: Phase 2a Block 1, Phase 2b, Final consolidate

set -e  # Exit on error

WORK_DIR="$HOME/phase2_parallel"
LOCK_FILE_BLOCK2="/tmp/phase2_block2_done.lock"
LOCK_FILE_2C="/tmp/phase2c_done.lock"

cd "$WORK_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ PHASE 2 OPTIMIZATION - VPS SERVER (REMOTE)                ║"
echo "║ Responsibilities: 2a-Block2, 2c                           ║"
echo "╚════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────
# PHASE 2a BLOCK 2 (90 combos)
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 1/2] Running PHASE 2a BLOCK 2 (trend_r1=[3,4,5], 90 combos)..."
echo "⏱️  Estimated time: 8-10 minutes"
python3 phase2a_trend_optimization_block_runner_vec.py 2

if [ ! -f "phase2a_trend_optimization_block_2_best_params.json" ]; then
    echo "❌ ERROR: Block 2 output file not found"
    exit 1
fi

echo "✓ Phase 2a Block 2 complete"
echo "   Creating lock file to signal TANK..."
touch "$LOCK_FILE_BLOCK2"

# ─────────────────────────────────────────────────────────────────
# PHASE 2c (5 volatility bands)
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 2/2] Running PHASE 2c (Volatility - 5 bands)..."
echo "⏱️  Estimated time: 3 minutes"
echo "⏱️  TANK simultaneously running: Phase 2b (Horaire)"

# First, we need to wait for 2a consolidation results from TANK
# because Phase 2c needs phase2a_trend_best_params.json

echo "   Waiting for TANK Phase 2a consolidation..."
PHASE2A_BEST="/tmp/phase2a_best_received.lock"
MAX_WAIT=900  # 15 minutes
ELAPSED=0

while [ ! -f "phase2a_trend_best_params.json" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))

    # Try to receive the file from TANK
    scp -q tank:~/phase2_work/phase2a_trend_best_params.json . 2>/dev/null || true

    if [ $((ELAPSED % 30)) -eq 0 ]; then
        echo "   Waiting... ($ELAPSED/$MAX_WAIT sec)"
    fi
done

if [ ! -f "phase2a_trend_best_params.json" ]; then
    echo "❌ ERROR: Did not receive phase2a_trend_best_params.json from TANK"
    exit 1
fi

echo "✓ Received phase2a_trend_best_params.json from TANK"
echo "   Proceeding with Phase 2c..."

# Now wait for Phase 2b best params (horaire)
echo "   Waiting for TANK Phase 2b (Horaire) completion..."
while [ ! -f "phase2b_horaire_best_params.json" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    scp -q tank:~/phase2_work/phase2b_horaire_best_params.json . 2>/dev/null || true

    if [ $((ELAPSED % 30)) -eq 0 ]; then
        echo "   Waiting... ($ELAPSED/$MAX_WAIT sec)"
    fi
done

if [ ! -f "phase2b_horaire_best_params.json" ]; then
    echo "❌ ERROR: Did not receive phase2b_horaire_best_params.json from TANK"
    exit 1
fi

echo "✓ Received phase2b_horaire_best_params.json from TANK"
echo "   Now running Phase 2c..."

python3 phase2c_volatility_optimization.py

if [ ! -f "phase2c_volatility_best_params.json" ]; then
    echo "❌ ERROR: Phase 2c failed"
    exit 1
fi

echo "✓ Phase 2c complete"
echo "   Creating lock file to signal TANK..."
touch "$LOCK_FILE_2C"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ ✓ VPS PHASE 2 TASKS COMPLETE                              ║"
echo "║   TANK will now consolidate and finish Phase 2            ║"
echo "╚════════════════════════════════════════════════════════════╝"
