# UNIVERSAL OPTIMIZATION FRAMEWORK v1
## Protocolo Estándar para Todas las Estrategias (COMB001, COMB002, COMB003+)

**Versión:** 1.0  
**Fecha:** 2026-04-24  
**Basado en:** Mogalef PDF Notes + COMB001/COMB002 Templates  
**Objetivo:** Automatizar optimización multi-timeframe, multi-activo con 4 fases independientes  

---

# I. FILOSOFÍA CORE

Basado en la metodología de Eric Mogalef:
- **NUNCA combinar optimizaciones** (cada fase locks la anterior)
- **Walk-forward validation**: Phase A (60% train) + Phase B (40% unseen)
- **Robustness = Phase_B_PF / Phase_A_PF** ≥ 0.80 (éxito)
- **Vectorización completa** para velocidad
- **Multi-activo / multi-timeframe**: optimizar en paralelo

---

# II. ESTRUCTURA GENÉRICA: 4 FASES INDEPENDIENTES

Cada estrategia `COMB_XXX` tiene exactamente 4 componentes:

```
PHASE 1: SIGNAL OPTIMIZATION
  ├─ Objetivo: Encontrar mejores parámetros de entrada (divergencia, momentum, etc.)
  ├─ Grid: 100-1000 combinaciones
  ├─ Locked: Phase A + Phase B data
  ├─ Output: best_signal_params.json (robustness >= 0.80)
  └─ Lock: SÍ para Phase 2+

PHASE 2: CONTEXTO OPTIMIZATION (Filters)
  ├─ Locked: Signal params from Phase 1
  ├─ Componentes: Trend Filter + Horaire + Volatility + Diario
  ├─ Grid: 50-500 combinaciones
  ├─ Output: best_contexto_params.json
  └─ Lock: SÍ para Phase 3+

PHASE 3: EXITS OPTIMIZATION (Targets + TimeStop)
  ├─ Locked: Signal + Contexto params
  ├─ Componentes: Profit Target (ATR mult), TimeStop bars, Opposite Signal
  ├─ Grid: 20-100 combinaciones
  ├─ Output: best_exits_params.json
  └─ Lock: SÍ para Phase 4

PHASE 4: STOPS OPTIMIZATION (Risk Management)
  ├─ Locked: Signal + Contexto + Exits
  ├─ Componentes: Stop Inteligente / SuperStop / Custom
  ├─ Grid: 15-50 combinaciones
  ├─ Output: best_stops_params.json
  └─ Final: best_combined_params.json
```

---

# III. APLICACIÓN A CADA ESTRATEGIA

## A. COMB_001_TREND

**Componentes del Framework:**

| Fase | Parámetro | Rango | Grid | Tipo |
|------|-----------|-------|------|------|
| **Signal** | stpmt_smooth_h | 1-10 | 5 | int |
| | stpmt_smooth_b | 1-10 | 5 | int |
| | stpmt_distance_max_h | 25-200 | 7 | int |
| | stpmt_distance_max_l | 25-200 | 7 | int |
| **Total Phase 1** | | | 5×5×7×7 = **1,225** | |
| | | | **Use: 625/activo** | |
| | | | Bloques: 500 BO + 125 TANK | |
| **Contexto** | trend_r1, r2, r3 | varies | 150 | int |
| | horaire_allowed_hours | [9-15], [9-17], etc | 6 | list |
| | atr_min, atr_max | 0-200 | 5 | float |
| **Exits** | target_atr_mult | 5-15 | 5 | float |
| | timescan_bars | 25-40 | 4 | int |
| **Stops** | stop_quality | 2-5 | 4 | int |
| | stop_coef_volat | 2-8 | 4 | float |

**Walk-Forward Split:**
- Phase A: 60% de datos históricos (train)
- Phase B: 40% restante (unseen validation)
- Éxito Phase 2-4: `Phase_B_PF >= 0.80 × Phase_A_PF`

---

## B. COMB_002_IMPULSE

**Diferencias clave vs COMB001:**

| Aspecto | COMB_001_TREND | COMB_002_IMPULSE |
|---------|----------------|-----------------|
| Signal | STPMT (mismo) | STPMT (mismo) |
| Trend Filter | ✅ Incluir | ❌ NO incluir |
| Volatility Filter | ✅ Incluir | ❌ NO (amputa gains) |
| Horaire Filter | ✅ SÍ | ✅ SÍ |
| Exits | 10 ATR Target | 10 ATR + Intelligent Scalping |
| Stops | Stop Inteligente | **SuperStop** |
| TimeStop | 30 bars | **15 bars** |

**Componentes del Framework:**

