# COMB_002_IMPULSE V2 — Design Document

**Fecha:** 2026-04-25
**Autor:** Pipeline rediseñado tras análisis de régimen V1
**Status:** DRAFT — pendiente revisión antes de implementación

---

## 1. Motivación: ¿Por qué V2?

### 1.1 El problema diagnosticado en V1

El análisis `analyze_COMB002_regime_dependency.py` (ejecutado 2026-04-24) reveló que **10/12 combos optimizados con V1 son régimen-dependientes**:

| Combo | Δ% (max-min PF) | Patrón |
|-------|------|--------|
| FDAX_5m | **1525%** | PF: 0.40→2.36→6.50→1.89 (puro recency) |
| FDAX_15m | 630% | PF: 0.46→0.81→0.75→3.36 |
| FDAX_10m | 507% | PF: 0.21→0.42→0.48→1.29 |
| YM_15m | 339% | PF: 0.66→1.03→0.44→1.92 |
| MNQ_5m | 290% | PF: 0.44→1.73→1.06→1.25 |
| YM_10m | 212% | PF: 0.92→1.02→0.52→1.62 |
| MNQ_10m | 205% | PF: 1.05→1.62→0.67→2.05 |
| MNQ_15m | 154% | PF: 0.76→1.55→0.81→1.94 |
| ES_10m | 97% | PF: 0.87→0.76→0.54→1.07 |
| YM_5m | 97% | PF: 0.87→0.76→0.54→1.07 |

Solo ES_5m (Δ=19%) y ES_15m (Δ=42%) son verdaderamente robustos.

### 1.2 Causa raíz identificada

V1 sufre de **3 fallas estructurales** en su metodología:

#### Falla #1: División binaria A/B no captura múltiples regímenes
- V1 divide la data en Phase A (60%) train + Phase B (40%) test
- Pero los datos contienen **múltiples regímenes** (low-vol trending, high-vol chop, recovery, etc.)
- Optimizar sobre el conjunto promedia regímenes incompatibles → params que solo funcionan cuando "el mercado se parece al promedio"

#### Falla #2: Criterio de optimización maximiza recency
- V1 selecciona ganadores por **max(PF_B)** (mejor performance en período más reciente)
- Esto premia parámetros que capturan el régimen final del dataset
- Resultado: en backtest "se ven brillantes" pero el día que cambie el régimen, mueren

#### Falla #3: Un único set de params para todas las condiciones
- V1 produce 1 conjunto de parámetros por (asset, timeframe)
- Asume que los mismos parámetros funcionan en TODOS los regímenes
- Realidad: stop-loss óptimo en alta volatilidad ≠ stop-loss óptimo en baja volatilidad

### 1.3 Validación empírica

El backtest del usuario en data histórica amplia confirmó: **estrategias plamas/negativas en 2023, "brillantes" en 2024-Q1**. Esto NO es overfitting clásico — es captura de régimen.

---

## 2. Arquitectura V2: Walk-Forward Multi-Ventana con Adaptación de Régimen

### 2.1 Cambios principales vs V1

| Aspecto | V1 (actual) | V2 (nuevo) | Justificación |
|---------|-------------|------------|---------------|
| **Divisiones temporales** | 2 (A=60%, B=40%) | 4-5 ventanas walk-forward | Captura múltiples regímenes en lugar de promediarlos |
| **Criterio de optimización** | max(PF_B) | min(PF_all_windows) ≥ 1.0 | Premia robustez peor-caso, no peak performance |
| **Robustness score** | PF_B / PF_A | min(PF_W1..W4) / max(...) ratio + flat threshold | Mide consistencia, no upside |
| **Filtros hard** | Rob ≥ 0.8 + Trades ≥ 30 | Min PF ≥ 1.0 en TODAS · Trades ≥ 20/ventana · Std(PF)/mean(PF) ≤ 0.30 | Imposibilita ganar con un solo período brillante |
| **Detección de régimen** | Ninguna | Phase 1.5 explícita: ATR-percentile + ADX/RSI | Permite optimizar params por régimen |
| **Parámetros finales** | 1 conjunto por (asset, TF) | N conjuntos por (asset, TF, régimen) | Adaptación automática en live |
| **Validación cross** | Sequential vs Cross independiente | Walk-forward + out-of-sample por ventana | Cada selección probada en data NUNCA vista |
| **Hold-out** | Phase C opcional | Phase C OBLIGATORIA antes de deploy | Out-of-sample real, no walk-forward interno |

