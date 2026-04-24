"""Phase 2b (5m): Horaire Filter Optimization

Tests 6 horaire profiles sequentially (no parallelism needed, fast).

Locked from Phase 1 + 2a:
  - Best STPMT signal (Phase 1)
  - Best Trend Filter (Phase 2a)

Profiles (UTC hours):
  1. all_days: [0..23] - no time filter
  2. daytime: [9..16] - standard trading hours
  3. daytime_evening: [9..16, 20..22] - Mogalef: day + evening
  4. early: [8..16] - pre-market included
  5. morning: [9..12] - morning only
  6. afternoon: [13..16] - afternoon only
"""

import csv
import json
from COMB_001_TREND_V1_vectorized import Comb001TrendParams, Comb001TrendVectorized, load_ohlc_csv

# Load Phase 1 + 2a
with open("phase1_5m_best_params.json") as f:
    phase1 = json.load(f)
with open("phase2a_5m_trend_filter_best_params.json") as f:
    phase2a = json.load(f)

SIGNAL_BEST = phase1["signal_best"]
TREND_BEST = phase2a

HORAIRE_PROFILES = {
    "all_days": list(range(0, 24)),
    "daytime": list(range(9, 17)),  # 9-16 UTC
    "daytime_evening": list(range(9, 17)) + list(range(20, 23)),  # 9-16, 20-22 UTC
    "early": list(range(8, 17)),  # 8-16 UTC
    "morning": list(range(9, 13)),  # 9-12 UTC
    "afternoon": list(range(13, 17)),  # 13-16 UTC
}

VOLATILITY_DEFAULT = (0.0, 500.0)
WEEKDAY_DEFAULT = []
EXIT_DEFAULT = {"target_atr_multiplier": 10.0, "timescan_bars": 30}
STOP_DEFAULT = {"stop_intelligent_quality": 2, "stop_intelligent_recent_volat": 2,
                "stop_intelligent_ref_volat": 20, "stop_intelligent_coef_volat": 5.0}


def main():
    print("\nLoading 5m data...")
    rows_a = load_ohlc_csv("YM_phase_A_5m.csv")
    rows_b = load_ohlc_csv("YM_phase_B_5m.csv")

    print("\n" + "="*80)
    print("PHASE 2b (5m) - HORAIRE FILTER OPTIMIZATION")
    print("="*80)
    print(f"Profiles: {list(HORAIRE_PROFILES.keys())}\n")

    results = []
    for profile_name, hours in HORAIRE_PROFILES.items():
        params = Comb001TrendParams(
            stpmt_smooth_h=SIGNAL_BEST["stpmt_smooth_h"],
            stpmt_smooth_b=SIGNAL_BEST["stpmt_smooth_b"],
            stpmt_distance_max_h=SIGNAL_BEST["stpmt_distance_max_h"],
            stpmt_distance_max_l=SIGNAL_BEST["stpmt_distance_max_l"],
            trend_r1=TREND_BEST["trend_r1"],
            trend_r2=TREND_BEST["trend_r2"],
            trend_r3=TREND_BEST["trend_r3"],
            horaire_allowed_hours_utc=hours,
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

        result = {
            "horaire_profile": profile_name,
            "hours": str(hours),
            "phase_a_pf": round(res_a.profit_factor, 4),
            "phase_a_wr": round(res_a.win_rate, 4),
            "phase_a_trades": len(res_a.trades),
            "phase_b_pf": round(res_b.profit_factor, 4),
            "phase_b_wr": round(res_b.win_rate, 4),
            "phase_b_trades": len(res_b.trades),
            "robustness": round(robustness, 4),
        }
        results.append(result)
        print(f"  {profile_name:18} -> Robustness={robustness:.4f}  A_PF={result['phase_a_pf']:.4f}  B_PF={result['phase_b_pf']:.4f}")

    # Sort by robustness
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # CSV log
    with open("phase2b_5m_horaire_log.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] phase2b_5m_horaire_log.csv")

    # Best JSON
    best = results[0]
    with open("phase2b_5m_horaire_best_params.json", "w") as f:
        json.dump({
            "phase": "2b",
            "horaire_profile": best["horaire_profile"],
            "hours": json.loads(best["hours"]),  # Convert back to list
            "robustness": best["robustness"],
            "phase_a_pf": best["phase_a_pf"],
            "phase_b_pf": best["phase_b_pf"],
        }, f, indent=2)
    print(f"[OK] phase2b_5m_horaire_best_params.json")

    print(f"\n[BEST] {best['horaire_profile']} {best['hours']}")
    print(f"       Robustness={best['robustness']:.4f}")


if __name__ == "__main__":
    main()
