#!/bin/bash
# Phase 3 Parallel Coordinator - Exits Optimization
#
# Divides 16 exit combinations into 2 blocks (8 each) across TANK + VPS
# Execution strategy:
# - TANK: Combos 1-8 (target_atr 5.0-10.0 × timescan 20-30)
# - VPS:  Combos 9-16 (target_atr 10.0-20.0 × timescan 40-50)
# - Time: ~10-15 minutes total (parallel)

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ PHASE 3 PARALLEL COORDINATOR                              ║"
echo "║ Exits Optimization (target_atr × timescan_bars)          ║"
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
echo "[PREP] Uploading Phase 3 script to servers..."

# Upload to TANK
scp -q phase3_exits_optimization.py tank:~/phase2_work/
echo "   ✓ Script uploaded to TANK"

# Upload to VPS
scp -q phase3_exits_optimization.py bo:~/phase2_parallel/
echo "   ✓ Script uploaded to VPS"

# ─────────────────────────────────────────────────────────────────
# Launch parallel execution
# ─────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ 🚀 LAUNCHING PHASE 3 PARALLEL EXECUTION                    ║"
echo "╚════════════════════════════════════════════════════════════╝"

TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
TANK_LOG="phase3_tank_${TIMESTAMP}.log"
VPS_LOG="phase3_vps_${TIMESTAMP}.log"

echo ""
echo "Execution started at $(date)"
echo "TANK log: $TANK_LOG"
echo "VPS log:  $VPS_LOG"
echo ""

# Start TANK in background
echo "Starting TANK Phase 3 (Combos 1-8)..."
ssh tank "cd ~/phase2_work && python3 phase3_exits_optimization.py" > "$TANK_LOG" 2>&1 &
TANK_PID=$!
echo "   PID: $TANK_PID"

# Start VPS in background
echo "Starting VPS Phase 3 (Combos 9-16)..."
ssh bo "cd ~/phase2_parallel && python3 phase3_exits_optimization.py" > "$VPS_LOG" 2>&1 &
VPS_PID=$!
echo "   PID: $VPS_PID"

echo ""
echo "Both servers executing Phase 3. Monitoring progress..."
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

    printf "\r[%02d:%02d] TANK: %-20s | VPS: %-20s" "$MINUTES" "$SECONDS" "$TANK_STATUS" "$VPS_STATUS"
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
    echo "✓ TANK: Success"
else
    echo "❌ TANK: Failed (see $TANK_LOG)"
fi

if [ $VPS_DONE -eq 1 ] && tail -1 "$VPS_LOG" | grep -q "BEST"; then
    echo "✓ VPS: Success"
else
    echo "❌ VPS: Failed (see $VPS_LOG)"
fi

echo ""
echo "Retrieving results from both servers..."
scp -q tank:~/phase2_work/phase3_exits_best_params.json . 2>/dev/null && echo "✓ TANK results downloaded"
scp -q bo:~/phase2_parallel/phase3_exits_best_params.json bo_phase3_exits_best_params.json 2>/dev/null && echo "✓ VPS results downloaded"

echo ""
echo "Logs saved:"
echo "  TANK: $TANK_LOG"
echo "  VPS:  $VPS_LOG"
