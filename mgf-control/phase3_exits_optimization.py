"""Phase 3 Optimization: Exits (Target ATR × TimeStop bars) - Sequential

Tests 16 combinations of profit target (ATR multiplier) and time-based exit (TimeStop bars).

Locked from Phase 1+2:
- stpmt_smooth_h: 3, stpmt_smooth_b: 2, distance_max: 50/50
- trend_r1: 3, trend_r2: 50, trend_r3: 200
- horaire_allowed_hours_utc: [12, 13, 14, 15]
- volatility_atr_min: 20.0, volatility_atr_max: 200.0

Phase 3: Test 16 combinations (4x4 grid)
- target_atr_multiplier: [5.0, 10.0, 15.0, 20.0]
- timescan_bars: [20, 30, 40, 50]
"""

import csv
import json
import sys
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

# Phase 2 Best (LOCKED)
PHASE2_BEST = {
    "trend_r1": 3,
    "trend_r2": 50,
    "trend_r3": 200,
    "horaire_allowed_hours_utc": [12, 13, 14, 15],
    "volatility_atr_min": 20.0,
    "volatility_atr_max": 200.0,
}

# Phase 3 Grid (4 x 4 = 16 combinations)
TARGET_ATR_MULTS = [5.0, 10.0, 15.0, 20.0]
TIMESCAN_BARS = [20, 30, 40, 50]

# Phase 4 Defaults (Stops - locked)
DEFAULT_STOP_QUAL = 2
DEFAULT_STOP_RECENT = 2
DEFAULT_STOP_REF = 20
DEFAULT_STOP_COEF = 5.0


def run_exits_tests(rows_a, rows_b):
    """Run 16 exit combinations (4 ATR mult × 4 TimeStop bars) sequentially."""
    print(f"\n{'='*80}")
    print(f"PHASE 3 OPTIMIZATION - EXITS [4x4 GRID = 16 COMBOS]")
    print(f"{'='*80}")
    print(f"Phase 1 Signal  : LOCKED (smooth_h=3, smooth_b=2, dist=50/50)")
    print(f"Phase 2 Contexto: LOCKED (r1=3, r2=50, r3=200, hours=[12-15], atr=20-200)")
    print(f"Phase 3 Tests   : 16 Exit combinations (4 ATR × 4 TimeStop)\n")

    results = []
    best_overall = None
    best_robustness = 0.0
    combo_num = 0

    for target_mult in TARGET_ATR_MULTS:
        for timescan in TIMESCAN_BARS:
            combo_num += 1

            print(f"\n[{combo_num:2d}/16] target_atr={target_mult:5.1f} | timescan_bars={timescan:2d}")

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
                # Phase 3 (VARIED)
                target_atr_multiplier=target_mult,
                timescan_bars=timescan,
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

            result = {
                "combo_id":        combo_num,
                "target_atr":      target_mult,
                "timescan_bars":   timescan,
                "phase_a_pf":      round(res_a.profit_factor, 4),
                "phase_a_wr":      round(res_a.win_rate, 4),
                "phase_a_trades":  len(res_a.trades),
                "phase_a_equity":  round(res_a.equity_points, 2),
                "phase_b_pf":      round(res_b.profit_factor, 4),
                "phase_b_wr":      round(res_b.win_rate, 4),
                "phase_b_trades":  len(res_b.trades),
                "phase_b_equity":  round(res_b.equity_points, 2),
                "robustness":      round(robustness, 4),
            }
            results.append(result)

            print(f"    PF_A={res_a.profit_factor:.4f} | PF_B={res_b.profit_factor:.4f} | Robustness={robustness:.4f}")

            if robustness > best_robustness:
                best_robustness = robustness
                best_overall = result

    # Sort by robustness
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Export full log
    log_file = "phase3_exits_optimization_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] {log_file}")

    # Export best params JSON
    best_dict = {
        "combo_id":       best_overall["combo_id"],
        "target_atr":     best_overall["target_atr"],
        "timescan_bars":  best_overall["timescan_bars"],
        "robustness":     best_overall["robustness"],
        "phase_a_pf":     best_overall["phase_a_pf"],
        "phase_b_pf":     best_overall["phase_b_pf"],
    }
    best_file = "phase3_exits_best_params.json"
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    print(f"\n[BEST] target_atr={best_overall['target_atr']} | timescan={best_overall['timescan_bars']:2d} -> Robustness={best_overall['robustness']:.4f}")

    return results, best_dict


def main():
    print("Loading Phase A and Phase B data...")
    rows_a = load_ohlc_csv("YM_phase_A_clean.csv")
    rows_b = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(rows_a)} rows")
    print(f"Phase B: {len(rows_b)} rows")

    run_exits_tests(rows_a, rows_b)


if __name__ == "__main__":
    main()
