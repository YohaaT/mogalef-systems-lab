"""COMB_001 Trend Trading Version A - Professional Trend Trading Strategy

Implements Eric Mogalef's independent optimization methodology:
- Signal: EL_STPMT_DIV divergence detection
- Contexto: Trend Filter + Horaire + Volatility filters
- Exits: 10 ATR profit target, 30-bar TimeStop, opposite signal
- Stops: Stop Inteligente (volatility-adaptive trailing)

Temporal contract: Signal evaluated on bar t → Entry on bar t+1 open
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
from EL_Mogalef_Trend_Filter_V2 import MogalefTrendFilterV2
from EL_Stop_Intelligent import StopIntelligent


@dataclass
class Comb001TrendParams:
    """Configuration for COMB_001 Trend Trading Version A."""

    # Signal component (EL_STPMT_DIV)
    stpmt_smooth_h: int = 2
    stpmt_smooth_b: int = 2
    stpmt_mode: int = 1
    stpmt_decal_entry: int = 0
    stpmt_distance_max_h: int = 200
    stpmt_distance_max_l: int = 200

    # Contexto - Trend Filter
    trend_r1: int = 1
    trend_r2: int = 90
    trend_r3: int = 150
    trend_trade_only_case: int = 0
    trend_blocked_cases: tuple = field(default_factory=tuple)
    trend_off_on: int = 1
    trend_enforce_date_kill_switch: bool = True

    # Contexto - Horaire (UTC hours allowed for trading)
    horaire_allowed_hours_utc: List[int] = field(default_factory=lambda: list(range(9, 16)))

    # Contexto - Volatility (ATR-based filter)
    volatility_atr_period: int = 14
    volatility_atr_min: float = 0.0
    volatility_atr_max: float = 500.0

    # Exits - Profit target
    target_atr_multiplier: float = 10.0

    # Exits - TimeStop
    timescan_bars: int = 30

    # Stops - Stop Inteligente
    stop_intelligent_quality: int = 2
    stop_intelligent_recent_volat: int = 2
    stop_intelligent_ref_volat: int = 20
    stop_intelligent_coef_volat: float = 5.0


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
class Comb001TrendResult:
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


class Comb001TrendStrategy:
    """COMB_001 Trend Trading implementation following Mogalef methodology.

    Independent optimization of 4 components:
    1. Signal: EL_STPMT_DIV divergence
    2. Contexto: Trend Filter + Horaire + Volatility
    3. Exits: 10 ATR target + TimeStop + opposite signal
    4. Stops: Stop Inteligente (volatility-adaptive)

    Causal contract maintained: signal bar t → entry bar t+1 open
    """

    def __init__(self, params: Optional[Comb001TrendParams] = None) -> None:
        self.params = params or Comb001TrendParams()
        self._validate_params()

    def _validate_params(self) -> None:
        """Validate parameter ranges."""
        if self.params.stpmt_smooth_h < 1 or self.params.stpmt_smooth_h > 10:
            raise ValueError(f"stpmt_smooth_h must be 1-10, got {self.params.stpmt_smooth_h}")
        if self.params.stpmt_smooth_b < 1 or self.params.stpmt_smooth_b > 10:
            raise ValueError(f"stpmt_smooth_b must be 1-10, got {self.params.stpmt_smooth_b}")
        if self.params.target_atr_multiplier <= 0:
            raise ValueError(f"target_atr_multiplier must be > 0, got {self.params.target_atr_multiplier}")
        if self.params.timescan_bars < 5:
            raise ValueError(f"timescan_bars must be >= 5, got {self.params.timescan_bars}")
        if self.params.volatility_atr_min < 0 or self.params.volatility_atr_max < self.params.volatility_atr_min:
            raise ValueError(f"Invalid volatility range: [{self.params.volatility_atr_min}, {self.params.volatility_atr_max}]")

    def run(self, rows: List[Dict[str, str]]) -> Comb001TrendResult:
        """Execute backtest on canonical OHLC data.

        Args:
            rows: List of dicts with keys: timestamp_utc, open, high, low, close

        Returns:
            Comb001TrendResult with all trades and metrics
        """
        if not rows:
            raise ValueError("No data rows provided")

        # Extract OHLC series
        timestamps = [row["timestamp_utc"] for row in rows]
        open_arr = [float(row["open"]) for row in rows]
        high_arr = [float(row["high"]) for row in rows]
        low_arr = [float(row["low"]) for row in rows]
        close_arr = [float(row["close"]) for row in rows]

        n = len(timestamps)

        # Compute components
        stpmt_result = compute_el_stpmt_div(
            high=high_arr,
            low=low_arr,
            close=close_arr,
            smooth_h=self.params.stpmt_smooth_h,
            smooth_b=self.params.stpmt_smooth_b,
            mode=self.params.stpmt_mode,
            decal_entry=self.params.stpmt_decal_entry,
            distance_max_h=self.params.stpmt_distance_max_h,
            distance_max_l=self.params.stpmt_distance_max_l,
        )
        # STPMT returns dict-like structure
        if isinstance(stpmt_result, dict):
            stpmt_pose = stpmt_result.get("pose", [None] * n)
        else:
            # Handle dataclass result if returned as object
            stpmt_pose = getattr(stpmt_result, "pose", [None] * n)

        # Trend Filter (pass None for dates if in ISO 8601 format to avoid validation issues)
        dates_for_filter = None
        if timestamps and not timestamps[0].startswith("202"):
            # If timestamp doesn't start with ISO format, pass it
            dates_for_filter = timestamps

        trend_filter = MogalefTrendFilterV2(
            r1=self.params.trend_r1,
            r2=self.params.trend_r2,
            r3=self.params.trend_r3,
            trade_only_case=self.params.trend_trade_only_case,
            blocked_cases=self.params.trend_blocked_cases,
            off_on=self.params.trend_off_on,
            enforce_date_kill_switch=self.params.trend_enforce_date_kill_switch,
        )
        trend_result = trend_filter.compute(open_arr, high_arr, low_arr, close_arr, dates=dates_for_filter)
        # TrendFilter returns MogalefTrendFilterV2Result object
        trend_sentiment = trend_result.sentiment if hasattr(trend_result, "sentiment") else ["block"] * n

        # ATR calculation
        atr = self._calculate_atr(high_arr, low_arr, close_arr, self.params.volatility_atr_period)

        # Stop Inteligente
        market_position = [0] * n  # Track position state (0=flat, 1=long, -1=short)
        stop_intel = StopIntelligent(
            quality=self.params.stop_intelligent_quality,
            recent_volat=self.params.stop_intelligent_recent_volat,
            ref_volat=self.params.stop_intelligent_ref_volat,
            coef_volat=self.params.stop_intelligent_coef_volat,
        )
        stop_intel_result = stop_intel.compute(high_arr, low_arr, close_arr, market_position)
        stop_intel_stops = stop_intel_result.stop

        # Main backtest loop
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
            current_timestamp = timestamps[i]
            current_pose = stpmt_pose[i]
            current_sentiment = trend_sentiment[i]
            current_atr = atr[i]
            current_hour = int(current_timestamp[11:13])

            # Check if trade is open
            if entry_index is not None:
                bars_in_trade = i - entry_index

                # Check 4 exit conditions in priority order
                exit_triggered = False
                exit_reason = None
                exit_price_val = None
                exit_index_val = i

                # 1. Check stop hit
                if entry_side == "long" and low_arr[i] <= stop_price:
                    exit_triggered = True
                    exit_reason = "stop"
                    exit_price_val = stop_price
                elif entry_side == "short" and high_arr[i] >= stop_price:
                    exit_triggered = True
                    exit_reason = "stop"
                    exit_price_val = stop_price

                # 2. Check target hit
                if not exit_triggered:
                    if entry_side == "long" and high_arr[i] >= target_price:
                        exit_triggered = True
                        exit_reason = "target"
                        exit_price_val = target_price
                    elif entry_side == "short" and low_arr[i] <= target_price:
                        exit_triggered = True
                        exit_reason = "target"
                        exit_price_val = target_price

                # 3. Check opposite signal (only if filter still allows)
                if not exit_triggered and current_pose is not None and current_sentiment == "pass":
                    if (entry_side == "long" and current_pose == -1) or \
                       (entry_side == "short" and current_pose == 1):
                        exit_triggered = True
                        exit_reason = "opposite_signal"
                        exit_price_val = open_arr[i + 1] if i + 1 < n else close_arr[i]
                        exit_index_val = i + 1

                # 4. Check TimeStop
                if not exit_triggered and bars_in_trade >= self.params.timescan_bars:
                    exit_triggered = True
                    exit_reason = "timescan"
                    exit_price_val = close_arr[i]

                # 5. Check end of data
                if not exit_triggered and i == n - 2:
                    exit_triggered = True
                    exit_reason = "end_of_data"
                    exit_price_val = close_arr[i + 1] if i + 1 < n else close_arr[i]
                    exit_index_val = i + 1 if i + 1 < n else i

                # Close trade if exit triggered
                if exit_triggered:
                    pnl = 0.0
                    if entry_side == "long":
                        pnl = exit_price_val - entry_price
                    else:  # short
                        pnl = entry_price - exit_price_val

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

                    # Reset position
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
                    market_position[i] = 0

            # Check entry conditions (if no position open)
            if entry_index is None:
                # All filters must pass
                has_signal = current_pose is not None
                filter_allows = current_sentiment == "pass"
                hour_allowed = current_hour in self.params.horaire_allowed_hours_utc
                volatility_ok = (self.params.volatility_atr_min <= current_atr <= self.params.volatility_atr_max) \
                    if current_atr is not None else False

                if has_signal and filter_allows and hour_allowed and volatility_ok:
                    # Prepare entry for next bar (t+1)
                    signal_index = i
                    signal_timestamp = current_timestamp
                    entry_index = i + 1
                    entry_timestamp = timestamps[i + 1] if i + 1 < n else current_timestamp
                    entry_price = open_arr[i + 1] if i + 1 < n else close_arr[i]
                    entry_side = "long" if current_pose == 1 else "short"
                    atr_at_entry = current_atr

                    # Calculate target (10 ATR from entry)
                    if current_atr is not None:
                        if entry_side == "long":
                            target_price = entry_price + (self.params.target_atr_multiplier * current_atr)
                        else:  # short
                            target_price = entry_price - (self.params.target_atr_multiplier * current_atr)

                    # Calculate initial stop (use Stop Inteligente if available, else signal bar low/high)
                    if i + 1 < n and stop_intel_stops[i + 1] is not None:
                        stop_price = stop_intel_stops[i + 1]
                    else:
                        # Causal fallback: use signal bar low/high
                        if entry_side == "long":
                            stop_price = low_arr[i]
                        else:  # short
                            stop_price = high_arr[i]

                    # Update market position for Stop Inteligente
                    market_position[i + 1] = 1 if entry_side == "long" else -1

        # Calculate metrics
        result = self._calculate_result(trades)
        return result

    @staticmethod
    def _calculate_atr(
        high: List[float],
        low: List[float],
        close: List[float],
        period: int = 14,
    ) -> List[Optional[float]]:
        """Calculate ATR (Average True Range)."""
        n = len(close)

        # True Range
        tr = [None] * n
        for i in range(0, n - 1):
            tr1 = high[i] - low[i]
            tr2 = abs(close[i + 1] - low[i])
            tr3 = abs(high[i] - close[i + 1])
            tr[i] = max(tr1, tr2, tr3)

        # SMA of TR
        atr = [None] * n
        for i in range(len(tr)):
            if i + period > len(tr):
                continue
            sample = tr[i : i + period]
            if any(v is None for v in sample):
                continue
            atr[i] = sum(sample) / period

        return atr

    def _calculate_result(self, trades: List[Trade]) -> Comb001TrendResult:
        """Calculate aggregate backtest metrics."""
        if not trades:
            return Comb001TrendResult(
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
        losses = sum(1 for t in trades if t.pnl_points <= 0)

        # Profit Factor
        gross_wins = sum(t.pnl_points for t in trades if t.pnl_points > 0)
        gross_losses = abs(sum(t.pnl_points for t in trades if t.pnl_points < 0))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else 0.0

        # Win Rate
        win_rate = (wins / len(trades)) if trades else 0.0

        # Max Drawdown
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        max_dd_idx = 0
        for i, t in enumerate(trades):
            cumulative += t.pnl_points
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
                max_dd_idx = i

        # Average win/loss
        avg_win = (gross_wins / wins) if wins > 0 else 0.0
        avg_loss = (gross_losses / losses) if losses > 0 else 0.0

        # Exit reason breakdown
        exit_reason_breakdown: Dict[str, int] = {}
        for t in trades:
            exit_reason_breakdown[t.exit_reason] = exit_reason_breakdown.get(t.exit_reason, 0) + 1

        return Comb001TrendResult(
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
            exit_reason_breakdown=exit_reason_breakdown,
        )


def load_ohlc_csv(path: str | Path) -> List[Dict[str, str]]:
    """Load canonical OHLC CSV."""
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp_utc", "open", "high", "low", "close"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def export_trades_csv(trades: List[Trade], path: str | Path) -> None:
    """Export trades with all fields including new Trend Trading data."""
    fieldnames = [
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
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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
                    "entry_price": f"{trade.entry_price:.10f}",
                    "exit_price": f"{trade.exit_price:.10f}",
                    "stop_price": f"{trade.stop_price:.10f}",
                    "target_price": f"{trade.target_price:.10f}",
                    "atr_at_entry": f"{trade.atr_at_entry:.10f}" if trade.atr_at_entry else "",
                    "pnl_points": f"{trade.pnl_points:.10f}",
                    "exit_reason": trade.exit_reason,
                    "bars_in_trade": trade.bars_in_trade,
                }
            )


def export_summary_json(result: Comb001TrendResult, path: str | Path) -> None:
    """Export backtest summary as JSON."""
    summary = {
        "trade_count": len(result.trades),
        "wins": result.wins,
        "losses": result.losses,
        "win_rate": f"{result.win_rate:.4f}",
        "equity_points": f"{result.equity_points:.4f}",
        "profit_factor": f"{result.profit_factor:.4f}",
        "max_drawdown": f"{result.max_drawdown:.4f}",
        "max_drawdown_trade_idx": result.max_drawdown_idx,
        "avg_win": f"{result.avg_win:.4f}",
        "avg_loss": f"{result.avg_loss:.4f}",
        "exit_reason_breakdown": result.exit_reason_breakdown,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run COMB_001 Trend Trading Version A on canonical OHLC CSV")
    parser.add_argument("csv_path", help="Path to canonical OHLC CSV")
    parser.add_argument("--trades-out", help="Optional path to export trade log as CSV")
    parser.add_argument("--summary-out", help="Optional path to export summary as JSON")
    args = parser.parse_args()

    rows = load_ohlc_csv(args.csv_path)
    strategy = Comb001TrendStrategy()
    result = strategy.run(rows)

    if args.trades_out:
        export_trades_csv(result.trades, args.trades_out)
        print(f"trades_csv={args.trades_out}")

    if args.summary_out:
        export_summary_json(result, args.summary_out)
        print(f"summary_json={args.summary_out}")

    print(f"trades={len(result.trades)}")
    print(f"wins={result.wins}")
    print(f"losses={result.losses}")
    print(f"win_rate={result.win_rate:.4f}")
    print(f"equity_points={result.equity_points:.4f}")
    print(f"profit_factor={result.profit_factor:.4f}")
    print(f"max_drawdown={result.max_drawdown:.4f}")
    print(f"avg_win={result.avg_win:.4f}")
    print(f"avg_loss={result.avg_loss:.4f}")
    print(f"exit_reason_breakdown={result.exit_reason_breakdown}")
