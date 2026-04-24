"""Phase 2 Consolidation: Combine Phase 2a (Trend), 2b (Horaire), 2c (Volatility)

Reads best params from:
- phase2a_trend_best_params.json (Trend Filter: r1, r2, r3)
- phase2b_horaire_best_params.json (Horaire: UTC hours)
- phase2c_volatility_best_params.json (Volatility: atr_min, atr_max)

Outputs:
- phase2_best_params.json (consolidated Phase 2 result)
- phase2_summary.json (Phase 1 + Phase 2 combined, ready for Phase 3)
"""

import json
from pathlib import Path


def load_json(filepath: str) -> dict:
    """Load JSON file, raise if not found."""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath) as f:
        return json.load(f)


def main():
    print("\n" + "="*80)
    print("PHASE 2 CONSOLIDATION - COMBINING TREND + HORAIRE + VOLATILITY")
    print("="*80)

    # Load Phase 1 best (fixed)
    print("\n[1] Loading Phase 1 best (Signal)...")
    try:
        phase1 = load_json("phase1_best_params.json")
        print(f"    smooth_h={phase1['stpmt_smooth_h']}, smooth_b={phase1['stpmt_smooth_b']}, "
              f"dist={phase1['stpmt_distance_max_h']}/{phase1['stpmt_distance_max_l']}")
        print(f"    Robustness: {phase1['robustness']:.4f}")
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    # Load Phase 2a best (Trend Filter)
    print("\n[2] Loading Phase 2a best (Trend Filter)...")
    try:
        phase2a = load_json("phase2a_trend_best_params.json")
        print(f"    trend_r1={phase2a['trend_r1']}, trend_r2={phase2a['trend_r2']}, trend_r3={phase2a['trend_r3']}")
        print(f"    Robustness: {phase2a['robustness']:.4f}")
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    # Load Phase 2b best (Horaire)
    print("\n[3] Loading Phase 2b best (Horaire)...")
    try:
        phase2b = load_json("phase2b_horaire_best_params.json")
        print(f"    hours={phase2b['hours']}")
        print(f"    Robustness: {phase2b['robustness']:.4f}")
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    # Load Phase 2c best (Volatility)
    print("\n[4] Loading Phase 2c best (Volatility)...")
    try:
        phase2c = load_json("phase2c_volatility_best_params.json")
        print(f"    atr_min={phase2c['atr_min']}, atr_max={phase2c['atr_max']}")
        print(f"    Robustness: {phase2c['robustness']:.4f}")
    except FileNotFoundError as e:
        print(f"    [ERROR] {e}")
        return 1

    # Consolidate Phase 2
    print("\n[5] Consolidating Phase 2...")
    phase2_consolidated = {
        "phase": 2,
        "signal_from_phase1": {
            "stpmt_smooth_h": phase1["stpmt_smooth_h"],
            "stpmt_smooth_b": phase1["stpmt_smooth_b"],
            "stpmt_distance_max_h": phase1["stpmt_distance_max_h"],
            "stpmt_distance_max_l": phase1["stpmt_distance_max_l"],
            "phase1_robustness": phase1["robustness"],
        },
        "trend_filter_best": {
            "trend_r1": phase2a["trend_r1"],
            "trend_r2": phase2a["trend_r2"],
            "trend_r3": phase2a["trend_r3"],
            "phase2a_robustness": phase2a["robustness"],
        },
        "horaire_best": {
            "horaire_allowed_hours_utc": phase2b["hours"],
            "phase2b_robustness": phase2b["robustness"],
        },
        "volatility_best": {
            "volatility_atr_min": phase2c["atr_min"],
            "volatility_atr_max": phase2c["atr_max"],
            "phase2c_robustness": phase2c["robustness"],
        },
        "overall_phase2_robustness": round(
            min(phase2a["robustness"], phase2b["robustness"], phase2c["robustness"]), 4
        ),
    }

    # Save Phase 2 consolidated
    phase2_file = "phase2_best_params.json"
    with open(phase2_file, "w") as f:
        json.dump(phase2_consolidated, f, indent=2)
    print(f"    [OK] {phase2_file}")

    # Create summary for Phase 3 (all locked params from 1+2)
    print("\n[6] Creating Phase 3 summary (all locked params)...")
    phase3_summary = {
        "phase": "3 (prepared from Phase 1+2)",
        "locked_signal": {
            "stpmt_smooth_h": phase1["stpmt_smooth_h"],
            "stpmt_smooth_b": phase1["stpmt_smooth_b"],
            "stpmt_distance_max_h": phase1["stpmt_distance_max_h"],
            "stpmt_distance_max_l": phase1["stpmt_distance_max_l"],
        },
        "locked_contexto": {
            "trend_r1": phase2a["trend_r1"],
            "trend_r2": phase2a["trend_r2"],
            "trend_r3": phase2a["trend_r3"],
            "horaire_allowed_hours_utc": phase2b["hours"],
            "volatility_atr_min": phase2c["atr_min"],
            "volatility_atr_max": phase2c["atr_max"],
        },
        "to_optimize": {
            "target_atr_multiplier": "[5.0, 10.0, 15.0, 20.0]",
            "timescan_bars": "[20, 30, 40, 50]",
            "note": "Phase 3 will optimize Exits (4 combinations of ATR mult × TimeStop bars)"
        }
    }

    phase3_file = "phase3_summary.json"
    with open(phase3_file, "w") as f:
        json.dump(phase3_summary, f, indent=2)
    print(f"    [OK] {phase3_file}")

    # Print summary
    print("\n" + "="*80)
    print("PHASE 2 COMPLETE - SUMMARY")
    print("="*80)
    print(f"Signal       (Phase 1): smooth_h={phase1['stpmt_smooth_h']}, smooth_b={phase1['stpmt_smooth_b']}, dist=50/50")
    print(f"             Robustness: {phase1['robustness']:.4f}")
    print()
    print(f"Trend Filter (Phase 2a): r1={phase2a['trend_r1']}, r2={phase2a['trend_r2']}, r3={phase2a['trend_r3']}")
    print(f"             Robustness: {phase2a['robustness']:.4f}")
    print()
    print(f"Horaire      (Phase 2b): hours={phase2b['hours']}")
    print(f"             Robustness: {phase2b['robustness']:.4f}")
    print()
    print(f"Volatility   (Phase 2c): atr_min={phase2c['atr_min']}, atr_max={phase2c['atr_max']}")
    print(f"             Robustness: {phase2c['robustness']:.4f}")
    print()
    print(f"Overall Phase 2 Robustness (min of 2a/2b/2c): {phase2_consolidated['overall_phase2_robustness']:.4f}")
    print("="*80)

    return 0


if __name__ == "__main__":
    exit(main())
