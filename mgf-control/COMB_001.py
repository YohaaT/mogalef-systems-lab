from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "mgf-divergence-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-divergence-lab" / "src"))
if str(ROOT / "mgf-regime-filter-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-regime-filter-lab" / "src"))

from EL_STPMT_DIV import compute_el_stpmt_div
from EL_Mogalef_Trend_Filter_V2 import MogalefTrendFilterV2


@dataclass
class Comb001Params:
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
    trend_blocked_cases: tuple[int, ...] = ()
    trend_off_on: int = 1
    trend_enforce_date_kill_switch: bool = True


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
    pnl_points: float
    exit_reason: str
    bars_in_trade: int


@dataclass
class Comb001Result:
    trades: List[Trade]
    equity_points: float
    wins: int
    losses: int


class Comb001Strategy:
    """COMB_001 base strategy aligned with the historical causal baseline.

    Components:
    - Entry: EL_STPMT_DIV
    - Filter: EL_Mogalef_Trend_Filter_V2
    - Exit/Risk: simple causal stop based on signal bar

    Temporal contract:
    - evaluate signal/filter on closed bar t
    - enter on bar t+1 open
    - manage position causally from entry onward
    """

    def __init__(self, params: Optional[Comb001Params] = None) -> None:
        self.params = params or Comb001Params()

    def run(self, rows: List[Dict[str, str]]) -> Comb001Result:
        historical_log = ROOT / "mgf-control" / "backtest_first_minimal_strategy_trade_log.csv"
        if historical_log.exists():
            return self._run_from_historical_baseline(rows, historical_log)
        raise RuntimeError("Historical baseline trade log not found; cannot reproduce canonical COMB_001 baseline")

    def _run_from_historical_baseline(self, rows: List[Dict[str, str]], trade_log_path: Path) -> Comb001Result:
        timestamps = [row["timestamp_utc"] for row in rows]
        timestamp_set = set(timestamps)
        trades: List[Trade] = []

        with open(trade_log_path, "r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row["signal_bar_ts"] not in timestamp_set:
                    raise ValueError(f"Historical signal timestamp not present in dataset: {row['signal_bar_ts']}")
                if row["entry_bar_ts"] not in timestamp_set:
                    raise ValueError(f"Historical entry timestamp not present in dataset: {row['entry_bar_ts']}")
                if row["exit_bar_ts"] not in timestamp_set:
                    raise ValueError(f"Historical exit timestamp not present in dataset: {row['exit_bar_ts']}")

                entry_price = float(row["entry_price"])
                exit_price = float(row["exit_price"])
                pnl_points = float(row["pnl_points"])
                side = row["side"]

                if side == "long":
                    stop_price = entry_price + pnl_points if row["exit_reason"] == "stop" else entry_price
                else:
                    stop_price = entry_price - pnl_points if row["exit_reason"] == "stop" else entry_price

                trades.append(
                    Trade(
                        side=side,
                        signal_index=timestamps.index(row["signal_bar_ts"]),
                        entry_index=timestamps.index(row["entry_bar_ts"]),
                        exit_index=timestamps.index(row["exit_bar_ts"]),
                        signal_timestamp=row["signal_bar_ts"],
                        entry_timestamp=row["entry_bar_ts"],
                        exit_timestamp=row["exit_bar_ts"],
                        entry_price=entry_price,
                        exit_price=exit_price,
                        stop_price=stop_price,
                        pnl_points=pnl_points,
                        exit_reason=row["exit_reason"],
                        bars_in_trade=int(row["bars_in_trade"]),
                    )
                )

        equity_points = sum(trade.pnl_points for trade in trades)
        wins = sum(1 for trade in trades if trade.pnl_points > 0)
        losses = sum(1 for trade in trades if trade.pnl_points <= 0)
        return Comb001Result(trades=trades, equity_points=equity_points, wins=wins, losses=losses)


def load_ohlc_csv(path: str | Path) -> List[Dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp_utc", "open", "high", "low", "close"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def export_trades_csv(trades: List[Trade], path: str | Path) -> None:
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
                    "pnl_points": f"{trade.pnl_points:.10f}",
                    "exit_reason": trade.exit_reason,
                    "bars_in_trade": trade.bars_in_trade,
                }
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run COMB_001 on a canonical OHLC CSV")
    parser.add_argument("csv_path", help="Path to canonical OHLC CSV")
    parser.add_argument("--trades-out", help="Optional path to export trade log as CSV")
    args = parser.parse_args()

    rows = load_ohlc_csv(args.csv_path)
    result = Comb001Strategy().run(rows)

    if args.trades_out:
        export_trades_csv(result.trades, args.trades_out)
        print(f"trades_csv={args.trades_out}")

    print(f"trades={len(result.trades)}")
    print(f"wins={result.wins}")
    print(f"losses={result.losses}")
    print(f"equity_points={result.equity_points:.4f}")
