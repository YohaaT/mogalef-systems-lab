#!/bin/bash
# ============================================================
# SETUP GITHUB REMOTE - Run this ONCE after creating repo on GitHub
# ============================================================
# Pre-requisito: Crear repo en https://github.com/new
#   Name: mogalef-systems-lab
#   Visibility: Private
#   NO inicializar con README
# ============================================================

GITHUB_USER="YohaaT"
REPO_NAME="mogalef-systems-lab"
REMOTE_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"

echo "============================================================"
echo "MOGALEF SYSTEMS LAB - GitHub Remote Setup"
echo "============================================================"
echo "Remote: $REMOTE_URL"
echo ""

# Add remote
git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"
echo "[OK] Remote configurado: $REMOTE_URL"

# Push initial commit
git branch -M main
git push -u origin main

echo ""
echo "============================================================"
echo "PUSH COMPLETADO"
echo ""
echo "Ahora configura BO y TANK con:"
echo "  ssh bo   -> bash setup_bo_git.sh"
echo "  ssh tank -> bash setup_tank_git.sh"
echo "============================================================"
