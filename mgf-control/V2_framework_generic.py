"""
V2 FRAMEWORK GENÉRICO — Core reutilizable para CUALQUIER estrategia

No contiene lógica específica de COMB_002. Exporta:
  - split_walkforward()
  - compute_regime_thresholds() / filter_rows_by_regime()
  - evaluate_vec()
  - score_walkforward() / score_across_windows()
  - passes_v2_filters()
  - Pool dispatcher helper

Importa:
  - load_ohlc_csv (de la estrategia)

Usado por: V2 phase runners (phase1, phase2a, phase2b, etc.)
Requiere: strategy_class + params_class importados por el caller
"""

import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# ───────────────────────────────────────────────────────────────────────────
# Thresholds V2 globales (ajustables)
# ───────────────────────────────────────────────────────────────────────────
V2_MIN_PF_PER_WINDOW = 1.0
V2_MIN_TRADES_PER_WINDOW = 20
V2_MAX_CV = 0.30
V2_N_WINDOWS = 5
V2_N_TRAIN_WINDOWS = 2

V2_REGIME_LOW_PCT = 33.33
V2_REGIME_HIGH_PCT = 66.67

REGIME_LABELS = ("low_vol", "med_vol", "high_vol")


# ───────────────────────────────────────────────────────────────────────────
# 1. WALK-FORWARD SPLIT
# ───────────────────────────────────────────────────────────────────────────

@dataclass
class WalkForwardFold:
    fold_id: int
    train_rows: list
    test_rows: list
    train_range: Tuple[str, str]
    test_range: Tuple[str, str]


def split_walkforward(rows: list, n_windows: int = V2_N_WINDOWS,
                      n_train: int = V2_N_TRAIN_WINDOWS) -> List[WalkForwardFold]:
    """Divide rows en n_windows. Genera folds de (n_train consecutive windows → test window)."""
    if len(rows) < n_windows * 100:
        raise ValueError(f"Insufficient rows ({len(rows)}) for {n_windows} windows")

    window_size = len(rows) // n_windows
    windows = [rows[i*window_size:(i+1)*window_size] for i in range(n_windows)]
    windows[-1] = rows[(n_windows-1)*window_size:]

    folds = []
    n_folds = n_windows - n_train
    for i in range(n_folds):
        train_blocks = windows[i:i+n_train]
        train_rows = [r for block in train_blocks for r in block]
        test_rows = windows[i+n_train]

        folds.append(WalkForwardFold(
            fold_id=i,
            train_rows=train_rows,
            test_rows=test_rows,
            train_range=(train_rows[0].get("timestamp", "?"), train_rows[-1].get("timestamp", "?")),
            test_range=(test_rows[0].get("timestamp", "?"), test_rows[-1].get("timestamp", "?")),
        ))

    return folds


def split_all_windows(rows: list, n_windows: int = V2_N_WINDOWS) -> List[list]:
    """Split sin folds — retorna las n_windows completas."""
    window_size = len(rows) // n_windows
    windows = [rows[i*window_size:(i+1)*window_size] for i in range(n_windows)]
    windows[-1] = rows[(n_windows-1)*window_size:]
    return windows


# ───────────────────────────────────────────────────────────────────────────
# 2. REGIME CLASSIFICATION
# ───────────────────────────────────────────────────────────────────────────

def _row_true_range(prev_close: float, high: float, low: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def compute_atr_series(rows: list, period: int = 14) -> List[float]:
    """ATR series sobre rows OHLC."""
    if len(rows) < period + 1:
        return []
    trs = []
    prev_close = float(rows[0]["close"])
    for r in rows[1:]:
        trs.append(_row_true_range(prev_close, float(r["high"]), float(r["low"])))
        prev_close = float(r["close"])

    atr = []
    for i in range(period - 1, len(trs)):
        atr.append(sum(trs[i-period+1:i+1]) / period)
    return atr


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * pct / 100)
    idx = max(0, min(len(sorted_vals) - 1, idx))
    return sorted_vals[idx]


@dataclass
class RegimeThresholds:
    atr_low: float
    atr_high: float


def compute_regime_thresholds(all_rows: list, period: int = 14) -> RegimeThresholds:
    """Calcula cut-offs de régimen sobre TODA la data."""
    atr = compute_atr_series(all_rows, period=period)
    return RegimeThresholds(
        atr_low=percentile(atr, V2_REGIME_LOW_PCT),
        atr_high=percentile(atr, V2_REGIME_HIGH_PCT),
    )


def classify_regime(window_rows: list, thresholds: RegimeThresholds,
                    period: int = 14) -> str:
    """Retorna régimen dominante de una ventana."""
    atr = compute_atr_series(window_rows, period=period)
    if not atr:
        return "med_vol"
    mean_atr = sum(atr) / len(atr)
    if mean_atr < thresholds.atr_low:
        return "low_vol"
    if mean_atr >= thresholds.atr_high:
        return "high_vol"
    return "med_vol"


def filter_rows_by_regime(rows: list, thresholds: RegimeThresholds,
                          target_regime: str, window_size: int = 500,
                          period: int = 14) -> list:
    """Filtra rows para mantener solo las que caen en target_regime."""
    if len(rows) < window_size:
        return rows if classify_regime(rows, thresholds, period) == target_regime else []

    kept = []
    for i in range(window_size, len(rows)):
        local_window = rows[i-window_size:i]
        if classify_regime(local_window, thresholds, period) == target_regime:
            kept.append(rows[i])
    return kept


