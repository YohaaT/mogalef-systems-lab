# V2 Porting Guide — Reutilizar el framework para nuevas estrategias

## Arquitectura reutilizable

```
V2_framework_generic.py (GENÉRICO — nunca cambiar)
  ├─ split_walkforward()
  ├─ compute_regime_thresholds() / filter_rows_by_regime()
  ├─ evaluate_vec()
  ├─ score_walkforward()
  └─ passes_v2_filters()

V2_PHASE_TEMPLATE.py (SKELETON — copiar y llenar 3 secciones)
  ├─ [ADAPTACIÓN A] Imports + grids
  ├─ [ADAPTACIÓN B] build_params()
  ├─ [ADAPTACIÓN C] _eval_combo()
  └─ main() (genérico)

COMB002_V2_phases.py (INSTANCIA de COMB_002 — ya completado)
```

---

## Workflow para nueva estrategia

### 1. Preparar tu estrategia

Necesitas que tu estrategia tenga esta interfaz:

```python
# Tu módulo: my_strategies.py

class MyStrategyParams:
    """Dataclass con todos los parámetros."""
    param1: float
    param2: int
    param3: float
    ...

class MyStrategy:
    """Estrategia de trading."""
    def __init__(self, params: MyStrategyParams):
        self.params = params

    def run(self, rows: List[Dict]) -> MyStrategyResult:
        """
        Ejecuta backtest sobre rows OHLC.
        Retorna resultado con:
          - profit_factor: float
          - win_rate: float
          - trades: List[Trade]
          - equity_points: float
        """
        ...

class MyStrategyResult:
    profit_factor: float
    win_rate: float
    trades: List[object]
    equity_points: float
```

### 2. Copiar template + llenar 3 secciones

```bash
cp V2_PHASE_TEMPLATE.py phase1_V2_my_strategy.py
# O múltiples fases si optimizas varios parámetros:
cp V2_PHASE_TEMPLATE.py phase2b_V2_my_strategy_volatility.py
```

### 3. Completar [ADAPTACIÓN A] — Imports + Grids

```python
from my_strategies import MyStrategy, MyStrategyParams, load_ohlc_csv
from V2_framework_generic import (
    split_walkforward, score_walkforward, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS,
)

# Reemplazar estos grids con los tuyos
PARAM1_RANGE = [1.0, 1.5, 2.0, 2.5, 3.0]
PARAM2_RANGE = [5, 10, 15, 20]
PARAM3_RANGE = [0.01, 0.02, 0.05, 0.10]
```

### 4. Completar [ADAPTACIÓN B] — build_params()

```python
def build_params(param1, param2, param3):
    """Construye params desde componentes individuales."""
    return MyStrategyParams(
        # Parámetros optimizados en ESTA phase
        param1=param1,
        param2=param2,
        param3=param3,

        # Parámetros FIJOS (valores por defecto)
        param4=1.0,
        param5=True,
        param6=25.0,
    )
```

### 5. Completar [ADAPTACIÓN C] — _eval_combo()

```python
def _eval_combo(combo):
    """Evalúa UN combo de parámetros."""
    # Desempacar (debe coincidir con order de itertools.product)
    param1, param2, param3 = combo

    # Construir params
    params = build_params(param1, param2, param3)

    # Evaluar sobre folds (genérico)
    score = score_walkforward(MyStrategy, params, _FOLDS)

    # Retornar row
    return {
        "param1": param1,
        "param2": param2,
        "param3": param3,
        "min_pf": score.min_pf,
        "max_pf": score.max_pf,
        "mean_pf": score.mean_pf,
        "cv": score.cv,
        "min_trades": score.min_trades,
        "passes_filters": score.passes_filters,
        "reject_reason": score.reject_reason or "",
    }
```

### 6. Ejecutar

```bash
python3 phase1_V2_my_strategy.py --asset ES --timeframe 5m --workers 4
```

---

## Patrón completo para múltiples phases

Si optimizas varios grupos de parámetros (ej: Phase 1 signal, Phase 2 volatility, Phase 3 stops):

```
phase1_V2_my_strategy_signal.py
  └─ Optimiza: signal_param1, signal_param2
  └─ Salida: my_strategy_phase1_ES_5m_top_params.json

phase2_V2_my_strategy_volatility.py
  ├─ Lee: my_strategy_phase1_ES_5m_top_params.json
  └─ Optimiza: vol_atr_min, vol_atr_max (manteniendo signal params fijos)
  └─ Salida: my_strategy_phase2_ES_5m_top_params.json

phase3_V2_my_strategy_stops.py
  ├─ Lee: my_strategy_phase2_ES_5m_top_params.json
  └─ Optimiza: stop_quality, stop_coef (manteniendo fijos signal + vol)
  └─ Salida: my_strategy_phase3_ES_5m_top_params.json
```