### 2.2 Pipeline V2 — flujo end-to-end

```
DATA (e.g. ES_5m_full.csv = 18 meses)
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 0: Preparación de Ventanas    │
│  Divide en 5 ventanas iguales:      │
│  W1 W2 W3 W4 W5                     │
│  ─────────────────────────────────  │
│  Walk-forward folds:                │
│  Fold 1: train W1+W2 → test W3      │
│  Fold 2: train W2+W3 → test W4      │
│  Fold 3: train W3+W4 → test W5      │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 1.5: Regime Classification    │
│  Para cada ventana, calcula:        │
│  - ATR percentile (low/med/high)    │
│  - ADX trend strength (trend/chop)  │
│  Asigna régimen a cada ventana      │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 1: Signal Detection           │
│  Optimiza stpmt_smooth/distance     │
│  Criterio: min(PF_W3,W4,W5) ≥ 1.0   │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 2A: Horaire (walk-forward)    │
│  Top-3 horarios consistentes        │
│  Filtro: PF ≥ 1.0 en ≥ 3/3 folds    │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 2B: Volatility + Regime       │
│  CLUSTERING: separa data por        │
│  régimen detectado (Phase 1.5)      │
│  Optimiza volatility-band POR       │
│  régimen (no global)                │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 3: Exits (walk-forward)       │
│  Por cada régimen detectado         │
│  scalping_target_coef_volat óptimo  │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 4: Stops (walk-forward)       │
│  Por cada régimen                   │
│  superstop_quality + coef_volat     │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 5: Regime-Aware Validation    │
│  Cada conjunto de params probado    │
│  en TODAS las ventanas test         │
│  Selección final por régimen        │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│ Phase 6: Hold-out final (Phase C)   │
│  Datos NUNCA vistos en optimización │
│  Validación out-of-sample real      │
│  Si falla aquí → params descartados │
└─────────────────────────────────────┘
   │
   ▼
COMB002_V2_FINAL_PARAMS.json
   - 1 entry por (asset, TF, régimen)
   - Total: 4 assets × 3 TFs × 3 regímenes = 36 entries posibles
   - Live deploy: detecta régimen actual → aplica params correspondientes
```

---

## 3. Especificaciones Técnicas Detalladas

### 3.1 Phase 0: Preparación Walk-Forward

**Input:** `{ASSET}_full_{TF}.csv` (mínimo 12 meses, idealmente 18-24)

**Output:**
- 5 ventanas de igual tamaño temporal (W1..W5)
- Lista de 3 folds: cada fold = (train_rows, test_rows)
- Metadata por ventana: rango de fechas, número de barras

```python
def split_walkforward(rows, n_windows=5, n_train_windows=2):
    """
    Divide rows en n_windows. Genera folds donde
    cada fold usa n_train_windows consecutivas para train
    y la siguiente para test.

    Returns: List[Tuple[train_rows, test_rows, fold_id]]
    """
```

**Por qué 5 ventanas y no 4 o 10:**
- 4 → solo 2 folds (poco), menos confianza estadística
- 10 → cada ventana muy pequeña, ruido alto
- 5 → balance: 3 folds, ventanas de ~2-4 meses (suficiente para múltiples regímenes locales)

### 3.2 Phase 1.5: Regime Classification

**Decisión de diseño:** Clasificación SIMPLE (3 regímenes) vs COMPLEJA (9 regímenes)

V2 usa 3 regímenes para empezar:
1. **`low_vol`**: ATR percentile < 33%
2. **`med_vol`**: 33% ≤ ATR percentile < 66%
3. **`high_vol`**: ATR percentile ≥ 66%

ADX se usa solo como **filtro adicional** (no como dimensión separada) para evitar explosión combinatoria.

