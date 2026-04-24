"""Phase 3 Consolidation - Merge TANK + VPS results and select best."""

import json
from pathlib import Path

def consolidate_phase3():
    """Load Phase 3 best params from both servers, consolidate."""

    print("=" * 80)
    print("PHASE 3 CONSOLIDATION")
    print("=" * 80)

    # Try to load from TANK
    try:
        with open("phase3_exits_best_params.json") as f:
            tank_result = json.load(f)
        print(f"\n[TANK] Loaded Phase 3 result:")
        print(f"  target_atr={tank_result['target_atr']}, timescan={tank_result['timescan_bars']}")
        print(f"  Robustness={tank_result['robustness']:.4f}")
    except FileNotFoundError:
        tank_result = None
        print("\n[TANK] No Phase 3 results found")

    # Try to load from VPS
    try:
        with open("bo_phase3_exits_best_params.json") as f:
            vps_result = json.load(f)
        print(f"\n[VPS] Loaded Phase 3 result:")
        print(f"  target_atr={vps_result['target_atr']}, timescan={vps_result['timescan_bars']}")
        print(f"  Robustness={vps_result['robustness']:.4f}")
    except FileNotFoundError:
        vps_result = None
        print("\n[VPS] No Phase 3 results found")

    # Select best (by robustness)
    if tank_result and vps_result:
        if tank_result['robustness'] >= vps_result['robustness']:
            best = tank_result
            source = "TANK"
        else:
            best = vps_result
            source = "VPS"
    elif tank_result:
        best = tank_result
        source = "TANK"
    elif vps_result:
        best = vps_result
        source = "VPS"
    else:
        raise FileNotFoundError("No Phase 3 results found from either server!")

    print(f"\n[BEST] Selected from {source}:")
    print(f"  target_atr={best['target_atr']}")
    print(f"  timescan_bars={best['timescan_bars']}")
    print(f"  Robustness={best['robustness']:.4f}")

    # Write consolidated result
    consolidated = {
        "phase": 3,
        "exits_best": {
            "target_atr_multiplier": best["target_atr"],
            "timescan_bars": best["timescan_bars"],
            "phase3_robustness": best["robustness"],
        },
        "phase_a_pf": best["phase_a_pf"],
        "phase_b_pf": best["phase_b_pf"],
    }

    with open("phase3_best_params.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    print(f"\n[OK] phase3_best_params.json")

    # Create Phase 4 summary (next phase - Stops)
    phase4_summary = {
        "phase": "4 (prepared from Phase 1+2+3)",
        "locked_signal": {
            "stpmt_smooth_h": 3,
            "stpmt_smooth_b": 2,
            "stpmt_distance_max_h": 50,
            "stpmt_distance_max_l": 50,
        },
        "locked_contexto": {
            "trend_r1": 3,
            "trend_r2": 50,
            "trend_r3": 200,
            "horaire_allowed_hours_utc": [12, 13, 14, 15],
            "volatility_atr_min": 20.0,
            "volatility_atr_max": 200.0,
        },
        "locked_exits": {
            "target_atr_multiplier": best["target_atr"],
            "timescan_bars": best["timescan_bars"],
        },
        "to_optimize": {
            "stop_intelligent_quality": "[1, 2, 3]",
            "stop_intelligent_recent_volat": "[1, 2, 3]",
            "stop_intelligent_ref_volat": "[10, 20, 30]",
            "stop_intelligent_coef_volat": "[3.0, 5.0, 7.0]",
            "note": "Phase 4 will optimize Stop Inteligente (4x3x3x3 = 108 combos)"
        }
    }

    with open("phase4_summary.json", "w") as f:
        json.dump(phase4_summary, f, indent=2)
    print(f"[OK] phase4_summary.json (ready for Phase 4)")

    print("\n" + "=" * 80)
    print("PHASE 3 CONSOLIDATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    consolidate_phase3()
