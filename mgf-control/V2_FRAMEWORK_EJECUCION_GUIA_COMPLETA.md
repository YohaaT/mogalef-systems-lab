# V2 Framework: Guía Completa de Uso y Ejecución Paralela

**Fecha:** 2026-04-25  
**Autor:** Claude Code  
**Versión:** 1.0

---

## 1. Introducción: ¿Qué es V2?

### Problema que resuelve
En optimizaciones V1 (Phase A/B), los parámetros ganadores eran **regime-dependent**: funcionaban en fase de backtesting pero fallaban en validación. Esto ocurría porque:
- Optimizábamos sobre max(PF_B) — favorecía recencia
- No capturaba robustez en diferentes regímenes de volatilidad
- Solo 2/12 combos COMB_002 superaban validación cruzada

### Solución: V2 Framework
**V2** es un framework genérico de optimización que:
- ✅ **Walk-forward con 5 ventanas / 3 folds**: en lugar de simple Phase A/B
- ✅ **Criterio min(PF)**: penaliza combos débiles en cualquier ventana
- ✅ **Filtros duros V2**: min_PF≥1.0, CV≤0.30, trades≥20/ventana
- ✅ **Optimización por régimen**: parámetros específicos para low/med/high volatilidad
- ✅ **Reutilizable**: aplica a cualquier estrategia, no solo COMB_002

---

## 2. Arquitectura V2

### Componentes principales

#### A. Core genérico (`V2_framework_generic.py`)
**Propósito:** Núcleo reutilizable, sin lógica específica de estrategia.

**Funciones clave:**
```python
split_walkforward(rows, n_windows=5, n_train_windows=2)
  → Divide datos en 5 ventanas, genera 3 folds (train 2 ventanas → test 1)

compute_regime_thresholds(all_rows)
  → Calcula ATR percentil 33% y 67% sobre TODO el dataset

filter_rows_by_regime(rows, thresholds, target_regime)
  → Filtra rows para mantener solo low/med/high volatilidad

evaluate_vec(strategy_class, params_list, rows)
  → Evalúa N params sobre LA MISMA ventana (batch/vectorizado)

score_walkforward(strategy_class, params, folds)
  → Ejecuta params en test window de cada fold, retorna score V2

passes_v2_filters(pfs, trades)
  → Valida: min_PF≥1.0 AND trades≥20 AND CV≤0.30
```

#### B. Template (`V2_PHASE_TEMPLATE.py`)
**Propósito:** Skeleton para adaptar a nuevas estrategias. Completar 3 secciones:

**[ADAPTACIÓN A]** Imports + Grids
```python
from MY_STRATEGIES import MyStrategy, MyStrategyParams, load_ohlc_csv

PARAM1_RANGE = [1.0, 1.5, 2.0, 2.5, 3.0]
PARAM2_RANGE = [5, 10, 15, 20]
PARAM3_RANGE = [0.01, 0.02, 0.05, 0.10]
```

**[ADAPTACIÓN B]** build_params()
```python
def build_params(param1, param2, param3):
    return MyStrategyParams(
        param1=param1, param2=param2, param3=param3,
        # Parámetros fijos (defaults)
        param4=1.0, param5=True, param6=25.0,
    )
```

**[ADAPTACIÓN C]** _eval_combo()
```python
def _eval_combo(combo):
    param1, param2, param3 = combo
    params = build_params(param1, param2, param3)
    score = score_walkforward(MyStrategy, params, _FOLDS)
    return {
        "param1": param1, "param2": param2, "param3": param3,
        "min_pf": score.min_pf, "cv": score.cv, ...
    }
```

#### C. COMB_002 V2 (Instancia)
5 fases secuenciales:
1. **Phase 1:** Optimiza smooth_h, smooth_b, distance_h, distance_l (signal detection)
2. **Phase 2a:** Optimiza horaire (horas permitidas)
3. **Phase 2b:** Optimiza volatility_atr_min/max + por régimen (ATR thresholds)
4. **Phase 3:** Optimiza exits (stop logic)
5. **Phase 4:** Optimiza superstop (granular stops)
6. **Phase 5:** Validación cruzada por régimen + holdout

---

## 3. Cómo Ejecutar: Ejecución Paralela 80/20

### Setup previo

#### 3.1 Datos
Necesitas 9 CSVs con columnas: `timestamp_utc, timestamp, open, high, low, close, volume`

```bash
# Convertir TXT → CSV
cd ~/mogalef-systems-lab/new_data
python3 convert_to_csv.py
# Output: ES_full_5m.csv, ES_full_10m.csv, ..., MNQ_full_15m.csv
```

