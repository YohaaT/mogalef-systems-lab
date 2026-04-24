"""Phase 3 Exits Optimizer - with Mogalef-Strict Phase 2 params"""

import csv
import json
from multiprocessing import Pool
from COMB_001_TREND_V1_vectorized import Comb001TrendParams, Comb001TrendVectorized, load_ohlc_csv

# Load Phase 1 + Phase 2 (MOGALEF-STRICT)
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)
with open("phase2_5m_best_params_mogalef_strict.json") as f:
    phase2 = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
CONTEXTO_BEST = phase2

# Exits grid
TARGET_VALUES = [7.0, 8.0, 9.0, 10.0]
TIMESCAN_VALUES = [20, 25, 30, 35]

def _worker(args):
    rows_a, rows_b, target, timescan = args

    params = Comb001TrendParams(
        stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
        stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
        stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
        stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
        trend_r1=CONTEXTO_BEST["trend_filter_best"]["trend_r1"],
        trend_r2=CONTEXTO_BEST["trend_filter_best"]["trend_r2"],
        trend_r3=CONTEXTO_BEST["trend_filter_best"]["trend_r3"],
        horaire_allowed_hours_utc=CONTEXTO_BEST["horaire_best"]["horaire_allowed_hours_utc"],
        contexto_blocked_weekdays=CONTEXTO_BEST["weekday_filter_best"]["blocked_weekdays"],
        volatility_atr_min=CONTEXTO_BEST["volatility_best"]["volatility_atr_min"],
        volatility_atr_max=CONTEXTO_BEST["volatility_best"]["volatility_atr_max"],
        target_atr_multiplier=target,
        timescan_bars=timescan,
        stop_intelligent_quality=1,
        stop_intelligent_recent_volat=1,
        stop_intelligent_ref_volat=10,
        stop_intelligent_coef_volat=3.0,
    )

    strat = Comb001TrendVectorized(params)
    res_a = strat.run(rows_a)
    res_b = strat.run(rows_b)

    robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

    return {
        "target_atr_multiplier": target,
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
    print("PHASE 3 (5m) - EXITS OPTIMIZATION (Mogalef-Strict Phase 2)")
    print("="*80)
    print("Grid: target_atr=%s x timescan=%s" % (TARGET_VALUES, TIMESCAN_VALUES))
    n_combos = len(TARGET_VALUES) * len(TIMESCAN_VALUES)
    print("Total combos: %d\n" % n_combos)

    args_list = [
        (rows_a, rows_b, t, ts)
        for t in TARGET_VALUES
        for ts in TIMESCAN_VALUES
    ]

    with Pool(processes=8) as pool:
        results = pool.map(_worker, args_list)

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    log_file = "phase3_5m_exits_mogalef_strict_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print("[OK] %s" % log_file)

    # Best JSON
    best = results[0]
    best_file = "phase3_5m_exits_mogalef_strict_best_params.json"
    with open(best_file, "w") as f:
        json.dump({
            "target_atr_multiplier": best["target_atr_multiplier"],
            "timescan_bars": best["timescan_bars"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
            "phase3_robustness": best["robustness"],
        }, f, indent=2)
    print("[OK] %s" % best_file)

    print("\n[BEST] target=%.1f, timescan=%d" % (best["target_atr_multiplier"], best["timescan_bars"]))
    print("       Robustness=%.4f  A_PF=%.4f  B_PF=%.4f" % (best["robustness"], best["phase_a_pf"], best["phase_b_pf"]))

    print("\n" + "="*80)
    print("PHASE 3 COMPLETE - Ready for Phase 4")
    print("="*80)

if __name__ == "__main__":
    main()