| Fase | Parámetro | Rango | Grid |
|------|-----------|-------|------|
| **Signal** | stpmt_smooth_h | 1-10 | 5 |
| | stpmt_smooth_b | 1-10 | 5 |
| | stpmt_distance_max_h | 25-200 | 7 |
| | stpmt_distance_max_l | 25-200 | 7 |
| **Total Phase 1** | | | **625/activo** |
| **Contexto** | horaire_allowed_hours | [9-15], [9-17], [9-22] | 3 |
| | dia_no_operar | [], [martes], [lun-mar] | 3 |
| **(SIN Trend Filter, SIN Volatility)** | | | **9 combos** |
| **Exits** | target_atr_mult | 5-15 | 5 |
| | scalping_target_coef | 2-6 | 5 |
| | timescan_bars | 10-20 | 5 |
| **Stops** | superstop_quality | 1-3 | 3 |
| | superstop_coef | 2-5 | 4 |

---

## C. COMB_003+ (Futuras)

**Patrón a seguir:**
1. Identificar 4 componentes clave
2. Definir grids (pequeños, vectorizables)
3. Crear Phase A/B split idéntico
4. Ejecutar 4 fases con locks

---

# IV. ESTRUCTURA DE DATOS

### Entrada: CSV Canónico

```csv
timestamp_utc,open,high,low,close
2023-01-02T09:00:00Z,4750.25,4765.50,4742.00,4758.75
2023-01-02T09:05:00Z,4758.75,4772.25,4757.00,4770.00
...
```

**Requisitos:**
- Columnas exactas: timestamp_utc, open, high, low, close
- Ordenadas cronológicamente
- Sin gaps (o interpolados)
- UTC timestamps (no local)

### Splits: Phase A + Phase B

```
Total rows: N
Phase A: rows[0:int(0.60*N)]  (60% - TRAIN)
Phase B: rows[int(0.60*N):]   (40% - UNSEEN VALIDATION)
```

**Importante:** Splits idénticos para TODOS los activos en TODOS los timeframes.

### Salida: JSON Params

```json
{
  "strategy": "COMB_001_TREND",
  "asset": "ES",
  "timeframe": "5m",
  "phase": 1,
  "optimization_date": "2026-04-24",
  
  "phase_a_metrics": {
    "trades": 45,
    "profit_factor": 2.156,
    "win_rate": 53.33,
    "max_drawdown": 2450.00,
    "avg_win": 485.23,
    "avg_loss": -312.45
  },
  
  "phase_b_metrics": {
    "trades": 28,
    "profit_factor": 1.823,
    "win_rate": 50.00,
    "max_drawdown": 1850.00,
    "avg_win": 420.15,
    "avg_loss": -345.20
  },
  
  "robustness": 0.846,
  "status": "PASS",
  
  "best_params": {
    "stpmt_smooth_h": 3,
    "stpmt_smooth_b": 2,
    "stpmt_distance_max_h": 50,
    "stpmt_distance_max_l": 50
  },
  
  "locked_for_phase": 2
}
```

---

# V. EJECUCIÓN: PSEUDOCÓDIGO GENÉRICO

### Para cualquier Fase X, cualquier Estrategia:

```python
def run_phase_X_optimization(
    strategy_name: str,  # "COMB_001_TREND" | "COMB_002_IMPULSE"
    asset: str,          # "ES" | "MNQ" | "YM" | "FDAX"
    timeframe: str,      # "5m" | "10m" | "15m"
    phase: int,          # 1, 2, 3, 4
    locked_params: dict  # {} for Phase 1, {signal_params} for Phase 2, etc.
):
    
    # 1. Load data (Phase A + Phase B)
    phase_a_data = load_csv(f"{asset}_phase_A_{timeframe}.csv")
    phase_b_data = load_csv(f"{asset}_phase_B_{timeframe}.csv")
    
    # 2. Get grid for this strategy + phase
    grid = STRATEGY_CONFIGS[strategy_name].phases[phase].grid
    
    # 3. Run vectorized backtest for each combo in grid
    results = []
    for combo in grid:
        params = {**locked_params, **combo}
        
        result_a = backtest(phase_a_data, params)
        result_b = backtest(phase_b_data, params)
        
        robustness = result_b.pf / result_a.pf
        results.append({
            "combo": combo,
            "phase_a": result_a,
            "phase_b": result_b,
            "robustness": robustness
        })
    
    # 4. Select best (highest robustness, >= 0.80)
    best = max(results, key=lambda x: x["robustness"])
    
    if best["robustness"] < 0.80:
        print(f"WARNING: Best robustness {best['robustness']:.2f} < 0.80")
    
    # 5. Export params + metrics
    export_json(best, f"{strategy_name}_{asset}_{timeframe}_phase{phase}_best.json")
    
    return best["combo"]  # Lock for next phase
```

---

# VI. PARALELISMO: DISTRIBUCIÓN DE CARGA

### Multi-Activo (4 activos):
```
BO (80%):  [ES 5m + MNQ 5m]        (Fase 1 Phase A)
TANK (20%): [YM 10m]                (Fase 1 Phase B simultáneamente)

Total time Fase 1: ~15 min (bottleneck = BO)
```

### Multi-Timeframe (mismo activo):
```
BO:   [5m Phase 1 Block 1]
TANK: [10m Phase 1 Block 2]

Ejecutar en serie: 5m → 10m → 15m (o paralelo si máquinas disponibles)
```

---

