"""COMB_003 Breakout Trading Version C - Structural Breakout Strategy

Implements Eric Mogalef's Breakout Trading methodology:
- Signal: Bullish/Bearish Breakout detection
- Contexto: Neutral Zone filter + Mogalef Trend Filter + Horaire
- Exits: Fixed profit target + Fixed stop loss
- Risk/Reward: 1:4 ratio (stop=15-20, target=60-80 points)

Temporal contract: Signal evaluated on bar t → Entry on bar t+1 open
Timeframe: 15-minute bars for swing/intraday trading
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

from EL_Mogalef_Trend_Filter_V2 import MogalefTrendFilterV2
from EL_NeutralZone_B_V2 import NeutralZoneBV2


@dataclass
class Comb003BreakoutParams:
    """Configuration for COMB_003 Breakout Trading Version C."""

    # Signal component (Breakout detection)
    breakout_lookback_high: int = 10  # Bars to look back for breakout high
    breakout_lookback_low: int = 10  # Bars to look back for breakout low
    breakout_min_breakout_points: float = 5.0  # Minimum pts to qualify as breakout

    # Contexto - Neutral Zone filter
    neutralzone_mme_period: int = 50  # EMA period for trend (50 for filter)
    neutralzone_ret_window: int = 90  # RET window (middle of 90 bars)
    neutralzone_trend_indic_size: int = 15  # Trend indicator size
    neutralzone_use_senti: str = "pass"  # "pass" only on senti=1/-1 (filter out 0)

    # Contexto - Trend Filter (Mogalef)
    trend_r1: int = 1
    trend_r2: int = 90
    trend_r3: int = 150

    # Contexto - Horaire (UTC hours allowed for trading)
    horaire_allowed_hours_utc: List[int] = field(default_factory=lambda: list(range(8, 22)))  # 8 AM - 10 PM UTC

    # Exits - Fixed stops and targets
    stop_loss_points: float = 20.0  # Fixed stop loss in points
    profit_target_points: float = 80.0  # Fixed profit target in points

    # Risk/Reward ratio check
    target_risk_reward_ratio: float = 4.0  # target/stop should be ~4:1


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
    pnl_points: float
    exit_reason: str  # "stop", "target"
    bars_in_trade: int


@dataclass
class Comb003BreakoutResult:
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


class Comb003BreakoutStrategy:
    """COMB_003 Breakout Trading implementation following Mogalef methodology.

    Independent components:
    1. Signal: Structural Breakout (price breaks above/below lookback range)
    2. Contexto: Neutral Zone + Trend Filter + Horaire
    3. Exits: Fixed stop + fixed target (1:4 risk/reward)

    Causal contract maintained: signal bar t → entry bar t+1 open
    """

    def __init__(self, params: Optional[Comb003BreakoutParams] = None) -> None:
        self.params = params or Comb003BreakoutParams()
        self._validate_params()

    def _validate_params(self) -> None:
        """Validate parameter ranges."""
        if self.params.breakout_lookback_high < 1:
            raise ValueError(f"breakout_lookback_high must be >= 1")
        if self.params.breakout_lookback_low < 1:
            raise ValueError(f"breakout_lookback_low must be >= 1")
        if self.params.stop_loss_points <= 0:
            raise ValueError(f"stop_loss_points must be > 0")
        if self.params.profit_target_points <= 0:
            raise ValueError(f"profit_target_points must be > 0")

    def run(self, rows: List[Dict[str, str]]) -> Comb003BreakoutResult:
        """Execute backtest on canonical OHLC data.

        Args:
            rows: List of dicts with keys: timestamp_utc, open, high, low, close

        Returns:
            Comb003BreakoutResult with all trades and metrics
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
            timestamps.append(row["timestamp_utc"])
            opens.append(float(row["open"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            closes.append(float(row["close"]))

        # Initialize Neutral Zone filter
        neutral_zone = NeutralZoneBV2(
            use_as="filter",
            mme_period=self.params.neutralzone_mme_period,
            ret_window=self.params.neutralzone_ret_window,
            trend_indic_size=self.params.neutralzone_trend_indic_size,
        )
        nz_result = neutral_zone.compute(highs, lows, closes, tick_size=1.0)
        nz_senti = nz_result.senti

        # Initialize Trend Filter
        trend_filter = MogalefTrendFilterV2(
            r1=self.params.trend_r1,
            r2=self.params.trend_r2,
            r3=self.params.trend_r3,
        )
        trend_result = trend_filter.compute(opens, highs, lows, closes)
        trend_sentiment = trend_result.sentiment if hasattr(trend_result, "sentiment") else ["block"] * n

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
        bars_in_trade = 0

        for i in range(n - 1):  # bar i is closed (signal bar)
            timestamp_utc = timestamps[i]
            high_i = highs[i]
            low_i = lows[i]
            close_i = closes[i]

            # Extract hour for horaire check
            hour = int(timestamp_utc[11:13]) if len(timestamp_utc) > 11 else None
            horaire_ok = hour in self.params.horaire_allowed_hours_utc if hour is not None else False

            # Neutral Zone filter
            nz_ok = nz_senti[i] != 0 if i < len(nz_senti) else False

            # Trend Filter
            trend_ok = trend_sentiment[i] == "pass" if i < len(trend_sentiment) else False

            # Contexto check
            contexto_ok = horaire_ok and nz_ok and trend_ok

            # Breakout signal detection
            long_breakout = False
            short_breakout = False

            if i >= self.params.breakout_lookback_high:
                # Check if price breaks above recent highs (long breakout)
                lookback_high = max(highs[i - self.params.breakout_lookback_high : i])
                if close_i > lookback_high + self.params.breakout_min_breakout_points:
                    long_breakout = True

            if i >= self.params.breakout_lookback_low:
                # Check if price breaks below recent lows (short breakout)
                lookback_low = min(lows[i - self.params.breakout_lookback_low : i])
                if close_i < lookback_low - self.params.breakout_min_breakout_points:
                    short_breakout = True

            # Entry logic (bar i signal → bar i+1 execution)
            if entry_side is None and contexto_ok:
                if long_breakout:
                    signal_index = i
                    signal_timestamp = timestamp_utc
                    entry_index = i + 1
                    entry_timestamp = timestamps[i + 1]
                    entry_price = opens[i + 1]
                    entry_side = "long"
                    stop_price = entry_price - self.params.stop_loss_points
                    target_price = entry_price + self.params.profit_target_points
                    bars_in_trade = 0

                elif short_breakout:
                    signal_index = i
                    signal_timestamp = timestamp_utc
                    entry_index = i + 1
                    entry_timestamp = timestamps[i + 1]
                    entry_price = opens[i + 1]
                    entry_side = "short"
                    stop_price = entry_price + self.params.stop_loss_points
                    target_price = entry_price - self.params.profit_target_points
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
                if (entry_side == "long" and low_trade <= stop_price) or \
                   (entry_side == "short" and high_trade >= stop_price):
                    exit_triggered = True
                    exit_reason = "stop"
                    exit_price_val = stop_price

                # 2. Target hit
                elif (entry_side == "long" and high_trade >= target_price) or \
                     (entry_side == "short" and low_trade <= target_price):
                    exit_triggered = True
                    exit_reason = "target"
                    exit_price_val = target_price

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
                        pnl_points=pnl_points,
                        exit_reason=exit_reason,
                        bars_in_trade=bars_in_trade,
                    )
                    trades.append(trade)
                    entry_side = None

        return self._calculate_result(trades)

    def _calculate_result(self, trades: List[Trade]) -> Comb003BreakoutResult:
        """Calculate backtest metrics from trades."""
        if not trades:
            return Comb003BreakoutResult(
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

        return Comb003BreakoutResult(
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
                        "pnl_points": round(trade.pnl_points, 2),
                        "exit_reason": trade.exit_reason,
                        "bars_in_trade": trade.bars_in_trade,
                    }
                )

    def export_summary_json(self, result: Comb003BreakoutResult, filepath: str) -> None:
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
    """Load OHLC data from CSV."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


if __name__ == "__main__":
    # Example usage
    params = Comb003BreakoutParams()
    strategy = Comb003BreakoutStrategy(params)

    # Load data
    data = load_ohlc_csv("YM_phase_A_clean.csv")
    result = strategy.run(data)

    print(f"Trades: {len(result.trades)}")
    print(f"Equity: {result.equity_points:.2f} pts")
    print(f"PF: {result.profit_factor:.4f}")
    print(f"WR: {result.win_rate:.2%}")
    print(f"Exit reasons: {result.exit_reason_breakdown}")
