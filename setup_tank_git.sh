#!/bin/bash
# ============================================================
# SETUP GIT ON TANK - Run remotely after pushing to GitHub
# ============================================================
# Uso: ssh tank "bash ~/mogalef-systems-lab/setup_tank_git.sh"
# ============================================================

GITHUB_USER="YohaaT"
REPO_NAME="mogalef-systems-lab"
REMOTE_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
WORKDIR="$HOME/mogalef-systems-lab"

echo "============================================================"
echo "CONFIGURANDO GIT EN TANK"
echo "============================================================"

# Configure git identity
git config --global user.name "YohaaT-TANK"
git config --global user.email "tank@mogalef-systems-lab"
git config --global core.autocrlf false

# Init git in existing directory
cd "$WORKDIR"
git init 2>/dev/null || true

# Configure remote
git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"

# Sync with GitHub
git fetch origin main
git checkout -b main 2>/dev/null || git checkout main
git reset --hard origin/main

echo ""
echo "[OK] TANK sincronizado con GitHub"
echo ""
echo "Workflow para TANK:"
echo "  1. Ejecutar optimizacion"
echo "  2. git add *.json *.py *.md"
echo "  3. git commit -m 'TANK: Phase 1 results - MNQ 5m'"
echo "  4. git push origin main"
echo ""
echo "Archivos de datos (CSV) NO van al repo."
echo "============================================================"
