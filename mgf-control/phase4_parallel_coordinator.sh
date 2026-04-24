#!/bin/bash
# Phase 4 Parallel Coordinator - Stop Inteligente Optimization
#
# Divides 108 combos into 2 blocks across TANK + VPS
# Execution strategy:
# - TANK Block 1: quality=[1,2] × recent=[1,2,3] × ref=[10,20] × coef=[3.0,5.0] = 48 combos
# - VPS Block 2:  quality=[3] × recent=[1,2,3] × ref=[10,20,30] × coef=[5.0,7.0] = 60 combos
# - Time: ~30-40 minutes total (parallel)

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ PHASE 4 PARALLEL COORDINATOR                              ║"
echo "║ Stop Inteligente Optimization (108 combos, 2 blocks)     ║"
echo "╚════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[PRE-FLIGHT] Checking connectivity..."

echo "   Testing TANK (192.168.1.162)..."
if ! ssh tank "echo 'Tank online'" >/dev/null 2>&1; then
    echo "   ❌ ERROR: Cannot connect to TANK"
    exit 1
fi
echo "   ✓ TANK online"

echo "   Testing VPS BO (79.72.62.202)..."
if ! ssh bo "echo 'VPS online'" >/dev/null 2>&1; then
    echo "   ❌ ERROR: Cannot connect to VPS"
    exit 1
fi
echo "   ✓ VPS online"

# ─────────────────────────────────────────────────────────────────
# Prepare scripts on remote servers
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[PREP] Uploading Phase 4 script to servers..."

# Upload to TANK
scp -q phase4_stops_optimization_block_runner.py tank:~/phase2_work/
echo "   ✓ Script uploaded to TANK"

# Upload to VPS
scp -q phase4_stops_optimization_block_runner.py bo:~/phase2_parallel/
echo "   ✓ Script uploaded to VPS"

# ─────────────────────────────────────────────────────────────────
# Launch parallel execution
# ─────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ 🚀 LAUNCHING PHASE 4 PARALLEL EXECUTION                    ║"
echo "╚════════════════════════════════════════════════════════════╝"

TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
TANK_LOG="phase4_tank_${TIMESTAMP}.log"
VPS_LOG="phase4_vps_${TIMESTAMP}.log"

echo ""
echo "Execution started at $(date)"
echo "TANK log: $TANK_LOG"
echo "VPS log:  $VPS_LOG"
echo ""

# Start TANK Block 1 in background
echo "Starting TANK Phase 4 Block 1 (48 combos)..."
ssh tank "cd ~/phase2_work && python3 phase4_stops_optimization_block_runner.py 1" > "$TANK_LOG" 2>&1 &
TANK_PID=$!
echo "   PID: $TANK_PID"

# Start VPS Block 2 in background
echo "Starting VPS Phase 4 Block 2 (60 combos)..."
ssh bo "cd ~/phase2_parallel && python3 phase4_stops_optimization_block_runner.py 2" > "$VPS_LOG" 2>&1 &
VPS_PID=$!
echo "   PID: $VPS_PID"

echo ""
echo "Both blocks executing in parallel. Monitoring progress..."
echo "(Press Ctrl+C to cancel)"
echo ""

# ─────────────────────────────────────────────────────────────────
# Monitor progress
# ─────────────────────────────────────────────────────────────────
TANK_DONE=0
VPS_DONE=0
START_TIME=$(date +%s)

while [ $TANK_DONE -eq 0 ] || [ $VPS_DONE -eq 0 ]; do
    sleep 10
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))

    # Check TANK status
    if kill -0 $TANK_PID 2>/dev/null; then
        TANK_STATUS="Running"
    else
        if wait $TANK_PID 2>/dev/null; then
            TANK_STATUS="✓ Completed"
            TANK_DONE=1
        else
            TANK_STATUS="❌ Failed"
            TANK_DONE=1
        fi
    fi

    # Check VPS status
    if kill -0 $VPS_PID 2>/dev/null; then
        VPS_STATUS="Running"
    else
        if wait $VPS_PID 2>/dev/null; then
            VPS_STATUS="✓ Completed"
            VPS_DONE=1
        else
            VPS_STATUS="❌ Failed"
            VPS_DONE=1
        fi
    fi

    printf "\r[%02d:%02d] TANK B1: %-20s | VPS B2: %-20s" "$MINUTES" "$SECONDS" "$TANK_STATUS" "$VPS_STATUS"
done

echo ""
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ EXECUTION SUMMARY                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"

CURRENT_TIME=$(date +%s)
TOTAL_ELAPSED=$((CURRENT_TIME - START_TIME))
TOTAL_MINUTES=$((TOTAL_ELAPSED / 60))
TOTAL_SECONDS=$((TOTAL_ELAPSED % 60))

echo ""
echo "Total time: ${TOTAL_MINUTES}m ${TOTAL_SECONDS}s"
echo ""
echo "Results:"

if [ $TANK_DONE -eq 1 ] && tail -1 "$TANK_LOG" | grep -q "BEST"; then
    echo "✓ TANK Block 1: Success"
else
    echo "❌ TANK Block 1: Failed (see $TANK_LOG)"
fi

if [ $VPS_DONE -eq 1 ] && tail -1 "$VPS_LOG" | grep -q "BEST"; then
    echo "✓ VPS Block 2: Success"
else
    echo "❌ VPS Block 2: Failed (see $VPS_LOG)"
fi

echo ""
echo "Retrieving results from both servers..."
scp -q tank:~/phase2_work/phase4_stops_optimization_block_1_best_params.json . 2>/dev/null && echo "✓ TANK Block 1 results downloaded"
scp -q bo:~/phase2_parallel/phase4_stops_optimization_block_2_best_params.json bo_phase4_stops_optimization_block_2_best_params.json 2>/dev/null && echo "✓ VPS Block 2 results downloaded"

echo ""
echo "Logs saved:"
echo "  TANK: $TANK_LOG"
echo "  VPS:  $VPS_LOG"
