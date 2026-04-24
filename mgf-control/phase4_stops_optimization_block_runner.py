"""Phase 4 Optimization: Stop Inteligente - Vectorized Block Runner

Tests Stop Inteligente parameters in parallel using multiprocessing.Pool.

Locked from Phase 1+2+3:
- Signal: smooth_h=3, smooth_b=2, distance_max=50/50
- Trend: r1=3, r2=50, r3=200
- Horaire: [12,13,14,15]
- Volatility: 20-200 ATR
- Exits: target_atr=10.0, timescan=30

Phase 4: Test 108 combinations (4x3x3x3 grid, split into 2 blocks)
- Block 1: quality=[1,2] × recent=[1,2,3] × ref=[10,20] × coef=[3.0,5.0]
- Block 2: quality=[3] × recent=[1,2,3] × ref=[10,20,30] × coef=[5.0,7.0]
"""

import csv
import json
import sys
from pathlib import Path
from multiprocessing import Pool

from COMB_001_TREND_V1_vectorized import (
    Comb001TrendParams,
    Comb001TrendVectorized,
    load_ohlc_csv,
)

# Phase 1+2+3 Best (LOCKED)
PHASE1_BEST = {
    "stpmt_smooth_h": 3,
    "stpmt_smooth_b": 2,
    "stpmt_distance_max_h": 50,
    "stpmt_distance_max_l": 50,
}

PHASE2_BEST = {
    "trend_r1": 3,
    "trend_r2": 50,
    "trend_r3": 200,
    "horaire_allowed_hours_utc": [12, 13, 14, 15],
    "volatility_atr_min": 20.0,
    "volatility_atr_max": 200.0,
}

PHASE3_BEST = {
    "target_atr_multiplier": 10.0,
    "timescan_bars": 30,
}

# Phase 4 Grid parameters
BLOCK_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Block 1: quality=[1,2] × recent=[1,2,3] × ref=[10,20] × coef=[3.0,5.0] = 48 combos
# Block 2: quality=[3] × recent=[1,2,3] × ref=[10,20,30] × coef=[5.0,7.0] = 60 combos

if BLOCK_NUM == 1:
    QUALITY_VALUES = [1, 2]
    RECENT_VALUES = [1, 2, 3]
    REF_VALUES = [10, 20]
    COEF_VALUES = [3.0, 5.0]
else:  # BLOCK_NUM == 2
    QUALITY_VALUES = [3]
    RECENT_VALUES = [1, 2, 3]
    REF_VALUES = [10, 20, 30]
    COEF_VALUES = [5.0, 7.0]


def _worker(args):
    """Worker function for multiprocessing.Pool."""
    (rows_a, rows_b, quality, recent, ref_vol, coef) = args

    params = Comb001TrendParams(
        # Phase 1 (LOCKED)
        stpmt_smooth_h=PHASE1_BEST["stpmt_smooth_h"],
        stpmt_smooth_b=PHASE1_BEST["stpmt_smooth_b"],
        stpmt_distance_max_h=PHASE1_BEST["stpmt_distance_max_h"],
        stpmt_distance_max_l=PHASE1_BEST["stpmt_distance_max_l"],
        # Phase 2 (LOCKED)
        trend_r1=PHASE2_BEST["trend_r1"],
        trend_r2=PHASE2_BEST["trend_r2"],
        trend_r3=PHASE2_BEST["trend_r3"],
        horaire_allowed_hours_utc=PHASE2_BEST["horaire_allowed_hours_utc"],
        volatility_atr_min=PHASE2_BEST["volatility_atr_min"],
        volatility_atr_max=PHASE2_BEST["volatility_atr_max"],
        # Phase 3 (LOCKED)
        target_atr_multiplier=PHASE3_BEST["target_atr_multiplier"],
        timescan_bars=PHASE3_BEST["timescan_bars"],
        # Phase 4 (VARIED)
        stop_intelligent_quality=quality,
        stop_intelligent_recent_volat=recent,
        stop_intelligent_ref_volat=ref_vol,
        stop_intelligent_coef_volat=coef,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "quality": quality,
        "recent": recent,
        "ref_vol": ref_vol,
        "coef": coef,
        "phase_a_pf": round(res_a.profit_factor, 4),
        "phase_a_wr": round(res_a.win_rate, 4),
        "phase_a_trades": len(res_a.trades),
        "phase_a_equity": round(res_a.equity_points, 2),
        "phase_b_pf": round(res_b.profit_factor, 4),
        "phase_b_wr": round(res_b.win_rate, 4),
        "phase_b_trades": len(res_b.trades),
        "phase_b_equity": round(res_b.equity_points, 2),
        "robustness": round(robustness, 4),
    }


def run_block(block_num, rows_a, rows_b):
    """Run Phase 4 block with multiprocessing."""
    print(f"\n{'='*80}")
    print(f"PHASE 4 OPTIMIZATION - BLOCK {block_num} [VECTORIZED + POOL]")
    print(f"{'='*80}")
    print(f"Phase 1+2+3 Locked (Signal + Contexto + Exits)")
    print(f"Phase 4 Tests   : Stop Inteligente parameters\n")

    # Build combinations
    args_list = []
    for quality in QUALITY_VALUES:
        for recent in RECENT_VALUES:
            for ref_vol in REF_VALUES:
                for coef in COEF_VALUES:
                    args_list.append((rows_a, rows_b, quality, recent, ref_vol, coef))

    total_combos = len(args_list)
    print(f"Total combos in block {block_num}: {total_combos}")
    print(f"  quality={QUALITY_VALUES}")
    print(f"  recent={RECENT_VALUES}")
    print(f"  ref_vol={REF_VALUES}")
    print(f"  coef={COEF_VALUES}\n")

    # Execute with Pool
    num_workers = 8
    with Pool(processes=num_workers) as pool:
        results = pool.map(_worker, args_list)

    # Sort by robustness
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Export log
    log_file = f"phase4_stops_optimization_block_{block_num}_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] {log_file}")

    # Export best
    best = results[0]
    best_file = f"phase4_stops_optimization_block_{block_num}_best_params.json"
    best_dict = {
        "block": block_num,
        "quality": best["quality"],
        "recent": best["recent"],
        "ref_vol": best["ref_vol"],
        "coef": best["coef"],
        "robustness": best["robustness"],
        "phase_a_pf": best["phase_a_pf"],
        "phase_b_pf": best["phase_b_pf"],
    }
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    # Top 10
    top10_file = f"phase4_stops_optimization_block_{block_num}_top10.csv"
    with open(top10_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:10])
    print(f"[OK] {top10_file}")

    print(f"\n[BEST] quality={best['quality']}, recent={best['recent']}, ref={best['ref_vol']}, coef={best['coef']:.1f}")
    print(f"       Robustness={best['robustness']:.4f}")


def main():
    print("Loading Phase A and Phase B data...")
    rows_a = load_ohlc_csv("YM_phase_A_clean.csv")
    rows_b = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(rows_a)} rows")
    print(f"Phase B: {len(rows_b)} rows")

    run_block(BLOCK_NUM, rows_a, rows_b)


if __name__ == "__main__":
    main()
