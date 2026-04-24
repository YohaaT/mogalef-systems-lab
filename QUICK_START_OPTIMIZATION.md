# QUICK START: OPTIMIZATION EXECUTION

**Cuando el usuario diga:** "Optimiza COMB_002" → Usa este documento  
**Referencia completa:** UNIVERSAL_OPTIMIZATION_FRAMEWORK_v1.md  
**Configuración específica:** COMB_002_IMPULSE_PHASE_CONFIG.json

---

# RECURSOS (Raw Material)

Los recursos de las estrategias (EasyLanguage, indicadores, señales, stops) están en:
```
C:\Users\Yohanny Tambo\Desktop\Bo_Oracle\mogalef-systems-lab\raw_material\
```
Archivos clave para COMB_002_IMPULSE:
- `EL_STPMT_DIV.txt` → Señal de divergencia
- `EL_Intelligent_Scalping_Target.txt` → Motor principal de salidas
- `Super_Stop_Long.txt` / `Super_Stop_Short.txt` → SuperStop
- `EL_Block_Hours_2019_b.txt` → Filtro horario Mogalef

---

# SSH CREDENTIALS & REMOTE EXECUTION

## SSH Configuration
```
SSH Config: C:\Users\Yohanny Tambo\.ssh\config
SSH Key: C:\Users\Yohanny Tambo\.ssh\B_O.key

Hosts:
  - BO: 79.72.62.202 (user: ubuntu)
  - TANK: 192.168.1.162 (user: ytambo)
```

## Connection Test
```bash
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ytambo@192.168.1.162
```

---

# RESUMEN EJECUTIVO

## ¿Qué es?
Un proceso automático de 4 fases que optimiza una estrategia de trading multi-activo (ES, MNQ, YM, FDAX) y multi-timeframe (5m, 10m, 15m) sin hacer preguntas.

## ¿Cuánto tarda?
**~110 minutos = 1h 50m total** (con paralelismo BO 80% / TANK 20%)

## ¿Cuál es el resultado?
Archivo JSON con parámetros óptimos para cada activo/timeframe, listo para compilar en NinjaTrader 8.

---

# FASES DE OPTIMIZACIÓN

## ✅ FASE 1: Optimización de Señal (60 min)
**Grid:** 625 combinaciones por activo  
**Qué optimiza:** STPMT divergence parameters (smooth_h, smooth_b, distance_max)  
**Salida:** `phase1_COMB_002_IMPULSE_{asset}_{timeframe}_best_params.json`

**Distribución de Carga: 80% BO / 20% TANK (PARALELO)**

```
BO (80% = 500 combos):
  ES 5m:   500 combos Block 1 → ssh -i key ubuntu@BO → 15 min
  
TANK (20% = 125 combos en paralelo):
  ES 5m:   125 combos Block 2 → ssh -i key ytambo@TANK → ~4 min
  MNQ 5m:  625 combos Block 1 → ssh -i key ubuntu@BO → 15 min
  
BO (siguiente):
  MNQ 5m:  125 combos Block 2 → TANK paralelo → ~4 min
  YM 10m:  625 combos Block 1 → BO → 15 min
  ... (repetir para FDAX)

Consolidar: 5 min (BO local)
Total: 60 min (con paralelismo)
```

**Ejecución exacta:**
```bash
# BO ejecuta Bloque 1 (500 combos) mientras TANK ejecuta Bloque 2 (125 combos)
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202 \
  "python phase1_vectorized_runner.py --asset ES --block 1 --combos 500"

# EN PARALELO (TANK):
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ytambo@192.168.1.162 \
  "python phase1_vectorized_runner.py --asset ES --block 2 --combos 125"
```

**Éxito:** Robustness >= 0.80 (Phase_B_PF / Phase_A_PF >= 0.80)

---

## ✅ FASE 2: Optimización de Filtros Contexto (15 min)
**Grid:** 12 combinaciones (Horaire + Diario)  
**Locked:** Phase 1 best_params (NO cambiar)  
**Qué optimiza:**
- Horaire (horas del día permitidas): 6 opciones
- Blocked weekdays (días bloqueados): 2 opciones

