#!/bin/bash
# Run Phase 1 Breakout Optimization in 5 blocks on VPS

VPS_USER="ubuntu"
VPS_IP="79.72.62.202"
VPS_PATH="/home/ubuntu/mogalef-optimization-breakout"
SSH_KEY="$HOME/.ssh/B_O.key"

echo "========================================================================"
echo "PHASE 1 BREAKOUT OPTIMIZATION - BLOCK MODE (5 BLOCKS x 125 COMBOS)"
echo "========================================================================"

echo ""
echo "[1] Creating project directory on VPS..."
ssh -i "$SSH_KEY" $VPS_USER@$VPS_IP "mkdir -p $VPS_PATH && cd $VPS_PATH && pwd"

echo ""
echo "[2] Copying strategy and dependency files..."
scp -i "$SSH_KEY" COMB_003_BREAKOUT_V1.py $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" phase1_breakout_optimization_block_runner.py $VPS_USER@$VPS_IP:$VPS_PATH/

# Required modules (dependencies)
scp -i "$SSH_KEY" ../mgf-regime-filter-lab/src/EL_NeutralZone_B_V2.py $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" ../mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py $VPS_USER@$VPS_IP:$VPS_PATH/

# Data files
scp -i "$SSH_KEY" YM_phase_A_clean.csv $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" YM_phase_B_clean.csv $VPS_USER@$VPS_IP:$VPS_PATH/

echo ""
echo "[3] Running Phase 1 Breakout Optimization Blocks on VPS..."
echo ""

for block in 1 2 3 4 5; do
    echo "========================================================================"
    echo "BLOCK $block/5"
    echo "========================================================================"
    ssh -i "$SSH_KEY" $VPS_USER@$VPS_IP "cd $VPS_PATH && python3 phase1_breakout_optimization_block_runner.py $block 2>&1 | tee breakout_block_${block}.log"
    echo ""
done

echo ""
echo "[4] Downloading block results..."
for block in 1 2 3 4 5; do
    scp -i "$SSH_KEY" $VPS_USER@$VPS_IP:$VPS_PATH/phase1_breakout_optimization_block_${block}_*.csv ./
    scp -i "$SSH_KEY" $VPS_USER@$VPS_IP:$VPS_PATH/phase1_breakout_optimization_block_${block}_*.json ./
    scp -i "$SSH_KEY" $VPS_USER@$VPS_IP:$VPS_PATH/breakout_block_${block}.log ./vps_breakout_block_${block}.log
done

echo ""
echo "[5] Combining all block results..."
python3 phase1_breakout_combine_blocks.py

echo ""
echo "========================================================================"
echo "[DONE] Phase 1 Breakout Optimization Complete!"
echo "========================================================================"
echo "Results:"
echo "  - phase1_breakout_optimization_full_log.csv (all 625 combos)"
echo "  - phase1_breakout_optimization_top10.csv (best 10)"
echo "  - phase1_breakout_best_params.json (best single combo)"
echo "========================================================================"
