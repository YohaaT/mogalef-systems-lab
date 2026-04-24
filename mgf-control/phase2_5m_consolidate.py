"""Phase 2 (5m) Consolidation

Merges Phase 2a + 2b + 2c + 2d results into final Phase 2 best parameters.
Locks all Contexto filters: Trend Filter + Horaire + Volatility + Weekday
"""

import json


def consolidate():
    print("=" * 70)
    print("PHASE 2 (5m) CONTEXTO CONSOLIDATION")
    print("=" * 70)

    # Load all sub-phases
    with open("phase1_5m_best_params.json") as f:
        phase1 = json.load(f)
    with open("phase2a_5m_trend_filter_best_params.json") as f:
        phase2a = json.load(f)
    with open("phase2b_5m_horaire_best_params.json") as f:
        phase2b = json.load(f)
    with open("phase2c_5m_volatility_best_params.json") as f:
        phase2c = json.load(f)
    with open("phase2d_5m_weekday_best_params.json") as f:
        phase2d = json.load(f)

    print("\n[PHASE 1 - SIGNAL]")
    print(f"  smooth_h={phase1['signal_best']['stpmt_smooth_h']}, "
          f"smooth_b={phase1['signal_best']['stpmt_smooth_b']}, "
          f"dist_h={phase1['signal_best']['stpmt_distance_max_h']}, "
          f"dist_l={phase1['signal_best']['stpmt_distance_max_l']}")
    print(f"  Robustness={phase1['signal_best']['phase1_robustness']:.4f}")

    print("\n[PHASE 2a - TREND FILTER]")
    print(f"  r1={phase2a['trend_r1']}, r2={phase2a['trend_r2']}, r3={phase2a['trend_r3']}")
    print(f"  Robustness={phase2a['robustness']:.4f}")

    print("\n[PHASE 2b - HORAIRE]")
    print(f"  profile={phase2b['horaire_profile']}, hours={phase2b['hours']}")
    print(f"  Robustness={phase2b['robustness']:.4f}")

    print("\n[PHASE 2c - VOLATILITY]")
    print(f"  profile={phase2c['volatility_profile']}, ATR({phase2c['atr_min']}, {phase2c['atr_max']})")
    print(f"  Robustness={phase2c['robustness']:.4f}")

    print("\n[PHASE 2d - WEEKDAY]")
    print(f"  combo={phase2d['weekday_combo']}, blocked={phase2d['blocked_days']}")
    print(f"  Robustness={phase2d['robustness']:.4f}")

    # Consolidated output
    consolidated = {
        "phase": 2,
        "timeframe": "5m",
        "signal_component": {
            "stpmt_smooth_h": phase1["signal_best"]["stpmt_smooth_h"],
            "stpmt_smooth_b": phase1["signal_best"]["stpmt_smooth_b"],
            "stpmt_distance_max_h": phase1["signal_best"]["stpmt_distance_max_h"],
            "stpmt_distance_max_l": phase1["signal_best"]["stpmt_distance_max_l"],
            "robustness": phase1["signal_best"]["phase1_robustness"],
        },
        "contexto_component": {
            "trend_filter": {
                "trend_r1": phase2a["trend_r1"],
                "trend_r2": phase2a["trend_r2"],
                "trend_r3": phase2a["trend_r3"],
                "robustness": phase2a["robustness"],
            },
            "horaire": {
                "profile": phase2b["horaire_profile"],
                "hours": phase2b["hours"],
                "robustness": phase2b["robustness"],
            },
            "volatility": {
                "profile": phase2c["volatility_profile"],
                "atr_min": phase2c["atr_min"],
                "atr_max": phase2c["atr_max"],
                "robustness": phase2c["robustness"],
            },
            "weekday_filter": {
                "combo": phase2d["weekday_combo"],
                "blocked_days": phase2d["blocked_days"],
                "robustness": phase2d["robustness"],
            },
        },
        "phase_a_pf": phase2d["phase_a_pf"],
        "phase_b_pf": phase2d["phase_b_pf"],
        "overall_robustness": phase2d["robustness"],
    }

    with open("phase2_5m_best_params.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    print("\n[OK] phase2_5m_best_params.json written")

    print("\n" + "=" * 70)
    print("PHASE 2 (5m) CONSOLIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    consolidate()
