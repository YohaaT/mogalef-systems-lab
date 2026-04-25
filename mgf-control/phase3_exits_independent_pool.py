"""Fase 3 — EXITS con POOL (25 combos)."""
from __future__ import annotations
import argparse, json, sys, time
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

def init_worker(data, comb):
    global _GLOBAL_DATA, _GLOBAL_COMB
    _GLOBAL_DATA = data
    _GLOBAL_COMB = comb

def run_single_combo_worker(combo: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if _GLOBAL_COMB == "001":
            p = Comb001TrendParams(target_atr_multiplier=combo["tp_mult"], timescan_bars=combo["timescan"], trend_enforce_date_kill_switch=False)
            strat = Comb001TrendStrategy(p)
        else:
            p = Comb002ImpulseV2Params(scalping_target_coef_volat=combo["tp_coef"], timescan_bars=combo["timescan"])
            strat = Comb002ImpulseV2Strategy(p)
        result = strat.run(_GLOBAL_DATA)
        return {**combo, "trades": len(result.trades), "pf": result.profit_factor, "wr": result.win_rate, "equity": result.equity_points, "max_dd": result.max_drawdown}
    except Exception as e:
        return {**combo, "error": str(e)}

def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 3 — EXITS (POOL)")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase3_results"))
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()

    data_path = Path(args.data_dir) / f"{args.asset}_full_{args.timeframe}.csv"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found"); return 1
    data = load_ohlc_csv(str(data_path))
    
    tp_vals = [6, 8, 10, 12, 15] if args.comb == "001" else [2, 3, 4, 5, 6]
    ts_vals = [10, 15, 20, 30, 45]
    combos = [{"tp_mult" if args.comb=="001" else "tp_coef": t, "timescan": ts} for t in tp_vals for ts in ts_vals]
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    
    n_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    t0 = time.time()
    results = []
    
    with Pool(processes=n_workers, initializer=init_worker, initargs=(data, args.comb)) as pool:
        for i, result in enumerate(pool.imap_unordered(run_single_combo_worker, combos)):
            results.append(result)
            if (i+1) % 5 == 0:
                print(f"  [{i+1}/{len(combos)}]")
    
    elapsed = time.time() - t0
    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)
    
    out_json = out_dir / f"phase3_exits_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"[OK] {out_json}\n[PERFORMANCE] {elapsed:.1f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
