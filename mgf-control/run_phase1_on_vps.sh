#!/bin/bash
# Run Phase 1 Optimization on VPS (BO)

VPS_USER="ubuntu"
VPS_IP="79.72.62.202"
VPS_PATH="/home/ubuntu/mogalef-optimization"
SSH_KEY="$HOME/.ssh/B_O.key"

echo "[1] Creating project directory on VPS..."
ssh -i "$SSH_KEY" $VPS_USER@$VPS_IP "mkdir -p $VPS_PATH && cd $VPS_PATH && pwd"

echo ""
echo "[2] Copying strategy and dependency files..."
# Main strategy and optimization
scp -i "$SSH_KEY" COMB_001_TREND_V1.py $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" phase1_optimization.py $VPS_USER@$VPS_IP:$VPS_PATH/

# Required modules (dependencies)
scp -i "$SSH_KEY" ../mgf-divergence-lab/src/EL_STPMT_DIV.py $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" ../mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" ../mgf-stop-lab/src/EL_Stop_Intelligent.py $VPS_USER@$VPS_IP:$VPS_PATH/

# Data files
scp -i "$SSH_KEY" YM_phase_A_clean.csv $VPS_USER@$VPS_IP:$VPS_PATH/
scp -i "$SSH_KEY" YM_phase_B_clean.csv $VPS_USER@$VPS_IP:$VPS_PATH/

echo ""
echo "[3] Running Phase 1 Optimization on VPS..."
ssh -i "$SSH_KEY" $VPS_USER@$VPS_IP "cd $VPS_PATH && python3 phase1_optimization.py 2>&1 | tee optimization.log"

echo ""
echo "[4] Downloading results..."
scp -i "$SSH_KEY" $VPS_USER@$VPS_IP:$VPS_PATH/phase1_optimization_*.csv ./
scp -i "$SSH_KEY" $VPS_USER@$VPS_IP:$VPS_PATH/phase1_best_params.json ./
scp -i "$SSH_KEY" $VPS_USER@$VPS_IP:$VPS_PATH/optimization.log ./vps_optimization.log

echo ""
echo "[DONE] Phase 1 results downloaded locally!"
