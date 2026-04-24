#!/bin/bash
# Phase 2 Fast Track - Consolidated 2b+2c execution
# Waits for Block 1 to finish, consolidates 2a, then runs 2b+2c in parallel

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ PHASE 2 FAST TRACK - CONSOLIDATED 2b+2c                   ║"
echo "╚════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────
# Step 1: Wait for TANK Block 1 to complete
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 1] Waiting for TANK Phase 2a Block 1 completion..."

MAX_WAIT=300  # 5 minutes
ELAPSED=0
while [ ! -f "phase2a_trend_optimization_block_1_best_params.json" ]; do
    if [ $ELAPSED -gt $MAX_WAIT ]; then
        echo "❌ TANK Block 1 timeout"
        exit 1
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    ssh tank "cd ~/phase2_work && ls phase2a_trend_optimization_block_1_best_params.json 2>/dev/null >/dev/null && echo 'Block 1 done' || echo 'Waiting... ($ELAPSED/$MAX_WAIT sec)'"
done

echo "✓ TANK Block 1 complete"
scp -q tank:~/phase2_work/phase2a_trend_optimization_block_1_best_params.json .
scp -q tank:~/phase2_work/phase2a_trend_optimization_block_1_log.csv .

# ─────────────────────────────────────────────────────────────────
# Step 2: Consolidate Phase 2a (merge blocks 1+2)
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 2] Consolidating Phase 2a (Block 1 + Block 2)..."

# Copy block 2 files from VPS to local first
scp -q bo:~/phase2_parallel/phase2a_trend_optimization_block_2_log.csv .
scp -q bo:~/phase2_parallel/phase2a_trend_optimization_block_2_best_params.json .

# Run consolidation locally
python3 phase2a_consolidate_blocks.py

if [ ! -f "phase2a_trend_best_params.json" ]; then
    echo "❌ Consolidation failed"
    exit 1
fi
echo "✓ Phase 2a consolidated"

# Copy consolidated result to both servers
echo "   Distributing consolidated params..."
scp -q phase2a_trend_best_params.json tank:~/phase2_work/
scp -q phase2a_trend_best_params.json bo:~/phase2_parallel/

# ─────────────────────────────────────────────────────────────────
# Step 3: Launch Phase 2b (TANK) + Phase 2c (VPS) in parallel
# ─────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ LAUNCHING PHASE 2b + 2c IN PARALLEL                       ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Phase 2b on TANK
echo ""
echo "[LAUNCHING] Phase 2b on TANK (Horaire - 6 profiles)..."
ssh tank "cd ~/phase2_work && bash -c 'python3 phase2b_horaire_optimization.py > phase2b.log 2>&1 &'" &
TANK_2B_PID=$!

# Phase 2c on VPS
echo "[LAUNCHING] Phase 2c on VPS (Volatility - 5 bands)..."
ssh bo "cd ~/phase2_parallel && bash -c 'python3 phase2c_volatility_optimization.py > phase2c.log 2>&1 &'" &
VPS_2C_PID=$!

echo ""
echo "Both phases launched in parallel"
echo "   TANK 2b PID: $TANK_2B_PID"
echo "   VPS 2c PID: $VPS_2C_PID"
echo ""
echo "Monitoring progress..."

# ─────────────────────────────────────────────────────────────────
# Step 4: Monitor both phases
# ─────────────────────────────────────────────────────────────────
TANK_DONE=0
VPS_DONE=0
START=$(date +%s)

while [ $TANK_DONE -eq 0 ] || [ $VPS_DONE -eq 0 ]; do
    sleep 10
    CURRENT=$(date +%s)
    ELAPSED=$((CURRENT - START))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))

    # Check TANK 2b
    if [ $TANK_DONE -eq 0 ]; then
        if ssh tank "test -f ~/phase2_work/phase2b_horaire_best_params.json" 2>/dev/null; then
            TANK_DONE=1
            TANK_STATUS="✓ 2b Done"
        else
            TANK_STATUS="2b Running"
        fi
    else
        TANK_STATUS="✓ 2b Done"
    fi

    # Check VPS 2c
    if [ $VPS_DONE -eq 0 ]; then
        if ssh bo "test -f ~/phase2_parallel/phase2c_volatility_best_params.json" 2>/dev/null; then
            VPS_DONE=1
            VPS_STATUS="✓ 2c Done"
        else
            VPS_STATUS="2c Running"
        fi
    else
        VPS_STATUS="✓ 2c Done"
    fi

    printf "\r[%02d:%02d] TANK: %-15s | VPS: %-15s" "$MINUTES" "$SECONDS" "$TANK_STATUS" "$VPS_STATUS"
done

echo ""
echo ""
echo "✓ Phase 2b + 2c complete"

# ─────────────────────────────────────────────────────────────────
# Step 5: Final consolidation
# ─────────────────────────────────────────────────────────────────
echo ""
echo "[STEP 5] Final consolidation (2a+2b+2c)..."

# Get results from servers
scp -q tank:~/phase2_work/phase2b_horaire_best_params.json .
scp -q bo:~/phase2_parallel/phase2c_volatility_best_params.json .

# Run final consolidation
python3 phase2_combine_results.py

if [ ! -f "phase2_best_params.json" ]; then
    echo "❌ Final consolidation failed"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ ✓ PHASE 2 COMPLETE - FAST TRACK                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Final Results:"
cat phase2_best_params.json | head -25
echo ""
echo "✓ phase2_best_params.json generated"
echo "✓ phase3_summary.json ready for Phase 3"