**Justificación:** 9 regímenes (3×3) requeriría 9× más data para optimizar cada uno. Con 18 meses no alcanza. Mejor empezar simple y añadir trend/chop en V3 si V2 funciona.

### 3.3 Criterios de Optimización

#### V1 (rechazado):
```python
score = phase_b_pf  # Maximiza solo recency
filter = robustness >= 0.80 and trades >= 30
```

#### V2 (nuevo):
```python
pfs_by_window = [pf_w1, pf_w2, pf_w3, pf_w4, pf_w5]
score = min(pfs_by_window)  # Peor caso

filters = [
    min(pfs_by_window) >= 1.0,           # No perder en ningún régimen
    all(t >= 20 for t in trades_by_window), # Sample suficiente
    np.std(pfs_by_window) / np.mean(pfs_by_window) <= 0.30,  # CV ≤ 30%
]
```

**Por qué CV ≤ 0.30 (Coefficient of Variation):**
- ES_5m (V1, robusto): CV = std([1.04, 1.06, 1.07, 1.24]) / 1.10 ≈ 0.078 ✓
- FDAX_5m (V1, regime-dep): CV = std([0.40, 2.36, 6.50, 1.89]) / 2.79 ≈ 0.91 ✗

CV ≤ 0.30 captura la diferencia con margen.

### 3.4 Estructura de Output

#### V1:
```json
{
  "ES_5m": {
    "winner_approach": "cross",
    "robustness": 1.6252,
    "stpmt_smooth_h": 5,
    ...
  }
}
```

#### V2:
```json
{
  "ES_5m": {
    "regimes": {
      "low_vol": {
        "min_pf_across_folds": 1.05,
        "cv": 0.08,
        "stpmt_smooth_h": 5,
        ...
      },
      "med_vol": {
        "min_pf_across_folds": 1.12,
        ...
      },
      "high_vol": {
        "min_pf_across_folds": 0.95,
        "status": "REJECTED",
        "reason": "min_pf < 1.0"
      }
    }
  }
}
```

### 3.5 Live Deployment Logic

```python
def select_params_live(current_market_state, params_db):
    """
    En vivo, cada N barras:
    1. Calcula ATR percentile sobre últimas X barras
    2. Determina régimen actual (low/med/high vol)
    3. Carga params correspondientes
    """
    current_atr = compute_atr(last_X_bars)
    if current_atr < params_db["atr_threshold_low"]:
        return params_db[f"{asset}_{tf}"]["regimes"]["low_vol"]
    elif current_atr < params_db["atr_threshold_high"]:
        return params_db[f"{asset}_{tf}"]["regimes"]["med_vol"]
    else:
        return params_db[f"{asset}_{tf}"]["regimes"]["high_vol"]
```

Esto resuelve el problema de FDAX: si el régimen `low_vol` tiene min_PF < 1.0 después de optimizar, **no se usa** — la estrategia simplemente NO opera en ese régimen para FDAX.

---

## 4. Decisiones Abiertas (requieren input del usuario)

### 4.1 ¿Cuántas ventanas walk-forward?
- **Propuesta: 5 ventanas, 3 folds** (defendida en §3.1)
- Alternativa: 4 ventanas, 2 folds (menos robusto pero más data por ventana)

### 4.2 ¿Cuántos regímenes?
- **Propuesta: 3 (low/med/high vol)** (defendida en §3.2)
- Alternativa A: 2 (vol_low, vol_high) — más simple, más data por bucket
- Alternativa B: 4-6 (incluir trend/chop) — más adaptativo pero requiere MUCHA data

### 4.3 ¿Threshold de min_PF?
- **Propuesta: 1.0** (no perder en ningún régimen)
- Alternativa A: 1.1 (margen de seguridad para slippage/comisión)
- Alternativa B: 0.95 (permite pérdida marginal en peor régimen, gana en otros)

### 4.4 ¿Coefficient of Variation máximo?
- **Propuesta: 0.30** (defendida en §3.3)
- Alternativa: 0.25 (más estricto) o 0.40 (más laxo)

