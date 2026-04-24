from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "mgf-divergence-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-divergence-lab" / "src"))
if str(ROOT / "mgf-regime-filter-lab" / "src") not in sys.path:
    sys.path.append(str(ROOT / "mgf-regime-filter-lab" / "src"))

from EL_STPMT_DIV import compute_el_stpmt_div
from EL_Mogalef_Trend_Filter_V2 import MogalefTrendFilterV2


@dataclass
class HistoricalTrade:
    trade_id: int
    side: str
    signal_bar_ts: str
    entry_bar_ts: str
    entry_price: float
    exit_bar_ts: str
    exit_price: float
    exit_reason: str
    pnl_points: float
    bars_in_trade: int


def load_ohlc_csv(path: str | Path) -> List[Dict[str, str]]:
    with open(path, "r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_historical_trade_log(path: str | Path) -> List[HistoricalTrade]:
    rows = list(csv.DictReader(open(path, "r", encoding="utf-8")))
    out: List[HistoricalTrade] = []
    for row in rows:
        out.append(
            HistoricalTrade(
                trade_id=int(row["trade_id"]),
                side=row["side"],
                signal_bar_ts=row["signal_bar_ts"],
                entry_bar_ts=row["entry_bar_ts"],
                entry_price=float(row["entry_price"]),
                exit_bar_ts=row["exit_bar_ts"],
                exit_price=float(row["exit_price"]),
                exit_reason=row["exit_reason"],
                pnl_points=float(row["pnl_points"]),
                bars_in_trade=int(row["bars_in_trade"]),
            )
        )
    return out


def verify_historical_combination(rows: List[Dict[str, str]], historical_trades: List[HistoricalTrade]) -> Dict[str, float]:
    timestamps = [row["timestamp_utc"] for row in rows]
    dates = [ts[:10] for ts in timestamps]
    open_ = [float(row["open"]) for row in rows]
    high = [float(row["high"]) for row in rows]
    low = [float(row["low"]) for row in rows]
    close = [float(row["close"]) for row in rows]

    stpmt = compute_el_stpmt_div(high=high, low=low, close=close)
    trend = MogalefTrendFilterV2().compute(open_=open_, high=high, low=low, close=close, dates=dates)

    ts_to_index = {ts: i for i, ts in enumerate(timestamps)}

    for trade in historical_trades:
        signal_idx = ts_to_index[trade.signal_bar_ts]
        entry_idx = ts_to_index[trade.entry_bar_ts]
        exit_idx = ts_to_index[trade.exit_bar_ts]

        expected_pose = 1 if trade.side == "long" else -1
        if stpmt["pose"][signal_idx] != expected_pose:
            raise AssertionError(f"Signal mismatch at {trade.signal_bar_ts}")
        if trend.sentiment[signal_idx] != "pass":
            raise AssertionError(f"Filter mismatch at {trade.signal_bar_ts}")
        if entry_idx != signal_idx + 1:
            raise AssertionError(f"Entry timing mismatch at {trade.signal_bar_ts}")
        if abs(open_[entry_idx] - trade.entry_price) > 1e-9:
            raise AssertionError(f"Entry price mismatch at {trade.signal_bar_ts}")
        if exit_idx < entry_idx:
            raise AssertionError(f"Exit before entry at {trade.signal_bar_ts}")

    equity_points = sum(trade.pnl_points for trade in historical_trades)
    wins = sum(1 for trade in historical_trades if trade.pnl_points > 0)
    losses = sum(1 for trade in historical_trades if trade.pnl_points <= 0)

    return {
        "trades": len(historical_trades),
        "wins": wins,
        "losses": losses,
        "equity_points": equity_points,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify the historical COMB_001 baseline against dataset and stored trade log")
    parser.add_argument("csv_path", help="Path to canonical OHLC CSV")
    parser.add_argument(
        "--trade-log",
        default=str(ROOT / "mgf-control" / "backtest_first_minimal_strategy_trade_log.csv"),
        help="Historical trade log path",
    )
    args = parser.parse_args()

    rows = load_ohlc_csv(args.csv_path)
    historical_trades = load_historical_trade_log(args.trade_log)
    result = verify_historical_combination(rows, historical_trades)

    print("historical_combination=EL_STPMT_DIV + EL_Mogalef_Trend_Filter_V2 + simple causal stop")
    print("signal_selection=stored historical runner output")
    print(f"trades={result['trades']}")
    print(f"wins={result['wins']}")
    print(f"losses={result['losses']}")
    print(f"equity_points={result['equity_points']:.4f}")
