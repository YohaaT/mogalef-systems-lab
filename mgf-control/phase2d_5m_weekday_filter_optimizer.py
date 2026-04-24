"""Phase 2d (5m): Weekday Filter Optimization

Tests 4 weekday block combinations sequentially.

Locked from Phase 1 + 2a + 2b + 2c:
  - Best STPMT signal (Phase 1)
  - Best Trend Filter (Phase 2a)
  - Best Horaire (Phase 2b)
  - Best Volatility (Phase 2c)

Combos (blocked weekdays, 0=Mon, 1=Tue):
  1. all_days: [] - no blocking
  2. no_tuesday: [1] - block Tuesday
  3. no_monday: [0] - block Monday
  4. no_mon_tue: [0, 1] - block both Monday and Tuesday
"""

import csv
import json
from COMB_001_TREND_V1_vectorized import Comb001TrendParams, Comb001TrendVectorized, load_ohlc_csv

# Load Phase 1 + 2a + 2b + 2c
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)
with open("phase2a_5m_trend_filter_best_params.json") as f:
    phase2a = json.load(f)
with open("phase2b_5m_horaire_best_params.json") as f:
    phase2b = json.load(f)
with open("phase2c_5m_volatility_best_params.json") as f:
    phase2c = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
TREND_BEST = phase2a
HORAIRE_BEST = phase2b["hours"]
VOLATILITY_BEST = phase2c

WEEKDAY_COMBOS = {
    "all_days": [],
    "no_tuesday": [1],
    "no_monday": [0],
    "no_mon_tue": [0, 1],
}

EXIT_DEFAULT = {"target_atr_multiplier": 10.0, "timescan_bars": 30}
STOP_DEFAULT = {"stop_intelligent_quality": 2, "stop_intelligent_recent_volat": 2,
                "stop_intelligent_ref_volat": 20, "stop_intelligent_coef_volat": 5.0}


def main():
    print("\nLoading 5m data...")
    rows_a = load_ohlc_csv("YM_phase_A_5m.csv")
    rows_b = load_ohlc_csv("YM_phase_B_5m.csv")

    print("\n" + "="*80)
    print("PHASE 2d (5m) - WEEKDAY FILTER OPTIMIZATION")
    print("="*80)
    print(f"Combos: {list(WEEKDAY_COMBOS.keys())}\n")

    results = []
    for combo_name, blocked_days in WEEKDAY_COMBOS.items():
        params = Comb001TrendParams(
            stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
            stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
            stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
            stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
            trend_r1=TREND_BEST["trend_r1"],
            trend_r2=TREND_BEST["trend_r2"],
            trend_r3=TREND_BEST["trend_r3"],
            horaire_allowed_hours_utc=HORAIRE_BEST,
            contexto_blocked_weekdays=blocked_days,
            volatility_atr_min=VOLATILITY_BEST["atr_min"],
            volatility_atr_max=VOLATILITY_BEST["atr_max"],
            **EXIT_DEFAULT,
            **STOP_DEFAULT,
        )

        strat = Comb001TrendVectorized(params)
        res_a = strat.run(rows_a)
        res_b = strat.run(rows_b)
        robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

        blocked_str = str(blocked_days) if blocked_days else "none"
        result = {
            "weekday_combo": combo_name,
            "blocked_days": blocked_str,
            "phase_a_pf": round(res_a.profit_factor, 4),
            "phase_a_wr": round(res_a.win_rate, 4),
            "phase_a_trades": len(res_a.trades),
            "phase_b_pf": round(res_b.profit_factor, 4),
            "phase_b_wr": round(res_b.win_rate, 4),
            "phase_b_trades": len(res_b.trades),
            "robustness": round(robustness, 4),
        }
        results.append(result)
        print(f"  {combo_name:15} {blocked_str:12} -> Robustness={robustness:.4f}  A_PF={result['phase_a_pf']:.4f}  B_PF={result['phase_b_pf']:.4f}")

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    with open("phase2d_5m_weekday_log.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] phase2d_5m_weekday_log.csv")

    # Best JSON
    best = results[0]
    with open("phase2d_5m_weekday_best_params.json", "w") as f:
        json.dump({
            "phase": "2d",
            "weekday_combo": best["weekday_combo"],
            "blocked_days": json.loads(best["blocked_days"]) if best["blocked_days"] != "none" else [],
            "robustness": best["robustness"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
        }, f, indent=2)
    print(f"[OK] phase2d_5m_weekday_best_params.json")

    print(f"\n[BEST] {best['weekday_combo']} {best['blocked_days']}")
    print(f"       Robustness={best['robustness']:.4f}")


if __name__ == "__main__":
    main()
