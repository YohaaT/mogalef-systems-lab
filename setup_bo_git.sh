#!/bin/bash
# ============================================================
# SETUP GIT ON BO - Run remotely after pushing to GitHub
# ============================================================
# Uso: ssh bo "bash ~/mogalef-systems-lab/setup_bo_git.sh"
# ============================================================

GITHUB_USER="YohaaT"
REPO_NAME="mogalef-systems-lab"
REMOTE_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
WORKDIR="$HOME/mogalef-systems-lab"

echo "============================================================"
echo "CONFIGURANDO GIT EN BO"
echo "============================================================"

# Configure git identity
git config --global user.name "YohaaT-BO"
git config --global user.email "bo@mogalef-systems-lab"
git config --global core.autocrlf false

# Init git in existing directory
cd "$WORKDIR"
git init 2>/dev/null || true

# Configure remote
git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"

# Fetch and sync with GitHub (keep local data files, get code from GitHub)
git fetch origin main

# Merge: take GitHub version for code, keep local data files
git checkout -b main 2>/dev/null || git checkout main
git reset --hard origin/main

echo ""
echo "[OK] BO sincronizado con GitHub"
echo ""
echo "Workflow para BO:"
echo "  1. Ejecutar optimizacion"
echo "  2. git add *.json *.py *.md"
echo "  3. git commit -m 'BO: Phase 1 results - ES 5m'"
echo "  4. git push origin main"
echo ""
echo "Archivos de datos (CSV) NO van al repo."
echo "============================================================"
