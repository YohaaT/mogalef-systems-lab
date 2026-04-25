"""COMB_002 Impulse V2 ADAPTIVE - true Intelligent Scalping Target.

Differences vs COMB_002_IMPULSE_V1:
  1. Uses IntelligentScalpingTarget (target recomputed every bar during trade,
     adjusts CLOSER to entry to minimise losses on bad trades — MTI Club spec).
  2. Adds day-of-week filter (`allowed_weekdays`, default = all 7 days).
  3. Defaults `horaire_allowed_hours_utc` to range(0,24) -> baseline NO temporal
     restrictions (Fase 0 baseline). Phases 2a / day-filter apply restrictions.

Temporal contract preserved: signal bar t -> entry bar t+1 open.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import sys

ROOT = Path(__file__).resolve().parents[1]
for sub in ("mgf-divergence-lab", "mgf-regime-filter-lab", "mgf-stop-lab"):
    p = str(ROOT / sub / "src")
    if p not in sys.path:
        sys.path.append(p)

from EL_STPMT_DIV import compute_el_stpmt_div
from EL_Intelligent_Scalping_Target import IntelligentScalpingTarget


@dataclass
class Comb002ImpulseV2Params:
    # Signal
    stpmt_smooth_h: int = 2
    stpmt_smooth_b: int = 2
    stpmt_mode: int = 1
    stpmt_decal_entry: int = 0
    stpmt_distance_max_h: int = 200
    stpmt_distance_max_l: int = 200

    # Horaire (default = ALL hours -> baseline)
    horaire_allowed_hours_utc: List[int] = field(default_factory=lambda: list(range(24)))

    # Day filter (default = ALL days, 0=Mon ... 6=Sun -> baseline)
    allowed_weekdays: List[int] = field(default_factory=lambda: list(range(7)))

    # Volatility filter (default = OFF for COMB_002 per Mogalef spec)
    volatility_atr_period: int = 14
    volatility_atr_min: float = 0.0
    volatility_atr_max: float = 1.0e9  # effectively OFF

    # Intelligent Scalping Target (adaptive)
    scalping_target_quality: int = 2
    scalping_target_recent_volat: int = 2
    scalping_target_ref_volat: int = 20
    scalping_target_coef_volat: float = 3.0
    scalping_target_first_low_or_more: int = 2
    scalping_target_first_high_or_more: int = 2

    # TimeStop
    timescan_bars: int = 15

    # SuperStop (kept simple for now: ATR-multiple stop set at entry)
    superstop_quality: int = 2
    superstop_coef_volat: float = 3.0


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
    target_price_at_exit: float
    atr_at_entry: float
    pnl_points: float
    exit_reason: str
    bars_in_trade: int


@dataclass
class Comb002ImpulseV2Result:
    trades: List[Trade]
    equity_points: float
    wins: int
    losses: int
    profit_factor: float
    win_rate: float
    max_drawdown: float
    avg_win: float
    avg_loss: float
    exit_reason_breakdown: Dict[str, int]


class Comb002ImpulseV2Strategy:
    def __init__(self, params: Optional[Comb002ImpulseV2Params] = None) -> None:
        self.params = params or Comb002ImpulseV2Params()

    @staticmethod
    def _atr_sma(highs: List[float], lows: List[float], closes: List[float], period: int) -> List[float]:
        import numpy as np
        try:
            from vec_mogalef_core import atr_sma
            return atr_sma(np.array(highs), np.array(lows), np.array(closes), period).tolist()
        except ImportError:
            # fallback to loop if vec not available
            n = len(highs)
            tr = [0.0] * n
            for i in range(n):
                c_prev = closes[i - 1] if i > 0 else closes[i]
                tr[i] = max(highs[i] - lows[i], abs(c_prev - highs[i]), abs(c_prev - lows[i]))
            atr = [0.0] * n
            if n >= period:
                window_sum = sum(tr[:period])
                atr[period - 1] = window_sum / period
                for i in range(period, n):
                    window_sum += tr[i] - tr[i - period]
                    atr[i] = window_sum / period
                for i in range(period - 1):
                    atr[i] = atr[period - 1]
            return atr

    def run(self, rows: List[Dict[str, str]]) -> Comb002ImpulseV2Result:
        if not rows:
            raise ValueError("No data provided")

        n = len(rows)
        timestamps: List[str] = []
        opens: List[float] = []
        highs: List[float] = []
        lows: List[float] = []
        closes: List[float] = []
        for row in rows:
            ts = row.get("timestamp_utc") or row.get("timestamp")
            timestamps.append(ts)
            opens.append(float(row["open"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            closes.append(float(row["close"]))

        atrs = self._atr_sma(highs, lows, closes, self.params.volatility_atr_period)

        stpmt = compute_el_stpmt_div(
            high=highs, low=lows, close=closes,
            smooth_h=self.params.stpmt_smooth_h,
            smooth_b=self.params.stpmt_smooth_b,
            mode=self.params.stpmt_mode,
            decal_entry=self.params.stpmt_decal_entry,
            distance_max_h=self.params.stpmt_distance_max_h,
            distance_max_l=self.params.stpmt_distance_max_l,
        )
        poses = stpmt.get("pose", [None] * n) if isinstance(stpmt, dict) else getattr(stpmt, "pose", [None] * n)

        # Pre-parse weekday + hour per bar
        hours = [int(ts[11:13]) if ts and len(ts) > 11 else None for ts in timestamps]
        weekdays = []
        for ts in timestamps:
            try:
                weekdays.append(datetime.strptime(ts[:10], "%Y-%m-%d").weekday())
            except Exception:
                weekdays.append(None)

        allowed_hours = set(self.params.horaire_allowed_hours_utc)
        allowed_days = set(self.params.allowed_weekdays)

        # Trade simulation. Scalping target is recomputed bar-by-bar during a trade
        # by running IntelligentScalpingTarget on the WINDOW [entry_index .. i] with
        # market_position fixed to current side. To keep this O(n) instead of O(n^2),
        # we compute the full target series ONCE assuming a synthetic continuous position;
        # the practical implementation below recomputes per-trade on small windows.
        scalping = IntelligentScalpingTarget(
            quality=self.params.scalping_target_quality,
            recent_volat=self.params.scalping_target_recent_volat,
            ref_volat=self.params.scalping_target_ref_volat,
            coef_volat=self.params.scalping_target_coef_volat,
            first_low_or_more=self.params.scalping_target_first_low_or_more,
            first_high_or_more=self.params.scalping_target_first_high_or_more,
        )

        trades: List[Trade] = []
        entry_side: Optional[str] = None
        entry_index = entry_price = atr_at_entry = 0
        signal_index = 0
        signal_timestamp = entry_timestamp = ""
        stop_price = 0.0
        current_target = 0.0
        bars_in_trade = 0

        for i in range(n - 1):
            ts = timestamps[i]
            hi, lo, cl, atr_i = highs[i], lows[i], closes[i], atrs[i]

            horaire_ok = hours[i] in allowed_hours if hours[i] is not None else False
            day_ok = weekdays[i] in allowed_days if weekdays[i] is not None else False
            vol_ok = self.params.volatility_atr_min <= atr_i <= self.params.volatility_atr_max
            contexto_ok = horaire_ok and day_ok and vol_ok

            pose_i = poses[i] if i < len(poses) else None

            if entry_side is None and pose_i is not None and contexto_ok:
                signal_index = i
                signal_timestamp = ts
                entry_index = i + 1
                entry_timestamp = timestamps[i + 1]
                entry_price = opens[i + 1]
                atr_at_entry = atr_i
                entry_side = "long" if pose_i == 1 else "short"

                if entry_side == "long":
                    stop_price = lo - (self.params.superstop_coef_volat * atr_at_entry / 2.0)
                    current_target = entry_price + (self.params.scalping_target_coef_volat * atr_at_entry)
                else:
                    stop_price = hi + (self.params.superstop_coef_volat * atr_at_entry / 2.0)
                    current_target = entry_price - (self.params.scalping_target_coef_volat * atr_at_entry)
                bars_in_trade = 0

            elif entry_side is not None:
                bars_in_trade += 1

                # Recompute adaptive target on window [entry_index .. i]
                start = entry_index
                window_h = highs[start : i + 1]
                window_l = lows[start : i + 1]
                window_c = closes[start : i + 1]
                mp = [1 if entry_side == "long" else -1] * len(window_c)
                tres = scalping.compute(window_h, window_l, window_c, mp)
                new_target = tres.target[0] if tres.target and tres.target[0] is not None else None

                # Closer-only update rule (target moves toward entry, never further away)
                if new_target is not None:
                    if entry_side == "long" and new_target < current_target:
                        current_target = new_target
                    elif entry_side == "short" and new_target > current_target:
                        current_target = new_target

                exit_triggered = False
                exit_reason = ""
                exit_price_val = 0.0

                if (entry_side == "long" and lo <= stop_price) or (entry_side == "short" and hi >= stop_price):
                    exit_triggered, exit_reason, exit_price_val = True, "stop", stop_price
                elif (entry_side == "long" and hi >= current_target) or (entry_side == "short" and lo <= current_target):
                    exit_triggered, exit_reason, exit_price_val = True, "target", current_target
                elif pose_i is not None:
                    side_int = 1 if entry_side == "long" else -1
                    if pose_i != side_int and contexto_ok:
                        exit_triggered, exit_reason, exit_price_val = True, "opposite_signal", cl
                elif bars_in_trade >= self.params.timescan_bars:
                    exit_triggered, exit_reason, exit_price_val = True, "timescan", cl

                if exit_triggered:
                    pnl = (exit_price_val - entry_price) if entry_side == "long" else (entry_price - exit_price_val)
                    trades.append(Trade(
                        side=entry_side,
                        signal_index=signal_index,
                        entry_index=entry_index,
                        exit_index=i,
                        signal_timestamp=signal_timestamp,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=ts,
                        entry_price=entry_price,
                        exit_price=exit_price_val,
                        stop_price=stop_price,
                        target_price_at_exit=current_target,
                        atr_at_entry=atr_at_entry,
                        pnl_points=pnl,
                        exit_reason=exit_reason,
                        bars_in_trade=bars_in_trade,
                    ))
                    entry_side = None

        return self._summary(trades)

    def _summary(self, trades: List[Trade]) -> Comb002ImpulseV2Result:
        if not trades:
            return Comb002ImpulseV2Result([], 0.0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, {})
        eq = sum(t.pnl_points for t in trades)
        wins = sum(1 for t in trades if t.pnl_points > 0)
        losses = sum(1 for t in trades if t.pnl_points < 0)
        win_pnl = [t.pnl_points for t in trades if t.pnl_points > 0]
        loss_pnl = [t.pnl_points for t in trades if t.pnl_points < 0]
        gw = sum(win_pnl) if win_pnl else 0.0
        gl = abs(sum(loss_pnl)) if loss_pnl else 1.0
        pf = gw / gl if gl > 0 else 0.0
        wr = wins / len(trades)
        avg_w = (sum(win_pnl) / len(win_pnl)) if win_pnl else 0.0
        avg_l = (sum(loss_pnl) / len(loss_pnl)) if loss_pnl else 0.0
        cum = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            cum += t.pnl_points
            peak = max(peak, cum)
            max_dd = max(max_dd, peak - cum)
        breakdown: Dict[str, int] = {}
        for t in trades:
            breakdown[t.exit_reason] = breakdown.get(t.exit_reason, 0) + 1
        return Comb002ImpulseV2Result(trades, eq, wins, losses, pf, wr, max_dd, avg_w, avg_l, breakdown)


def load_ohlc_csv(filepath: str) -> List[Dict[str, str]]:
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "timestamp" in row and "timestamp_utc" not in row:
                row["timestamp_utc"] = row.get("timestamp")
            rows.append(row)
    return rows


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = ap.parse_args()

    data = load_ohlc_csv(args.csv)
    if args.limit > 0:
        data = data[: args.limit]
    strat = Comb002ImpulseV2Strategy()
    res = strat.run(data)
    print(f"trades={len(res.trades)}  equity={res.equity_points:.2f}  PF={res.profit_factor:.4f}  "
          f"WR={res.win_rate:.2%}  max_dd={res.max_drawdown:.2f}  exits={res.exit_reason_breakdown}")