# ───────────────────────────────────────────────────────────────────────────
# 3. VEC EVALUATION (strategy-agnostic)
# ───────────────────────────────────────────────────────────────────────────

@dataclass
class ParamEvaluation:
    """Resultado de evaluar UN combo de params."""
    params: object  # Comb002ImpulseParams o lo que sea
    pf: float
    wr: float
    trades: int
    equity: float


def evaluate_vec(strategy_class, params_list: list, rows: list) -> List[ParamEvaluation]:
    """
    Evalúa N params sobre LA MISMA ventana.

    Args:
        strategy_class: Clase de estrategia (ej: Comb002ImpulseStrategy)
        params_list: List[params_instance] — cada uno debe ser compatible con strategy_class
        rows: list of OHLC dicts

    Returns:
        List[ParamEvaluation]
    """
    evaluations = []
    for p in params_list:
        strategy = strategy_class(p)
        result = strategy.run(rows)
        evaluations.append(ParamEvaluation(
            params=p,
            pf=round(result.profit_factor, 4),
            wr=round(result.win_rate, 4),
            trades=len(result.trades),
            equity=round(result.equity_points, 2),
        ))
    return evaluations


def evaluate_single(strategy_class, params, rows: list) -> ParamEvaluation:
    """Helper: evalúa un solo params."""
    return evaluate_vec(strategy_class, [params], rows)[0]


# ───────────────────────────────────────────────────────────────────────────
# 4. SCORING & FILTERS V2
# ───────────────────────────────────────────────────────────────────────────

@dataclass
class WalkForwardScore:
    pfs: List[float]
    trades: List[int]
    min_pf: float
    max_pf: float
    mean_pf: float
    cv: float
    min_trades: int
    passes_filters: bool
    reject_reason: Optional[str] = None


def score_walkforward(strategy_class, params, folds: List[WalkForwardFold]) -> WalkForwardScore:
    """Ejecuta params en TEST window de cada fold. Retorna score V2."""
    pfs = []
    trades = []
    for fold in folds:
        ev = evaluate_single(strategy_class, params, fold.test_rows)
        pfs.append(ev.pf)
        trades.append(ev.trades)
    return _build_score(pfs, trades)


def score_across_windows(strategy_class, params, windows: List[list]) -> WalkForwardScore:
    """Evalúa params sobre cada ventana completa (cross-regime sanity check)."""
    pfs = []
    trades = []
    for w in windows:
        ev = evaluate_single(strategy_class, params, w)
        pfs.append(ev.pf)
        trades.append(ev.trades)
    return _build_score(pfs, trades)


def _build_score(pfs: List[float], trades: List[int]) -> WalkForwardScore:
    min_pf = min(pfs) if pfs else 0.0
    max_pf = max(pfs) if pfs else 0.0
    mean_pf = statistics.mean(pfs) if pfs else 0.0
    cv = (statistics.stdev(pfs) / mean_pf) if (len(pfs) > 1 and mean_pf > 0) else 0.0
    min_trades = min(trades) if trades else 0

    ok, reason = passes_v2_filters(pfs, trades)

    return WalkForwardScore(
        pfs=[round(p, 4) for p in pfs],
        trades=trades,
        min_pf=round(min_pf, 4),
        max_pf=round(max_pf, 4),
        mean_pf=round(mean_pf, 4),
        cv=round(cv, 4),
        min_trades=min_trades,
        passes_filters=ok,
        reject_reason=reason,
    )


def passes_v2_filters(pfs: List[float], trades: List[int]) -> Tuple[bool, Optional[str]]:
    """Filtros HARD V2: min_PF≥1.0 · trades≥20 · CV≤0.30."""
    if not pfs:
        return (False, "no_pfs")

    min_pf = min(pfs)
    if min_pf < V2_MIN_PF_PER_WINDOW:
        return (False, f"min_pf={min_pf:.3f} < {V2_MIN_PF_PER_WINDOW}")

    min_tr = min(trades) if trades else 0
    if min_tr < V2_MIN_TRADES_PER_WINDOW:
        return (False, f"min_trades={min_tr} < {V2_MIN_TRADES_PER_WINDOW}")

    if len(pfs) > 1:
        mean_pf = statistics.mean(pfs)
        cv = statistics.stdev(pfs) / mean_pf if mean_pf > 0 else float("inf")
        if cv > V2_MAX_CV:
            return (False, f"cv={cv:.3f} > {V2_MAX_CV}")

    return (True, None)


# ───────────────────────────────────────────────────────────────────────────
# 5. POOL HELPER: Generic worker dispatcher
# ───────────────────────────────────────────────────────────────────────────

def pool_init_worker(folds, base_params=None):
    """Inicializador genérico para Pool. Almacena en globals."""
    global _FOLDS, _BASE_PARAMS
    _FOLDS = folds
    _BASE_PARAMS = base_params


def dispatch_to_pool(worker_func, combo_list, n_workers: int, chunksize: int = 2,
                     folds=None, base_params=None):
    """Ejecuta worker_func sobre combo_list con Pool. Retorna resultados."""
    from multiprocessing import Pool
    with Pool(n_workers, initializer=pool_init_worker, initargs=(folds, base_params)) as pool:
        results = list(pool.imap_unordered(worker_func, combo_list, chunksize=chunksize))
    return results
