"""Phase 2c Optimization: Volatility (ATR bounds) - Sequential

Tests 5 predefined ATR volatility bands sequentially.

Locked from Phase 1:
- stpmt_smooth_h: 3, stpmt_smooth_b: 2, distance_max: 50/50

Locked from Phase 2a:
- trend_r1/r2/r3: loaded from phase2a best params

Locked from Phase 2b:
- horaire_allowed_hours_utc: loaded from phase2b best params

Phase 2c: Test 5 volatility bands
1. (0, 500)      (no filter)
2. (10, 500)     (min floor)
3. (0, 200)      (max ceiling)
4. (10, 250)     (tight band)
5. (20, 200)     (very selective)
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

# Volatility profiles (5 options)
VOLATILITY_PROFILES = {
    1: {
        "name": "no_filter",
        "atr_min": 0.0,
        "atr_max": 500.0,
        "desc": "No volatility filter (0-500)"
    },
    2: {
        "name": "min_floor",
        "atr_min": 10.0,
        "atr_max": 500.0,
        "desc": "Minimum floor (10-500)"
    },
    3: {
        "name": "max_ceiling",
        "atr_min": 0.0,
        "atr_max": 200.0,
        "desc": "Maximum ceiling (0-200)"
    },
    4: {
        "name": "tight_band",
        "atr_min": 10.0,
        "atr_max": 250.0,
        "desc": "Tight band (10-250)"
    },
    5: {
        "name": "very_selective",
        "atr_min": 20.0,
        "atr_max": 200.0,
        "desc": "Very selective (20-200)"
    },
}

# Load Phase 2a/2b best (will read from file)
PHASE2A_BEST = None
PHASE2B_BEST = None

# Defaults (locked from Phase 2c)
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


def load_phase2b_best():
    """Load Phase 2b best params from JSON."""
    global PHASE2B_BEST

    candidate = "phase2b_horaire_best_params.json"
    if Path(candidate).exists():
        with open(candidate) as f:
            PHASE2B_BEST = json.load(f)
        print(f"[OK] Loaded Phase 2b best from {candidate}")
        return

    raise FileNotFoundError("No Phase 2b best params found. Run phase2b first!")


def run_volatility_tests(rows_a, rows_b):
    """Run 5 volatility tests sequentially."""
    print(f"\n{'='*80}")
    print(f"PHASE 2c OPTIMIZATION - VOLATILITY BANDS [SEQUENTIAL]")
    print(f"{'='*80}")
    print(f"Phase 1 Signal  : LOCKED (smooth_h=3, smooth_b=2, dist=50/50)")
    print(f"Phase 2a Trend  : LOCKED (r1={PHASE2A_BEST['trend_r1']}, r2={PHASE2A_BEST['trend_r2']}, r3={PHASE2A_BEST['trend_r3']})")
    print(f"Phase 2b Horaire: LOCKED (hours={PHASE2B_BEST['hours']})")
    print(f"Phase 2c Tests  : 5 Volatility bands (sequential)\n")

    results = []
    best_overall = None
    best_robustness = 0.0

    for profile_id in range(1, 6):
        profile = VOLATILITY_PROFILES[profile_id]
        atr_min = profile["atr_min"]
        atr_max = profile["atr_max"]

        print(f"\n[{profile_id}/5] {profile['name']:20} -> {profile['desc']}")
        print(f"    ATR Range: {atr_min}-{atr_max}")

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
            # Phase 2b (LOCKED)
            horaire_allowed_hours_utc=json.loads(PHASE2B_BEST["hours"]),
            # Phase 2c (VARIED)
            volatility_atr_min=atr_min,
            volatility_atr_max=atr_max,
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
            "atr_min":         atr_min,
            "atr_max":         atr_max,
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
    log_file = "phase2c_volatility_optimization_log.csv"
    with open(log_file, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] {log_file}")

    # Export best params JSON
    best_dict = {
        "profile_id":    best_overall["profile_id"],
        "profile_name":  best_overall["profile_name"],
        "atr_min":       best_overall["atr_min"],
        "atr_max":       best_overall["atr_max"],
        "robustness":    best_overall["robustness"],
        "phase_a_pf":    best_overall["phase_a_pf"],
        "phase_b_pf":    best_overall["phase_b_pf"],
    }
    best_file = "phase2c_volatility_best_params.json"
    with open(best_file, "w") as f:
        json.dump(best_dict, f, indent=2)
    print(f"[OK] {best_file}")

    print(f"\n[BEST] {best_overall['profile_name']:20} -> Robustness={best_overall['robustness']:.4f}")

    return results, best_dict


def main():
    print("Loading Phase 2a best params...")
    load_phase2a_best()
    print(f"Trend params: r1={PHASE2A_BEST['trend_r1']}, r2={PHASE2A_BEST['trend_r2']}, r3={PHASE2A_BEST['trend_r3']}")

    print("\nLoading Phase 2b best params...")
    load_phase2b_best()
    print(f"Horaire params: hours={PHASE2B_BEST['hours']}")

    print("\nLoading Phase A and Phase B data...")
    rows_a = load_ohlc_csv("YM_phase_A_clean.csv")
    rows_b = load_ohlc_csv("YM_phase_B_clean.csv")
    print(f"Phase A: {len(rows_a)} rows")
    print(f"Phase B: {len(rows_b)} rows")

    run_volatility_tests(rows_a, rows_b)


if __name__ == "__main__":
    main()
