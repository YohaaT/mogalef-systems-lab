"""
Verification: Vectorized vs Original COMB_001_TREND_V1 backtest.

Runs both implementations on MNQ 5min with fixed params and compares
trade-by-trade. Any mismatch is a bug in the vectorized version.

Usage:
    python verify_vectorized_equivalence.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / "mgf-control"
DATA_FILE = ROOT / "mgf-data" / "market" / "MNQ__5m__regular_session__max_available_from_source.csv"
OUTPUT_DIR = CTRL

TOLERANCE_PRICE = 1e-5
TOLERANCE_PNL   = 0.01

# Fixed params for the verification test
TEST_PARAMS = dict(
    stpmt_smooth_h=2,
    stpmt_smooth_b=2,
    stpmt_distance_max_h=200,
    stpmt_distance_max_l=200,
    trend_r1=1,
    trend_r2=90,
    trend_r3=150,
    horaire_allowed_hours_utc=list(range(9, 16)),
    volatility_atr_min=0.0,
    volatility_atr_max=500.0,
    target_atr_multiplier=10.0,
    timescan_bars=30,
    stop_intelligent_coef_volat=5.0,
)


def load_csv(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _compare_trades(orig_trades, vec_trades, report_lines):
    """Compare two lists of trade dicts. Returns True if identical."""
    ok = True

    if len(orig_trades) != len(vec_trades):
        report_lines.append(
            f"[FAIL] Trade count mismatch: original={len(orig_trades)}, vectorized={len(vec_trades)}"
        )
        ok = False

    n = min(len(orig_trades), len(vec_trades))
    for idx in range(n):
        o = orig_trades[idx]
        v = vec_trades[idx]
        diffs = []

        if o["entry_index"] != v["entry_index"]:
            diffs.append(f"entry_index orig={o['entry_index']} vec={v['entry_index']}")

        if abs(float(o["entry_price"]) - float(v["entry_price"])) > TOLERANCE_PRICE:
            diffs.append(f"entry_price orig={o['entry_price']} vec={v['entry_price']}")

        if abs(float(o["exit_price"]) - float(v["exit_price"])) > TOLERANCE_PRICE:
            diffs.append(f"exit_price orig={o['exit_price']} vec={v['exit_price']}")

        if o["exit_reason"] != v["exit_reason"]:
            diffs.append(f"exit_reason orig={o['exit_reason']} vec={v['exit_reason']}")

        if abs(float(o["pnl"]) - float(v["pnl"])) > TOLERANCE_PNL:
            diffs.append(f"pnl orig={o['pnl']} vec={v['pnl']}")

        if diffs:
            report_lines.append(f"[FAIL] Trade #{idx}: " + " | ".join(diffs))
            ok = False

    return ok


def run_original(rows):
    """Run the existing COMB_001_TREND_V1 strategy and return trades as list of dicts."""
    for p in [
        ROOT / "mgf-divergence-lab" / "src",
        ROOT / "mgf-regime-filter-lab" / "src",
        ROOT / "mgf-stop-lab" / "src",
        CTRL,
    ]:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    from COMB_001_TREND_V1 import Comb001TrendParams, Comb001TrendStrategy

    params = Comb001TrendParams(**TEST_PARAMS)
    strategy = Comb001TrendStrategy(params)

    t0 = time.perf_counter()
    result = strategy.run(rows)
    elapsed = time.perf_counter() - t0

    trades_out = []
    for t in result.trades:
        trades_out.append({
            "entry_index": t.entry_index,
            "entry_price": round(t.entry_price, 6),
            "exit_price": round(t.exit_price, 6),
            "exit_reason": t.exit_reason,
            "side": t.side,
            "pnl": round(t.pnl_points, 6),
        })

    return trades_out, result.equity_points, elapsed


def run_vectorized(rows):
    """Run COMB_001_TREND_V1_vectorized and return trades as list of dicts."""
    for p in [
        ROOT / "mgf-divergence-lab" / "src",
        ROOT / "mgf-regime-filter-lab" / "src",
        ROOT / "mgf-stop-lab" / "src",
        CTRL,
    ]:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    from COMB_001_TREND_V1_vectorized import Comb001TrendVectorized, Comb001TrendParams

    params = Comb001TrendParams(**TEST_PARAMS)
    strategy = Comb001TrendVectorized(params)

    t0 = time.perf_counter()
    result = strategy.run(rows)
    elapsed = time.perf_counter() - t0

    trades_out = []
    for t in result.trades:
        trades_out.append({
            "entry_index": t.entry_index,
            "entry_price": round(t.entry_price, 6),
            "exit_price": round(t.exit_price, 6),
            "exit_reason": t.exit_reason,
            "side": t.side,
            "pnl": round(t.pnl_points, 6),
        })

    return trades_out, result.equity_points, elapsed


def main():
    print("=" * 72)
    print("VECTORIZED EQUIVALENCE VERIFICATION - COMB_001_TREND_V1")
    print("=" * 72)
    print(f"Dataset : {DATA_FILE.name}")

    rows = load_csv(DATA_FILE)
    print(f"Rows    : {len(rows)}")

    report_lines = []
    summary = {}

    # --- Original ---
    print("\n[1] Running ORIGINAL (loop)...")
    orig_trades, orig_equity, orig_time = run_original(rows)
    print(f"    Trades : {len(orig_trades)}")
    print(f"    Equity : {orig_equity:.2f} pts")
    print(f"    Time   : {orig_time:.3f}s")
    summary["original_trades"] = len(orig_trades)
    summary["original_equity"] = round(orig_equity, 4)
    summary["original_time_s"] = round(orig_time, 3)

    # Export original trades
    orig_path = OUTPUT_DIR / "verify_original_trades.csv"
    with open(orig_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entry_index", "entry_price", "exit_price", "exit_reason", "side", "pnl"])
        w.writeheader()
        w.writerows(orig_trades)
    print(f"    Saved  : {orig_path.name}")

    # --- Vectorized ---
    print("\n[2] Running VECTORIZED (numpy + multiprocessing)...")
    vec_trades, vec_equity, vec_time = run_vectorized(rows)
    print(f"    Trades : {len(vec_trades)}")
    print(f"    Equity : {vec_equity:.2f} pts")
    print(f"    Time   : {vec_time:.3f}s")
    summary["vectorized_trades"] = len(vec_trades)
    summary["vectorized_equity"] = round(vec_equity, 4)
    summary["vectorized_time_s"] = round(vec_time, 3)

    # Export vectorized trades
    vec_path = OUTPUT_DIR / "verify_vectorized_trades.csv"
    with open(vec_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["entry_index", "entry_price", "exit_price", "exit_reason", "side", "pnl"])
        w.writeheader()
        w.writerows(vec_trades)
    print(f"    Saved  : {vec_path.name}")

    # --- Compare ---
    print("\n[3] Comparing trade-by-trade...")
    passed = _compare_trades(orig_trades, vec_trades, report_lines)

    speedup = orig_time / vec_time if vec_time > 0 else 0
    summary["speedup_x"] = round(speedup, 1)
    summary["equivalence_passed"] = passed
    summary["mismatches"] = len(report_lines)

    # --- Report ---
    print("\n" + "=" * 72)
    if passed:
        print("[PASS] Vectorized produces IDENTICAL trades to original.")
    else:
        print(f"[FAIL] {len(report_lines)} mismatch(es) found:")
        for line in report_lines[:20]:
            print(f"       {line}")
        if len(report_lines) > 20:
            print(f"       ... and {len(report_lines) - 20} more")

    print(f"\nSpeedup : {speedup:.1f}x  ({orig_time:.3f}s -> {vec_time:.3f}s)")
    print("=" * 72)

    # Save report
    report_path = OUTPUT_DIR / "verify_equivalence_report.json"
    summary["mismatches_detail"] = report_lines[:50]
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Report  : {report_path.name}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
