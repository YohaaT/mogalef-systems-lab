"""
COMB_002_IMPULSE V2 — Engine de Walk-Forward + Regime Classification + VEC Evaluation

Este módulo NO cambia la estrategia de trading. Reutiliza:
  - Comb002ImpulseStrategy  (motor de backtest V1)
  - Comb002ImpulseParams    (struct de params V1)
  - load_ohlc_csv           (loader V1)

Lo que añade V2:
  1. split_walkforward(rows, n_windows=5, n_train=2)
       Divide data en ventanas iguales, genera folds (train_block → test_window).

  2. classify_regime(window_rows)
       Clasifica ventana por volatility (low/med/high) usando ATR percentile.

  3. evaluate_vec(params_list, rows)
       VEC: evalúa MULTIPLES combinaciones de params sobre la MISMA ventana
       de data en paralelo (cache de preprocesamiento).

  4. score_walkforward(params, folds)
       Score principal V2: min(PF_all_folds). Reemplaza max(PF_B) de V1.

  5. passes_v2_filters(pfs_by_window, trades_by_window)
       min(PF) ≥ 1.0 · trades ≥ 20/ventana · CV ≤ 0.30.

Ver: COMB002_V2_DESIGN_DOC.md para motivación completa.
"""

import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import (
    Comb002ImpulseStrategy,
    Comb002ImpulseParams,
    load_ohlc_csv,
)

# ───────────────────────────────────────────────────────────────────────────
# Thresholds V2 (ver §3.3 del DESIGN_DOC)
# ───────────────────────────────────────────────────────────────────────────
V2_MIN_PF_PER_WINDOW = 1.0       # §4.3: no perder en ningún régimen/ventana
V2_MIN_TRADES_PER_WINDOW = 20    # §3.3: sample suficiente por ventana
V2_MAX_CV = 0.30                 # §4.4: Coefficient of Variation máximo
V2_N_WINDOWS = 5                 # §4.1: 5 ventanas walk-forward
V2_N_TRAIN_WINDOWS = 2           # §4.1: 2 ventanas train + 1 test por fold

# ATR percentile cuts para regime classification (§3.2)
V2_REGIME_LOW_PCT = 33.33
V2_REGIME_HIGH_PCT = 66.67

REGIME_LABELS = ("low_vol", "med_vol", "high_vol")


# ───────────────────────────────────────────────────────────────────────────
# 1. Walk-forward split
# ───────────────────────────────────────────────────────────────────────────

@dataclass
class WalkForwardFold:
    fold_id: int
    train_rows: list
    test_rows: list
    train_range: Tuple[str, str]  # (start_ts, end_ts)
    test_range: Tuple[str, str]


def split_walkforward(rows: list, n_windows: int = V2_N_WINDOWS,
                      n_train: int = V2_N_TRAIN_WINDOWS) -> List[WalkForwardFold]:
    """
    Divide `rows` en `n_windows` ventanas iguales. Genera folds donde cada fold
    toma `n_train` ventanas consecutivas como train y la siguiente como test.

    Con n_windows=5, n_train=2 → 3 folds:
      Fold 0: train W1+W2 → test W3
      Fold 1: train W2+W3 → test W4
      Fold 2: train W3+W4 → test W5
    """
    if len(rows) < n_windows * 100:
        raise ValueError(f"Insufficient rows ({len(rows)}) for {n_windows} windows — need ≥{n_windows*100}")

    window_size = len(rows) // n_windows
    windows = [rows[i*window_size:(i+1)*window_size] for i in range(n_windows)]
    # Ajusta la última ventana para absorber el remanente
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
    """Simple split: retorna las n_windows sin folds. Útil para regime classification."""
    window_size = len(rows) // n_windows
    windows = [rows[i*window_size:(i+1)*window_size] for i in range(n_windows)]
    windows[-1] = rows[(n_windows-1)*window_size:]
    return windows


# ───────────────────────────────────────────────────────────────────────────
# 2. Regime classification
# ───────────────────────────────────────────────────────────────────────────

