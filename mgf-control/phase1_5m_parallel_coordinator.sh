#!/bin/bash
# Phase 1 (5m) Parallel Coordinator — Signal Optimization
#
# Split: TANK=Block1 (175 combos), VPS_BO=Block2 (450 combos)
# VPS gets more work (faster machine, ~30-40% speedup)

set -e

echo "================================================================"
echo " PHASE 1 (5m) PARALLEL COORDINATOR — Signal Optimization"
echo " TANK  Block 1:  combos   1-175  (smooth_h=[1], smooth_h=2 partial)"
echo " VPS   Block 2:  combos 176-625  (smooth_h=[2,3,4,5])"
echo "================================================================"

# ── Pre-flight ────────────────────────────────────────────────────────────────
echo ""
echo "[PRE-FLIGHT] Checking connectivity..."

echo "   Testing TANK (192.168.1.162)..."
if ! ssh tank "echo ok" >/dev/null 2>&1; then echo "   ERROR: TANK offline"; exit 1; fi
echo "   TANK online"

echo "   Testing VPS BO (79.72.62.202)..."
if ! ssh bo "echo ok" >/dev/null 2>&1; then echo "   ERROR: VPS offline"; exit 1; fi
echo "   VPS online"

# ── Upload scripts and 5m data ────────────────────────────────────────────────
echo ""
echo "[PREP] Uploading scripts and 5m data..."

# TANK
scp -q phase1_5m_signal_block_runner.py tank:~/phase2_work/
scp -q COMB_001_TREND_V1_vectorized.py tank:~/phase2_work/
scp -q YM_phase_A_5m.csv tank:~/phase2_work/
scp -q YM_phase_B_5m.csv tank:~/phase2_work/
echo "   TANK: scripts + data uploaded"

# VPS
scp -q phase1_5m_signal_block_runner.py bo:~/phase2_parallel/
scp -q COMB_001_TREND_V1_vectorized.py bo:~/phase2_parallel/
scp -q YM_phase_A_5m.csv bo:~/phase2_parallel/
scp -q YM_phase_B_5m.csv bo:~/phase2_parallel/
echo "   VPS:  scripts + data uploaded"

# ── Launch parallel ────────────────────────────────────────────────────────────
echo ""
echo "================================================================"
echo " LAUNCHING PHASE 1 (5m) PARALLEL EXECUTION"
echo "================================================================"

TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
TANK_LOG="phase1_5m_tank_${TIMESTAMP}.log"
VPS_LOG="phase1_5m_vps_${TIMESTAMP}.log"

echo ""
echo "Started at: $(date)"
echo "TANK log: $TANK_LOG"
echo "VPS  log: $VPS_LOG"
echo ""

# Block 1 on TANK (175 combos)
echo "Starting TANK Block 1 (175 combos)..."
ssh tank "cd ~/phase2_work && python3 phase1_5m_signal_block_runner.py 1" > "$TANK_LOG" 2>&1 &
TANK_PID=$!
echo "   PID: $TANK_PID"

# Block 2 on VPS (450 combos)
echo "Starting VPS Block 2 (450 combos)..."
ssh bo "cd ~/phase2_parallel && python3 phase1_5m_signal_block_runner.py 2" > "$VPS_LOG" 2>&1 &
VPS_PID=$!
echo "   PID: $VPS_PID"

echo ""
echo "Both blocks running. Monitoring..."
echo "(Ctrl+C to cancel)"
echo ""

# ── Monitor ───────────────────────────────────────────────────────────────────
TANK_DONE=0
VPS_DONE=0
START_TIME=$(date +%s)

while [ $TANK_DONE -eq 0 ] || [ $VPS_DONE -eq 0 ]; do
    sleep 15
    ELAPSED=$(( $(date +%s) - START_TIME ))
    MINS=$((ELAPSED / 60))
    SECS=$((ELAPSED % 60))

    if kill -0 $TANK_PID 2>/dev/null; then
        TANK_STATUS="Running"
    else
        wait $TANK_PID 2>/dev/null && TANK_STATUS="Completed" || TANK_STATUS="FAILED"
        TANK_DONE=1
    fi

    if kill -0 $VPS_PID 2>/dev/null; then
        VPS_STATUS="Running"
    else
        wait $VPS_PID 2>/dev/null && VPS_STATUS="Completed" || VPS_STATUS="FAILED"
        VPS_DONE=1
    fi

    printf "\r[%02d:%02d] TANK B1: %-15s | VPS B2: %-15s" \
           "$MINS" "$SECS" "$TANK_STATUS" "$VPS_STATUS"
done

echo ""
echo ""
echo "================================================================"
echo " EXECUTION SUMMARY"
echo "================================================================"
TOTAL_ELAPSED=$(( $(date +%s) - START_TIME ))
echo "Total time: $((TOTAL_ELAPSED/60))m $((TOTAL_ELAPSED%60))s"
echo ""

# ── Retrieve results ──────────────────────────────────────────────────────────
echo "Retrieving results..."
scp -q tank:~/phase2_work/phase1_5m_signal_block_1_best_params.json . 2>/dev/null \
    && echo "TANK Block 1 results downloaded" || echo "WARNING: TANK results not found"
scp -q bo:~/phase2_parallel/phase1_5m_signal_block_2_best_params.json \
    bo_phase1_5m_signal_block_2_best_params.json 2>/dev/null \
    && echo "VPS  Block 2 results downloaded" || echo "WARNING: VPS results not found"

# Also grab logs and CSVs
scp -q tank:~/phase2_work/phase1_5m_signal_block_1_log.csv . 2>/dev/null && echo "TANK log CSV downloaded"
scp -q tank:~/phase2_work/phase1_5m_signal_block_1_top10.csv . 2>/dev/null
scp -q bo:~/phase2_parallel/phase1_5m_signal_block_2_log.csv bo_phase1_5m_signal_block_2_log.csv 2>/dev/null && echo "VPS  log CSV downloaded"
scp -q bo:~/phase2_parallel/phase1_5m_signal_block_2_top10.csv bo_phase1_5m_signal_block_2_top10.csv 2>/dev/null

echo ""
echo "Logs: $TANK_LOG  |  $VPS_LOG"
echo "Run phase1_5m_consolidate.py to merge and select best."