# VII. VALIDACIÓN CRUZADA

### Robustness Check (cada fase):
```
Éxito:  Phase_B_PF >= 0.80 × Phase_A_PF  ✅
Fallo:  Phase_B_PF < 0.80 × Phase_A_PF   ❌ (revisar parámetros)
```

### Post-Optimization (después Fase 4):
```
1. Comparar Phase B metrics vs baselines históricos
2. Verificar exit reasons distribution (no solo stops o solo targets)
3. Analizar entrada temporal (horaires respetados)
4. Verificar drawdown máximo <= 30% de capital (seguridad)
```

---

# VIII. FLUJO COMPLETO (Ejemplo: COMB_002_IMPULSE)

```
START
  ↓
FASE 0: Prep Data (5 min)
  └─ Verificar Phase A + B splits para 4 activos
  ↓
FASE 1: Signal Optimization (60 min total)
  ├─ ES 5m: 625 combos (15 min)
  ├─ MNQ 5m: 625 combos (15 min)
  ├─ YM 10m: 625 combos (15 min)
  ├─ FDAX 5m: 625 combos (15 min)
  └─ Consolidar: 4 × best_signal_params.json ✅
  ↓
FASE 2: Contexto Optimization (15 min total)
  ├─ Lock: Phase 1 best_signal_params
  ├─ ES 5m: 9 combos (Horaire + Diario, sin Trend/Volatility)
  ├─ ... (3 más)
  └─ Consolidar: 4 × best_contexto_params.json ✅
  ↓
FASE 3: Exits Optimization (20 min total)
  ├─ Lock: Phase 1 + Phase 2 best_params
  ├─ Grid: target_atr_mult × scalping_target_coef × timescan_bars
  ├─ ... (4 activos)
  └─ Consolidar: 4 × best_exits_params.json ✅
  ↓
FASE 4: Stops Optimization (15 min total)
  ├─ Lock: Phase 1 + 2 + 3 best_params
  ├─ Grid: superstop_quality × superstop_coef
  ├─ ... (4 activos)
  └─ Consolidar: 4 × best_stops_params.json ✅
  ↓
FINAL RESULTS
  └─ master_params.json (combining all phases)
     {
       "ES_5m": {...},
       "MNQ_5m": {...},
       "YM_10m": {...},
       "FDAX_5m": {...}
     }
  ↓
END (Total: ~110 min = 1h 50 min)
```

---

# IX. CHEKLIST DE USO

Cuando se pida: **"Optimiza COMB_002"**

- [ ] **Fase 0**: ¿Existen Phase A + B splits para todos los activos/timeframes?
- [ ] **Fase 1**: Ejecutar signal optimization (4 activos en paralelo)
  - [ ] Verificar robustness >= 0.80 para cada activo
  - [ ] Exportar best_signal_params.json
- [ ] **Fase 2**: Ejecutar contexto optimization (locked con Phase 1)
  - [ ] Verificar robustness >= 0.80
  - [ ] Exportar best_contexto_params.json
- [ ] **Fase 3**: Ejecutar exits optimization (locked con Phase 1+2)
  - [ ] Verificar robustness >= 0.80
  - [ ] Exportar best_exits_params.json
- [ ] **Fase 4**: Ejecutar stops optimization (locked con Phase 1+2+3)
  - [ ] Verificar robustness >= 0.80
  - [ ] Exportar best_stops_params.json
- [ ] **FINAL**: Consolidar master_params.json
  - [ ] Exportar a NT8 (C# parameter mappings)
  - [ ] Compilar en NinjaTrader 8
  - [ ] Validar backtests coinciden con Python

---

# X. ESTRATEGIAS SOPORTADAS

| Nombre | Alias | Signal | Contexto | Exits | Stops | Status |
|--------|-------|--------|----------|-------|-------|--------|
| COMB_001_TREND | TREND | STPMT | TrendFilter+Volatility | 10ATR+TimeStop(30) | StopIntel | ✅ |
| COMB_002_IMPULSE | IMPULSE | STPMT | Horaire+Diario | 10ATR+ScalpTarget+TimeStop(15) | SuperStop | ✅ |
| COMB_003_* | TBD | TBD | TBD | TBD | TBD | 🔄 |

---

# XI. NOTAS IMPORTANTES

- **NUNCA cambiar Mogalef PDF recomendaciones**: Horaires 9-17 + 20-22, no martes
- **NUNCA mezclar optimizaciones**: Cada fase es independiente
- **NUNCA usar Phase B para reoptimizar**: Es para validación únicamente
- **Vectorizar TODO**: No loops secuenciales, usar NumPy/Pandas operations
- **Documentar robustness**: Si <0.80, es red flag para sobreoptimización

---

**Fin del Framework v1**

---

Siguientes pasos:
1. Crear `COMB_002_IMPULSE_CONFIG.json` con grids para Fases 1-4
2. Crear `phase1_vectorized_runner.py` (genérico para cualquier estrategia)
3. Crear `phase2_contexto_runner.py`, etc.
4. Integrar con Master catalog para component selection
