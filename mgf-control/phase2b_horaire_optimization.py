"""Phase 2b Optimization: Horaire (UTC allowed hours) - Sequential

Tests 6 predefined UTC hour profiles sequentially.

Locked from Phase 1:
- stpmt_smooth_h: 3, stpmt_smooth_b: 2, distance_max: 50/50

Locked from Phase 2a:
- trend_r1/r2/r3: loaded from phase2a best params

Phase 2b: Test 6 horaire profiles
1. [0-23]     (no filter)
2. [9-15]     (US regular - default)
3. [9-17]     (US extended)
4. [8-16]     (pre-market)
5. [9-12]     (morning)
6. [12-15]    (afternoon)
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

# Horaire profiles (6 options)
HORAIRE_PROFILES = {
    1: {
        "name": "no_filter",
        "hours": list(range(0, 24)),
        "desc": "Trade all hours [0-23]"
    },
    2: {
        "name": "us_regular",
        "hours": list(range(9, 16)),
        "desc": "US regular session [9-15] UTC"
    },
    3: {
        "name": "us_extended",
        "hours": list(range(9, 18)),
        "desc": "US extended [9-17] UTC"
    },
    4: {
        "name": "pre_market",
        "hours": list(range(8, 17)),
        "desc": "Pre-market [8-16] UTC"
    },
    5: {
        "name": "morning",
        "hours": list(range(9, 13)),
        "desc": "Morning only [9-12] UTC"
    },
    6: {
        "name": "afternoon",
        "hours": list(range(12, 16)),
        "desc": "Afternoon only [12-15] UTC"
    },
}

# Load Phase 2a best (will read from file)
PHASE2A_BEST = None

# Defaults (locked from Phase 2a)
DEFAULT_VOLATILITY_MIN = 0.0
DEFAULT_VOLATILITY_MAX = 500.0
DEFAULT_TARGET_ATR_MULT = 10.0
DEFAULT_TIMESCAN_BARS = 30
DEFAULT_STOP_QUAL = 2
DEFAULT_STOP_RECENT = 2
DEFAULT_STOP_REF = 20
DEFAULT_STOP_COEF = 5.0


def load_phase2a_best():
    """Load Phase 2a best params from JSON."""
    global PHASE2A_BEST

    # Try to find the best params file
    # Priority: consolidated > block_2 > block_1
    candidates = [
        "phase2a_trend_best_params.json",  # consolidated
        "phase2a_trend_optimization_block_2_best_params.json",
        "phase2a_trend_optimization_block_1_best_params.json",
    ]

    for candidate in candidates:
        if Path(candidate).exists():
            with open(candidate) as f:
                PHASE2A_BEST = json.load(f)
            print(f"[OK] Loaded Phase 2a best from {candidate}")
            return

    raise FileNotFoundError("No Phase 2a best params found. Run phase2a first!")


def run_horaire_tests(rows_a, rows_b):
    """Run 6 horaire tests sequentially."""
    print(f"\n{'='*80}")
    print(f"PHASE 2b OPTIMIZATION - HORAIRE PROFILES [SEQUENTIAL]")
    print(f"{'='*80}")
    print(f"Phase 1 Signal  : LOCKED (smooth_h=3, smooth_b=2, dist=50/50)")
    print(f"Phase 2a Trend  : LOCKED (r1={PHASE2A_BEST['trend_r1']}, r2={PHASE2A_BEST['trend_r2']}, r3={PHASE2A_BEST['trend_r3']})")
    print(f"Phase 2b Tests  : 6 Horaire profiles (sequential)\n")

    results = []
    best_overall = None
    best_robustness = 0.0

    for profile_id in range(1, 7):
        profile = HORAIRE_PROFILES[profile_id]
        hours = profile["hours"]

        print(f"\n[{profile_id}/6] {profile['name']:20} -> {profile['desc']}")
        print(f"    Hours: {hours}")

        params = Comb001TrendParams(
            # Phase 1 (LOCKED)
            stpmt_smooth_h=PHASE1_BEST["stpmt_smooth_h"],
            stpmt_smooth_b=PHASE1_BEST["stpmt_smooth_b"],
            stpmt_distance_max_h=PHASE1_BEST["stpmt_distance_max_h"],
            stpmt_distance_max_l=PHASE1_BEST["stpmt_distance_max_l"],
            # Phase 2a (LOCKED)
            trend_r1=PHASE2A_BEST["trend_r1"],
            trend_r2=PHASE2A_BEST["trend_r2"],
            trend_r3=PHASE2A_BEST["trend_r3"],
            # Phase 2b (VARIED)
            horaire_allowed_hours_utc=hours,
            # Phase 2b Defaults (Volatility)
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

        result = {
            "profile_id":      profile_id,
            "profile_name":    profile["name"],
            "hours":           str(hours),
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
    log_file = "phase2b_horaire_optimization_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] {log_file}")

    # Export best params JSON
    best_dict = {
        "profile_id":    best_overall["profile_id"],
        "profile_name":  best_overall["profile_name"],
        "hours":         best_overall["hours"],
        "robustness":    best_overall["robustness"],
        "phase_a_pf":    best_overall["phase_a_pf"],
        "phase_b_pf":    best_overall["phase_b_pf"],
    }
    best_file = "phase2b_horaire_best_params.json"
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    print(f"\n[BEST] {best_overall['profile_name']:20} -> Robustness={best_overall['robustness']:.4f}")

    return results, best_dict


def main():
    print("Loading Phase 2a best params...")
    load_phase2a_best()
    print(f"Trend params: r1={PHASE2A_BEST['trend_r1']}, r2={PHASE2A_BEST['trend_r2']}, r3={PHASE2A_BEST['trend_r3']}")

    print("\nLoading Phase A and Phase B data...")
    rows_a = load_ohlc_csv("YM_phase_A_clean.csv")
    rows_b = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(rows_a)} rows")
    print(f"Phase B: {len(rows_b)} rows")

    run_horaire_tests(rows_a, rows_b)


if __name__ == "__main__":
    main()
