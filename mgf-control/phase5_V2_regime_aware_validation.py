"""
COMB_002_IMPULSE V2 — Phase 5: Regime-Aware Cross-Validation

Para cada régimen, toma el TOP-1 de Phase 4 (best params por régimen) y lo
valida en TODAS las ventanas de TODA la data (no solo las del régimen).

Razón: en live, el régimen puede cambiar MIENTRAS hay posición abierta. Estos
params deberían al menos NO perder catastróficamente en otros regímenes.

Criterio de ganador final por régimen:
  - OK            : passes_filters V2 en su régimen nativo + min_PF ≥ 0.8 en los otros
  - DEGRADED      : passes en nativo pero falla cross-regime
  - REJECTED      : falla en nativo

Input : COMB002_V2_phase4_{ASSET}_{TF}_top_params_by_regime.json
        {ASSET}_full_{TF}.csv
Output: COMB002_V2_phase5_{ASSET}_{TF}_final_by_regime.json

Uso:
  python3 phase5_V2_regime_aware_validation.py --asset ES --timeframe 5m
"""

import argparse
import json
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseParams, load_ohlc_csv
from COMB_002_IMPULSE_V2_walkforward import (
    split_walkforward, score_walkforward, score_across_windows,
    split_all_windows, filter_rows_by_regime, REGIME_LABELS,
    V2_N_WINDOWS, V2_N_TRAIN_WINDOWS, RegimeThresholds,
    passes_v2_filters,
)

CROSS_REGIME_MIN_PF = 0.8  # En régimen no-nativo, no debe caer bajo este PF

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]


def build_params(p: dict) -> Comb002ImpulseParams:
    return Comb002ImpulseParams(
        stpmt_smooth_h=p["smooth_h"], stpmt_smooth_b=p["smooth_b"],
        stpmt_distance_max_h=p["dist_max_h"], stpmt_distance_max_l=p["dist_max_l"],
        horaire_allowed_hours_utc=p["horaire_hours"],
        volatility_atr_min=p["atr_min"], volatility_atr_max=p["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=p["scalp_coef"],
        timescan_bars=p["timescan"],
        superstop_quality=p["superstop_quality"],
        superstop_coef_volat=p["superstop_coef_volat"],
    )


def main():
    parser = argparse.ArgumentParser(description="COMB_002 V2 Phase 5 — Regime-Aware Validation")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None)
    parser.add_argument("--phase4-json", type=Path, default=None)
    parser.add_argument("--regime-window", type=int, default=500)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    p4_file = args.phase4_json or Path(f"COMB002_V2_phase4_{args.asset}_{args.timeframe}_top_params_by_regime.json")

    if not data_file.exists() or not p4_file.exists():
        print(f"[ERROR] Missing file")
        sys.exit(1)

    with open(p4_file) as fh:
        p4 = json.load(fh)

    rows = load_ohlc_csv(str(data_file))
    th_data = p4.get("atr_thresholds", {})
    thresholds = RegimeThresholds(atr_low=th_data.get("low", 0), atr_high=th_data.get("high", 0))

    all_windows = split_all_windows(rows, V2_N_WINDOWS)

    print(f"\n=== V2 Phase 5 {args.asset} {args.timeframe} ===")

    final_by_regime = {}
    for regime in REGIME_LABELS:
        top = p4["by_regime"].get(regime, {}).get("top", [])
        if not top:
            final_by_regime[regime] = {"status": "NO_PARAMS", "reason": "Phase 4 produced nothing"}
            print(f"  [{regime}] NO_PARAMS")
            continue

        best = top[0]
        params = build_params(best)

        # Score en su propio régimen (folds nativos)
        regime_rows = filter_rows_by_regime(rows, thresholds, regime,
                                            window_size=args.regime_window)
        try:
            native_folds = split_walkforward(regime_rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)
            native_score = score_walkforward(params, native_folds)
        except ValueError:
            native_score = None

        # Score en TODAS las ventanas completas (cross-regime sanity)
        cross_score = score_across_windows(params, all_windows)

        # Decisión final
        if native_score is None or not native_score.passes_filters:
            status = "REJECTED"
            reason = native_score.reject_reason if native_score else "insufficient native data"
        elif cross_score.min_pf < CROSS_REGIME_MIN_PF:
            status = "DEGRADED"
            reason = f"cross-regime min_pf={cross_score.min_pf:.3f} < {CROSS_REGIME_MIN_PF}"
        else:
            status = "OK"
            reason = "passes native + cross-regime filters"

        final_by_regime[regime] = {
            "status": status,
            "reason": reason,
            "params": best,
            "native_score": {
                "pfs": native_score.pfs if native_score else [],
                "min_pf": native_score.min_pf if native_score else 0,
                "cv": native_score.cv if native_score else 0,
                "min_trades": native_score.min_trades if native_score else 0,
                "passes_filters": native_score.passes_filters if native_score else False,
            },
            "cross_regime_score": {
                "pfs": cross_score.pfs,
                "min_pf": cross_score.min_pf,
                "max_pf": cross_score.max_pf,
                "cv": cross_score.cv,
                "trades": cross_score.trades,
            },
        }
        icon = {"OK": "✅", "DEGRADED": "⚠️", "REJECTED": "❌", "NO_PARAMS": "❌"}.get(status, "?")
        print(f"  [{regime}] {icon} {status} | native_min_pf={native_score.min_pf if native_score else 0:.3f} "
              f"cross_min_pf={cross_score.min_pf:.3f} | {reason}")

    out_json = args.out_dir / f"COMB002_V2_phase5_{args.asset}_{args.timeframe}_final_by_regime.json"
    with open(out_json, "w") as fh:
        json.dump({
            "asset": args.asset, "timeframe": args.timeframe,
            "phase": "V2_phase5_regime_aware_validation",
            "atr_thresholds": th_data,
            "cross_regime_min_pf_threshold": CROSS_REGIME_MIN_PF,
            "final_by_regime": final_by_regime,
        }, fh, indent=2)
    print(f"\n[OK] {out_json}")


if __name__ == "__main__":
    main()
