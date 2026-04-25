"""Fase 4 — Optimización INDEPENDIENTE filtro STOPS.

Varía parámetros de Stop Intelligent / Scalping Target / SuperStop:
  - quality (1,2,3) × coef_volat (3,4,5,6,7) = 15 combos

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


def run_single_combo(
    comb: str,
    quality: int,
    coef: float,
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    try:
        if comb == "001":
            params = Comb001TrendParams(
                stop_intelligent_quality=quality,
                stop_intelligent_coef_volat=coef,
                horaire_allowed_hours_utc=list(range(24)),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(params)
        else:
            params = Comb002ImpulseV2Params(
                scalping_target_quality=quality,
                scalping_target_coef_volat=coef,
                superstop_quality=quality,
                superstop_coef_volat=coef,
                horaire_allowed_hours_utc=list(range(24)),
                allowed_weekdays=list(range(7)),
            )
            strat = Comb002ImpulseV2Strategy(params)

        result = strat.run(data)
        return {
            "quality": quality,
            "coef_volat": coef,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {"quality": quality, "coef_volat": coef, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 4 — Optimización independiente STOPS")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase4_results"))
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / f"{args.asset}_full_{args.timeframe}.csv"
    if not csv_path.exists():
        print(f"[ERROR] {csv_path} not found")
        return 1
    print(f"[phase4] Loading {csv_path.name}...")
    data = load_ohlc_csv(str(csv_path))
    print(f"  {len(data):,} rows")

    combos = [(q, c) for q in [1, 2, 3] for c in [3, 4, 5, 6, 7]]
    print(f"[phase4] Grid: {len(combos)} stop combos")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    for i, (quality, coef) in enumerate(combos):
        res = run_single_combo(args.comb, quality, coef, data)
        results.append(res)
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(combos)}] completed")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase4] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase4] Top-5 by PF:")
    for i, r in enumerate(results_ok[:5], 1):
        print(f"  {i}. quality={r['quality']} coef={r['coef_volat']} PF={r['pf']:.3f} trades={r['trades']}")

    out_json = out_dir / f"phase4_stops_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"\n[OK] {out_json}")

    print(f"\n[phase4] Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
