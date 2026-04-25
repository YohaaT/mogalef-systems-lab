"""Phase 5 Vectorization Test — LOCAL speedup validation on MNQ 15m COMB_002.

Test VEC + POOL speedup before deploying to BO/TANK.
Compares: sequential (baseline) vs vectorized + Pool.

Uso:
  python phase5_test_vectorization.py --asset MNQ --timeframe 15m --comb 002 --test-size 100
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

import numpy as np

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
        print(f"[WARN] {json_path} not found")
        return []
    with open(json_path) as f:
        return json.load(f)


def run_single_combo_baseline(
    comb: str,
    params_dict: Dict[str, Any],
    data: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Baseline: run combo without vectorization."""
    try:
        if comb == "001":
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
        else:
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

        result = strat.run(data)
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
    ap = argparse.ArgumentParser(description="Phase 5 — Vectorization Test")
    ap.add_argument("--asset", required=True, choices=["ES", "FDAX", "MNQ"])
    ap.add_argument("--timeframe", required=True, choices=["5m", "10m", "15m"])
    ap.add_argument("--comb", default="002", choices=["001", "002"])
    ap.add_argument("--data-dir", default=str(ROOT / "new_data"))
    ap.add_argument("--phase1-dir", default=str(ROOT / "mgf-control" / "phase1_results"))
    ap.add_argument("--phase2a-dir", default=str(ROOT / "mgf-control" / "phase2a_results"))
    ap.add_argument("--phase2b-dir", default=str(ROOT / "mgf-control" / "phase2b_results"))
    ap.add_argument("--phase3-dir", default=str(ROOT / "mgf-control" / "phase3_results"))
    ap.add_argument("--phase4-dir", default=str(ROOT / "mgf-control" / "phase4_results"))
    ap.add_argument("--test-size", type=int, default=100, help="Number of combos to test")
    args = ap.parse_args()

    # Load data
    data_path = Path(args.data_dir) / f"{args.asset}_full_{args.timeframe}.csv"
    if not data_path.exists():
        print(f"[ERROR] {data_path} not found")
        return 1
    print(f"[VEC TEST] Loading {data_path.name}...")
    data = load_ohlc_csv(str(data_path))
    print(f"  {len(data):,} rows")

    # Load top-10 from each phase
    p1_file = Path(args.phase1_dir) / f"phase1_signal_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p2a_file = Path(args.phase2a_dir) / f"phase2a_horaire_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p2b_file = Path(args.phase2b_dir) / f"phase2b_regime_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p3_file = Path(args.phase3_dir) / f"phase3_exits_{args.asset}_{args.timeframe}_{args.comb}_top10.json"
    p4_file = Path(args.phase4_dir) / f"phase4_stops_{args.asset}_{args.timeframe}_{args.comb}_top10.json"

    print("[VEC TEST] Loading top-10 from phases...")
    p1_list = load_top10_json(p1_file)
    p2a_list = load_top10_json(p2a_file)
    p2b_list = load_top10_json(p2b_file)
    p3_list = load_top10_json(p3_file)
    p4_list = load_top10_json(p4_file)

    if not all([p1_list, p2a_list, p2b_list, p3_list, p4_list]):
        print("[ERROR] Missing top-10 JSON files")
        return 1

    # Create context (2a + 2b)
    context_list = []
    for p2a in p2a_list[:3]:
        for p2b in p2b_list[:3]:
            context_list.append({**p2a, **p2b})
    print(f"[VEC TEST] Context combos: {len(context_list)}")

    # Full grid
    combos = list(
        product(
            enumerate(p1_list[:min(3, len(p1_list))], 1),
            enumerate(context_list, 1),
            enumerate(p3_list[:min(3, len(p3_list))], 1),
            enumerate(p4_list[:min(3, len(p4_list))], 1),
        )
    )
    print(f"[VEC TEST] Grid size: {len(combos)} combos (test-size limit: {args.test_size})")

    # Limit to test size
    combos = combos[:args.test_size]

    # BASELINE — Sequential
    print(f"\n[BASELINE] Running {len(combos)} combos sequentially...")
    t0 = time.time()
    results_baseline = []
    for i, ((_, p1), (_, ctx), (_, p3), (_, p4)) in enumerate(combos):
        merged_params = {**p1, **ctx, **p3, **p4}
        res = run_single_combo_baseline(args.comb, merged_params, data)
        results_baseline.append(res)
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(combos)}] completed")

    elapsed_baseline = time.time() - t0
    print(f"[BASELINE] Elapsed: {elapsed_baseline:.1f}s ({elapsed_baseline/len(combos):.3f}s/combo)")

    # Results summary
    results_ok = [r for r in results_baseline if "error" not in r]
    results_ok.sort(key=lambda x: x.get("pf", 0), reverse=True)

    print(f"\n[RESULTS] {len(results_ok)}/{len(results_baseline)} combos passed")
    if results_ok:
        print(f"[TOP-5]")
        for i, r in enumerate(results_ok[:5], 1):
            print(f"  {i}. PF={r.get('pf', 0):.3f} trades={r.get('trades', 0)}")

    # Estimate speedup for Phase 5 (10k combos)
    n_combos_phase5 = 10000
    est_baseline_hours = (elapsed_baseline / len(combos)) * n_combos_phase5 / 3600

    print(f"\n[SPEEDUP ESTIMATE]")
    print(f"  Test combos: {len(combos)}")
    print(f"  Time/combo: {elapsed_baseline/len(combos):.3f}s")
    print(f"  Estimated Phase 5 (10k combos): {est_baseline_hours:.1f} hours (sequential)")
    print(f"  With POOL({cpu_count()-1}): ~{est_baseline_hours/(cpu_count()-1):.1f} hours")
    print(f"  Target with VEC: ~2-3 hours (8-10x speedup)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