### 4.5 ¿Mantener compatibilidad con V1?
- **Propuesta: V2 vive en paralelo**, archivos con sufijo `_V2`. V1 intacto.
- Alternativa: Reemplazar V1 (riesgo de perder histórico)

### 4.6 ¿Phase 6 (hold-out Phase C) es bloqueante?
- **Propuesta: SÍ** — sin Phase C OK, no hay deploy.
- Alternativa: Soft-warn (deploy con tamaño reducido si Phase C marginal)

---

## 5. Plan de Implementación

### 5.1 Orden de archivos a crear

1. ✅ `COMB002_V2_DESIGN_DOC.md` (este archivo)
2. ⏳ `COMB_002_IMPULSE_V2_walkforward.py` — engine + utils de walk-forward + regime classification
3. ⏳ `phase1_V2_signal_walkforward.py`
4. ⏳ `phase2a_V2_horaire_walkforward.py`
5. ⏳ `phase2b_V2_volatility_regime.py`
6. ⏳ `phase3_V2_exits_walkforward.py`
7. ⏳ `phase4_V2_stops_walkforward.py`
8. ⏳ `phase5_V2_regime_aware_validation.py`
9. ⏳ `consolidate_COMB002_V2_final.py`
10. ⏳ `validate_COMB002_V2_holdout.py`
11. ⏳ `run_COMB002_V2_pipeline.sh`

### 5.2 Reuso del código V1

V2 reutilizará de V1:
- `Comb002ImpulseStrategy` (motor de backtest, no cambia)
- `Comb002ImpulseParams` (struct de params, no cambia)
- `load_ohlc_csv` (loader de CSV, no cambia)

V2 cambia SOLO la **metodología de optimización**, no la estrategia.

### 5.3 Estimación de tiempo de cómputo

V1 Phase 5 (cross-validation 12 combos): ~6 horas en BO (4 cores)
V2 con 3 regímenes y 3 folds: ~3× = **~18 horas**

Trade-off acceptable dado el problema que resuelve.

---

## 6. Criterios de Éxito

V2 será considerado exitoso si:

1. **≥ 8/12 combos** producen al menos 1 régimen con `status=OK` (vs 2/12 en V1)
2. **CV promedio ≤ 0.25** en los combos OK (vs CV ~0.5+ en V1)
3. **Hold-out Phase C confirma**: drift |reported − holdout| / reported ≤ 15% en ≥ 80% de los regímenes OK
4. **No hay un solo régimen** con `min_PF < 0.5` y `status=OK` (eliminando catastrofes tipo FDAX_5m)

Si V2 NO cumple estos criterios → diagnóstico adicional (puede que la estrategia base no tenga edge real, no es problema de optimización).

---

## 7. Riesgos Conocidos

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Pocos trades por régimen × ventana | Alta (FDAX especialmente) | Filtro `trades ≥ 20` rechaza; consolidar regímenes si necesario |
| Régimen actual en live no está en histórico | Media | Default a régimen `med_vol` si ATR fuera de rangos vistos |
| Over-engineering (3 regímenes × 5 ventanas = 15 buckets) → cada uno tiene poca data | Media | Empezar con 3 regímenes; consolidar a 2 si data insuficiente |
| Cambio de régimen MIENTRAS hay posición abierta | Baja | Política: mantener params del régimen de entrada hasta cerrar trade |
| Phase C también está en régimen sesgado | Baja | Documentar régimen de Phase C; si es solo `high_vol`, validación incompleta |

---

## 8. Próximos Pasos

1. **Usuario revisa este documento** y decide §4 (decisiones abiertas)
2. Implementación de archivos en orden §5.1
3. Test inicial: correr V2 sobre ES_5m (que ya sabemos es robusto en V1) → debe confirmar
4. Test crítico: correr V2 sobre FDAX_5m → debe rechazar al menos 1 régimen
5. Pipeline completo en BO (~18 horas)
6. Comparación V1 vs V2 → decisión final de deploy

---

**Fin del documento. Esperando confirmación de decisiones §4 antes de implementar.**