```
Combos: 6 × 2 = 12
Tiempo: ~3 min (secuencial)
Consolidar: 2 min
Total: 15 min (para 4 activos)
```

**Características COMB_002:**
- ✅ SÍ Horaire filter (9-17 + 20-22 per Mogalef)
- ✅ SÍ Weekday filter (no martes)
- ❌ NO Trend Filter (COMB_001 feature)
- ❌ NO Volatility Filter (kills IMPULSE performance)

**Distribución de Carga: 80% BO / 20% TANK (PARALELO)**

```
BO (80% = 10 combos):
  ES 5m:   10 combos Block 1 → ssh -i key ubuntu@BO → 2 min
  
TANK (20% = 2 combos en paralelo):
  ES 5m:   2 combos Block 2 → ssh -i key ytambo@TANK → ~1 min
  MNQ 5m:  10 combos Block 1 → ssh -i key ubuntu@BO → 2 min
  
BO (siguiente):
  MNQ 5m:  2 combos Block 2 → TANK paralelo → ~1 min
  YM 10m:  10 combos Block 1 → BO → 2 min
  YM 10m:  2 combos Block 2 → TANK paralelo → ~1 min
  FDAX 5m: 10 combos Block 1 → BO → 2 min
  FDAX 5m: 2 combos Block 2 → TANK paralelo → ~1 min

Consolidar: 2 min (BO local)
Total: 15 min (con paralelismo)
```

**Ejecución exacta:**
```bash
# BO ejecuta Bloque 1 (10 combos) mientras TANK ejecuta Bloque 2 (2 combos)
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202 \
  "python phase2_contexto_runner.py --asset ES --block 1 --combos 10"

# EN PARALELO (TANK):
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ytambo@192.168.1.162 \
  "python phase2_contexto_runner.py --asset ES --block 2 --combos 2"
```

**Éxito:** Robustness >= 0.80

---

## ✅ FASE 3: Optimización de Salidas (20 min)
**Grid:** 150 combinaciones  
**Locked:** Phase 1 + Phase 2 best_params  
**Qué optimiza:**
- target_atr_multiplier (5-15 ATR): 5 valores
- scalping_target_coef_volat (2-6): 5 valores
- timescan_bars (10-20): 6 valores

```
Combos: 5 × 5 × 6 = 150
Tiempo: ~10 min (vectorizado)
Consolidar: 5 min
Total: 15 min (extrapolado para 4 activos)
```

**Nota:** Intelligent Scalping Target es el motor principal de COMB_002 (Mogalef)

**Distribución de Carga: 80% BO / 20% TANK (PARALELO)**

```
BO (80% = 120 combos):
  ES 5m:   120 combos Block 1 → ssh -i key ubuntu@BO → 8 min
  
TANK (20% = 30 combos en paralelo):
  ES 5m:   30 combos Block 2 → ssh -i key ytambo@TANK → ~2 min
  MNQ 5m:  120 combos Block 1 → ssh -i key ubuntu@BO → 8 min
  
BO (siguiente):
  MNQ 5m:  30 combos Block 2 → TANK paralelo → ~2 min
  YM 10m:  120 combos Block 1 → BO → 8 min
  YM 10m:  30 combos Block 2 → TANK paralelo → ~2 min
  FDAX 5m: 120 combos Block 1 → BO → 8 min
  FDAX 5m: 30 combos Block 2 → TANK paralelo → ~2 min

Consolidar: 5 min (BO local)
Total: 20 min (con paralelismo)
```

**Ejecución exacta:**
```bash
# BO ejecuta Bloque 1 (120 combos) mientras TANK ejecuta Bloque 2 (30 combos)
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202 \
  "python phase3_exits_runner.py --asset ES --block 1 --combos 120"

# EN PARALELO (TANK):
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ytambo@192.168.1.162 \
  "python phase3_exits_runner.py --asset ES --block 2 --combos 30"
```

**Éxito:** Robustness >= 0.80

---

## ✅ FASE 4: Optimización de Stops (10 min)
**Grid:** 20 combinaciones  
**Locked:** Phase 1 + 2 + 3 best_params  
**Qué optimiza:**
- superstop_quality (1-4): 4 valores
- superstop_coef_volat (2.0-5.0): 5 valores

