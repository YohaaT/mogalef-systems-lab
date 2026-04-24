"""Phase 1 Optimization Block Runner - Vectorized + multiprocessing.Pool version.

Produces identical results as phase1_optimization_block_runner.py but uses
COMB_001_TREND_V1_vectorized.py for numpy-accelerated signal computation
and Pool to run all 125 combos in parallel across available cores.

Blocks (same as original):
- Block 1: smooth_h=1 (125 combos)
- Block 2: smooth_h=2 (125 combos)
- Block 3: smooth_h=3 (125 combos)
- Block 4: smooth_h=4 (125 combos)
- Block 5: smooth_h=5 (125 combos)
"""

import csv
import json
import sys
import time
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path

from COMB_001_TREND_V1_vectorized import (
    Comb001TrendParams,
    Comb001TrendVectorized,
    load_ohlc_csv,
)

# Parameter ranges (identical to original runner)
SMOOTH_H_RANGE    = [1, 2, 3, 4, 5]
SMOOTH_B_RANGE    = [1, 2, 3, 4, 5]
DIST_H_RANGE      = [50, 100, 150, 200, 300]
DIST_L_RANGE      = [50, 100, 150, 200, 300]


# ── Worker (must be top-level for Pool pickling) ──────────────────────────────

def _worker(args):
    """Run one combo on Phase A and Phase B; return result dict."""
    block_num, combo_num, smooth_h, smooth_b, dist_h, dist_l, rows_a, rows_b = args

    params = Comb001TrendParams(
        stpmt_smooth_h=smooth_h,
        stpmt_smooth_b=smooth_b,
        stpmt_distance_max_h=dist_h,
        stpmt_distance_max_l=dist_l,
        # Contexto defaults
        trend_r1=1, trend_r2=90, trend_r3=150,
        horaire_allowed_hours_utc=list(range(9, 16)),
        volatility_atr_min=0.0, volatility_atr_max=500.0,
        # Exits defaults
        target_atr_multiplier=10.0, timescan_bars=30,
        # Stops defaults
        stop_intelligent_quality=2, stop_intelligent_recent_volat=2,
        stop_intelligent_ref_volat=20, stop_intelligent_coef_volat=5.0,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "block":          block_num,
        "combo":          combo_num,
        "smooth_h":       smooth_h,
        "smooth_b":       smooth_b,
        "dist_max_h":     dist_h,
        "dist_max_l":     dist_l,
        "phase_a_pf":     round(res_a.profit_factor, 4),
        "phase_a_wr":     round(res_a.win_rate, 4),
        "phase_a_trades": len(res_a.trades),
        "phase_a_equity": round(res_a.equity_points, 2),
        "phase_b_pf":     round(res_b.profit_factor, 4),
        "phase_b_wr":     round(res_b.win_rate, 4),
        "phase_b_trades": len(res_b.trades),
        "phase_b_equity": round(res_b.equity_points, 2),
        "robustness":     round(robustness, 4),
    }


# ── Block runner ──────────────────────────────────────────────────────────────

def run_block(block_num: int, rows_a: list, rows_b: list):
    smooth_h_values = [SMOOTH_H_RANGE[block_num - 1]]
    total_combos = len(smooth_b_range := SMOOTH_B_RANGE) * len(DIST_H_RANGE) * len(DIST_L_RANGE)
    workers = cpu_count()

    print(f"\n{'='*80}")
    print(f"PHASE 1 OPTIMIZATION - BLOCK {block_num} [VECTORIZED + POOL]")
    print(f"{'='*80}")
    print(f"smooth_h values : {smooth_h_values}")
    print(f"Total combos    : {total_combos}")
    print(f"Workers (cores) : {workers}")

    # Build args list (combos in same order as original for reproducibility)
    args_list = []
    combo_num = 0
    for smooth_h in smooth_h_values:
        for smooth_b in SMOOTH_B_RANGE:
            for dist_h in DIST_H_RANGE:
                for dist_l in DIST_L_RANGE:
                    combo_num += 1
                    args_list.append((block_num, combo_num, smooth_h, smooth_b, dist_h, dist_l, rows_a, rows_b))

    t0 = time.perf_counter()
    with Pool(workers) as pool:
        results = pool.map(_worker, args_list)
    elapsed = time.perf_counter() - t0

    # Sort by robustness descending
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Print best found
    best = results[0]
    print(f"\n[DONE] {total_combos} combos in {elapsed:.1f}s ({elapsed/total_combos:.2f}s/combo)")
    print(f"BEST: smooth_h={best['smooth_h']}, smooth_b={best['smooth_b']}, "
          f"dist={best['dist_max_h']}/{best['dist_max_l']} -> "
          f"Robustness={best['robustness']:.4f} "
          f"(PF_A={best['phase_a_pf']:.4f}, PF_B={best['phase_b_pf']:.4f})")

    # Export full log
    log_file = f"phase1_optimization_block_{block_num}_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {log_file}")

    # Export top 10
    top10_file = f"phase1_optimization_block_{block_num}_top10.csv"
    with open(top10_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:10])
    print(f"[OK] {top10_file}")

    # Export best params JSON
    best_dict = {
        "block":                  block_num,
        "stpmt_smooth_h":         best["smooth_h"],
        "stpmt_smooth_b":         best["smooth_b"],
        "stpmt_distance_max_h":   best["dist_max_h"],
        "stpmt_distance_max_l":   best["dist_max_l"],
        "robustness":             best["robustness"],
        "phase_a_pf":             best["phase_a_pf"],
        "phase_b_pf":             best["phase_b_pf"],
    }
    best_file = f"phase1_optimization_block_{block_num}_best_params.json"
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    return results, best_dict


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python phase1_optimization_block_runner_vec.py <block_number>")
        print("block_number: 1-5")
        sys.exit(1)

    block_num = int(sys.argv[1])
    if block_num < 1 or block_num > 5:
        print("Invalid block number. Must be 1-5")
        sys.exit(1)

    print("Loading Phase A and Phase B data...")
    rows_a = load_ohlc_csv("YM_phase_A_clean.csv")
    rows_b = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(rows_a)} rows")
    print(f"Phase B: {len(rows_b)} rows")

    run_block(block_num, rows_a, rows_b)


if __name__ == "__main__":
    main()
