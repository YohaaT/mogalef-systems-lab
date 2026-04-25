"""COMB_002 Impulse Trading Version B - Professional Scalping Strategy

Implements Eric Mogalef's independent optimization methodology:
- Signal: EL_STPMT_DIV divergence detection
- Contexto: Horaire + Volatility filters (NO Trend Filter - catches impulses in all regimes)
- Exits: Intelligent Scalping Target, 15-bar TimeStop, opposite signal
- Stops: SuperStop (faster/tighter than Stop Inteligente)

Temporal contract: Signal evaluated on bar t → Entry on bar t+1 open
TimeStop: 15 bars (shorter than Trend's 30 bars for quicker profit-taking)
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "mgf-divergence-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-divergence-lab" / "src"))
if str(ROOT / "mgf-regime-filter-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-regime-filter-lab" / "src"))
if str(ROOT / "mgf-stop-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-stop-lab" / "src"))

from EL_STPMT_DIV import compute_el_stpmt_div


@dataclass
class Comb002ImpulseParams:
    """Configuration for COMB_002 Impulse Trading Version B."""

    # Signal component (EL_STPMT_DIV)
    stpmt_smooth_h: int = 2
    stpmt_smooth_b: int = 2
    stpmt_mode: int = 1
    stpmt_decal_entry: int = 0
    stpmt_distance_max_h: int = 200
    stpmt_distance_max_l: int = 200

    # Contexto - Horaire (UTC hours allowed for trading)
    horaire_allowed_hours_utc: List[int] = field(default_factory=lambda: list(range(9, 16)))

    # Contexto - Volatility (ATR-based filter)
    volatility_atr_period: int = 14
    volatility_atr_min: float = 0.0
    volatility_atr_max: float = 500.0

    # Exits - Intelligent Scalping Target
    scalping_target_quality: int = 2
    scalping_target_recent_volat: int = 2
    scalping_target_ref_volat: int = 20
    scalping_target_coef_volat: float = 3.0  # Lower than Stop Inteligente for smaller targets

    # Exits - TimeStop (shorter for impulse)
    timescan_bars: int = 15

    # Stops - SuperStop
    superstop_quality: int = 2
    superstop_coef_volat: float = 3.0  # Tighter stop for scalping


@dataclass
class Trade:
    """A completed trade with full exit reasoning."""

    side: str  # "long" or "short"
    signal_index: int  # Bar index where signal appeared
    entry_index: int  # Bar index where entry executed (t+1)
    exit_index: int  # Bar index where exit executed
    signal_timestamp: str
    entry_timestamp: str
    exit_timestamp: str
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    atr_at_entry: float
    pnl_points: float
    exit_reason: str  # "stop", "target", "opposite_signal", "timescan"
    bars_in_trade: int


@dataclass
class Comb002ImpulseResult:
    """Backtest result with all metrics and trade-level details."""

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


class Comb002ImpulseStrategy:
    """COMB_002 Impulse Trading implementation following Mogalef methodology.

    Independent optimization of 3 main components:
    1. Signal: EL_STPMT_DIV divergence
    2. Contexto: Horaire + Volatility (NO Trend Filter - catches all impulses)
    3. Exits: Intelligent Scalping Target + TimeStop (15 bars) + opposite signal
    4. Stops: SuperStop (tighter than Stop Inteligente)

    Causal contract maintained: signal bar t → entry bar t+1 open
    """

    def __init__(self, params: Optional[Comb002ImpulseParams] = None) -> None:
        self.params = params or Comb002ImpulseParams()
        self._validate_params()

    def _validate_params(self) -> None:
        """Validate parameter ranges."""
        if self.params.stpmt_smooth_h < 1 or self.params.stpmt_smooth_h > 10:
            raise ValueError(f"stpmt_smooth_h must be 1-10, got {self.params.stpmt_smooth_h}")
        if self.params.stpmt_smooth_b < 1 or self.params.stpmt_smooth_b > 10:
            raise ValueError(f"stpmt_smooth_b must be 1-10, got {self.params.stpmt_smooth_b}")
        if self.params.scalping_target_coef_volat <= 0:
            raise ValueError(f"scalping_target_coef_volat must be > 0, got {self.params.scalping_target_coef_volat}")
        if self.params.timescan_bars < 5:
            raise ValueError(f"timescan_bars must be >= 5, got {self.params.timescan_bars}")
        if self.params.volatility_atr_min < 0 or self.params.volatility_atr_max < self.params.volatility_atr_min:
            raise ValueError(f"Invalid volatility range: [{self.params.volatility_atr_min}, {self.params.volatility_atr_max}]")

    def run(self, rows: List[Dict[str, str]]) -> Comb002ImpulseResult:
        """Execute backtest on canonical OHLC data.

        Args:
            rows: List of dicts with keys: timestamp_utc, open, high, low, close

        Returns:
            Comb002ImpulseResult with all trades and metrics
        """
        if not rows:
            raise ValueError("No data provided")

        # Parse OHLC
        n = len(rows)
        timestamps = []
        opens = []
        highs = []
        lows = []
        closes = []

        for row in rows:
            ts = row.get("timestamp_utc") or row.get("timestamp")
            timestamps.append(ts)
            opens.append(float(row["open"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            closes.append(float(row["close"]))

        # Calculate ATR
        atrs = self.calculate_atr(highs, lows, closes, self.params.volatility_atr_period)

        # Calculate STPMT signal
        stpmt_result = compute_el_stpmt_div(
            high=highs,
            low=lows,
            close=closes,
            smooth_h=self.params.stpmt_smooth_h,
            smooth_b=self.params.stpmt_smooth_b,
            mode=self.params.stpmt_mode,
            decal_entry=self.params.stpmt_decal_entry,
            distance_max_h=self.params.stpmt_distance_max_h,
            distance_max_l=self.params.stpmt_distance_max_l,
        )

        # STPMT returns dict-like structure with "pose" key
        if isinstance(stpmt_result, dict):
            poses = stpmt_result.get("pose", [None] * n)
        else:
            poses = getattr(stpmt_result, "pose", [None] * n)

        # Main backtest loop
        trades = []
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

        for i in range(n - 1):  # bar i is closed (signal bar)
            timestamp_utc = timestamps[i]
            high_i = highs[i]
            low_i = lows[i]
            close_i = closes[i]
            atr_i = atrs[i]

            # Extract hour for horaire check
            hour = int(timestamp_utc[11:13]) if len(timestamp_utc) > 11 else None

            # Check if trading allowed
            horaire_ok = hour in self.params.horaire_allowed_hours_utc if hour is not None else False
            volatility_ok = self.params.volatility_atr_min <= atr_i <= self.params.volatility_atr_max

            # Contexto check: Only horaire + volatility (NO trend filter for impulse)
            contexto_ok = horaire_ok and volatility_ok

            # Signal
            pose_i = poses[i]

            # Entry logic (bar i signal → bar i+1 execution)
            if entry_side is None and pose_i is not None and contexto_ok:
                # Mark entry for next bar
                signal_index = i
                signal_timestamp = timestamp_utc
                entry_index = i + 1
                entry_timestamp = timestamps[i + 1]
                entry_price = opens[i + 1]
                atr_at_entry = atr_i
                entry_side = "long" if pose_i == 1 else "short"

                # Calculate target using Intelligent Scalping Target logic
                # Simplified: scalping_target = entry_price ± (coef_volat × ATR)
                if entry_side == "long":
                    target_price = entry_price + (self.params.scalping_target_coef_volat * atr_at_entry)
                    # SuperStop: simple low-based stop with volatility adjustment
                    stop_price = low_i - (self.params.superstop_coef_volat * atr_at_entry / 2)
                else:
                    target_price = entry_price - (self.params.scalping_target_coef_volat * atr_at_entry)
                    # SuperStop: simple high-based stop with volatility adjustment
                    stop_price = high_i + (self.params.superstop_coef_volat * atr_at_entry / 2)

                bars_in_trade = 0

            # Exit logic
            elif entry_side is not None:
                bars_in_trade += 1
                high_trade = highs[i]
                low_trade = lows[i]
                close_trade = closes[i]

                exit_triggered = False
                exit_reason = None
                exit_price_val = None

                # 1. Stop hit
                if (entry_side == "long" and low_trade <= stop_price) or (entry_side == "short" and high_trade >= stop_price):
                    exit_triggered = True
                    exit_reason = "stop"
                    exit_price_val = stop_price
                # 2. Target hit
                elif (entry_side == "long" and high_trade >= target_price) or (entry_side == "short" and low_trade <= target_price):
                    exit_triggered = True
                    exit_reason = "target"
                    exit_price_val = target_price
                # 3. Opposite signal (only if horaire + volatility still ok)
                elif pose_i is not None:
                    entry_side_int = 1 if entry_side == "long" else -1
                    if pose_i != entry_side_int and contexto_ok:
                        exit_triggered = True
                        exit_reason = "opposite_signal"
                        exit_price_val = close_trade
                # 4. TimeStop (15 bars for impulse)
                elif bars_in_trade >= self.params.timescan_bars:
                    exit_triggered = True
                    exit_reason = "timescan"
                    exit_price_val = close_trade

                if exit_triggered:
                    pnl_points = (exit_price_val - entry_price) if entry_side == "long" else (entry_price - exit_price_val)
                    trade = Trade(
                        side=entry_side,
                        signal_index=signal_index,
                        entry_index=entry_index,
                        exit_index=i,
                        signal_timestamp=signal_timestamp,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=timestamps[i],
                        entry_price=entry_price,
                        exit_price=exit_price_val,
                        stop_price=stop_price,
                        target_price=target_price,
                        atr_at_entry=atr_at_entry,
                        pnl_points=pnl_points,
                        exit_reason=exit_reason,
                        bars_in_trade=bars_in_trade,
                    )
                    trades.append(trade)
                    entry_side = None

        return self._calculate_result(trades)

    @staticmethod
    def calculate_atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Calculate ATR (Average True Range) with SMA."""
        n = len(high)
        tr = [0.0] * n

        for i in range(n):
            h = high[i]
            l = low[i]
            c = close[i]
            c_prev = close[i - 1] if i > 0 else c

            tr1 = h - l
            tr2 = abs(c_prev - h)
            tr3 = abs(c_prev - l)
            tr[i] = max(tr1, tr2, tr3)

        # SMA of TR
        atr = [0.0] * n
        for i in range(period - 1, n):
            atr[i] = sum(tr[i - period + 1 : i + 1]) / period

        for i in range(period - 1):
            atr[i] = atr[period - 1]

        return atr

    def _calculate_result(self, trades: List[Trade]) -> Comb002ImpulseResult:
        """Calculate backtest metrics from trades."""
        if not trades:
            return Comb002ImpulseResult(
                trades=[],
                equity_points=0.0,
                wins=0,
                losses=0,
                profit_factor=0.0,
                win_rate=0.0,
                max_drawdown=0.0,
                max_drawdown_idx=0,
                avg_win=0.0,
                avg_loss=0.0,
                exit_reason_breakdown={},
            )

        equity_points = sum(t.pnl_points for t in trades)
        wins = sum(1 for t in trades if t.pnl_points > 0)
        losses = sum(1 for t in trades if t.pnl_points < 0)

        winning_trades = [t.pnl_points for t in trades if t.pnl_points > 0]
        losing_trades = [t.pnl_points for t in trades if t.pnl_points < 0]

        total_wins = sum(winning_trades) if winning_trades else 0.0
        total_losses = abs(sum(losing_trades)) if losing_trades else 1.0

        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        win_rate = wins / len(trades) if trades else 0.0
        avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0.0

        # Max drawdown
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        max_dd_idx = 0
        for idx, trade in enumerate(trades):
            cumulative += trade.pnl_points
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
                max_dd_idx = idx

        # Exit reason breakdown
        exit_reasons = {}
        for trade in trades:
            reason = trade.exit_reason
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

        return Comb002ImpulseResult(
            trades=trades,
            equity_points=equity_points,
            wins=wins,
            losses=losses,
            profit_factor=profit_factor,
            win_rate=win_rate,
            max_drawdown=max_dd,
            max_drawdown_idx=max_dd_idx,
            avg_win=avg_win,
            avg_loss=avg_loss,
            exit_reason_breakdown=exit_reasons,
        )

    def export_trades_csv(self, trades: List[Trade], filepath: str) -> None:
        """Export all trades to CSV."""
        if not trades:
            return

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "side",
                    "signal_index",
                    "entry_index",
                    "exit_index",
                    "signal_timestamp",
                    "entry_timestamp",
                    "exit_timestamp",
                    "entry_price",
                    "exit_price",
                    "stop_price",
                    "target_price",
                    "atr_at_entry",
                    "pnl_points",
                    "exit_reason",
                    "bars_in_trade",
                ],
            )
            writer.writeheader()
            for trade in trades:
                writer.writerow(
                    {
                        "side": trade.side,
                        "signal_index": trade.signal_index,
                        "entry_index": trade.entry_index,
                        "exit_index": trade.exit_index,
                        "signal_timestamp": trade.signal_timestamp,
                        "entry_timestamp": trade.entry_timestamp,
                        "exit_timestamp": trade.exit_timestamp,
                        "entry_price": round(trade.entry_price, 2),
                        "exit_price": round(trade.exit_price, 2),
                        "stop_price": round(trade.stop_price, 2),
                        "target_price": round(trade.target_price, 2),
                        "atr_at_entry": round(trade.atr_at_entry, 4),
                        "pnl_points": round(trade.pnl_points, 2),
                        "exit_reason": trade.exit_reason,
                        "bars_in_trade": trade.bars_in_trade,
                    }
                )

    def export_summary_json(self, result: Comb002ImpulseResult, filepath: str) -> None:
        """Export backtest summary to JSON."""
        summary = {
            "trade_count": len(result.trades),
            "wins": result.wins,
            "losses": result.losses,
            "win_rate": round(result.win_rate, 4),
            "equity_points": round(result.equity_points, 2),
            "profit_factor": round(result.profit_factor, 4),
            "max_drawdown": round(result.max_drawdown, 2),
            "avg_win": round(result.avg_win, 2),
            "avg_loss": round(result.avg_loss, 2),
            "exit_reason_breakdown": result.exit_reason_breakdown,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)


def load_ohlc_csv(filepath: str) -> List[Dict[str, str]]:
    """Load OHLC data from CSV. Renames 'timestamp' -> 'timestamp_utc' for compatibility."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Rename 'timestamp' to 'timestamp_utc' if needed
            if 'timestamp' in row and 'timestamp_utc' not in row:
                row['timestamp_utc'] = row.pop('timestamp')
            rows.append(row)
    return rows


if __name__ == "__main__":
    # Example usage
    params = Comb002ImpulseParams()
    strategy = Comb002ImpulseStrategy(params)

    # Load data
    data = load_ohlc_csv("YM_phase_A_clean.csv")
    result = strategy.run(data)

    print(f"Trades: {len(result.trades)}")
    print(f"Equity: {result.equity_points:.2f} pts")
    print(f"PF: {result.profit_factor:.4f}")
    print(f"WR: {result.win_rate:.2%}")
    print(f"Exit reasons: {result.exit_reason_breakdown}")
