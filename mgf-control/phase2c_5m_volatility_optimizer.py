"""Phase 2c (5m): Volatility Filter Optimization

Tests 5 volatility profiles sequentially.

Locked from Phase 1 + 2a + 2b:
  - Best STPMT signal (Phase 1)
  - Best Trend Filter (Phase 2a)
  - Best Horaire (Phase 2b)

Profiles (ATR min, ATR max):
  1. none: (0, 500) - no volatility filter
  2. min_floor: (10, 500) - eliminate very low volatility
  3. max_ceiling: (0, 200) - eliminate very high volatility
  4. tight: (10, 250) - moderate band
  5. selective: (20, 200) - tight band (Mogalef style)
"""

import csv
import json
from COMB_001_TREND_V1_vectorized import Comb001TrendParams, Comb001TrendVectorized, load_ohlc_csv

# Load Phase 1 + 2a + 2b
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)
with open("phase2a_5m_trend_filter_best_params.json") as f:
    phase2a = json.load(f)
with open("phase2b_5m_horaire_best_params.json") as f:
    phase2b = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
TREND_BEST = phase2a
HORAIRE_BEST = phase2b["hours"]

VOLATILITY_PROFILES = {
    "none": (0.0, 500.0),
    "min_floor": (10.0, 500.0),
    "max_ceiling": (0.0, 200.0),
    "tight": (10.0, 250.0),
    "selective": (20.0, 200.0),
}

WEEKDAY_DEFAULT = []
EXIT_DEFAULT = {"target_atr_multiplier": 10.0, "timescan_bars": 30}
STOP_DEFAULT = {"stop_intelligent_quality": 2, "stop_intelligent_recent_volat": 2,
                "stop_intelligent_ref_volat": 20, "stop_intelligent_coef_volat": 5.0}


def main():
    print("\nLoading 5m data...")
    rows_a = load_ohlc_csv("YM_phase_A_5m.csv")
    rows_b = load_ohlc_csv("YM_phase_B_5m.csv")

    print("\n" + "="*80)
    print("PHASE 2c (5m) - VOLATILITY FILTER OPTIMIZATION")
    print("="*80)
    print(f"Profiles: {list(VOLATILITY_PROFILES.keys())}\n")

    results = []
    for profile_name, (atr_min, atr_max) in VOLATILITY_PROFILES.items():
        params = Comb001TrendParams(
            stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
            stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
            stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
            stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
            trend_r1=TREND_BEST["trend_r1"],
            trend_r2=TREND_BEST["trend_r2"],
            trend_r3=TREND_BEST["trend_r3"],
            horaire_allowed_hours_utc=HORAIRE_BEST,
            contexto_blocked_weekdays=WEEKDAY_DEFAULT,
            volatility_atr_min=atr_min,
            volatility_atr_max=atr_max,
            **EXIT_DEFAULT,
            **STOP_DEFAULT,
        )

        strat = Comb001TrendVectorized(params)
        res_a = strat.run(rows_a)
        res_b = strat.run(rows_b)
        robustness = res_b.profit_factor / res_a.profit_factor if res_a.profit_factor > 0 else 0.0

        result = {
            "volatility_profile": profile_name,
            "atr_min": atr_min,
            "atr_max": atr_max,
            "phase_a_pf": round(res_a.profit_factor, 4),
            "phase_a_wr": round(res_a.win_rate, 4),
            "phase_a_trades": len(res_a.trades),
            "phase_b_pf": round(res_b.profit_factor, 4),
            "phase_b_wr": round(res_b.win_rate, 4),
            "phase_b_trades": len(res_b.trades),
            "robustness": round(robustness, 4),
        }
        results.append(result)
        print(f"  {profile_name:12} ({atr_min:5.1f},{atr_max:6.1f}) -> Robustness={robustness:.4f}  A_PF={result['phase_a_pf']:.4f}  B_PF={result['phase_b_pf']:.4f}")

    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    with open("phase2c_5m_volatility_log.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] phase2c_5m_volatility_log.csv")

    # Best JSON
    best = results[0]
    with open("phase2c_5m_volatility_best_params.json", "w") as f:
        json.dump({
            "phase": "2c",
            "volatility_profile": best["volatility_profile"],
            "atr_min": best["atr_min"],
            "atr_max": best["atr_max"],
            "robustness": best["robustness"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
        }, f, indent=2)
    print(f"[OK] phase2c_5m_volatility_best_params.json")

    print(f"\n[BEST] {best['volatility_profile']} ATR ({best['atr_min']}, {best['atr_max']})")
    print(f"       Robustness={best['robustness']:.4f}")


if __name__ == "__main__":
    main()