def _row_true_range(prev_close: float, high: float, low: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def compute_atr_series(rows: list, period: int = 14) -> List[float]:
    """ATR series (simple moving average de TR) sobre rows OHLC."""
    if len(rows) < period + 1:
        return []
    trs = []
    prev_close = float(rows[0]["close"])
    for r in rows[1:]:
        high = float(r["high"])
        low = float(r["low"])
        close = float(r["close"])
        trs.append(_row_true_range(prev_close, high, low))
        prev_close = close

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
    atr_low: float    # percentile 33% del ATR sobre TODA la data
    atr_high: float   # percentile 67%


def compute_regime_thresholds(all_rows: list, period: int = 14) -> RegimeThresholds:
    """Calcula los cuts de régimen sobre TODA la data disponible (una vez)."""
    atr = compute_atr_series(all_rows, period=period)
    return RegimeThresholds(
        atr_low=percentile(atr, V2_REGIME_LOW_PCT),
        atr_high=percentile(atr, V2_REGIME_HIGH_PCT),
    )


def classify_regime(window_rows: list, thresholds: RegimeThresholds,
                    period: int = 14) -> str:
    """Retorna el régimen dominante de una ventana usando ATR medio."""
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
    """
    Filtra rows para mantener solo barras cuyo régimen LOCAL (calculado en
    ventana deslizante de `window_size`) coincida con `target_regime`.
    Útil para Phase 2B (volatility + regime clustering).
    """
    if len(rows) < window_size:
        return rows if classify_regime(rows, thresholds, period) == target_regime else []

    kept = []
    for i in range(window_size, len(rows)):
        local_window = rows[i-window_size:i]
        if classify_regime(local_window, thresholds, period) == target_regime:
            kept.append(rows[i])
    return kept


# ───────────────────────────────────────────────────────────────────────────
# 3. VEC evaluation (batch de params sobre una misma ventana)
# ───────────────────────────────────────────────────────────────────────────

@dataclass
class ParamEvaluation:
    params: Comb002ImpulseParams
    pf: float
    wr: float
    trades: int
    equity: float


def evaluate_vec(params_list: List[Comb002ImpulseParams], rows: list) -> List[ParamEvaluation]:
    """
    VEC: evalúa N conjuntos de params sobre LA MISMA ventana de rows.
    Cachea la lista de rows (sin re-parseo). Retorna una evaluación por combo.

    Nota: Comb002ImpulseStrategy.run() internamente vectoriza indicadores por
    run. El caller puede paralelizar esto con multiprocessing Pool por fuera.
    """
    evaluations = []
    for p in params_list:
        strategy = Comb002ImpulseStrategy(p)
        result = strategy.run(rows)
        evaluations.append(ParamEvaluation(
            params=p,
            pf=round(result.profit_factor, 4),
            wr=round(result.win_rate, 4),
            trades=len(result.trades),
            equity=round(result.equity_points, 2),
        ))
    return evaluations


def evaluate_single(params: Comb002ImpulseParams, rows: list) -> ParamEvaluation:
    """Helper: evalúa un solo conjunto de params."""
    return evaluate_vec([params], rows)[0]


# ───────────────────────────────────────────────────────────────────────────
# 4. Score walk-forward y filtros V2
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


def score_walkforward(params: Comb002ImpulseParams,
                      folds: List[WalkForwardFold]) -> WalkForwardScore:
    """
    Ejecuta `params` en el TEST window de cada fold.
    Score principal V2 = min(PF_across_folds).
    """
    pfs = []
    trades = []
    for fold in folds:
        ev = evaluate_single(params, fold.test_rows)
        pfs.append(ev.pf)
        trades.append(ev.trades)

    return _build_score(pfs, trades)


def score_across_windows(params: Comb002ImpulseParams,
                         windows: List[list]) -> WalkForwardScore:
    """Variante: evalúa params sobre cada ventana completa (no fold test)."""
    pfs = []
    trades = []
    for w in windows:
        ev = evaluate_single(params, w)
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
    """
    Filtros HARD V2 (todos deben pasar):
      1. min(PF) ≥ 1.0          → no perder en ningún régimen
      2. min(trades) ≥ 20       → sample suficiente
      3. CV = std/mean ≤ 0.30   → consistencia entre ventanas
    """
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
# 5. Helpers de selección: top-N por min_pf (no por max_pf)
# ───────────────────────────────────────────────────────────────────────────

def select_top_n_walkforward(candidates: List[Tuple[Comb002ImpulseParams, WalkForwardScore]],
                              n: int = 3,
                              require_filter_pass: bool = True
                              ) -> List[Tuple[Comb002ImpulseParams, WalkForwardScore]]:
    """
    Ordena candidatos por `min_pf` descendente (V2 criterion).
    Si require_filter_pass=True, solo retorna los que pasan filtros V2.
    """
    if require_filter_pass:
        candidates = [(p, s) for p, s in candidates if s.passes_filters]
    candidates.sort(key=lambda ps: (ps[1].min_pf, -ps[1].cv, ps[1].mean_pf), reverse=True)
    return candidates[:n]


# ───────────────────────────────────────────────────────────────────────────
# 6. CLI rápido para verificar el engine
# ───────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="V2 engine smoke-test")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--n-windows", type=int, default=V2_N_WINDOWS)
    parser.add_argument("--n-train", type=int, default=V2_N_TRAIN_WINDOWS)
    args = parser.parse_args()

    rows = load_ohlc_csv(str(args.csv))
    print(f"Loaded {len(rows)} rows from {args.csv}")

    folds = split_walkforward(rows, args.n_windows, args.n_train)
    print(f"Generated {len(folds)} walk-forward folds (n_windows={args.n_windows}, n_train={args.n_train})")
    for f in folds:
        print(f"  fold {f.fold_id}: train={len(f.train_rows)} rows · test={len(f.test_rows)} rows")

    windows = split_all_windows(rows, args.n_windows)
    thresholds = compute_regime_thresholds(rows)
    print(f"\nATR thresholds: low<{thresholds.atr_low:.2f} · high≥{thresholds.atr_high:.2f}")
    for i, w in enumerate(windows):
        reg = classify_regime(w, thresholds)
        print(f"  W{i+1}: {len(w)} rows · regime={reg}")
