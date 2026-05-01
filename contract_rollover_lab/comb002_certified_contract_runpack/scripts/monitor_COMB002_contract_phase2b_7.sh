#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="${ASSETS:-ES,FDAX,NQ}"
TIMEFRAMES="${TIMEFRAMES:-15m,10m,5m}"
WORKERS="${WORKERS:-3}"
PHASE2A_DIR="${PHASE2A_DIR:-$ROOT/outputs/contract_phase2a_signal_madrid}"
OUT_DIR="${OUT_DIR:-$ROOT/outputs/contract_phase2b_7}"
LOG_DIR="$ROOT/logs"
RUNNER="$ROOT/scripts/run_COMB002_contract_phase2b_7_continue.py"
STAMP="$(hostname -s 2>/dev/null || hostname)"
RUN_LOG="$LOG_DIR/contract_phase2b_7_${STAMP}.log"
PID_FILE="$LOG_DIR/contract_phase2b_7_${STAMP}.pid"

mkdir -p "$LOG_DIR" "$OUT_DIR"

complete=1
for tf in ${TIMEFRAMES//,/ }; do
  for asset in ${ASSETS//,/ }; do
    stem="COMB002_contract_${asset}_${tf}_friday_to_expiry_week_monday_label_left"
    phase7="$OUT_DIR/$asset/$tf/${stem}_phase7_consistency_summary.json"
    if [[ ! -f "$phase7" ]]; then
      complete=0
      break 2
    fi
  done
done

if [[ "$complete" -eq 1 ]]; then
  echo "[monitor] already complete: $ASSETS / $TIMEFRAMES"
  exit 0
fi

if pgrep -af "run_COMB002_contract_phase2b_7_continue.py" >/dev/null 2>&1; then
  echo "[monitor] runner already active"
  exit 0
fi

echo "[monitor] starting continuation runner"
nohup python3 "$RUNNER" \
  --assets "$ASSETS" \
  --timeframes "$TIMEFRAMES" \
  --phase2a-dir "$PHASE2A_DIR" \
  --out-dir "$OUT_DIR" \
  --workers "$WORKERS" \
  > "$RUN_LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "[monitor] pid=$(cat "$PID_FILE") log=$RUN_LOG"
