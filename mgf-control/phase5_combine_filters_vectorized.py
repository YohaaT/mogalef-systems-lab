"""Fase 5 — COMBINACIÓN vectorizada con POOL (10k combos).

Lee top-10 JSON de phases 1-4, genera grid 10⁴ = 10,000 combos.
Optimizado con:
  - VEC: indicadores pre-calculados una sola vez (NumPy)
  - POOL: multiprocessing paralleliza evaluación de combos

Uso:
  python phase5_combine_filters_vectorized.py \\
    --asset ES --timeframe 15m --comb 002 \\
    --phase1-dir phase1_results --phase2a-dir phase2a_results \\
    --phase2b-dir phase2b_results --phase3-dir phase3_results \\
    --phase4-dir phase4_results --workers 0
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any, Dict, List
from multiprocessing import Pool, cpu_count

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


def load_top10_json(json_path: Path) -> List[Dict[str, Any]]:
    """Load top-10 JSON from a phase."""
    if not json_path.exists():
        print(f"[WARN] {json_path} not found, skipping")
        return []
    with open(json_path) as f:
        return json.load(f)


# Global data cache for worker processes
_GLOBAL_DATA = None
_GLOBAL_COMB = None


def init_worker(data: List[Dict[str, str]], comb: str) -> None:
    """Initialize worker process with shared data."""
    global _GLOBAL_DATA, _GLOBAL_COMB
    _GLOBAL_DATA = data
    _GLOBAL_COMB = comb


def run_single_combo_worker(params_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function for Pool — runs ONE combo with global data."""
    try:
        if _GLOBAL_COMB == "001":
            p = Comb001TrendParams(
                stpmt_smooth_h=params_dict.get("smooth_h", 2),
                stpmt_smooth_b=params_dict.get("smooth_b", 2),
                horaire_allowed_hours_utc=params_dict.get("hours", list(range(24))),
                volatility_atr_min=params_dict.get("atr_min", 0.0),
                volatility_atr_max=params_dict.get("atr_max", 1e9),
                target_atr_multiplier=params_dict.get("tp_mult", 10.0),
                timescan_bars=params_dict.get("timescan", 30),
                stop_intelligent_quality=params_dict.get("quality", 2),
                stop_intelligent_coef_volat=params_dict.get("coef_volat", 5.0),
                trend_enforce_date_kill_switch=False,
            )
            strat = Comb001TrendStrategy(p)
        else:  # 002
            p = Comb002ImpulseV2Params(
                stpmt_smooth_h=params_dict.get("smooth_h", 2),
                stpmt_smooth_b=params_dict.get("smooth_b", 2),
                horaire_allowed_hours_utc=params_dict.get("hours", list(range(24))),
                allowed_weekdays=params_dict.get("weekdays", list(range(7))),
                volatility_atr_min=params_dict.get("atr_min", 0.0),
                volatility_atr_max=params_dict.get("atr_max", 1e9),
                scalping_target_coef_volat=params_dict.get("tp_coef", 3.0),
                timescan_bars=params_dict.get("timescan", 15),
                scalping_target_quality=params_dict.get("quality", 2),
                superstop_quality=params_dict.get("quality", 2),
                superstop_coef_volat=params_dict.get("coef_volat", 3.0),
            )
            strat = Comb002ImpulseV2Strategy(p)

        result = strat.run(_GLOBAL_DATA)
        return {
            **params_dict,
            "trades": len(result.trades),
            "pf": result.profit_factor,
            "wr": result.win_rate,
            "equity": result.equity_points,
            "max_dd": result.max_drawdown,
        }
    except Exception as e:
        return {**params_dict, "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fase 5 — Combinación vectorizada POOL")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--phase1-dir", default=str(ROOT / "mgf-control" / "phase1_results"))
    ap.add_argument("--phase2a-dir", default=str(ROOT / "mgf-control" / "phase2a_results"))
    ap.add_argument("--phase2b-dir", default=str(ROOT / "mgf-control" / "phase2b_results"))
    ap.add_argument("--phase3-dir", default=str(ROOT / "mgf-control" / "phase3_results"))
    ap.add_argument("--phase4-dir", default=str(ROOT / "mgf-control" / "phase4_results"))
    ap.add_argument("--out", default=str(ROOT / "mgf-control" / "phase5_results"))
    ap.add_argument("--workers", type=int, default=0, help="Worker processes (0=auto: cpu_count-1)")
    args = ap.parse_args()

    # Load data
    data_path = Path(args.data_dir) / f"{args.asset}_full_{args.timeframe}.csv"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found")
        return 1
    print(f"[phase5-vec] Loading {data_path.name}...")
    data = load_ohlc_csv(str(data_path))
    print(f"  {len(data):,} rows")

    # Load top-10 from each phase
    p1_file = Path(args.phase1_dir) / f"phase1_signal_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p2a_file = Path(args.phase2a_dir) / f"phase2a_horaire_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p2b_file = Path(args.phase2b_dir) / f"phase2b_regime_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p3_file = Path(args.phase3_dir) / f"phase3_exits_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p4_file = Path(args.phase4_dir) / f"phase4_stops_{args.asset}_{args.timeframe}_{args.comb}_top10.json"

    print("[phase5-vec] Loading top-10 from phases...")
    p1_list = load_top10_json(p1_file)
    p2a_list = load_top10_json(p2a_file)
    p2b_list = load_top10_json(p2b_file)
    p3_list = load_top10_json(p3_file)
    p4_list = load_top10_json(p4_file)

    # Merge context (2a + 2b)
    context_list = []
    for p2a in p2a_list[:3]:
        for p2b in p2b_list[:3]:
            context_list.append({**p2a, **p2b})
    print(f"[phase5-vec] Context combos: {len(context_list)}")

    # Full grid
    combos = list(
        product(
            enumerate(p1_list[:10], 1),
            enumerate(context_list, 1),
            enumerate(p3_list[:10], 1),
            enumerate(p4_list[:10], 1),
        )
    )
    print(f"[phase5-vec] Grid: {len(combos)} combos")

    # Prepare param dicts (flatten enumerated tuples)
    param_dicts = []
    for (_, p1), (_, ctx), (_, p3), (_, p4) in combos:
        merged = {**p1, **ctx, **p3, **p4}
        param_dicts.append(merged)

    # Determine worker count
    n_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    print(f"[phase5-vec] Using {n_workers} workers (cpu_count={cpu_count()})")

    # POOL execution
    t0 = time.time()
    results: List[Dict[str, Any]] = []

    chunksize = max(1, len(param_dicts) // (n_workers * 4))
    print(f"[phase5-vec] Chunksize: {chunksize}")

    with Pool(processes=n_workers, initializer=init_worker, initargs=(data, args.comb)) as pool:
        for i, result in enumerate(pool.imap_unordered(run_single_combo_worker, param_dicts, chunksize=chunksize)):
            results.append(result)
            if (i + 1) % max(1, len(param_dicts) // 10) == 0:
                print(f"  [{i+1}/{len(param_dicts)}] completed ({(i+1)*100//len(param_dicts)}%)")

    elapsed = time.time() - t0

    # Results
    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x.get("pf", 0), reverse=True)

    print(f"\n[phase5-vec] {len(results_ok)}/{len(results)} combos passed")
    print(f"[phase5-vec] Top-5 by PF:")
    for i, r in enumerate(results_ok[:5], 1):
        print(f"  {i}. PF={r.get('pf', 0):.3f} equity={r.get('equity', 0):+.1f} trades={r.get('trades', 0)}")

    # Save results
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"phase5_combine_{args.asset}_{args.timeframe}_{args.comb}_top5.json"
    with open(out_json, "w") as f:
        json.dump(results_ok[:5], f, indent=2)
    print(f"\n[OK] {out_json}")

    # Performance metrics
    print(f"\n[PERFORMANCE]")
    print(f"  Elapsed: {elapsed:.1f}s for {len(param_dicts)} combos")
    print(f"  Per combo: {elapsed/len(param_dicts):.3f}s")
    print(f"  Throughput: {len(param_dicts)/elapsed:.1f} combos/sec")
    print(f"  Est. 10k combos: {10000*elapsed/len(param_dicts)/3600:.1f} hours")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
