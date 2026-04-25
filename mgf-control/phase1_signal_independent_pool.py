"""Fase 1 — Optimización INDEPENDIENTE SEÑAL (POOL parallelization).

Varía STPMT_DIV: smooth_h/b (2,3,4,5) × dist_max_h/l (75,125,175,225,275) = 400 combos
Usa multiprocessing.Pool para paralelizar evaluación (4-5x speedup vs secuencial).

Top-10 by PF.

Uso:
  python phase1_signal_independent_pool.py --asset ES --timeframe 15m --comb 002 --workers 0
"""

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
from COMB_002_IMPULSE_V2_adaptive import (
    Comb002ImpulseV2Strategy,
    Comb002ImpulseV2Params,
    load_ohlc_csv,
)


_GLOBAL_DATA = None
_GLOBAL_COMB = None


def init_worker(data: List[Dict[str, str]], comb: str) -> None:
    """Initialize worker process with shared data."""
    global _GLOBAL_DATA, _GLOBAL_COMB
    _GLOBAL_DATA = data
    _GLOBAL_COMB = comb


def run_single_combo_worker(combo: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function for Pool — runs ONE combo with global data."""
    try:
        if _GLOBAL_COMB == "001":
            params = Comb001TrendParams(
                stpmt_smooth_h=int(combo["smooth_h"]),
                stpmt_smooth_b=int(combo["smooth_b"]),
                stpmt_dist_max_h=int(combo.get("dist_max_h", 200)),
                stpmt_dist_max_l=int(combo.get("dist_max_l", 200)),
                horaire_allowed_hours_utc=list(range(24)),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(params)
        else:  # 002
            params = Comb002ImpulseV2Params(
                stpmt_smooth_h=int(combo["smooth_h"]),
                stpmt_smooth_b=int(combo["smooth_b"]),
                stpmt_dist_max_h=int(combo.get("dist_max_h", 200)),
                stpmt_dist_max_l=int(combo.get("dist_max_l", 200)),
                horaire_allowed_hours_utc=list(range(24)),
                allowed_weekdays=list(range(7)),
            )
            strat = Comb002ImpulseV2Strategy(params)

        result = strat.run(_GLOBAL_DATA)
        return {
            **combo,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {**combo, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 1 — Optimización independiente SEÑAL (POOL)")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase1_results"))
    ap.add_argument("--workers", type=int, default=0, help="Worker processes (0=auto: cpu_count-1)")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / f"{args.asset}_full_{args.timeframe}.csv"
    if not csv_path.exists():
        print(f"[ERROR] {csv_path} not found")
        return 1
    print(f"[phase1-pool] Loading {csv_path.name}...")
    data = load_ohlc_csv(str(csv_path))
    print(f"  {len(data):,} rows")

    smooth_vals = [2, 3, 4, 5]
    dist_max_vals = [75, 125, 175, 225, 275]
    combos = [
        {"smooth_h": sh, "smooth_b": sb, "dist_max_h": dmh, "dist_max_l": dml}
        for sh in smooth_vals
        for sb in smooth_vals
        for dmh in dist_max_vals
        for dml in dist_max_vals
    ]
    print(f"[phase1-pool] Grid: {len(combos)} signal combos")

    n_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    print(f"[phase1-pool] Using {n_workers} workers (cpu_count={cpu_count()})")

    t0 = time.time()
    results: List[Dict[str, Any]] = []

    chunksize = max(1, len(combos) // (n_workers * 4))
    print(f"[phase1-pool] Chunksize: {chunksize}")

    with Pool(processes=n_workers, initializer=init_worker, initargs=(data, args.comb)) as pool:
        for i, result in enumerate(pool.imap_unordered(run_single_combo_worker, combos, chunksize=chunksize)):
            results.append(result)
            if (i + 1) % max(1, len(combos) // 10) == 0:
                print(f"  [{i+1}/{len(combos)}] completed ({(i+1)*100//len(combos)}%)")

    elapsed = time.time() - t0

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)

    print(f"\n[phase1-pool] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase1-pool] Top-5 by PF:")
    for i, r in enumerate(results_ok[:5], 1):
        print(f"  {i}. smooth=({r['smooth_h']},{r['smooth_b']}) dist=({r.get('dist_max_h', 200)},{r.get('dist_max_l', 200)}) PF={r['pf']:.3f} trades={r['trades']}")

    out_json = out_dir / f"phase1_signal_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"\n[OK] {out_json}")

    print(f"\n[PERFORMANCE]")
    print(f"  Elapsed: {elapsed:.1f}s for {len(combos)} combos")
    print(f"  Per combo: {elapsed/len(combos):.3f}s")
    print(f"  Speedup vs sequential (7.6s/combo): {7.6*len(combos)/elapsed:.1f}x")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