**Template para leer base de phase anterior:**

```python
# En [ADAPTACIÓN A]
BASE_PARAMS_FILE = Path("my_strategy_phase1_{asset}_{tf}_top_params.json")

# En main()
with open(BASE_PARAMS_FILE.format(asset=args.asset, tf=args.timeframe)) as fh:
    p1 = json.load(fh)
base_params = p1["top"]  # List of top-3 from phase 1

# En [ADAPTACIÓN B/C]
def build_params(base_idx, new_param):
    base = base_params[base_idx]
    return MyStrategyParams(
        # Reutiliza del phase anterior
        signal_param1=base["signal_param1"],
        signal_param2=base["signal_param2"],

        # Optimiza nuevo parámetro en ESTA phase
        new_param=new_param,

        # Defaults
        ...
    )

def _eval_combo(combo):
    base_idx, new_param = combo
    params = build_params(base_idx, new_param)
    # ... resto igual
```

---

## Ejemplo completo: TREND_FOLLOW_V1

Archivos necesarios:

```python
# trend_follow.py (tu estrategia)
class TrendFollowV1Params:
    sma_period: int
    atr_multiple: float
    stop_loss_pct: float

class TrendFollowV1:
    def __init__(self, params): ...
    def run(self, rows): ...

class TrendFollowResult:
    profit_factor: float
    win_rate: float
    trades: list
    equity_points: float
```

Fases:

```bash
# Phase 1: Optimiza SMA period
cp V2_PHASE_TEMPLATE.py phase1_V2_trendfollow_sma.py
# Editar [A], [B], [C] para SMA

python3 phase1_V2_trendfollow_sma.py --asset ES --timeframe 5m
# Salida: trendfollow_V2_phase1_ES_5m_top_params.json

# Phase 2: Optimiza ATR + stop loss (teniendo SMA fijo)
cp V2_PHASE_TEMPLATE.py phase2_V2_trendfollow_atr_stop.py
# Editar [A], [B], [C] para ATR + stop loss
# [B/C] leer JSON anterior, mantener sma_period fijo

python3 phase2_V2_trendfollow_atr_stop.py --asset ES --timeframe 5m
# Salida: trendfollow_V2_phase2_ES_5m_top_params.json
```

---

## Checklist de portación

- [ ] Tu estrategia tiene `.run()` que retorna resultado con `profit_factor`, `win_rate`, `trades`, `equity_points`
- [ ] Tienes `ParamsClass` (dataclass o similar) con todos los parámetros
- [ ] Defines GRIDS para los parámetros a optimizar (secciones [ADAPTACIÓN A])
- [ ] Escribes `build_params()` para construir params desde componentes (sección [ADAPTACIÓN B])
- [ ] Escribes `_eval_combo()` que desempaca, construye, evalúa (sección [ADAPTACIÓN C])
- [ ] Cambias el nombre del archivo en `main()` si quieres (ej: `trendfollow_V2_phase1_...`)
- [ ] Ejecutas: `python3 phase1_V2_TU_ESTRATEGIA.py --asset ES --timeframe 5m --workers 4`

---

## Troubleshooting

### "Insufficient rows — need X"
Tu CSV tiene muy pocas barras para 5 ventanas walk-forward.
- Opción A: Descargar más data
- Opción B: Reducir `V2_N_WINDOWS = 4` en el template (no recomendado, pierde robustez)

### "0/N combos passed filters"
El criterio V2 es duro: min_PF ≥ 1.0, CV ≤ 0.30.
- Opción: Tu estrategia no tiene edge (muy pocas trades, inconsistente)
- Opción: Ampliar grids (parámetros más suaves) o reducir threshold en `V2_MIN_PF_PER_WINDOW`

### "Slow execution"
Demasiadas combinaciones (grid × grid × grid es exponencial).
- Reducir tamaño de grids
- Aumentar `--workers` (máx. cores disponibles)
- Usar `chunksize=4` o mayor en `imap_unordered()`

---

## FAQs

**¿Puedo usar el template para optimizar por régimen (como Phase 2B)?**

Sí. El template es genérico. Simplemente:
1. En `main()`, itera sobre regímenes y filtra rows por régimen
2. Llama a `split_walkforward()` sobre las rows filtradas
3. Resto es igual

Ver `phase2b_V2_volatility_regime.py` para patrón completo.

**¿Puedo combinar múltiples fases en un archivo?**

No recomendado (complexity). Mejor: 1 archivo por fase, cada uno lee output anterior.

**¿El framework V2 importa de COMB_002?**

No. `V2_framework_generic.py` solo importa tipos base (`dataclass`, `statistics`, etc.). Completamente agnóstico de estrategia.