```
Combos: 4 × 5 = 20
Tiempo: ~5 min
Consolidar: 2 min
Total: 7 min (extrapolado para 4 activos)
```

**Distribución de Carga: 80% BO / 20% TANK (PARALELO)**

```
BO (80% = 16 combos):
  ES 5m:   16 combos Block 1 → ssh -i key ubuntu@BO → 3 min
  
TANK (20% = 4 combos en paralelo):
  ES 5m:   4 combos Block 2 → ssh -i key ytambo@TANK → ~1 min
  MNQ 5m:  16 combos Block 1 → ssh -i key ubuntu@BO → 3 min
  
BO (siguiente):
  MNQ 5m:  4 combos Block 2 → TANK paralelo → ~1 min
  YM 10m:  16 combos Block 1 → BO → 3 min
  YM 10m:  4 combos Block 2 → TANK paralelo → ~1 min
  FDAX 5m: 16 combos Block 1 → BO → 3 min
  FDAX 5m: 4 combos Block 2 → TANK paralelo → ~1 min

Consolidar: 2 min (BO local)
Total: 10 min (con paralelismo)
```

**Ejecución exacta:**
```bash
# BO ejecuta Bloque 1 (16 combos) mientras TANK ejecuta Bloque 2 (4 combos)
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ubuntu@79.72.62.202 \
  "python phase4_stops_runner.py --asset ES --block 1 --combos 16"

# EN PARALELO (TANK):
ssh -i "C:\Users\Yohanny Tambo\.ssh\B_O.key" ytambo@192.168.1.162 \
  "python phase4_stops_runner.py --asset ES --block 2 --combos 4"
```

**Éxito:** Robustness >= 0.80, Max Drawdown <= 30%

---

## ✅ CONSOLIDACIÓN FINAL (5 min)
**Output:** `COMB_002_IMPULSE_MASTER_PARAMS.json`

```json
{
  "ES_5m": { "stpmt_smooth_h": X, ... },
  "MNQ_5m": { "stpmt_smooth_h": Y, ... },
  "YM_10m": { "stpmt_smooth_h": Z, ... },
  "FDAX_5m": { "stpmt_smooth_h": W, ... }
}
```

**Mapeo automático a C#:** Usar `COMB_002_IMPULSE_PHASE_CONFIG.json > c_sharp_mapping`

---

# ANTES DE EMPEZAR: CHECKLIST

- [ ] Existen Phase A + B splits para TODOS los activos/timeframes
  - [ ] ES_phase_A_5m.csv, ES_phase_B_5m.csv
  - [ ] MNQ_phase_A_5m.csv, MNQ_phase_B_5m.csv
  - [ ] YM_phase_A_10m.csv, YM_phase_B_10m.csv
  - [ ] FDAX_phase_A_5m.csv, FDAX_phase_B_5m.csv
  - (Y versiones 10m, 15m si aplica)

- [ ] CSVs tienen columnas correctas: `timestamp_utc, open, high, low, close`
- [ ] Data está en UTC (no local)
- [ ] Data está cronológicamente ordenada
- [ ] Sin gaps (o interpolados)

---

# DURANTE LA EJECUCIÓN: MONITOREO

### Fase 1:
```
Expected: 625 combos × 4 activos × 2 datasets = 5,000 backtests
Time: ~60 min (80% BO @ 8-9 combos/sec + 20% TANK @ 2-3 combos/sec)
Success: Robustness >= 0.80 para cada activo

Salida esperada:
  phase1_COMB_002_IMPULSE_ES_5m_best_params.json ✅
  phase1_COMB_002_IMPULSE_MNQ_5m_best_params.json ✅
  phase1_COMB_002_IMPULSE_YM_10m_best_params.json ✅
  phase1_COMB_002_IMPULSE_FDAX_5m_best_params.json ✅
```

