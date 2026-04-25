"""
CONSOLIDATE COMB_002_IMPULSE — Master Params (Phase 1-4 Combined)
Fusiona los mejores params de cada fase (secuencial) en un master_params.json
por activo y timeframe.

Salida: COMB002_MASTER_PARAMS_SEQUENTIAL.json
  {
    "strategy": "COMB_002_IMPULSE",
    "optimization_date": "2026-04-24",
    "approach": "sequential",
    "assets": ["ES", "MNQ", "YM", "FDAX"],
    "timeframes": ["5m", "10m", "15m"],
    "by_asset_tf": {
      "ES_5m": {...},
      "ES_10m": {...},
      ...
    }
  }

Uso:
  python3 consolidate_COMB002_master_params.py

Nota: Este consolidado es ANTES de Phase 5 Cross-Validation.
Phase 5 reoptimizará cada fase en crudo y comparará el cross-ganador vs este secuencial.
"""

import json
import sys
from pathlib import Path
from datetime import date

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]


def load_phase_params(asset: str, timeframe: str, phase: int) -> dict:
    """Load best_params.json for a specific phase."""
    fname = f"COMB002_phase{phase}_{asset}_{timeframe}_best_params.json"
    p = Path(fname)
    if not p.exists():
        print(f"[WARNING] {fname} not found. Skipping {asset} {timeframe} phase {phase}.")
        return None
    with open(p) as fh:
        return json.load(fh)


def consolidate_asset_tf(asset: str, timeframe: str) -> dict:
    """Consolidate all 4 phases for one asset/timeframe combo."""
    ph1 = load_phase_params(asset, timeframe, 1)
    ph2a = load_phase_params(asset, timeframe, "2a")
    ph2b = load_phase_params(asset, timeframe, "2b")
    ph3 = load_phase_params(asset, timeframe, 3)
    ph4 = load_phase_params(asset, timeframe, 4)

    if not all([ph1, ph2a, ph2b, ph3, ph4]):
        return None

    consolidated = {
        "asset": asset,
        "timeframe": timeframe,
        "strategy": "COMB_002_IMPULSE",
        "approach": "sequential",

        # Phase 1 — Signal
        "phase1": {
            "optimization_id": ph1.get("optimization_id", f"OPT-COMB002-{asset}-{timeframe}-PH1-20260424"),
            "stpmt_smooth_h": ph1["stpmt_smooth_h"],
            "stpmt_smooth_b": ph1["stpmt_smooth_b"],
            "stpmt_distance_max_h": ph1["stpmt_distance_max_h"],
            "stpmt_distance_max_l": ph1["stpmt_distance_max_l"],
            "robustness": ph1["robustness"],
            "phase_a_pf": ph1["phase_a_pf"],
            "phase_b_pf": ph1["phase_b_pf"],
        },

        # Phase 2a — Horaire
        "phase2a": {
            "optimization_id": ph2a.get("optimization_id", f"OPT-COMB002-{asset}-{timeframe}-PH2a-20260424"),
            "horaire_label": ph2a["horaire_label"],
            "horaire_allowed_hours_utc": ph2a["horaire_allowed_hours_utc"],
            "robustness": ph2a["robustness"],
            "phase_a_pf": ph2a["phase_a_pf"],
            "phase_b_pf": ph2a["phase_b_pf"],
        },

        # Phase 2b — Volatility
        "phase2b": {
            "optimization_id": ph2b.get("optimization_id", f"OPT-COMB002-{asset}-{timeframe}-PH2b-20260424"),
            "volatility_label": ph2b["volatility_label"],
            "volatility_atr_min": ph2b["volatility_atr_min"],
            "volatility_atr_max": ph2b["volatility_atr_max"],
            "robustness": ph2b["robustness"],
            "phase_a_pf": ph2b["phase_a_pf"],
            "phase_b_pf": ph2b["phase_b_pf"],
        },

        # Phase 3 — Exits
        "phase3": {
            "optimization_id": ph3.get("optimization_id", f"OPT-COMB002-{asset}-{timeframe}-PH3-20260424"),
            "scalping_target_coef_volat": ph3["scalping_target_coef_volat"],
            "timescan_bars": ph3["timescan_bars"],
            "robustness": ph3["robustness"],
            "phase_a_pf": ph3["phase_a_pf"],
            "phase_b_pf": ph3["phase_b_pf"],
        },

        # Phase 4 — SuperStop
        "phase4": {
            "optimization_id": ph4.get("optimization_id", f"OPT-COMB002-{asset}-{timeframe}-PH4-20260424"),
            "superstop_quality": ph4["superstop_quality"],
            "superstop_coef_volat": ph4["superstop_coef_volat"],
            "robustness": ph4["robustness"],
            "phase_a_pf": ph4["phase_a_pf"],
            "phase_b_pf": ph4["phase_b_pf"],
        },

        # Final robustness (Phase 4 is the ultimate validation)
        "final_robustness": ph4["robustness"],
        "final_phase_a_pf": ph4["phase_a_pf"],
        "final_phase_b_pf": ph4["phase_b_pf"],
        "final_phase_a_trades": ph4["phase_a_trades"],
        "final_phase_b_trades": ph4["phase_b_trades"],
        "robustness_pass": ph4["robustness"] >= 0.80,
        "min_trades_pass": ph4["phase_a_trades"] >= 30,
    }

    return consolidated


