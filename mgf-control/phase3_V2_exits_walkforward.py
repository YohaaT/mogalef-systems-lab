"""
COMB_002_IMPULSE V2 — Phase 3: Exits (Walk-Forward, POR RÉGIMEN)

Optimiza scalping_target_coef_volat + timescan_bars dentro de cada régimen.
Itera sobre los top-3 POR RÉGIMEN de Phase 2B.

Input : COMB002_V2_phase2b_{ASSET}_{TF}_top_params_by_regime.json
        {ASSET}_full_{TF}.csv
Output: COMB002_V2_phase3_{ASSET}_{TF}_top_params_by_regime.json

Uso:
  python3 phase3_V2_exits_walkforward.py --asset ES --timeframe 5m
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
    compute_regime_thresholds, filter_rows_by_regime,
    REGIME_LABELS, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS,
    RegimeThresholds,
)

SCALP_COEF_RANGE = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
TIMESCAN_RANGE   = [10, 15, 20, 30, 45]

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

_FOLDS = None
_BASE = None


def _init_worker(folds, base):
    global _FOLDS, _BASE
    _FOLDS = folds
    _BASE = base


def _eval_combo(combo):
    base_idx, scalp_coef, timescan = combo
    b = _BASE[base_idx]

    params = Comb002ImpulseParams(
        stpmt_smooth_h=b["smooth_h"], stpmt_smooth_b=b["smooth_b"],
        stpmt_distance_max_h=b["dist_max_h"], stpmt_distance_max_l=b["dist_max_l"],
        horaire_allowed_hours_utc=b["horaire_hours"],
        volatility_atr_min=b["atr_min"], volatility_atr_max=b["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=scalp_coef,
        timescan_bars=timescan,
        superstop_quality=2,
        superstop_coef_volat=3.0,
    )

    score = score_walkforward(params, _FOLDS)
    return {
        "base_idx": base_idx,
        "smooth_h": b["smooth_h"], "smooth_b": b["smooth_b"],
        "dist_max_h": b["dist_max_h"], "dist_max_l": b["dist_max_l"],
        "horaire_label": b["horaire_label"], "horaire_hours": b["horaire_hours"],
        "atr_min": b["atr_min"], "atr_max": b["atr_max"],
        "scalp_coef": scalp_coef, "timescan": timescan,
        "min_pf": score.min_pf, "max_pf": score.max_pf, "mean_pf": score.mean_pf,
        "cv": score.cv, "min_trades": score.min_trades,
        "pfs": score.pfs, "trades": score.trades,
        "passes_filters": score.passes_filters,
        "reject_reason": score.reject_reason or "",
    }


def optimize_regime(regime: str, regime_rows: list, base: list, workers: int) -> list:
    if len(regime_rows) < V2_N_WINDOWS * 100:
        return []
    try:
        folds = split_walkforward(regime_rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)
    except ValueError:
        return []

    combos = [(i, c, t) for i in range(len(base)) for c, t in product(SCALP_COEF_RANGE, TIMESCAN_RANGE)]
    with Pool(workers, initializer=_init_worker, initargs=(folds, base)) as pool:
        results = list(pool.imap_unordered(_eval_combo, combos, chunksize=2))

    ok = [r for r in results if r["passes_filters"]]
    ok.sort(key=lambda r: (r["min_pf"], -r["cv"]), reverse=True)
    return ok[:3]


def main():
    parser = argparse.ArgumentParser(description="COMB_002 V2 Phase 3 — Exits per Regime")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None)
    parser.add_argument("--phase2b-json", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--regime-window", type=int, default=500)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    p2b_file = args.phase2b_json or Path(f"COMB002_V2_phase2b_{args.asset}_{args.timeframe}_top_params_by_regime.json")

    if not data_file.exists() or not p2b_file.exists():
        print(f"[ERROR] Missing file")
        sys.exit(1)

    with open(p2b_file) as fh:
        p2b = json.load(fh)

    rows = load_ohlc_csv(str(data_file))
    th_data = p2b.get("atr_thresholds", {})
    thresholds = RegimeThresholds(atr_low=th_data.get("low", 0), atr_high=th_data.get("high", 0))

    print(f"\n=== V2 Phase 3 {args.asset} {args.timeframe} ===")

    out_by_regime = {}
    for regime in REGIME_LABELS:
        base = p2b["by_regime"].get(regime, {}).get("top", [])
        if not base:
            print(f"  [{regime}] no base from Phase 2B — skipping")
            out_by_regime[regime] = {"n_top": 0, "top": []}
            continue

        regime_rows = filter_rows_by_regime(rows, thresholds, regime,
                                            window_size=args.regime_window)
        print(f"  [{regime}] rows={len(regime_rows)} base={len(base)}")
        top = optimize_regime(regime, regime_rows, base, args.workers)
        out_by_regime[regime] = {"n_rows": len(regime_rows), "n_top": len(top), "top": top}
        for r in top:
            print(f"    scalp={r['scalp_coef']} ts={r['timescan']} "
                  f"min_pf={r['min_pf']:.3f} cv={r['cv']:.3f}")

    out_json = args.out_dir / f"COMB002_V2_phase3_{args.asset}_{args.timeframe}_top_params_by_regime.json"
    with open(out_json, "w") as fh:
        json.dump({
            "asset": args.asset, "timeframe": args.timeframe,
            "phase": "V2_phase3_exits",
            "atr_thresholds": th_data,
            "by_regime": out_by_regime,
        }, fh, indent=2)
    print(f"\n[OK] {out_json}")


if __name__ == "__main__":
    main()