### Fase 2:
```
Expected: 12 combos × 4 activos × 2 datasets = 96 backtests
Time: ~15 min
Success: Robustness >= 0.80 para cada activo (con Phase 1 locked)

Salida esperada:
  phase2_COMB_002_IMPULSE_ES_5m_best_params.json ✅
  phase2_COMB_002_IMPULSE_MNQ_5m_best_params.json ✅
  phase2_COMB_002_IMPULSE_YM_10m_best_params.json ✅
  phase2_COMB_002_IMPULSE_FDAX_5m_best_params.json ✅
```

### Fase 3:
```
Expected: 150 combos × 4 activos × 2 datasets = 1,200 backtests
Time: ~20 min
Success: Robustness >= 0.80 para cada activo (con Phase 1+2 locked)

Salida esperada:
  phase3_COMB_002_IMPULSE_ES_5m_best_params.json ✅
  phase3_COMB_002_IMPULSE_MNQ_5m_best_params.json ✅
  phase3_COMB_002_IMPULSE_YM_10m_best_params.json ✅
  phase3_COMB_002_IMPULSE_FDAX_5m_best_params.json ✅
```

### Fase 4:
```
Expected: 20 combos × 4 activos × 2 datasets = 160 backtests
Time: ~10 min
Success: Robustness >= 0.80 para cada activo

Salida esperada:
  phase4_COMB_002_IMPULSE_ES_5m_best_params.json ✅
  phase4_COMB_002_IMPULSE_MNQ_5m_best_params.json ✅
  phase4_COMB_002_IMPULSE_YM_10m_best_params.json ✅
  phase4_COMB_002_IMPULSE_FDAX_5m_best_params.json ✅
```

---

# RED FLAGS (Si pasa, parar y revisar)

| Situación | Causa Probable | Acción |
|-----------|-----------------|--------|
| Robustness < 0.80 en Fase 1 | Signal demasiado sobreoptimizado | Reducir grid, revisar Phase B data |
| Pocas trades (< 20) | Data insuficiente o filtros bloqueando | Expandir ventana data o relajar filtros |
| Trade muy pequeño (< 50 puntos ES) | Parámetros demasiado restrictivos | Aumentar tolerancia en Phase 2 |
| Drawdown > 50% | Stop inefectivo | Revisar Phase 4 (SuperStop quality) |
| Fase X tarda 3× más que esperado | Backtest muy lento | Optimizar código vectorización |

---

# DESPUÉS: EXPORTAR A NT8

Una vez `COMB_002_IMPULSE_MASTER_PARAMS.json` listo:

1. **Leer mapping de C#:**
   ```
   COMB_002_IMPULSE_PHASE_CONFIG.json > final_consolidation > c_sharp_mapping
   ```

2. **Actualizar C# code:**
   ```csharp
   // Parámetros optimizados para ES_5m
   StpmtSmoothH = 3;
   StpmtSmoothB = 2;
   StpmtDistMaxH = 50;
   StpmtDistMaxL = 50;
   HoraireHours = "9,10,11,12,13,14,15,16,17,20,21,22";
   // ... etc
   ```

3. **Compilar en NinjaTrader 8 (F5)**

4. **Validar backtests coinciden con Python ±0.00001**

---

# RESUMEN FINAL

```
Comando del usuario: "Optimiza COMB_002"

Yo, automáticamente:
├─ FASE 1 (60 min): Optimizar Signal (625 combos × 4 activos)
├─ FASE 2 (15 min): Optimizar Contexto (12 combos × 4 activos) [locked Phase 1]
├─ FASE 3 (20 min): Optimizar Exits (150 combos × 4 activos) [locked Phase 1+2]
├─ FASE 4 (10 min): Optimizar Stops (20 combos × 4 activos) [locked Phase 1+2+3]
└─ CONSOLIDAR (5 min): Master params para NT8

Total: 110 min = 1h 50m

Output: COMB_002_IMPULSE_MASTER_PARAMS.json → C# → NinjaTrader 8 ✅
```

---

## ¿Preguntas?

Este documento + UNIVERSAL_OPTIMIZATION_FRAMEWORK_v1.md + COMB_002_IMPULSE_PHASE_CONFIG.json contienen TODO lo necesario para ejecutar automáticamente.

**No se requieren preguntas adicionales una vez iniciada la optimización.**
