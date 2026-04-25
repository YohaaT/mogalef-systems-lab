"""Fase 2a — HORAIRE con POOL (30 combos)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
for sub in ("mgf-divergence-lab", "mgf-regime-filter-lab", "mgf-stop-lab"):
    p = str(ROOT / sub / "src")
    if p not in sys.path:
        sys.path.append(p)
sys.path.append(str(Path(__file__).resolve().parent))

from COMB_001_TREND_V1 import Comb001TrendStrategy, Comb001TrendParams
from COMB_002_IMPULSE_V2_adaptive import Comb002ImpulseV2Strategy, Comb002ImpulseV2Params, load_ohlc_csv

_GLOBAL_DATA = None
_GLOBAL_COMB = None

def init_worker(data: List[Dict[str, str]], comb: str) -> None:
    global _GLOBAL_DATA, _GLOBAL_COMB
    _GLOBAL_DATA = data
    _GLOBAL_COMB = comb

def run_single_combo_worker(combo: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if _GLOBAL_COMB == "001":
            params = Comb001TrendParams(
                horaire_allowed_hours_utc=combo.get("hours", list(range(24))),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(params)
        else:
            params = Comb002ImpulseV2Params(
                horaire_allowed_hours_utc=combo.get("hours", list(range(24))),
                allowed_weekdays=list(range(7)),
            )
            strat = Comb002ImpulseV2Strategy(params)
        result = strat.run(_GLOBAL_DATA)
        return {**combo, "trades": len(result.trades), "pf": result.profit_factor, "wr": result.win_rate, "equity": result.equity_points, "max_dd": result.max_drawdown}
    except Exception as e:
        return {**combo, "error": str(e)}

def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 2a — HORAIRE (POOL)")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase2a_results"))
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()

    data_path = Path(args.data_dir) / f"{args.asset}_full_{args.timeframe}.csv"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found")
        return 1
    print(f"[phase2a-pool] Loading {data_path.name}...")
    data = load_ohlc_csv(str(data_path))
    print(f"  {len(data):,} rows")

    combos = [
        {"hours": list(range(24))},
        {"hours": list(range(9, 13))},
        {"hours": list(range(13, 17))},
        {"hours": list(range(20, 23))},
    ] + [{"hours": [h]} for h in range(24)]
    print(f"[phase2a-pool] Grid: {len(combos)} hour combos")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    n_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    t0 = time.time()
    results: List[Dict[str, Any]] = []

    with Pool(processes=n_workers, initializer=init_worker, initargs=(data, args.comb)) as pool:
        for i, result in enumerate(pool.imap_unordered(run_single_combo_worker, combos)):
            results.append(result)
            print(f"  [{i+1}/{len(combos)}] completed")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase2a-pool] {len(results_ok)}/{len(results)} combos passed")

    out_json = out_dir / f"phase2a_horaire_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"[OK] {out_json}")
    print(f"[PERFORMANCE] {elapsed:.1f}s for {len(combos)} combos ({elapsed/len(combos):.1f}s/combo)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
