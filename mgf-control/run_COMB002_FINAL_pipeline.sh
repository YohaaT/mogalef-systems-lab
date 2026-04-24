#!/bin/bash
# COMB_002_IMPULSE — Pipeline final end-to-end
#
# Corre en secuencia (después de que Phase 5 haya terminado en los 12 combos):
#   1. Consolidador        → COMB002_FINAL_PARAMS.json + COMB002_FINAL_decisions.csv
#   2. Report generator    → COMB002_FINAL_REPORT.md
#   3. Hold-out validator  → COMB002_FINAL_holdout_results.csv + COMB002_FINAL_holdout_report.md
#   4. Git push            → commits los 4 artefactos finales a GitHub
#
# Uso:
#   bash run_COMB002_FINAL_pipeline.sh
#   bash run_COMB002_FINAL_pipeline.sh --no-push         # skip git push
#   bash run_COMB002_FINAL_pipeline.sh --skip-holdout    # skip sanity+holdout (si falta data)

set -e

PUSH=1
RUN_HOLDOUT=1

for arg in "$@"; do
    case "$arg" in
        --no-push)      PUSH=0 ;;
        --skip-holdout) RUN_HOLDOUT=0 ;;
        -h|--help)
            grep "^#" "$0" | head -20
            exit 0
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "COMB_002 IMPULSE — Final Pipeline | $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "================================================================================"

# ── Guard: verificar que haya 12 phase5 y 12 phase4 best_params ──────────────
ph4_count=$(ls COMB002_phase4_*_best_params.json 2>/dev/null | wc -l)
ph5_count=$(ls COMB002_phase5_*_best_params.json 2>/dev/null | wc -l)

echo "[CHECK] Phase 4 files found: $ph4_count / 12"
echo "[CHECK] Phase 5 files found: $ph5_count / 12"

if [ "$ph5_count" -lt 12 ]; then
    echo "[WARNING] Phase 5 incompleto ($ph5_count/12). Faltan combos — el consolidador los marcará como MISSING."
fi

# ── Step 1: Consolidador ─────────────────────────────────────────────────────
echo ""
echo "--- STEP 1/3: Consolidador (sequential vs cross) ---"
python3 consolidate_COMB002_final_winner.py

# ── Step 2: Report generator ─────────────────────────────────────────────────
echo ""
echo "--- STEP 2/3: Generando reporte MD ---"
python3 generate_COMB002_FINAL_report.py

# ── Step 3: Hold-out / sanity ────────────────────────────────────────────────
if [ "$RUN_HOLDOUT" -eq 1 ]; then
    echo ""
    echo "--- STEP 3/3: Hold-out + sanity re-ejecución ---"
    python3 validate_COMB002_FINAL_holdout.py || {
        echo "[WARN] Hold-out falló — continúa con el resto del pipeline"
    }
else
    echo ""
    echo "--- STEP 3/3: skipped (--skip-holdout) ---"
fi

# ── Step 4: Git push ─────────────────────────────────────────────────────────
if [ "$PUSH" -eq 1 ]; then
    echo ""
    echo "--- STEP 4: Git push de artefactos FINAL ---"
    cd ..
    files=(
        "mgf-control/COMB002_FINAL_PARAMS.json"
        "mgf-control/COMB002_FINAL_decisions.csv"
        "mgf-control/COMB002_FINAL_REPORT.md"
    )
    if [ "$RUN_HOLDOUT" -eq 1 ]; then
        files+=(
            "mgf-control/COMB002_FINAL_holdout_results.csv"
            "mgf-control/COMB002_FINAL_holdout_report.md"
        )
    fi

    # Agrega solo los que existen
    to_add=()
    for f in "${files[@]}"; do
        [ -f "$f" ] && to_add+=("$f")
    done

    if [ "${#to_add[@]}" -gt 0 ]; then
        git add "${to_add[@]}"
        msg="COMB_002 FINAL — consolidación Phase 4 vs Phase 5 | $(date -u +%Y%m%d)"
        git commit -m "$msg" && git push && echo "[GIT] Pushed: $msg"
    else
        echo "[GIT] No hay archivos para pushear"
    fi
    cd "$SCRIPT_DIR"
fi

echo ""
echo "================================================================================"
echo "PIPELINE DONE | $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "================================================================================"
echo "Artefactos finales:"
ls -lh COMB002_FINAL_*.{json,csv,md} 2>/dev/null | awk '{print "  "$NF" ("$5")"}'
