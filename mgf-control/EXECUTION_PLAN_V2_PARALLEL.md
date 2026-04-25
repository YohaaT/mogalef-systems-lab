# Plan de Ejecución V2 en Paralelo — BO (80%) + TANK (20%)

**Estado:** Documentado, pendiente de aprobación  
**Fecha creación:** 2026-04-25  
**Autor:** Claude Code

---

## 1. Distribución de Carga (80/20)

### BO (Cloud Server) — 80% de la carga

Procesa **9 combos de 12 totales** (75% exactamente):

| Asset  | TF  | Fase | Duración estimada | Orden |
|--------|-----|------|-------------------|-------|
| ES     | 5m  | 1-5  | ~45 min           | 1     |
| ES     | 10m | 1-5  | ~45 min           | 2     |
| ES     | 15m | 1-5  | ~55 min           | 3     |
| FDAX   | 5m  | 1-5  | ~40 min           | 4     |
| FDAX   | 10m | 1-5  | ~40 min           | 5     |
| MNQ    | 5m  | 1-5  | ~40 min           | 6     |
| MNQ    | 10m | 1-5  | ~45 min           | 7 (HANDOFF) |
| MNQ    | 15m | 1-5  | ~55 min           | 8 (HANDOFF) |
| FDAX   | 15m | 1-5  | ~55 min           | 9 (HANDOFF) |

**BO subtotal:** 6 assets/TF (ES, FDAX 5m+10m, MNQ 5m) + 3 handoff (MNQ 10m+15m, FDAX 15m)  
**BO tiempo total:** ~6-7 horas (sin paralelo entre assets)

### TANK (Local Server) — 20% de la carga

Procesa **3 combos de 12 totales** (25%):

| Asset  | TF  | Fase | Duración estimada | Orden |
|--------|-----|------|-------------------|-------|
| MNQ    | 10m | 1-5  | ~45 min           | 1     |
| MNQ    | 15m | 1-5  | ~55 min           | 2     |
| FDAX   | 15m | 1-5  | ~55 min           | 3     |

**TANK subtotal:** 3 assets/TF  
**TANK tiempo total:** ~2.5-3 horas  
**Handoff ETA:** TANK termina en ~3h, BO aún procesando (en combo 5-6 de 9)

---

## 2. Ejecución Secuencial (Sin Paralelismo Entre Assets)

Ambos servidores ejecutan **secuencialmente por TF**, no en paralelo:

```
BO ejecuta:
  Phase1 ES_5m    → Phase2 ES_5m    → ... → Phase5 ES_5m    (6 fases, ~45min)
  Phase1 ES_10m   → Phase2 ES_10m   → ... → Phase5 ES_10m   (6 fases, ~45min)
  Phase1 ES_15m   → Phase2 ES_15m   → ... → Phase5 ES_15m   (6 fases, ~55min)
  [... continua MNQ/FDAX 5m+10m ...]
  [cuando TANK termine → handoff MNQ 10m+15m, FDAX 15m]

TANK ejecuta (en paralelo con BO):
  Phase1 MNQ_10m  → Phase2 MNQ_10m  → ... → Phase5 MNQ_10m  (6 fases, ~45min)
  Phase1 MNQ_15m  → Phase2 MNQ_15m  → ... → Phase5 MNQ_15m  (6 fases, ~55min)
  Phase1 FDAX_15m → Phase2 FDAX_15m → ... → Phase5 FDAX_15m (6 fases, ~55min)
  [después: espera handoff de BO]
```

**Nota:** Cada asset/TF corre sus 5 fases sin interrumpir → consuma ~45-55 min según complejidad.

---

## 3. Protocolo de Handoff (TANK → BO)

Cuando TANK **termine sus 3 combos** (~3 horas):

**TANK** ejecuta estos 3 combos en secuencia:
```bash
# TANK: fase 1-5 para MNQ 10m, MNQ 15m, FDAX 15m
python3 phase1_V2_impulse_walkforward.py --asset MNQ --timeframe 10m --workers 2
python3 phase1_V2_impulse_walkforward.py --asset MNQ --timeframe 15m --workers 2
python3 phase1_V2_impulse_walkforward.py --asset FDAX --timeframe 15m --workers 2
# [+ phases 2-5 para cada]
# ~ 2.5-3 horas total
```

