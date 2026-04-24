"""COMB_001_TREND (5m) — Final Consolidation (All Phases 1-4)

Merges Phase 1 + Phase 2 + Phase 3 + Phase 4 results into single JSON
with all optimized parameters ready for NT8 port and live trading.
"""

import json


def consolidate_all():
    print("=" * 80)
    print("COMB_001_TREND (5m) — FINAL CONSOLIDATION (PHASES 1-4)")
    print("=" * 80)

    # Load all phases
    with open("phase1_5m_best_params.json") as f:
        phase1 = json.load(f)
    with open("phase2_5m_best_params.json") as f:
        phase2 = json.load(f)
    with open("phase3_5m_exits_best_params.json") as f:
        phase3 = json.load(f)
    with open("phase4_5m_best_params.json") as f:
        phase4 = json.load(f)

    print("\n[PHASE 1 - SIGNAL]")
    sig = phase1["signal_best"]
    print(f"  smooth_h={sig['stpmt_smooth_h']}, smooth_b={sig['stpmt_smooth_b']}, "
          f"dist_h={sig['stpmt_distance_max_h']}, dist_l={sig['stpmt_distance_max_l']}")
    print(f"  Robustness: {sig['phase1_robustness']:.4f}")

    print("\n[PHASE 2 - CONTEXTO]")
    ctx = phase2["contexto_component"]
    print(f"  Trend Filter: r1={ctx['trend_filter']['trend_r1']}, "
          f"r2={ctx['trend_filter']['trend_r2']}, r3={ctx['trend_filter']['trend_r3']}")
    print(f"    └─ Robustness: {ctx['trend_filter']['robustness']:.4f}")
    print(f"  Horaire: {ctx['horaire']['profile']} → {ctx['horaire']['hours']}")
    print(f"    └─ Robustness: {ctx['horaire']['robustness']:.4f}")
    print(f"  Volatility: {ctx['volatility']['profile']} → "
          f"ATR({ctx['volatility']['atr_min']}, {ctx['volatility']['atr_max']})")
    print(f"    └─ Robustness: {ctx['volatility']['robustness']:.4f}")
    print(f"  Weekday: {ctx['weekday_filter']['combo']} → {ctx['weekday_filter']['blocked_days']}")
    print(f"    └─ Robustness: {ctx['weekday_filter']['robustness']:.4f}")

    print("\n[PHASE 3 - EXITS]")
    exit_p = phase3
    print(f"  target_atr_multiplier: {exit_p['target_atr_multiplier']}")
    print(f"  timescan_bars: {exit_p['timescan_bars']}")
    print(f"  Robustness: {exit_p['robustness']:.4f}")

    print("\n[PHASE 4 - STOPS]")
    stop_p = phase4["stops_best"]
    print(f"  quality={stop_p['stop_intelligent_quality']}, "
          f"recent={stop_p['stop_intelligent_recent_volat']}, "
          f"ref_vol={stop_p['stop_intelligent_ref_volat']}, "
          f"coef={stop_p['stop_intelligent_coef_volat']:.1f}")
    print(f"  Robustness: {stop_p['phase4_robustness']:.4f}")

    # Build final consolidated JSON
    final = {
        "strategy": "COMB_001_TREND",
        "version": "5m_optimized",
        "timeframe": "5 minutes",
        "asset": "YM (E-mini Dow Jones)",
        "validation": {
            "phase_a_bars": 81438,
            "phase_b_bars": 54544,
            "phase_a_pf": phase4["phase_a_pf"],
            "phase_b_pf": phase4["phase_b_pf"],
            "final_robustness": phase4["phase_b_pf"] / phase4["phase_a_pf"] if phase4["phase_a_pf"] > 0 else 0.0,
        },
        "parameters": {
            "signal": {
                "stpmt_smooth_h": sig["stpmt_smooth_h"],
                "stpmt_smooth_b": sig["stpmt_smooth_b"],
                "stpmt_distance_max_h": sig["stpmt_distance_max_h"],
                "stpmt_distance_max_l": sig["stpmt_distance_max_l"],
            },
            "contexto": {
                "trend_filter": {
                    "trend_r1": ctx["trend_filter"]["trend_r1"],
                    "trend_r2": ctx["trend_filter"]["trend_r2"],
                    "trend_r3": ctx["trend_filter"]["trend_r3"],
                },
                "horaire": {
                    "allowed_hours_utc": ctx["horaire"]["hours"],
                },
                "volatility": {
                    "atr_period": 14,
                    "atr_min": ctx["volatility"]["atr_min"],
                    "atr_max": ctx["volatility"]["atr_max"],
                },
                "weekday_filter": {
                    "blocked_weekdays": ctx["weekday_filter"]["blocked_days"],
                },
            },
            "exits": {
                "target_atr_multiplier": exit_p["target_atr_multiplier"],
                "timescan_bars": exit_p["timescan_bars"],
            },
            "stops": {
                "stop_intelligent_quality": stop_p["stop_intelligent_quality"],
                "stop_intelligent_recent_volat": stop_p["stop_intelligent_recent_volat"],
                "stop_intelligent_ref_volat": stop_p["stop_intelligent_ref_volat"],
                "stop_intelligent_coef_volat": stop_p["stop_intelligent_coef_volat"],
            },
        },
        "robustness_per_phase": {
            "phase_1_signal": sig["phase1_robustness"],
            "phase_2a_trend_filter": ctx["trend_filter"]["robustness"],
            "phase_2b_horaire": ctx["horaire"]["robustness"],
            "phase_2c_volatility": ctx["volatility"]["robustness"],
            "phase_2d_weekday": ctx["weekday_filter"]["robustness"],
            "phase_3_exits": exit_p["robustness"],
            "phase_4_stops": stop_p["phase4_robustness"],
        },
        "mogalef_alignment": {
            "independent_optimization": "Each phase locks previous (no cumulative testing)",
            "signal_type": "STPMT Divergence",
            "trend_filter": "Mogalef Trend Filter V2 (R1/R2/R3)",
            "horaire_coverage": "9h-17h + 20h-22h CET (tested via profiles)",
            "volatility_filter": "ATR bands (Mogalef recommended)",
            "weekday_filter": "No Monday/Tuesday (from PDF)",
            "profit_target": "10 ATR (10.0 multiplier)",
            "time_stop": "30 bars (TimeStop)",
            "trailing_stop": "Stop Intelligent (volatility-adaptive)",
            "validation": "Walk-forward 60/40 split (Phase A train, Phase B unseen)",
        },
    }

    with open("COMB_001_TREND_5m_FINAL_PARAMS.json", "w") as f:
        json.dump(final, f, indent=2)

    print("\n" + "=" * 80)
    print("[OK] COMB_001_TREND_5m_FINAL_PARAMS.json written")
    print("=" * 80)
    print(f"\nFinal Robustness: {final['validation']['final_robustness']:.4f}")
    print(f"Phase A PF: {final['validation']['phase_a_pf']:.4f}")
    print(f"Phase B PF: {final['validation']['phase_b_pf']:.4f}")
    print("\nReady for:")
    print("  1. NT8 C# port (COMB001_TREND.cs)")
    print("  2. Live strategy analyzer backtest")
    print("  3. Forward testing on unseen data")


if __name__ == "__main__":
    consolidate_all()
