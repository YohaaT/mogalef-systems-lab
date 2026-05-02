#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="${ASSETS:-ES,FDAX,NQ}"
TIMEFRAMES="${TIMEFRAMES:-15m,10m,5m}"
WORKERS="${WORKERS:-3}"
LANES="${LANES:-accumulated,independent}"
INDEPENDENT_TIMEFRAMES="${INDEPENDENT_TIMEFRAMES:-$TIMEFRAMES}"
GIT_SYNC="${GIT_SYNC:-1}"
PHASE2A_DIR="${PHASE2A_DIR:-$ROOT/outputs/contract_phase2a_signal_madrid}"
OUT_DIR="${OUT_DIR:-$ROOT/outputs/contract_phase2a_forward_dual}"
LOG_DIR="$ROOT/logs"
RUNNER="$ROOT/scripts/run_COMB002_contract_phase2a_forward_dual.py"
HOST="$(hostname -s 2>/dev/null || hostname)"
RUN_LOG="$LOG_DIR/contract_phase2a_forward_dual_${HOST}.log"
PID_FILE="$LOG_DIR/contract_phase2a_forward_dual_${HOST}.pid"

mkdir -p "$LOG_DIR" "$OUT_DIR"

if [[ "$GIT_SYNC" == "1" ]] && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" pull --ff-only >/dev/null 2>&1 || true
fi

complete=1
lane_enabled() {
  [[ ",$LANES," == *",$1,"* ]]
}

independent_tf_enabled() {
  [[ ",$INDEPENDENT_TIMEFRAMES," == *",$1,"* ]]
}

for tf in ${TIMEFRAMES//,/ }; do
  for asset in ${ASSETS//,/ }; do
    stem="COMB002_contract_${asset}_${tf}_friday_to_expiry_week_monday_label_left"
    acc="$OUT_DIR/$asset/$tf/accumulated/${stem}_phase5_accumulated_validation.json"
    ind="$OUT_DIR/$asset/$tf/independent_from_phase2a/${stem}_phase4_from_phase1_stops_top_params.json"
    if lane_enabled accumulated && [[ ! -f "$acc" ]]; then
      complete=0
      break 2
    fi
    if lane_enabled independent && independent_tf_enabled "$tf" && [[ ! -f "$ind" ]]; then
      complete=0
      break 2
    fi
  done
done

if [[ "$complete" -eq 1 ]]; then
  echo "[monitor] already complete: $ASSETS / $TIMEFRAMES"
  exit 0
fi

if pgrep -af "python[0-9.]* .*run_COMB002_contract_phase2a_forward_dual.py" >/dev/null 2>&1; then
  echo "[monitor] runner already active"
  exit 0
fi

echo "[monitor] starting dual-lane runner"
nohup python3 "$RUNNER" \
  --assets "$ASSETS" \
  --timeframes "$TIMEFRAMES" \
  --phase2a-dir "$PHASE2A_DIR" \
  --out-dir "$OUT_DIR" \
  --lanes "$LANES" \
  --independent-timeframes "$INDEPENDENT_TIMEFRAMES" \
  --workers "$WORKERS" \
  > "$RUN_LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "[monitor] pid=$(cat "$PID_FILE") log=$RUN_LOG"
