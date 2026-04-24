#!/bin/bash
# Phase 2 Parallel Execution - TANK Server Script
#
# TANK responsibilities:
# 1. Execute Phase 2a Block 1
# 2. Phase 2b (Horaire)
# 3. Wait for VPS Phase 2c, then consolidate all results
#
# VPS will run: Phase 2a Block 2, Phase 2c in parallel

set -e  # Exit on error

WORK_DIR="$HOME/phase2_work"
LOCK_FILE="/tmp/phase2_block2_done.lock"

cd "$WORK_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ PHASE 2 OPTIMIZATION - TANK SERVER (LOCAL)                ║"
echo "║ Responsibilities: 2a-Block1, 2b, Final Consolidate       ║"
echo "╚════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────
# PHASE 2a BLOCK 1 (60 combos)
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 1/4] Running PHASE 2a BLOCK 1 (trend_r1=[1,2], 60 combos)..."
echo "⏱️  Estimated time: 5-6 minutes"
python3 phase2a_trend_optimization_block_runner_vec.py 1

if [ ! -f "phase2a_trend_optimization_block_1_best_params.json" ]; then
    echo "❌ ERROR: Block 1 output file not found"
    exit 1
fi
echo "✓ Phase 2a Block 1 complete"

# ─────────────────────────────────────────────────────────────────
# WAIT FOR VPS BLOCK 2 COMPLETION
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 2/4] Waiting for VPS to complete Phase 2a Block 2..."
echo "⏱️  VPS running: Phase 2a Block 2 (~8 min)"

MAX_WAIT=900  # 15 minutes
ELAPSED=0
POLL_INTERVAL=10

while [ ! -f "$LOCK_FILE" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
    echo "   Waiting... ($ELAPSED/$MAX_WAIT sec)"
done

if [ ! -f "$LOCK_FILE" ]; then
    echo "❌ ERROR: VPS Block 2 did not complete in time (${MAX_WAIT}s)"
    exit 1
fi

echo "✓ VPS Block 2 complete (lock file detected)"

# ─────────────────────────────────────────────────────────────────
# RECEIVE BLOCK 2 RESULTS FROM VPS
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 2B] Receiving Phase 2a Block 2 results from VPS..."
scp -q bo:~/phase2_parallel/phase2a_trend_optimization_block_2_log.csv .
scp -q bo:~/phase2_parallel/phase2a_trend_optimization_block_2_best_params.json .
scp -q bo:~/phase2_parallel/phase2a_trend_optimization_block_2_top10.csv .
echo "✓ Block 2 results received from VPS"

# ─────────────────────────────────────────────────────────────────
# CONSOLIDATE PHASE 2a
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 3/4] Consolidating Phase 2a Blocks 1+2 (150 combos)..."
python3 phase2a_consolidate_blocks.py

if [ ! -f "phase2a_trend_best_params.json" ]; then
    echo "❌ ERROR: Phase 2a consolidation failed"
    exit 1
fi
echo "✓ Phase 2a consolidated"

# ─────────────────────────────────────────────────────────────────
# PHASE 2b (6 horaire profiles)
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 4/4] Running PHASE 2b (Horaire - 6 profiles)..."
echo "⏱️  Estimated time: 3 minutes"
echo "⏱️  VPS simultaneously running: Phase 2c (Volatility)"
python3 phase2b_horaire_optimization.py

if [ ! -f "phase2b_horaire_best_params.json" ]; then
    echo "❌ ERROR: Phase 2b failed"
    exit 1
fi
echo "✓ Phase 2b complete"

# ─────────────────────────────────────────────────────────────────
# WAIT FOR VPS PHASE 2c
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 4B] Waiting for VPS Phase 2c completion..."
PHASE2C_LOCK="/tmp/phase2c_done.lock"
ELAPSED=0
MAX_WAIT=600  # 10 minutes

while [ ! -f "$PHASE2C_LOCK" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
    echo "   Waiting... ($ELAPSED/$MAX_WAIT sec)"
done

if [ ! -f "$PHASE2C_LOCK" ]; then
    echo "❌ ERROR: VPS Phase 2c did not complete"
    exit 1
fi

echo "✓ VPS Phase 2c complete"

# ─────────────────────────────────────────────────────────────────
# RECEIVE PHASE 2c RESULTS
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[FINAL] Receiving Phase 2c results from VPS..."
scp -q bo:~/phase2_parallel/phase2c_volatility_optimization_log.csv .
scp -q bo:~/phase2_parallel/phase2c_volatility_best_params.json .
echo "✓ Phase 2c results received"

# ─────────────────────────────────────────────────────────────────
# FINAL CONSOLIDATION
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[FINAL] Consolidating ALL Phase 2 results (2a + 2b + 2c)..."
python3 phase2_combine_results.py

if [ ! -f "phase2_best_params.json" ]; then
    echo "❌ ERROR: Final consolidation failed"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ ✓ PHASE 2 OPTIMIZATION COMPLETE                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 RESULTS:"
cat phase2_best_params.json | head -20
echo "..."
echo ""
echo "📁 Output files ready for Phase 3"
echo "   ✓ phase2_best_params.json"
echo "   ✓ phase3_summary.json"
