"""Phase 2a Optimization: Trend Filter (R1, R2, R3) - Vectorized + Pool

Optimizes Contexto component (Trend Filter) while locking Phase 1 best Signal.

Phase 1 Best (LOCKED):
- stpmt_smooth_h: 3
- stpmt_smooth_b: 2
- stpmt_distance_max_h: 50
- stpmt_distance_max_l: 50

Phase 2a Grid:
- trend_r1: [1, 2, 3, 4, 5]
- trend_r2: [50, 70, 90, 110, 130, 150]
- trend_r3: [100, 150, 200, 250, 300]
Total: 5 × 6 × 5 = 150 combos (can be split into 2 blocks of 75 each)
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

# Phase 1 Best (LOCKED)
PHASE1_BEST = {
    "stpmt_smooth_h": 3,
    "stpmt_smooth_b": 2,
    "stpmt_distance_max_h": 50,
    "stpmt_distance_max_l": 50,
}

# Phase 2a Grid: Trend Filter parameters
TREND_R1_RANGE    = [1, 2, 3, 4, 5]
TREND_R2_RANGE    = [50, 70, 90, 110, 130, 150]
TREND_R3_RANGE    = [100, 150, 200, 250, 300]

# Defaults (locked from Phase 1)
DEFAULT_HORAIRE = list(range(9, 16))  # 9-15 UTC
DEFAULT_VOLATILITY_MIN = 0.0
DEFAULT_VOLATILITY_MAX = 500.0
DEFAULT_TARGET_ATR_MULT = 10.0
DEFAULT_TIMESCAN_BARS = 30
DEFAULT_STOP_QUAL = 2
DEFAULT_STOP_RECENT = 2
DEFAULT_STOP_REF = 20
DEFAULT_STOP_COEF = 5.0


def _worker(args):
    """Run one combo on Phase A and Phase B; return result dict."""
    block_num, combo_num, r1, r2, r3, rows_a, rows_b = args

    params = Comb001TrendParams(
        # Phase 1 Locked (Signal)
        stpmt_smooth_h=PHASE1_BEST["stpmt_smooth_h"],
        stpmt_smooth_b=PHASE1_BEST["stpmt_smooth_b"],
        stpmt_distance_max_h=PHASE1_BEST["stpmt_distance_max_h"],
        stpmt_distance_max_l=PHASE1_BEST["stpmt_distance_max_l"],
        # Phase 2a (Trend Filter - VARIED)
        trend_r1=r1,
        trend_r2=r2,
        trend_r3=r3,
        # Phase 2a Defaults (Horaire, Volatility)
        horaire_allowed_hours_utc=DEFAULT_HORAIRE,
        volatility_atr_min=DEFAULT_VOLATILITY_MIN,
        volatility_atr_max=DEFAULT_VOLATILITY_MAX,
        # Phase 3 Defaults (Exits)
        target_atr_multiplier=DEFAULT_TARGET_ATR_MULT,
        timescan_bars=DEFAULT_TIMESCAN_BARS,
        # Phase 4 Defaults (Stops)
        stop_intelligent_quality=DEFAULT_STOP_QUAL,
        stop_intelligent_recent_volat=DEFAULT_STOP_RECENT,
        stop_intelligent_ref_volat=DEFAULT_STOP_REF,
        stop_intelligent_coef_volat=DEFAULT_STOP_COEF,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "block":          block_num,
        "combo":          combo_num,
        "trend_r1":       r1,
        "trend_r2":       r2,
        "trend_r3":       r3,
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


def run_block(block_num: int, rows_a: list, rows_b: list):
    """Run Phase 2a Trend Filter optimization for a specific block."""
    # Divide 150 combos into 2 blocks if needed
    # Block 1: r1 values [1,2] (60 combos = 2×6×5)
    # Block 2: r1 values [3,4,5] (90 combos = 3×6×5)
    # OR: run as 1 block of 150 if preferred

    if block_num == 1:
        r1_values = [1, 2]  # 60 combos
    elif block_num == 2:
        r1_values = [3, 4, 5]  # 90 combos
    else:
        raise ValueError("Block must be 1 or 2 for Phase 2a (150 combos total)")

    total_combos = len(r1_values) * len(TREND_R2_RANGE) * len(TREND_R3_RANGE)
    workers = cpu_count()

    print(f"\n{'='*80}")
    print(f"PHASE 2a OPTIMIZATION - BLOCK {block_num} [TREND FILTER - VECTORIZED + POOL]")
    print(f"{'='*80}")
    print(f"trend_r1 values : {r1_values}")
    print(f"trend_r2 range  : {TREND_R2_RANGE} ({len(TREND_R2_RANGE)} values)")
    print(f"trend_r3 range  : {TREND_R3_RANGE} ({len(TREND_R3_RANGE)} values)")
    print(f"Total combos    : {total_combos}")
    print(f"Workers (cores) : {workers}")
    print(f"Phase 1 Signal  : LOCKED (smooth_h=3, smooth_b=2, dist=50/50, robustness=1.3424)")

    # Build args list
    args_list = []
    combo_num = 0
    for r1 in r1_values:
        for r2 in TREND_R2_RANGE:
            for r3 in TREND_R3_RANGE:
                combo_num += 1
                args_list.append((block_num, combo_num, r1, r2, r3, rows_a, rows_b))

    t0 = time.perf_counter()
    with Pool(workers) as pool:
        results = pool.map(_worker, args_list)
    elapsed = time.perf_counter() - t0

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Print best
    best = results[0]
    print(f"\n[DONE] {total_combos} combos in {elapsed:.1f}s ({elapsed/total_combos:.2f}s/combo)")
    print(f"BEST: trend_r1={best['trend_r1']}, trend_r2={best['trend_r2']}, "
          f"trend_r3={best['trend_r3']} -> "
          f"Robustness={best['robustness']:.4f} "
          f"(PF_A={best['phase_a_pf']:.4f}, PF_B={best['phase_b_pf']:.4f})")

    # Export full log
    log_file = f"phase2a_trend_optimization_block_{block_num}_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {log_file}")

    # Export top 10
    top10_file = f"phase2a_trend_optimization_block_{block_num}_top10.csv"
    with open(top10_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:10])
    print(f"[OK] {top10_file}")

    # Export best params JSON
    best_dict = {
        "block":      block_num,
        "trend_r1":   best["trend_r1"],
        "trend_r2":   best["trend_r2"],
        "trend_r3":   best["trend_r3"],
        "robustness": best["robustness"],
        "phase_a_pf": best["phase_a_pf"],
        "phase_b_pf": best["phase_b_pf"],
    }
    best_file = f"phase2a_trend_optimization_block_{block_num}_best_params.json"
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    return results, best_dict


def main():
    if len(sys.argv) < 2:
        print("Usage: python phase2a_trend_optimization_block_runner_vec.py <block_number>")
        print("block_number: 1 (r1=[1,2], 60 combos) or 2 (r1=[3,4,5], 90 combos)")
        print("Total: 150 combos across 2 blocks")
        sys.exit(1)

    block_num = int(sys.argv[1])
    if block_num < 1 or block_num > 2:
        print("Invalid block number. Must be 1 or 2")
        sys.exit(1)

    print("Loading Phase A and Phase B data...")
    rows_a = load_ohlc_csv("YM_phase_A_clean.csv")
    rows_b = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(rows_a)} rows")
    print(f"Phase B: {len(rows_b)} rows")

    run_block(block_num, rows_a, rows_b)


if __name__ == "__main__":
    main()
