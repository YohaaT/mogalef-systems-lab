#!/bin/bash
# Phase 2 Parallel Coordinator - Local Control Script
#
# Launches both TANK and VPS scripts in parallel and monitors progress
#
# Workflow:
# ┌──────────────────────────────────┬──────────────────────────────────┐
# │ TANK (192.168.1.162)              │ VPS BO (79.72.62.202)            │
# ├──────────────────────────────────┼──────────────────────────────────┤
# │ 2a Block 1 (5 min)    ┐           │ 2a Block 2 (8 min)    ┐          │
# │                       ├─→ Sync    │                       ├─→ Sync   │
# │ [Wait for Block 2]    │           │ [Signal TANK]         │          │
# │                       │           │                       │          │
# │ 2a Consolidate (1 min)            │ 2c (3 min)            │          │
# │ 2b Horaire (3 min)    ┐           │ [Wait for 2a+2b]      ├─→ Sync   │
# │                       ├─→ Final   │ [Signal TANK]         │          │
# │ Final Consolidate     │           │                       │          │
# └──────────────────────────────────┴──────────────────────────────────┘
#
# Total time: ~8-10 minutes (vs 20-25 minutes sequential)

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ PHASE 2 PARALLEL COORDINATOR                              ║"
echo "║ Orchestrating bilateral execution on TANK + VPS           ║"
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
echo "[PREP] Uploading coordinator scripts to servers..."

# Upload scripts to TANK
scp -q phase2_parallel_tank.sh tank:~/phase2_work/
ssh tank "chmod +x ~/phase2_work/phase2_parallel_tank.sh"
echo "   ✓ Scripts uploaded to TANK"

# Upload scripts to VPS
scp -q phase2_parallel_vps.sh bo:~/phase2_parallel/
ssh bo "chmod +x ~/phase2_parallel/phase2_parallel_vps.sh"
echo "   ✓ Scripts uploaded to VPS"

# ─────────────────────────────────────────────────────────────────
# Launch parallel execution
# ─────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ 🚀 LAUNCHING PARALLEL EXECUTION                            ║"
echo "╚════════════════════════════════════════════════════════════╝"

TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
TANK_LOG="phase2_tank_${TIMESTAMP}.log"
VPS_LOG="phase2_vps_${TIMESTAMP}.log"

echo ""
echo "Execution started at $(date)"
echo "TANK log: $TANK_LOG"
echo "VPS log:  $VPS_LOG"
echo ""

# Start TANK in background
echo "Starting TANK execution (Local)..."
ssh tank "cd ~/phase2_work && bash phase2_parallel_tank.sh" > "$TANK_LOG" 2>&1 &
TANK_PID=$!
echo "   PID: $TANK_PID"

# Start VPS in background
echo "Starting VPS execution (Remote)..."
ssh bo "cd ~/phase2_parallel && bash phase2_parallel_vps.sh" > "$VPS_LOG" 2>&1 &
VPS_PID=$!
echo "   PID: $VPS_PID"

echo ""
echo "Both executions started. Monitoring progress..."
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

if [ $TANK_DONE -eq 1 ] && tail -1 "$TANK_LOG" | grep -q "COMPLETE"; then
    echo "✓ TANK: Success"
else
    echo "❌ TANK: Failed (see $TANK_LOG)"
fi

if [ $VPS_DONE -eq 1 ] && tail -1 "$VPS_LOG" | grep -q "COMPLETE"; then
    echo "✓ VPS: Success"
else
    echo "❌ VPS: Failed (see $VPS_LOG)"
fi

echo ""
echo "Retrieving final results from TANK..."
scp -q tank:~/phase2_work/phase2_best_params.json .
scp -q tank:~/phase2_work/phase3_summary.json .

if [ -f "phase2_best_params.json" ]; then
    echo "✓ Final params downloaded"
    echo ""
    echo "═════════════════════════════════════════════════════════"
    echo "PHASE 2 FINAL RESULTS:"
    echo "═════════════════════════════════════════════════════════"
    cat phase2_best_params.json
    echo ""
    echo "Phase 3 ready: phase3_summary.json"
fi

echo ""
echo "Logs saved:"
echo "  TANK: $TANK_LOG"
echo "  VPS:  $VPS_LOG"