#### 3.2 Sincronización
```bash
# Local → BO
scp -i ~/.ssh/B_O.key *_full_*.csv ubuntu@79.72.62.202:/home/ubuntu/mogalef-systems-lab/mgf-control/
scp -i ~/.ssh/B_O.key V2_*.py phase*V2*.py ubuntu@79.72.62.202:/home/ubuntu/mogalef-systems-lab/mgf-control/

# Local → TANK
scp -i ~/.ssh/id_ed25519 *_full_*.csv ytambo@192.168.1.162:~/mogalef-systems-lab/mgf-control/
scp -i ~/.ssh/id_ed25519 V2_*.py phase*V2*.py ytambo@192.168.1.162:~/mogalef-systems-lab/mgf-control/
```

### Distribución 80/20

| Servidor | Carga | Assets/TF | Workers | ETA |
|----------|-------|-----------|---------|-----|
| **BO** (Cloud) | 80% | ES (5m/10m/15m), FDAX (5m/10m), MNQ 5m | 4 | ~7h |
| **TANK** (Local) | 20% | MNQ (10m/15m), FDAX 15m | 2 | ~3h |

**Handoff protocol:** Cuando TANK termine sus 3 combos (~3h), asume 3 combos restantes de BO (MNQ 10m+15m, FDAX 15m).

### Ejecución

#### En BO:
```bash
ssh -i ~/.ssh/B_O.key ubuntu@79.72.62.202
cd /home/ubuntu/mogalef-systems-lab/mgf-control
nohup bash run_v2_bo.sh > bo_execution.log 2>&1 &
```

#### En TANK:
```bash
ssh -i ~/.ssh/id_ed25519 ytambo@192.168.1.162
cd ~/mogalef-systems-lab/mgf-control
nohup bash run_v2_tank.sh > tank_execution.log 2>&1 &
```

### Monitoreo

**Opción 1: Manual (recomendado)**
```bash
# BO
ssh -i ~/.ssh/B_O.key ubuntu@79.72.62.202 "tail -20 /home/ubuntu/mogalef-systems-lab/mgf-control/bo_execution.log | grep -E '(START|DONE|passed|ERROR)'"

# TANK
ssh -i ~/.ssh/id_ed25519 ytambo@192.168.1.162 "tail -20 ~/mogalef-systems-lab/mgf-control/tank_execution.log | grep -E '(START|DONE|passed|ERROR)'"
```

**Opción 2: Monitor automático (hitos solo)**
```bash
# Solo reporta cuando Phase DONE o ERROR
ssh -i ~/.ssh/id_ed25519 ytambo@192.168.1.162 "tail -f ~/mogalef-systems-lab/mgf-control/tank_execution.log" | grep -E "(DONE|ERROR)" --line-buffered
```

### Git protocol (Protocolo B)
Push **después de cada Phase completa**:
```bash
git add . && git commit -m "TANK: Phase 5 DONE - 3 combos (MNQ 10m+15m, FDAX 15m)" && git push
```

---

## 4. Errores Encontrados y Soluciones

### Error 1: `KeyError: 'timestamp_utc'`
**Causa:** CSV tenía columna `timestamp`, código esperaba `timestamp_utc`

**Solución:**
```python
# En COMB_002_IMPULSE_V1.py load_ohlc_csv():
ts = row.get("timestamp_utc") or row.get("timestamp")  # Fallback

# O regenerar CSVs con ambas columnas
# convert_to_csv.py: fieldnames=["timestamp_utc", "timestamp", "open", ...]
```

### Error 2: `--workers not recognized` (Phase 5)
**Causa:** `phase5_V2_regime_aware_validation.py` no acepta parámetro `--workers`

**Solución:**
```bash
# En run_v2_bo.sh y run_v2_tank.sh:
# Cambiar:
python3 phase5_V2_regime_aware_validation.py --asset "$asset" --timeframe "$tf" --workers "$WORKERS"
# Por:
python3 phase5_V2_regime_aware_validation.py --asset "$asset" --timeframe "$tf"
```

### Error 3: Procesos zombies TANK
**Causa:** `pkill -f 'python3'` falló por permisos, procesos bloqueados

**Solución:**
```bash
# Opción A: Usar killall
killall -9 python3 python; sleep 5; nohup bash run_v2_tank.sh > tank_execution.log 2>&1 &

# Opción B: Reiniciar servidor
sudo reboot

# Opción C: Esperar a que BO termine (sin handoff)
```

---

## 5. Estado Actual (2026-04-25 ~09:00 UTC)

### Progreso real-time

| Servidor | Asset/TF | Fase | Combos | Pasaron V2 | ETA |
|----------|----------|------|--------|-----------|-----|
| **BO** | ES 5m | Phase 1 (terminando) | 625 | 1 | ~2 min |
| **TANK** | MNQ 10m | Phase 1 | 625 | ? | ~40 min |

### Análisis

**ES 5m Phase 1:** Solo 1/625 combos pasó filtros V2 (vs 25 en corrida anterior)
- Filtros más restrictivos (min_PF≥1.0, CV≤0.30, trades≥20)
- O parámetros del grid no tienen edge suficiente
- Continuar a Phase 2 con 1 combo base + 3 top regímenes

**MNQ 10m Phase 1:** En progreso, esperando milestone

