"""Fase 2b — REGIME con POOL (7 combos)."""
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
import numpy as np

_GLOBAL_DATA = None
_GLOBAL_COMB = None
_GLOBAL_REGIME_MASK = None

def init_worker(data: List[Dict[str, str]], comb: str, regime_mask: Dict[str, np.ndarray]) -> None:
    global _GLOBAL_DATA, _GLOBAL_COMB, _GLOBAL_REGIME_MASK
    _GLOBAL_DATA = data
    _GLOBAL_COMB = comb
    _GLOBAL_REGIME_MASK = regime_mask

def run_single_combo_worker(combo: Dict[str, Any]) -> Dict[str, Any]:
    try:
        regime_key = combo.get("regime_key", "all")
        filtered_data = [d for i, d in enumerate(_GLOBAL_DATA) if _GLOBAL_REGIME_MASK.get(regime_key, [True]*len(_GLOBAL_DATA))[i]]
        if _GLOBAL_COMB == "001":
            strat = Comb001TrendStrategy(Comb001TrendParams(trend_enforce_date_kill_switch=False))
        else:
            strat = Comb002ImpulseV2Strategy(Comb002ImpulseV2Params())
        result = strat.run(filtered_data)
        return {**combo, "trades": len(result.trades), "pf": result.profit_factor, "wr": result.win_rate, "equity": result.equity_points, "max_dd": result.max_drawdown}
    except Exception as e:
        return {**combo, "error": str(e)}

def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 2b — REGIME (POOL)")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase2b_results"))
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()

    data_path = Path(args.data_dir) / f"{args.asset}_full_{args.timeframe}.csv"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found"); return 1
    print(f"[phase2b-pool] Loading {data_path.name}...")
    data = load_ohlc_csv(str(data_path))
    
    atr = np.array([float(d.get('atr', 0)) for d in data])
    p33, p67 = np.percentile(atr, 33), np.percentile(atr, 67)
    regime_mask = {
        "all": np.ones(len(data), dtype=bool),
        "low": atr < p33,
        "med": (atr >= p33) & (atr < p67),
        "high": atr >= p67,
    }
    
    combos = [{"regime_key": k} for k in regime_mask.keys()]
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    
    n_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    t0 = time.time()
    results = []
    
    with Pool(processes=n_workers, initializer=init_worker, initargs=(data, args.comb, regime_mask)) as pool:
        for i, result in enumerate(pool.imap_unordered(run_single_combo_worker, combos)):
            results.append(result)
            print(f"  [{i+1}/{len(combos)}]")
    
    elapsed = time.time() - t0
    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["pf"], reverse=True)
    
    out_json = out_dir / f"phase2b_regime_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:10], f, indent=2)
    print(f"[OK] {out_json}\n[PERFORMANCE] {elapsed:.1f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
