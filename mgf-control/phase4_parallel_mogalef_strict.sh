#!/bin/bash
# Phase 4 Parallel Execution (TANK Block 1 + VPS Block 2) - Mogalef-Strict

echo "=========================================="
echo "PHASE 4 PARALLEL LAUNCH (Mogalef-Strict)"
echo "=========================================="

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TANK_LOG="phase4_tank_mogalef_${TIMESTAMP}.log"
VPS_LOG="phase4_vps_mogalef_${TIMESTAMP}.log"

echo "Syncing scripts to TANK..."
ssh tank "mkdir -p ~/phase2_work" 2>/dev/null
scp phase4_5m_stops_optimizer.py tank:~/phase2_work/ 2>/dev/null
scp COMB_001_TREND_V1_vectorized.py tank:~/phase2_work/ 2>/dev/null
scp YM_phase_A_5m.csv tank:~/phase2_work/ 2>/dev/null
scp YM_phase_B_5m.csv tank:~/phase2_work/ 2>/dev/null
scp phase1_5m_best_params.json tank:~/phase2_work/ 2>/dev/null
scp phase2_5m_best_params_mogalef_strict.json tank:~/phase2_work/ 2>/dev/null

echo "Syncing scripts to VPS..."
ssh bo "mkdir -p ~/phase2_parallel" 2>/dev/null
scp phase4_5m_stops_optimizer.py bo:~/phase2_parallel/ 2>/dev/null
scp COMB_001_TREND_V1_vectorized.py bo:~/phase2_parallel/ 2>/dev/null
scp YM_phase_A_5m.csv bo:~/phase2_parallel/ 2>/dev/null
scp YM_phase_B_5m.csv bo:~/phase2_parallel/ 2>/dev/null
scp phase1_5m_best_params.json bo:~/phase2_parallel/ 2>/dev/null
scp phase2_5m_best_params_mogalef_strict.json bo:~/phase2_parallel/ 2>/dev/null

echo ""
echo "Starting Phase 4 Block 1 on TANK..."
ssh tank "cd ~/phase2_work && nohup python3 phase4_5m_stops_optimizer.py 1 > /tmp/phase4_block1.log 2>&1 &"
TANK_PID=$!

echo "Starting Phase 4 Block 2 on VPS..."
ssh bo "cd ~/phase2_parallel && nohup python3 phase4_5m_stops_optimizer.py 2 > /tmp/phase4_block2.log 2>&1 &"
VPS_PID=$!

echo ""
echo "Both blocks running in parallel..."
echo "  TANK Block 1 PID: $TANK_PID"
echo "  VPS Block 2 PID: $VPS_PID"

# Monitor both
echo ""
echo "Monitoring progress..."
while true; do
    tank_status=$(ssh tank "ps aux | grep -c 'python3 phase4'" 2>/dev/null)
    vps_status=$(ssh bo "ps aux | grep -c 'python3 phase4'" 2>/dev/null)
    
    if [ "$tank_status" -lt 2 ] && [ "$vps_status" -lt 2 ]; then
        echo "Both blocks completed"
        break
    fi
    
    echo -ne "\r[TANK: Running] [VPS: Running]"
    sleep 5
done

echo ""
echo "Downloading results..."
scp tank:~/phase2_work/phase4_5m_stops_block_1_best_params.json . 2>/dev/null
scp bo:~/phase2_parallel/phase4_5m_stops_block_2_best_params.json . 2>/dev/null

echo ""
echo "=========================================="
echo "Phase 4 parallel execution complete"
echo "Results ready for consolidation"
echo "=========================================="