**BO** estado en ~3h:
- ✅ Completado: ES (5m, 10m, 15m) + FDAX 5m + MNQ 5m = 5 combos
- 🔄 En ejecución: FDAX 10m (combo #5 de 9)
- ⏳ Pendientes: FDAX 10m → MNQ 10m → MNQ 15m → FDAX 15m

**Handoff acción:**

TANK conecta a BO via SSH y **asume** los 3 combos que quedan:

```bash
# TANK envía comando a BO para verificar estado
ssh -i ~/.ssh/B_O.key ubuntu@79.72.62.202 "ps aux | grep phase"

# Después que BO termine FDAX 10m:
# TANK toma MNQ 10m, MNQ 15m, FDAX 15m de la lista de BO
# BO se detiene (si es necesario), TANK continua
```

**Timeline del handoff:**
- T+0h: Ambos inician (BO + TANK en paralelo)
- T+3h: TANK termina 3 combos, inicia handoff
- T+3h-6h: TANK procesa los 3 combos restantes (handoff)
- T+6-7h: BO termina sus primeros 6 combos (sin handoff, si TANK no asume)
- **Total paralelo:** ~7h vs ~10.5h secuencial → **~33% speedup**

---

## 4. Comandos de Ejecución

### En BO (cloud):

```bash
cd /home/ubuntu/mogalef-systems-lab/mgf-control

# Ejecutar 5 fases para cada combo, secuencialmente
# Opción A: Manual (sin script)
for asset in ES ES FDAX MNQ MNQ; do
  for tf in 5m 10m 15m; do
    echo "[BO] Iniciando $asset $tf"
    python3 phase1_V2_impulse_walkforward.py --asset $asset --timeframe $tf --workers 4
    python3 phase2a_V2_horaire_filter.py --asset $asset --timeframe $tf --workers 4
    python3 phase2b_V2_volatility_regime.py --asset $asset --timeframe $tf --workers 4
    python3 phase3_V2_exits_trendstop.py --asset $asset --timeframe $tf --workers 4
    python3 phase4_V2_superstop_granular.py --asset $asset --timeframe $tf --workers 4
    python3 phase5_V2_regime_aware_validation.py --asset $asset --timeframe $tf --workers 4
  done
done

# Opción B: Script de batch (recomendado)
bash run_COMB002_V2_pipeline.sh --assets "ES FDAX MNQ" --timeframes "5m 10m 15m" --workers 4
```

### En TANK (local):

```bash
cd ~/mogalef-systems-lab/mgf-control

# Ejecutar los 3 combos handoff
for asset in MNQ MNQ FDAX; do
  for tf in 10m 15m 15m; do
    echo "[TANK] Iniciando $asset $tf"
    python3 phase1_V2_impulse_walkforward.py --asset $asset --timeframe $tf --workers 2
    python3 phase2a_V2_horaire_filter.py --asset $asset --timeframe $tf --workers 2
    python3 phase2b_V2_volatility_regime.py --asset $asset --timeframe $tf --workers 2
    python3 phase3_V2_exits_trendstop.py --asset $asset --timeframe $tf --workers 2
    python3 phase4_V2_superstop_granular.py --asset $asset --timeframe $tf --workers 2
    python3 phase5_V2_regime_aware_validation.py --asset $asset --timeframe $tf --workers 2
  done
done
```

---

## 5. Monitoreo y Checkpoints

### Checkpoint A (T+1h):
- BO: Debería completar ES_5m, iniciando ES_10m
- TANK: Debería estar en fase 2-3 de MNQ_10m

### Checkpoint B (T+2h):
- BO: Completado ES (5m+10m), en ES_15m
- TANK: Completado MNQ_10m, en MNQ_15m

### Checkpoint C (T+3h):
- BO: Completado ES (5m+10m+15m), en FDAX_5m
- TANK: Completado MNQ (10m+15m) + FDAX_15m → **HANDOFF READY**

### Checkpoint D (T+4.5h):
- BO: En FDAX_10m (combo #5)
- TANK: Asume MNQ_10m, MNQ_15m de BO

### Checkpoint E (T+7h):
- BO + TANK: **Ambos terminados**
- Ejecutar: `consolidate_COMB002_V2_final.py` + `validate_COMB002_V2_holdout.py`

---

## 6. Cómo Ejecutar (SIN COMENZAR AÚN)

### Paso 1: Aprobación
[ ] Usuario revisa y aprueba este plan

### Paso 2: SSH a BO
```bash
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202
cd /home/ubuntu/mogalef-systems-lab/mgf-control
```

### Paso 3: SSH a TANK (terminal separada)
```bash
ssh -i "C:\Users\Yohanny Tambo\.ssh\id_ed25519" ytambo@192.168.1.162
cd ~/mogalef-systems-lab/mgf-control
```

### Paso 4: Ejecutar en paralelo (BO + TANK simultáneamente)
- **En BO:** `bash run_COMB002_V2_pipeline.sh --assets "ES FDAX MNQ" --workers 4`
- **En TANK:** `for asset in MNQ FDAX; do [fases 1-5]; done` (o equivalente)

### Paso 5: Monitoreo cada 60 min (opcional)
```bash
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202 \
  "ps aux | grep phase | grep -v grep | wc -l"
```

---

## 7. Alternativa: Secuencial Puro (Sin Handoff)

Si prefieres ejecutar **solo BO**, sin TANK:

```bash
# BO ejecuta todos los 12 combos secuencialmente
# ~ 10-12 horas total (sin paralelismo)
bash run_COMB002_V2_pipeline.sh --assets "ES FDAX MNQ" --timeframes "5m 10m 15m" --workers 4
```

---

## 8. Resumen

| Métrica | Paralelo (80/20) | Secuencial (BO solo) |
|---------|------------------|----------------------|
| Tiempo total | ~7 horas | ~11 horas |
| BO carga | 6 combos (45-55m c/u) | 12 combos |
| TANK carga | 3 combos (45-55m c/u) | 0 combos |
| Handoff | Sí (TANK → BO) | N/A |
| Speedup | +33% aprox | N/A |
| Utilización recurso | 80/20 BO/TANK | 100 BO, 0 TANK |

---

**PROXIMAMENTE:** Esperar aprobación del usuario antes de ejecutar.

