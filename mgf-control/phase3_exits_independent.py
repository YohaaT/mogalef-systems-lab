"""Fase 3 — Optimización INDEPENDIENTE filtro SALIDAS (TP/TimeStop).

Varía:
  - COMB_001: target_atr_multiplier (6,8,10,12,15) × timescan_bars (10,15,20,30,45) = 25 combos
  - COMB_002: scalping_target_coef (2,3,4,5,6) × timescan_bars (10,15,20,30,45) = 25 combos

Top-10 by PF.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
for sub in ("mgf-divergence-lab", "mgf-regime-filter-lab", "mgf-stop-lab"):
    p = str(ROOT / sub / "src")
    if p not in sys.path:
        sys.path.append(p)
sys.path.append(str(Path(__file__).resolve().parent))

from COMB_001_TREND_V1 import Comb001TrendStrategy, Comb001TrendParams
from COMB_002_IMPULSE_V2_adaptive import (
    Comb002ImpulseV2Strategy,
    Comb002ImpulseV2Params,
    load_ohlc_csv,
)


def run_single_combo_001(
    tp_mult: float,
    timescan: int,
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    try:
        params = Comb001TrendParams(
            target_atr_multiplier=tp_mult,
            timescan_bars=timescan,
            horaire_allowed_hours_utc=list(range(24)),
            trend_enforce_date_kill_switch=False,
        )
        strat = Comb001TrendStrategy(params)
        result = strat.run(data)
        return {
            "tp_mult": tp_mult,
            "timescan": timescan,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {"tp_mult": tp_mult, "timescan": timescan, "error": str(e)}


def run_single_combo_002(
    tp_coef: float,
    timescan: int,
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    try:
        params = Comb002ImpulseV2Params(
            scalping_target_coef_volat=tp_coef,
            timescan_bars=timescan,
            horaire_allowed_hours_utc=list(range(24)),
            allowed_weekdays=list(range(7)),
        )
        strat = Comb002ImpulseV2Strategy(params)
        result = strat.run(data)
        return {
            "tp_coef": tp_coef,
            "timescan": timescan,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {"tp_coef": tp_coef, "timescan": timescan, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 3 — Optimización independiente SALIDAS")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase3_results"))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / f"{args.asset}_full_{args.timeframe}.csv"
    if not csv_path.exists():
        print(f"[ERROR] {csv_path} not found")
        return 1
    print(f"[phase3] Loading {csv_path.name}...")
    data = load_ohlc_csv(str(csv_path))
    print(f"  {len(data):,} rows")

    tp_vals = [6, 8, 10, 12, 15] if args.comb == "001" else [2, 3, 4, 5, 6]
    ts_vals = [10, 15, 20, 30, 45]
    combos = list((tp, ts) for tp in tp_vals for ts in ts_vals)
    print(f"[phase3] Grid: {len(combos)} exit combos")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    run_func = run_single_combo_001 if args.comb == "001" else run_single_combo_002
    for i, (tp_val, ts_val) in enumerate(combos):
        res = run_func(tp_val, ts_val, data)
        results.append(res)
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(combos)}] completed")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase3] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase3] Top-5 by PF:")
    for i, r in enumerate(results_ok[:5], 1):
        tp_key = "tp_mult" if args.comb == "001" else "tp_coef"
        print(
            f"  {i}. {tp_key}={r[tp_key]} ts={r['timescan']} "
            f"PF={r['pf']:.3f} trades={r['trades']}"
        )

    out_json = out_dir / f"phase3_exits_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"\n[OK] {out_json}")

    print(f"\n[phase3] Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
