"""
COMB_002_IMPULSE V2 — Phase 4: Stops (Walk-Forward, POR RÉGIMEN)

Optimiza superstop_quality + superstop_coef_volat dentro de cada régimen.
Itera sobre los top-3 POR RÉGIMEN de Phase 3.

Input : COMB002_V2_phase3_{ASSET}_{TF}_top_params_by_regime.json
        {ASSET}_full_{TF}.csv
Output: COMB002_V2_phase4_{ASSET}_{TF}_top_params_by_regime.json

Uso:
  python3 phase4_V2_stops_walkforward.py --asset ES --timeframe 5m
"""

import argparse
import json
import sys
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseParams, load_ohlc_csv
from COMB_002_IMPULSE_V2_walkforward import (
    split_walkforward, score_walkforward,
    filter_rows_by_regime, REGIME_LABELS,
    V2_N_WINDOWS, V2_N_TRAIN_WINDOWS, RegimeThresholds,
)

SUPERSTOP_QUALITY_RANGE = [1, 2, 3, 4]
SUPERSTOP_COEF_RANGE    = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

_FOLDS = None
_BASE = None


def _init_worker(folds, base):
    global _FOLDS, _BASE
    _FOLDS = folds
    _BASE = base


def _eval_combo(combo):
    base_idx, ss_q, ss_c = combo
    b = _BASE[base_idx]

    params = Comb002ImpulseParams(
        stpmt_smooth_h=b["smooth_h"], stpmt_smooth_b=b["smooth_b"],
        stpmt_distance_max_h=b["dist_max_h"], stpmt_distance_max_l=b["dist_max_l"],
        horaire_allowed_hours_utc=b["horaire_hours"],
        volatility_atr_min=b["atr_min"], volatility_atr_max=b["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=b["scalp_coef"],
        timescan_bars=b["timescan"],
        superstop_quality=ss_q,
        superstop_coef_volat=ss_c,
    )

    score = score_walkforward(params, _FOLDS)
    return {
        "base_idx": base_idx,
        "smooth_h": b["smooth_h"], "smooth_b": b["smooth_b"],
        "dist_max_h": b["dist_max_h"], "dist_max_l": b["dist_max_l"],
        "horaire_label": b["horaire_label"], "horaire_hours": b["horaire_hours"],
        "atr_min": b["atr_min"], "atr_max": b["atr_max"],
        "scalp_coef": b["scalp_coef"], "timescan": b["timescan"],
        "superstop_quality": ss_q, "superstop_coef_volat": ss_c,
        "min_pf": score.min_pf, "max_pf": score.max_pf, "mean_pf": score.mean_pf,
        "cv": score.cv, "min_trades": score.min_trades,
        "pfs": score.pfs, "trades": score.trades,
        "passes_filters": score.passes_filters,
        "reject_reason": score.reject_reason or "",
    }


def optimize_regime(regime_rows: list, base: list, workers: int) -> list:
    if len(regime_rows) < V2_N_WINDOWS * 100:
        return []
    try:
        folds = split_walkforward(regime_rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)
    except ValueError:
        return []

    combos = [(i, q, c) for i in range(len(base))
              for q, c in product(SUPERSTOP_QUALITY_RANGE, SUPERSTOP_COEF_RANGE)]
    with Pool(workers, initializer=_init_worker, initargs=(folds, base)) as pool:
        results = list(pool.imap_unordered(_eval_combo, combos, chunksize=2))

    ok = [r for r in results if r["passes_filters"]]
    ok.sort(key=lambda r: (r["min_pf"], -r["cv"]), reverse=True)
    return ok[:3]


def main():
    parser = argparse.ArgumentParser(description="COMB_002 V2 Phase 4 — Stops per Regime")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None)
    parser.add_argument("--phase3-json", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--regime-window", type=int, default=500)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    p3_file = args.phase3_json or Path(f"COMB002_V2_phase3_{args.asset}_{args.timeframe}_top_params_by_regime.json")

    if not data_file.exists() or not p3_file.exists():
        print(f"[ERROR] Missing file")
        sys.exit(1)

    with open(p3_file) as fh:
        p3 = json.load(fh)

    rows = load_ohlc_csv(str(data_file))
    th_data = p3.get("atr_thresholds", {})
    thresholds = RegimeThresholds(atr_low=th_data.get("low", 0), atr_high=th_data.get("high", 0))

    print(f"\n=== V2 Phase 4 {args.asset} {args.timeframe} ===")

    out_by_regime = {}
    for regime in REGIME_LABELS:
        base = p3["by_regime"].get(regime, {}).get("top", [])
        if not base:
            print(f"  [{regime}] no base from Phase 3 — skipping")
            out_by_regime[regime] = {"n_top": 0, "top": []}
            continue

        regime_rows = filter_rows_by_regime(rows, thresholds, regime,
                                            window_size=args.regime_window)
        print(f"  [{regime}] rows={len(regime_rows)} base={len(base)}")
        top = optimize_regime(regime_rows, base, args.workers)
        out_by_regime[regime] = {"n_rows": len(regime_rows), "n_top": len(top), "top": top}
        for r in top:
            print(f"    ss_q={r['superstop_quality']} ss_c={r['superstop_coef_volat']} "
                  f"min_pf={r['min_pf']:.3f} cv={r['cv']:.3f}")

    out_json = args.out_dir / f"COMB002_V2_phase4_{args.asset}_{args.timeframe}_top_params_by_regime.json"
    with open(out_json, "w") as fh:
        json.dump({
            "asset": args.asset, "timeframe": args.timeframe,
            "phase": "V2_phase4_stops",
            "atr_thresholds": th_data,
            "by_regime": out_by_regime,
        }, fh, indent=2)
    print(f"\n[OK] {out_json}")


if __name__ == "__main__":
    main()