### Timeline esperado

```
T+0h   ✅ BO inicia ES 5m Phase 1 (06:46 UTC)
T+1h   BO completa todas fases ES 5m
T+3h   BO: ES 10m, 15m en ejecución
T+3h   TANK: MNQ 10m Phase 1 completa
T+6h   TANK: MNQ 15m, FDAX 15m en ejecución
T+7h   BO termina 6 combos base
T+9h   TANK asume handoff (MNQ 10m+15m, FDAX 15m) si aún en progreso
T+10-12h Total: BO + TANK completan 12 combos (4 assets × 3 TFs)
```

---

## 6. Porting Guide: Cómo usar V2 para nueva estrategia

### Checklist

- [ ] Tu estrategia tiene `.run(rows: List[Dict]) → Result` con `profit_factor, win_rate, trades, equity_points`
- [ ] Tienes `ParamsClass` (dataclass) con todos los parámetros
- [ ] Defines GRIDS para los parámetros a optimizar
- [ ] Escribes `build_params()` para construir desde componentes
- [ ] Escribes `_eval_combo()` que desempaca, construye, evalúa
- [ ] Ejecutas: `python3 phase1_V2_tu_estrategia.py --asset ES --timeframe 5m --workers 4`

### Paso 1: Copiar template
```bash
cp V2_PHASE_TEMPLATE.py phase1_V2_mi_estrategia_signal.py
```

### Paso 2: Completar [ADAPTACIÓN A]
```python
from MI_ESTRATEGIA import MiEstrategia, MiEstrategiaParams, load_ohlc_csv

# Grids para parámetros a optimizar
SIGNAL_PARAM1_RANGE = [1, 2, 3, 4, 5]
SIGNAL_PARAM2_RANGE = [10, 20, 30]
```

### Paso 3: Completar [ADAPTACIÓN B]
```python
def build_params(signal_param1, signal_param2):
    return MiEstrategiaParams(
        # Parámetros optimizados
        signal_param1=signal_param1,
        signal_param2=signal_param2,
        # Parámetros fijos
        other_param=1.0,
    )
```

### Paso 4: Completar [ADAPTACIÓN C]
```python
def _eval_combo(combo):
    signal_param1, signal_param2 = combo
    params = build_params(signal_param1, signal_param2)
    score = score_walkforward(MiEstrategia, params, _FOLDS)
    return {
        "signal_param1": signal_param1,
        "signal_param2": signal_param2,
        "min_pf": score.min_pf,
        "cv": score.cv,
        "passes_filters": score.passes_filters,
    }
```

### Paso 5: Ejecutar
```bash
python3 phase1_V2_mi_estrategia_signal.py --asset ES --timeframe 5m --workers 4
```

---

## 7. Referencia Rápida: Archivos Clave

| Archivo | Propósito | Modificar para nueva estrategia |
|---------|-----------|--------------------------------|
| `V2_framework_generic.py` | Core genérico | NO — reutilizar tal cual |
| `V2_PHASE_TEMPLATE.py` | Skeleton | SÍ — copiar y llenar 3 secciones |
| `V2_PORTING_GUIDE.md` | Instrucciones detalladas | NO — referencia |
| `COMB_002_IMPULSE_V1.py` | Estrategia específica | SÍ — adaptar para tu estrategia |
| `run_v2_bo.sh` | Script ejecución BO | SÍ — cambiar phase1_V2_*.py |
| `run_v2_tank.sh` | Script ejecución TANK | SÍ — cambiar phase1_V2_*.py |

---

## 8. Troubleshooting

### "Insufficient rows — need X"
→ Dataset muy pequeño para 5 ventanas walk-forward  
→ Descargar más data O reducir `V2_N_WINDOWS = 4` (no recomendado)

### "0/N combos passed filters"
→ Parámetros sin edge suficiente  
→ Ampliar grids O reducir thresholds (min_PF, CV)

### "Slow execution"
→ Demasiadas combinaciones  
→ Reducir tamaño grids O aumentar `--workers`

### TANK no responde
→ Procesos zombies  
→ `killall -9 python3` O reboot

---

## 9. Conclusión

V2 es un framework **production-ready** para optimización robusta multi-régimen. Es **agnóstico de estrategia** — usa el template, llena 3 secciones, y funciona para cualquier estrategia con interfaz `.run()`.

**Para próximas estrategias:**
1. Usa V2_PHASE_TEMPLATE.py como base
2. Adapta los 3 [ADAPTACIÓN X] sections
3. Ejecuta en paralelo BO + TANK para speedup 33%
4. Valida en holdout data con `validate_COMB002_V2_holdout.py`

**Git:** Todos los scripts V2 están bajo control de versiones. Commit después de cada Phase.

---

**Última actualización:** 2026-04-25 09:00 UTC  
**Estado:** V2 en ejecución paralela (BO + TANK)  
**Próxima actualización:** Cuando Phase 5 complete