def main():
    print(f"\n{'='*80}")
    print(f"COMB_002_IMPULSE — Consolidate Sequential Optimization (Phase 1-4)")
    print(f"{'='*80}\n")

    master = {
        "strategy": "COMB_002_IMPULSE",
        "approach": "sequential",
        "optimization_date": date.today().strftime("%Y-%m-%d"),
        "consolidation_date": date.today().strftime("%Y-%m-%d"),
        "assets": SUPPORTED_ASSETS,
        "timeframes": SUPPORTED_TIMEFRAMES,
        "by_asset_tf": {},
        "summary": {
            "total_combos": len(SUPPORTED_ASSETS) * len(SUPPORTED_TIMEFRAMES),
            "completed": 0,
            "passed_robustness": 0,
            "passed_trades": 0,
            "passed_both": 0,
            "warnings": [],
        }
    }

    for asset in SUPPORTED_ASSETS:
        for tf in SUPPORTED_TIMEFRAMES:
            key = f"{asset}_{tf}"
            consolidated = consolidate_asset_tf(asset, tf)

            if consolidated is None:
                print(f"[SKIP] {key} — missing phase data")
                master["summary"]["warnings"].append(f"Missing phase data for {key}")
                continue

            master["by_asset_tf"][key] = consolidated
            master["summary"]["completed"] += 1

            if consolidated["robustness_pass"]:
                master["summary"]["passed_robustness"] += 1
            if consolidated["min_trades_pass"]:
                master["summary"]["passed_trades"] += 1
            if consolidated["robustness_pass"] and consolidated["min_trades_pass"]:
                master["summary"]["passed_both"] += 1

            status = "✓ PASS" if (consolidated["robustness_pass"] and consolidated["min_trades_pass"]) else "✗ WARN"
            print(f"[{status}] {key:12} | Rob={consolidated['final_robustness']:7.4f} | "
                  f"PF_B={consolidated['final_phase_b_pf']:.4f} | T_A={consolidated['final_phase_a_trades']:3d}")

    output_file = "COMB002_MASTER_PARAMS_SEQUENTIAL.json"
    with open(output_file, "w") as fh:
        json.dump(master, fh, indent=2)

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"  Total combos:        {master['summary']['total_combos']}")
    print(f"  Completed:           {master['summary']['completed']}")
    print(f"  Passed robustness:   {master['summary']['passed_robustness']}")
    print(f"  Passed min trades:   {master['summary']['passed_trades']}")
    print(f"  Passed both:         {master['summary']['passed_both']}")
    print(f"  Warnings:            {len(master['summary']['warnings'])}")
    print(f"\n[OK] {output_file}")
    print(f"{'='*80}\n")

    print("NEXT STEP: Phase 5 Cross-Validation (Independent optimization of each phase,")
    print("then grid of top-3 combinations). Use phase5_COMB002_cross_validation_pool_runner.py")


if __name__ == "__main__":
    main()
