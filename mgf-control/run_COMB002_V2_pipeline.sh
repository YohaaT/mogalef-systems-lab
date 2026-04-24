#!/bin/bash
# COMB_002_IMPULSE V2 — Pipeline end-to-end con walk-forward + regímenes
#
# Ejecuta en BATCH POR TIMEFRAME (primero todos los 5m, luego 10m, luego 15m)
# dentro de cada batch: 4 workers en paralelo (uno por activo).
#
# Phases:
#   Phase 1 → 2A → 2B → 3 → 4 → 5    (por cada asset/TF, secuencial)
#   Consolidador → Holdout → Git push  (al final, una vez)
#
# Uso:
#   bash run_COMB002_V2_pipeline.sh
#   bash run_COMB002_V2_pipeline.sh --no-push
#   bash run_COMB002_V2_pipeline.sh --only-tf 5m        # solo 5m
#   bash run_COMB002_V2_pipeline.sh --only-asset ES     # solo ES
#   bash run_COMB002_V2_pipeline.sh --workers 2          # workers por proceso

set -e

PUSH=1
WORKERS_PER_PROC=1
ONLY_TF=""
ONLY_ASSET=""
SKIP_HOLDOUT=0

for arg in "$@"; do
    case "$arg" in
        --no-push)          PUSH=0 ;;
        --skip-holdout)     SKIP_HOLDOUT=1 ;;
        --only-tf=*)        ONLY_TF="${arg#*=}" ;;
        --only-tf)          shift; ONLY_TF="$1" ;;
        --only-asset=*)     ONLY_ASSET="${arg#*=}" ;;
        --only-asset)       shift; ONLY_ASSET="$1" ;;
        --workers=*)        WORKERS_PER_PROC="${arg#*=}" ;;
        --workers)          shift; WORKERS_PER_PROC="$1" ;;
        -h|--help)
            grep "^#" "$0" | head -25
            exit 0
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ASSETS=("ES" "MNQ" "YM" "FDAX")
TIMEFRAMES=("5m" "10m" "15m")

if [ -n "$ONLY_TF" ]; then TIMEFRAMES=("$ONLY_TF"); fi
if [ -n "$ONLY_ASSET" ]; then ASSETS=("$ONLY_ASSET"); fi

echo "================================================================================"
echo "COMB_002 V2 — Walk-forward + Regime Pipeline | $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "================================================================================"
echo "Assets     : ${ASSETS[*]}"
echo "Timeframes : ${TIMEFRAMES[*]}"
echo "Workers/proc: $WORKERS_PER_PROC"
echo ""

# ── Ejecuta las 5 phases secuenciales para un combo (asset, tf) ──────────────
run_combo() {
    local asset="$1"
    local tf="$2"
    local wk="$3"
    local log="/tmp/v2_${asset}_${tf}.log"

    echo "[START] $asset $tf → log: $log"
    {
        echo "=== $(date -u) === Phase 1: Signal"
        python3 phase1_V2_signal_walkforward.py --asset "$asset" --timeframe "$tf" --workers "$wk" || exit 1
        echo "=== $(date -u) === Phase 2A: Horaire"
        python3 phase2a_V2_horaire_walkforward.py --asset "$asset" --timeframe "$tf" --workers "$wk" || exit 1
        echo "=== $(date -u) === Phase 2B: Volatility × Regime"
        python3 phase2b_V2_volatility_regime.py --asset "$asset" --timeframe "$tf" --workers "$wk" || exit 1
        echo "=== $(date -u) === Phase 3: Exits per regime"
        python3 phase3_V2_exits_walkforward.py --asset "$asset" --timeframe "$tf" --workers "$wk" || exit 1
        echo "=== $(date -u) === Phase 4: Stops per regime"
        python3 phase4_V2_stops_walkforward.py --asset "$asset" --timeframe "$tf" --workers "$wk" || exit 1
        echo "=== $(date -u) === Phase 5: Regime-aware validation"
        python3 phase5_V2_regime_aware_validation.py --asset "$asset" --timeframe "$tf" || exit 1
        echo "=== $(date -u) === V2 PIPELINE DONE for $asset $tf"
    } > "$log" 2>&1
    rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "[DONE]  $asset $tf"
    else
        echo "[FAIL]  $asset $tf (check $log)"
    fi
}

# ── BATCH POR TIMEFRAME: primero todos los 5m, luego 10m, luego 15m ─────────
# Dentro de cada batch, workers paralelos por asset
for tf in "${TIMEFRAMES[@]}"; do
    echo ""
    echo "================================================================================"
    echo "BATCH TIMEFRAME: $tf | $(date -u +'%H:%M:%S UTC')"
    echo "================================================================================"

    pids=()
    for asset in "${ASSETS[@]}"; do
        run_combo "$asset" "$tf" "$WORKERS_PER_PROC" &
        pids+=($!)
    done

    for pid in "${pids[@]}"; do
        wait "$pid" || echo "[WARN] pid $pid exited non-zero"
    done

    echo "[BATCH DONE] $tf | $(date -u +'%H:%M:%S UTC')"
done

# ── Consolidador final ──────────────────────────────────────────────────────
echo ""
echo "--- CONSOLIDATOR ---"
python3 consolidate_COMB002_V2_final.py

# ── Hold-out (si hay data phase_C) ───────────────────────────────────────────
if [ "$SKIP_HOLDOUT" -eq 0 ]; then
    echo ""
    echo "--- HOLD-OUT (Phase C) ---"
    python3 validate_COMB002_V2_holdout.py || echo "[WARN] holdout validator falló (¿falta phase_C data?)"
fi

# ── Git push ────────────────────────────────────────────────────────────────
if [ "$PUSH" -eq 1 ]; then
    echo ""
    echo "--- GIT PUSH ---"
    cd ..
    to_add=()
    for f in \
        mgf-control/COMB002_V2_FINAL_PARAMS.json \
        mgf-control/COMB002_V2_FINAL_decisions.csv \
        mgf-control/COMB002_V2_holdout_results.csv \
        mgf-control/COMB002_V2_holdout_report.md; do
        [ -f "$f" ] && to_add+=("$f")
    done
    # También los top_params.json por phase (para auditoría)
    for f in mgf-control/COMB002_V2_phase*_top_params*.json \
             mgf-control/COMB002_V2_phase5_*_final_by_regime.json; do
        [ -f "$f" ] && to_add+=("$f")
    done

    if [ "${#to_add[@]}" -gt 0 ]; then
        git add "${to_add[@]}"
        msg="COMB_002 V2 — walk-forward + regime | $(date -u +%Y%m%d)"
        git commit -m "$msg" && git push && echo "[GIT] Pushed: $msg"
    fi
    cd "$SCRIPT_DIR"
fi

echo ""
echo "================================================================================"
echo "V2 PIPELINE COMPLETE | $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "================================================================================"
ls -lh COMB002_V2_FINAL_*.{json,csv} 2>/dev/null | awk '{print "  "$NF" ("$5")"}'
