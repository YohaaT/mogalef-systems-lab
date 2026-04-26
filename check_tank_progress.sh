#!/bin/bash
# Revisa el progreso de los pipelines de optimizacion en TANK via SSH.
# Uso: ./check_tank_progress.sh [host]
# Por defecto conecta al alias 'tank'. Puedes pasar otro host como argumento.

TANK="${1:-tank}"
WORKDIR="$HOME/mogalef-systems-lab/mgf-control"

PIPELINES=(
  "MNQ:15m:001" "MNQ:15m:002"
  "ES:5m:001"   "ES:5m:002"
  "FDAX:5m:001" "FDAX:5m:002"
  "FDAX:10m:001" "FDAX:10m:002"
  "MNQ:5m:001"  "MNQ:5m:002"
  "ES:10m:002"  "MNQ:10m:001"
)

ssh -o ConnectTimeout=10 "$TANK" bash <<REMOTE
set -e
cd "$WORKDIR"

SEP="\$(printf '%0.s-' {1..60})"

echo ""
echo "=== TANK PROGRESS REPORT === \$(date -u '+%Y-%m-%d %H:%M UTC')"
echo "\$SEP"

# --- Procesos activos ---
echo ""
echo "[PROCESOS ACTIVOS]"
PROCS=\$(ps aux | grep python3 | grep -v grep | wc -l)
if [ "\$PROCS" -gt 0 ]; then
  echo "  \$PROCS proceso(s) python3 corriendo:"
  ps aux | grep python3 | grep -v grep | awk '{printf "  PID %-7s CPU %-5s MEM %-5s %s\n", \$2, \$3, \$4, \$11}'
else
  echo "  Sin procesos python3 activos."
fi

# --- Resultados por fase ---
echo ""
echo "[RESULTADOS POR FASE]"
for DIR in phase1_results phase2a_results phase2b_results phase3_results phase4_results phase5_results; do
  if [ -d "\$DIR" ]; then
    COUNT=\$(find "\$DIR" -name '*.json' 2>/dev/null | wc -l)
    printf "  %-22s %3d archivos JSON\n" "\$DIR" "\$COUNT"
  else
    printf "  %-22s (no existe aun)\n" "\$DIR"
  fi
done

# --- Estado por pipeline ---
echo ""
echo "[ESTADO POR PIPELINE]"
printf "  %-18s %-8s %-8s %-8s %-8s %-8s %-8s %s\n" \
  "PIPELINE" "Ph1" "Ph2a" "Ph2b" "Ph3" "Ph4" "Ph5" "LOG"

PIPELINES=(
  "MNQ:15m:001" "MNQ:15m:002"
  "ES:5m:001"   "ES:5m:002"
  "FDAX:5m:001" "FDAX:5m:002"
  "FDAX:10m:001" "FDAX:10m:002"
  "MNQ:5m:001"  "MNQ:5m:002"
  "ES:10m:002"  "MNQ:10m:001"
)

for P in "\${PIPELINES[@]}"; do
  IFS=':' read ASSET TF COMB <<< "\$P"
  TAG="\${ASSET}_\${TF}_\${COMB}"
  LABEL="\${ASSET} \${TF} C\${COMB}"

  ph1="-"; ph2a="-"; ph2b="-"; ph3="-"; ph4="-"; ph5="-"
  [ -f "phase1_results/\${TAG}_top10.json" ]  && ph1="OK"
  [ -f "phase2a_results/\${TAG}_top10.json" ] && ph2a="OK"
  [ -f "phase2b_results/\${TAG}_top10.json" ] && ph2b="OK"
  [ -f "phase3_results/\${TAG}_top10.json" ]  && ph3="OK"
  [ -f "phase4_results/\${TAG}_top10.json" ]  && ph4="OK"
  [ -f "phase5_results/\${TAG}_top10.json" ]  && ph5="OK"

  # Estado del log
  LOGFILE=""
  for CANDIDATE in \
    "logs/tank_VEC_OPT_\${TAG}.log" \
    "logs/tank_\${TAG}.log"; do
    [ -f "\$CANDIDATE" ] && LOGFILE="\$CANDIDATE" && break
  done

  if [ -n "\$LOGFILE" ]; then
    LAST=\$(tail -1 "\$LOGFILE" 2>/dev/null)
    if echo "\$LAST" | grep -qi "OK\|complete"; then
      STATUS="DONE"
    elif echo "\$LAST" | grep -qi "error\|traceback\|exception"; then
      STATUS="ERROR"
    else
      STATUS="RUNNING"
    fi
  else
    STATUS="NO LOG"
  fi

  printf "  %-18s %-8s %-8s %-8s %-8s %-8s %-8s %s\n" \
    "\$LABEL" "\$ph1" "\$ph2a" "\$ph2b" "\$ph3" "\$ph4" "\$ph5" "\$STATUS"
done

# --- Ultimas lineas de logs con error o recientes ---
echo ""
echo "[ULTIMAS LINEAS DE LOGS CON ACTIVIDAD]"
if ls logs/*.log 2>/dev/null | head -1 > /dev/null 2>&1; then
  for LOG in \$(ls -t logs/*.log 2>/dev/null | head -5); do
    echo ""
    echo "  >> \$LOG"
    tail -3 "\$LOG" | sed 's/^/     /'
  done
else
  echo "  Sin logs disponibles aun."
fi

echo ""
echo "\$SEP"
echo "Fin del reporte."
echo ""
REMOTE
