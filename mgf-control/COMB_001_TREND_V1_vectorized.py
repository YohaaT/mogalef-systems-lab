"""
COMB_001_TREND_V1_vectorized.py

Vectorized + multiprocessing version of COMB_001_TREND_V1.
Produces identical results as the original loop; optimization combos
run in parallel via multiprocessing.Pool.

Architecture:
- Phase 1 (vectorized): ATR, STPMT signals, Trend Filter, Horaire, Volatility
  computed as numpy arrays over full dataset in one pass.
- Phase 2 (loop): Position management loop (inherently stateful, cannot be
  vectorized without look-ahead risk). Runs after all array signals are ready.
- Pool: Each combo in the parameter grid gets one worker process; the pool
  distributes across all available cores.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in [
    ROOT / "mgf-divergence-lab" / "src",
    ROOT / "mgf-regime-filter-lab" / "src",
    ROOT / "mgf-stop-lab" / "src",
]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


# ── Shared dataclasses (same as original for drop-in compatibility) ──────────

@dataclass
class Comb001TrendParams:
    stpmt_smooth_h: int = 2
    stpmt_smooth_b: int = 2
    stpmt_mode: int = 1
    stpmt_decal_entry: int = 0
    stpmt_distance_max_h: int = 200
    stpmt_distance_max_l: int = 200
    trend_r1: int = 1
    trend_r2: int = 90
    trend_r3: int = 150
    trend_trade_only_case: int = 0
    trend_blocked_cases: tuple = field(default_factory=tuple)
    trend_off_on: int = 1
    trend_enforce_date_kill_switch: bool = True
    horaire_allowed_hours_utc: List[int] = field(default_factory=lambda: list(range(9, 16)))
    contexto_blocked_weekdays: List[int] = field(default_factory=list)  # 0=Mon,1=Tue,...6=Sun
    volatility_atr_period: int = 14
    volatility_atr_min: float = 0.0
    volatility_atr_max: float = 500.0
    target_atr_multiplier: float = 10.0
    timescan_bars: int = 30
    stop_intelligent_quality: int = 2
    stop_intelligent_recent_volat: int = 2
    stop_intelligent_ref_volat: int = 20
    stop_intelligent_coef_volat: float = 5.0


@dataclass
class Trade:
    side: str
    signal_index: int
    entry_index: int
    exit_index: int
    signal_timestamp: str
    entry_timestamp: str
    exit_timestamp: str
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    atr_at_entry: float
    pnl_points: float
    exit_reason: str
    bars_in_trade: int


@dataclass
class Comb001TrendResult:
    trades: List[Trade]
    equity_points: float
    wins: int
    losses: int
    profit_factor: float
    win_rate: float
    max_drawdown: float
    max_drawdown_idx: int
    avg_win: float
    avg_loss: float
    exit_reason_breakdown: Dict[str, int]


# ── Vectorized ATR ────────────────────────────────────────────────────────────

def _calc_atr_numpy(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """ATR using numpy. Result[i] = ATR computed from bars i..i+period-1 (same window as original)."""
    n = len(close)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    # TR = max(H-L, |C_prev - H|, |C_prev - L|)  — original uses i+1 close as "previous"
    # Original loop: for i in range(0, n-1): tr[i] = max(H[i]-L[i], |C[i+1]-L[i]|, |H[i]-C[i+1]|)
    tr[:-1] = np.maximum(
        high[:-1] - low[:-1],
        np.maximum(
            np.abs(close[1:] - low[:-1]),
            np.abs(high[:-1] - close[1:])
        )
    )
    tr[-1] = high[-1] - low[-1]  # last bar has no next-bar close

    # SMA over rolling window (same as original: atr[i] = mean(tr[i:i+period]))
    atr = np.full(n, np.nan)
    for i in range(n - period + 1):
        atr[i] = tr[i:i + period].mean()

    return atr


# ── Core strategy class ───────────────────────────────────────────────────────

class Comb001TrendVectorized:
    """Drop-in replacement for Comb001TrendStrategy using vectorized signal computation."""

    def __init__(self, params: Optional[Comb001TrendParams] = None) -> None:
        self.params = params or Comb001TrendParams()

    def run(self, rows: List[Dict[str, str]]) -> Comb001TrendResult:
        if not rows:
            raise ValueError("No data rows provided")

        # ── 1. Load arrays ────────────────────────────────────────────────────
        timestamps = [r["timestamp_utc"] for r in rows]
        open_arr  = np.array([float(r["open"])  for r in rows])
        high_arr  = np.array([float(r["high"])  for r in rows])
        low_arr   = np.array([float(r["low"])   for r in rows])
        close_arr = np.array([float(r["close"]) for r in rows])
        n = len(timestamps)

        # ── 2. Vectorized ATR ─────────────────────────────────────────────────
        atr = _calc_atr_numpy(high_arr, low_arr, close_arr, self.params.volatility_atr_period)

        # ── 3. STPMT signals (external lib, already vectorized internally) ────
        from EL_STPMT_DIV import compute_el_stpmt_div
        stpmt_result = compute_el_stpmt_div(
            high=list(high_arr),
            low=list(low_arr),
            close=list(close_arr),
            smooth_h=self.params.stpmt_smooth_h,
            smooth_b=self.params.stpmt_smooth_b,
            mode=self.params.stpmt_mode,
            decal_entry=self.params.stpmt_decal_entry,
            distance_max_h=self.params.stpmt_distance_max_h,
            distance_max_l=self.params.stpmt_distance_max_l,
        )
        if isinstance(stpmt_result, dict):
            stpmt_pose = stpmt_result.get("pose", [None] * n)
        else:
            stpmt_pose = getattr(stpmt_result, "pose", [None] * n)

        # ── 4. Trend Filter ───────────────────────────────────────────────────
        from EL_Mogalef_Trend_Filter_V2 import MogalefTrendFilterV2
        trend_filter = MogalefTrendFilterV2(
            r1=self.params.trend_r1,
            r2=self.params.trend_r2,
            r3=self.params.trend_r3,
            trade_only_case=self.params.trend_trade_only_case,
            blocked_cases=self.params.trend_blocked_cases,
            off_on=self.params.trend_off_on,
            enforce_date_kill_switch=self.params.trend_enforce_date_kill_switch,
        )
        dates_for_filter = None
        if timestamps and not timestamps[0].startswith("202"):
            dates_for_filter = timestamps
        trend_result = trend_filter.compute(
            list(open_arr), list(high_arr), list(low_arr), list(close_arr), dates=dates_for_filter
        )
        trend_sentiment = trend_result.sentiment if hasattr(trend_result, "sentiment") else ["block"] * n

        # ── 5. Vectorized Horaire mask ────────────────────────────────────────
        allowed_set = set(self.params.horaire_allowed_hours_utc)
        hours = np.array([int(ts[11:13]) for ts in timestamps])
        horaire_mask = np.isin(hours, list(allowed_set))

        # ── 5b. Vectorized Weekday block mask ─────────────────────────────────
        from datetime import datetime as _dt
        blocked_days = set(self.params.contexto_blocked_weekdays)
        if blocked_days:
            weekdays = np.array([_dt.strptime(ts[:10], "%Y-%m-%d").weekday() for ts in timestamps])
            weekday_mask = ~np.isin(weekdays, list(blocked_days))
        else:
            weekday_mask = np.ones(n, dtype=bool)

        # ── 6. Vectorized Volatility mask ─────────────────────────────────────
        atr_min = self.params.volatility_atr_min
        atr_max = self.params.volatility_atr_max
        volat_mask = (atr >= atr_min) & (atr <= atr_max)

        # ── 7. Stop Inteligente (pre-compute with flat position; updated in loop) ──
        from EL_Stop_Intelligent import StopIntelligent
        market_position = [0] * n
        stop_intel = StopIntelligent(
            quality=self.params.stop_intelligent_quality,
            recent_volat=self.params.stop_intelligent_recent_volat,
            ref_volat=self.params.stop_intelligent_ref_volat,
            coef_volat=self.params.stop_intelligent_coef_volat,
        )
        stop_intel_result = stop_intel.compute(list(high_arr), list(low_arr), list(close_arr), market_position)
        stop_intel_stops = stop_intel_result.stop

        # ── 8. Position management loop (stateful — cannot vectorize causally) ─
        trades: List[Trade] = []
        entry_side = None
        entry_index = None
        entry_price = None
        entry_timestamp = None
        signal_index = None
        signal_timestamp = None
        target_price = None
        stop_price = None
        atr_at_entry = None
        bars_in_trade = 0

        for i in range(n - 1):
            current_pose = stpmt_pose[i]
            current_sentiment = trend_sentiment[i]
            current_atr = float(atr[i]) if not np.isnan(atr[i]) else None
            h_ok = bool(horaire_mask[i]) and bool(weekday_mask[i])
            v_ok = bool(volat_mask[i]) if current_atr is not None else False

            if entry_index is not None:
                bars_in_trade = i - entry_index
                exit_triggered = False
                exit_reason = None
                exit_price_val = None
                exit_index_val = i

                # Priority 1: stop
                if entry_side == "long" and low_arr[i] <= stop_price:
                    exit_triggered = True
                    exit_reason = "stop"
                    exit_price_val = stop_price
                elif entry_side == "short" and high_arr[i] >= stop_price:
                    exit_triggered = True
                    exit_reason = "stop"
                    exit_price_val = stop_price

                # Priority 2: target
                if not exit_triggered:
                    if entry_side == "long" and high_arr[i] >= target_price:
                        exit_triggered = True
                        exit_reason = "target"
                        exit_price_val = target_price
                    elif entry_side == "short" and low_arr[i] <= target_price:
                        exit_triggered = True
                        exit_reason = "target"
                        exit_price_val = target_price

                # Priority 3: opposite signal
                if not exit_triggered and current_pose is not None and current_sentiment == "pass":
                    if (entry_side == "long" and current_pose == -1) or \
                       (entry_side == "short" and current_pose == 1):
                        exit_triggered = True
                        exit_reason = "opposite_signal"
                        exit_price_val = float(open_arr[i + 1]) if i + 1 < n else float(close_arr[i])
                        exit_index_val = i + 1

                # Priority 4: timescan
                if not exit_triggered and bars_in_trade >= self.params.timescan_bars:
                    exit_triggered = True
                    exit_reason = "timescan"
                    exit_price_val = float(close_arr[i])

                # Priority 5: end of data
                if not exit_triggered and i == n - 2:
                    exit_triggered = True
                    exit_reason = "end_of_data"
                    exit_price_val = float(close_arr[i + 1]) if i + 1 < n else float(close_arr[i])
                    exit_index_val = i + 1 if i + 1 < n else i

                if exit_triggered:
                    pnl = (exit_price_val - entry_price) if entry_side == "long" else (entry_price - exit_price_val)
                    trades.append(Trade(
                        side=entry_side,
                        signal_index=signal_index,
                        entry_index=entry_index,
                        exit_index=exit_index_val,
                        signal_timestamp=signal_timestamp,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=timestamps[exit_index_val] if exit_index_val < n else timestamps[n - 1],
                        entry_price=entry_price,
                        exit_price=exit_price_val,
                        stop_price=stop_price,
                        target_price=target_price,
                        atr_at_entry=atr_at_entry,
                        pnl_points=pnl,
                        exit_reason=exit_reason,
                        bars_in_trade=bars_in_trade,
                    ))
                    entry_side = entry_index = entry_price = entry_timestamp = None
                    signal_index = signal_timestamp = target_price = stop_price = atr_at_entry = None
                    bars_in_trade = 0
                    market_position[i] = 0

            # Entry check (vectorized masks used here for instant lookup)
            if entry_index is None:
                has_signal = current_pose is not None
                filter_allows = current_sentiment == "pass"

                if has_signal and filter_allows and h_ok and v_ok:
                    signal_index = i
                    signal_timestamp = timestamps[i]
                    entry_index = i + 1
                    entry_timestamp = timestamps[i + 1] if i + 1 < n else timestamps[i]
                    entry_price = float(open_arr[i + 1]) if i + 1 < n else float(close_arr[i])
                    entry_side = "long" if current_pose == 1 else "short"
                    atr_at_entry = current_atr

                    if current_atr is not None:
                        mult = self.params.target_atr_multiplier * current_atr
                        target_price = entry_price + mult if entry_side == "long" else entry_price - mult

                    if i + 1 < n and stop_intel_stops[i + 1] is not None:
                        stop_price = stop_intel_stops[i + 1]
                    else:
                        stop_price = float(low_arr[i]) if entry_side == "long" else float(high_arr[i])

                    market_position[i + 1] = 1 if entry_side == "long" else -1

        return self._calculate_result(trades)

    @staticmethod
    def _calculate_result(trades: List[Trade]) -> Comb001TrendResult:
        if not trades:
            return Comb001TrendResult(
                trades=[], equity_points=0.0, wins=0, losses=0,
                profit_factor=0.0, win_rate=0.0, max_drawdown=0.0,
                max_drawdown_idx=0, avg_win=0.0, avg_loss=0.0,
                exit_reason_breakdown={},
            )
        pnls = np.array([t.pnl_points for t in trades])
        equity_points = float(pnls.sum())
        wins   = int((pnls > 0).sum())
        losses = int((pnls <= 0).sum())
        gross_wins   = float(pnls[pnls > 0].sum())
        gross_losses = float(abs(pnls[pnls < 0].sum()))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else 0.0
        win_rate = wins / len(trades)

        cumul = np.cumsum(pnls)
        peak  = np.maximum.accumulate(cumul)
        dd    = peak - cumul
        max_dd_idx = int(dd.argmax())
        max_dd     = float(dd[max_dd_idx])

        avg_win  = gross_wins   / wins   if wins   > 0 else 0.0
        avg_loss = gross_losses / losses if losses > 0 else 0.0

        breakdown: Dict[str, int] = {}
        for t in trades:
            breakdown[t.exit_reason] = breakdown.get(t.exit_reason, 0) + 1

        return Comb001TrendResult(
            trades=trades, equity_points=equity_points, wins=wins, losses=losses,
            profit_factor=profit_factor, win_rate=win_rate, max_drawdown=max_dd,
            max_drawdown_idx=max_dd_idx, avg_win=avg_win, avg_loss=avg_loss,
            exit_reason_breakdown=breakdown,
        )


# ── Multiprocessing optimization runner ──────────────────────────────────────

def _run_single_combo(args: Tuple) -> dict:
    """Worker function: runs one parameter combo. Pickleable (top-level)."""
    rows, params_dict = args
    params = Comb001TrendParams(**params_dict)
    strategy = Comb001TrendVectorized(params)
    result = strategy.run(rows)
    gross_wins   = sum(t.pnl_points for t in result.trades if t.pnl_points > 0)
    gross_losses = abs(sum(t.pnl_points for t in result.trades if t.pnl_points < 0))
    return {
        **params_dict,
        "trades": len(result.trades),
        "wins": result.wins,
        "losses": result.losses,
        "equity": round(result.equity_points, 4),
        "profit_factor": round(result.profit_factor, 4),
        "win_rate": round(result.win_rate, 4),
        "max_drawdown": round(result.max_drawdown, 4),
        "gross_wins": round(gross_wins, 4),
        "gross_losses": round(gross_losses, 4),
    }


def run_optimization_pool(
    rows_phase_a: List[Dict[str, str]],
    rows_phase_b: List[Dict[str, str]],
    param_grid: List[dict],
    n_workers: Optional[int] = None,
) -> List[dict]:
    """
    Run all parameter combos in parallel using multiprocessing.Pool.

    Args:
        rows_phase_a: Training data rows
        rows_phase_b: Validation data rows
        param_grid:   List of param dicts (one per combo)
        n_workers:    Number of processes (defaults to cpu_count())

    Returns:
        List of result dicts sorted by robustness descending
    """
    n_workers = n_workers or cpu_count()
    print(f"[Pool] {len(param_grid)} combos / {n_workers} workers")

    args_a = [(rows_phase_a, p) for p in param_grid]
    args_b = [(rows_phase_b, p) for p in param_grid]

    with Pool(n_workers) as pool:
        results_a = pool.map(_run_single_combo, args_a)
        results_b = pool.map(_run_single_combo, args_b)

    combined = []
    for a, b in zip(results_a, results_b):
        pf_a = a["profit_factor"]
        pf_b = b["profit_factor"]
        robustness = pf_b / pf_a if pf_a > 0 else 0.0
        combined.append({
            **{f"phase_a_{k}": v for k, v in a.items()},
            **{f"phase_b_{k}": v for k, v in b.items()},
            "robustness": round(robustness, 4),
        })

    combined.sort(key=lambda x: x["robustness"], reverse=True)
    return combined


# ── CSV helpers ───────────────────────────────────────────────────────────────

def load_ohlc_csv(path: str | Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def export_results_csv(results: List[dict], path: str | Path) -> None:
    if not results:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
