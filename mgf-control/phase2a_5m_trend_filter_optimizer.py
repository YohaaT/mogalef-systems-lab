"""Phase 2a (5m): Trend Filter Optimization

Tests 150 combinations of Mogalef Trend Filter parameters (R1, R2, R3).
Single-block execution on one server (can split if needed).

Locked from Phase 1:
  - Best STPMT signal params

Locked at defaults:
  - horaire=[12..15] UTC
  - volatility=(0, 500)
  - exits, stops at defaults
"""

import csv
import json
import sys
from multiprocessing import Pool
from pathlib import Path

from COMB_001_TREND_V1_vectorized import (
    Comb001TrendParams,
    Comb001TrendVectorized,
    load_ohlc_csv,
)

# Load Phase 1 best signal
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
print(f"Loaded Phase 1 best signal: smooth_h={SIGNAL_BEST['stpmt_smooth_h']}, "
      f"smooth_b={SIGNAL_BEST['stpmt_smooth_b']}, "
      f"dist_h={SIGNAL_BEST['stpmt_distance_max_h']}, "
      f"dist_l={SIGNAL_BEST['stpmt_distance_max_l']}")

# Trend Filter grid: 150 combos
R1_VALUES  = [1, 2, 3, 4, 5]
R2_VALUES  = [50, 70, 90, 110, 130, 150]
R3_VALUES  = [100, 150, 200, 250, 300]

# Locked defaults
HORAIRE_DEFAULT = list(range(12, 16))  # 12-15 UTC
VOLATILITY_DEFAULT = (0.0, 500.0)
WEEKDAY_DEFAULT = []
EXIT_DEFAULT = {"target_atr_multiplier": 10.0, "timescan_bars": 30}
STOP_DEFAULT = {"stop_intelligent_quality": 2, "stop_intelligent_recent_volat": 2,
                "stop_intelligent_ref_volat": 20, "stop_intelligent_coef_volat": 5.0}


def _worker(args):
    rows_a, rows_b, r1, r2, r3 = args

    params = Comb001TrendParams(
        stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
        stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
        stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
        stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
        trend_r1=r1,
        trend_r2=r2,
        trend_r3=r3,
        horaire_allowed_hours_utc=HORAIRE_DEFAULT,
        contexto_blocked_weekdays=WEEKDAY_DEFAULT,
        volatility_atr_min=VOLATILITY_DEFAULT[0],
        volatility_atr_max=VOLATILITY_DEFAULT[1],
        **EXIT_DEFAULT,
        **STOP_DEFAULT,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "trend_r1": r1,
        "trend_r2": r2,
        "trend_r3": r3,
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


def main():
    print("\nLoading 5m data...")
    rows_a = load_ohlc_csv("YM_phase_A_5m.csv")
    rows_b = load_ohlc_csv("YM_phase_B_5m.csv")
    print(f"Phase A: {len(rows_a)} bars | Phase B: {len(rows_b)} bars")

    print("\n" + "="*80)
    print("PHASE 2a (5m) - TREND FILTER OPTIMIZATION")
    print("="*80)
    print(f"Grid: R1={R1_VALUES} x R2={R2_VALUES} x R3={R3_VALUES}")
    print(f"Total combos: {len(R1_VALUES) * len(R2_VALUES) * len(R3_VALUES)}\n")

    args_list = [
        (rows_a, rows_b, r1, r2, r3)
        for r1 in R1_VALUES
        for r2 in R2_VALUES
        for r3 in R3_VALUES
    ]

    with Pool(processes=8) as pool:
        results = pool.map(_worker, args_list)

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    log_file = "phase2a_5m_trend_filter_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {log_file}")

    # Best JSON
    best = results[0]
    best_file = "phase2a_5m_trend_filter_best_params.json"
    with open(best_file, "w") as f:
        json.dump({
            "phase": "2a",
            "trend_r1": best["trend_r1"],
            "trend_r2": best["trend_r2"],
            "trend_r3": best["trend_r3"],
            "robustness": best["robustness"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
        }, f, indent=2)
    print(f"[OK] {best_file}")

    # Top 10
    with open("phase2a_5m_trend_filter_top10.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:10])

    print(f"\n[BEST] r1={best['trend_r1']}, r2={best['trend_r2']}, r3={best['trend_r3']}")
    print(f"       Robustness={best['robustness']:.4f}  A_PF={best['phase_a_pf']:.4f}  B_PF={best['phase_b_pf']:.4f}")


if __name__ == "__main__":
    main()
