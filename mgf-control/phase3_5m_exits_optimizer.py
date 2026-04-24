"""Phase 3 (5m): Exits Optimization

Tests 16 combinations of exit parameters (Profit Target ATR multiplier × TimeStop bars).

Locked from Phase 1 + 2:
  - Best STPMT signal (Phase 1)
  - Best Contexto (Phase 2: trend + horaire + volatility + weekday)

Grid (16 combos):
  - target_atr_multiplier: [7.0, 8.0, 9.0, 10.0]
  - timescan_bars: [20, 25, 30, 35]
"""

import csv
import json
from multiprocessing import Pool
from COMB_001_TREND_V1_vectorized import Comb001TrendParams, Comb001TrendVectorized, load_ohlc_csv

# Load Phase 1 + 2
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)
with open("phase2_5m_best_params.json") as f:
    phase2 = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
CONTEXTO_BEST = phase2["contexto_component"]

# Exit grid
TARGET_ATR_VALUES = [7.0, 8.0, 9.0, 10.0]
TIMESCAN_VALUES = [20, 25, 30, 35]

STOP_DEFAULT = {
    "stop_intelligent_quality": 2,
    "stop_intelligent_recent_volat": 2,
    "stop_intelligent_ref_volat": 20,
    "stop_intelligent_coef_volat": 5.0,
}


def _worker(args):
    rows_a, rows_b, target_atr, timescan = args

    params = Comb001TrendParams(
        stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
        stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
        stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
        stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
        trend_r1=CONTEXTO_BEST["trend_filter"]["trend_r1"],
        trend_r2=CONTEXTO_BEST["trend_filter"]["trend_r2"],
        trend_r3=CONTEXTO_BEST["trend_filter"]["trend_r3"],
        horaire_allowed_hours_utc=CONTEXTO_BEST["horaire"]["hours"],
        contexto_blocked_weekdays=CONTEXTO_BEST["weekday_filter"]["blocked_days"],
        volatility_atr_min=CONTEXTO_BEST["volatility"]["atr_min"],
        volatility_atr_max=CONTEXTO_BEST["volatility"]["atr_max"],
        target_atr_multiplier=target_atr,
        timescan_bars=timescan,
        **STOP_DEFAULT,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "target_atr_multiplier": target_atr,
        "timescan_bars": timescan,
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

    print("\n" + "="*80)
    print("PHASE 3 (5m) - EXITS OPTIMIZATION")
    print("="*80)
    print(f"Grid: target_atr={TARGET_ATR_VALUES} x timescan={TIMESCAN_VALUES}")
    print(f"Total combos: {len(TARGET_ATR_VALUES) * len(TIMESCAN_VALUES)}\n")

    args_list = [
        (rows_a, rows_b, target, ts)
        for target in TARGET_ATR_VALUES
        for ts in TIMESCAN_VALUES
    ]

    with Pool(processes=8) as pool:
        results = pool.map(_worker, args_list)

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    log_file = "phase3_5m_exits_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"[OK] {log_file}")

    # Best JSON
    best = results[0]
    with open("phase3_5m_exits_best_params.json", "w") as f:
        json.dump({
            "phase": 3,
            "target_atr_multiplier": best["target_atr_multiplier"],
            "timescan_bars": best["timescan_bars"],
            "robustness": best["robustness"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
        }, f, indent=2)
    print(f"[OK] phase3_5m_exits_best_params.json")

    # Top 5
    with open("phase3_5m_exits_top5.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results[:5])

    print(f"\n[BEST] target_atr={best['target_atr_multiplier']}, timescan={best['timescan_bars']}")
    print(f"       Robustness={best['robustness']:.4f}  A_PF={best['phase_a_pf']:.4f}  B_PF={best['phase_b_pf']:.4f}")


if __name__ == "__main__":
    main()
