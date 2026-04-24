"""
COMB_002_IMPULSE V2 — Phase 2A: Horaire (Walk-Forward Pool Runner)

Optimiza horaire_allowed_hours_utc manteniendo los top params de Phase 1.
Walk-forward en 5 ventanas / 3 folds. Filtros V2 hard.

Diferencias vs V1:
  - Lee top-3 de Phase 1 V2 (no solo el #1) para explorar robustez
  - Score = min(PF_all_folds), NO max(PF_B)
  - Rechaza horarios con PF inconsistente entre folds

Input : COMB002_V2_phase1_{ASSET}_{TF}_top_params.json
        {ASSET}_full_{TF}.csv
Output: COMB002_V2_phase2a_{ASSET}_{TF}_top_params.json

Uso:
  python3 phase2a_V2_horaire_walkforward.py --asset ES --timeframe 5m
"""

import argparse
import csv
import json
import sys
from itertools import combinations
from multiprocessing import Pool, cpu_count
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseParams, load_ohlc_csv
from COMB_002_IMPULSE_V2_walkforward import (
    split_walkforward,
    score_walkforward,
    V2_N_WINDOWS,
    V2_N_TRAIN_WINDOWS,
)

# ── Blocks horarios candidatos (UTC) ────────────────────────────────────────
HORAIRE_BLOCKS = {
    "RTH_US":       list(range(13, 20)),   # 13-19 UTC (US regular)
    "RTH_EARLY":    list(range(13, 17)),
    "RTH_LATE":     list(range(16, 20)),
    "PRE_MARKET":   list(range(9, 13)),
    "US_FULL":      list(range(9, 20)),
    "EU_AM":        list(range(7, 12)),
    "EU_FULL":      list(range(7, 16)),
    "AM_PEAK":      list(range(13, 16)),
    "PM_PEAK":      list(range(17, 20)),
    "24H":          list(range(24)),
}

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

_FOLDS = None
_BASE_PARAMS = None


def _init_worker(folds, base_params):
    global _FOLDS, _BASE_PARAMS
    _FOLDS = folds
    _BASE_PARAMS = base_params


def _eval_combo(combo):
    base_idx, label, hours = combo
    base = _BASE_PARAMS[base_idx]

    params = Comb002ImpulseParams(
        stpmt_smooth_h=base["smooth_h"],
        stpmt_smooth_b=base["smooth_b"],
        stpmt_distance_max_h=base["dist_max_h"],
        stpmt_distance_max_l=base["dist_max_l"],
        horaire_allowed_hours_utc=hours,
        volatility_atr_min=0.0,
        volatility_atr_max=500.0,
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=3.0,
        timescan_bars=15,
        superstop_quality=2,
        superstop_coef_volat=3.0,
    )

    score = score_walkforward(params, _FOLDS)
    return {
        "base_idx":       base_idx,
        "smooth_h":       base["smooth_h"],
        "smooth_b":       base["smooth_b"],
        "dist_max_h":     base["dist_max_h"],
        "dist_max_l":     base["dist_max_l"],
        "horaire_label":  label,
        "horaire_hours":  hours,
        "min_pf":         score.min_pf,
        "max_pf":         score.max_pf,
        "mean_pf":        score.mean_pf,
        "cv":             score.cv,
        "min_trades":     score.min_trades,
        "pfs":            score.pfs,
        "trades":         score.trades,
        "passes_filters": score.passes_filters,
        "reject_reason":  score.reject_reason or "",
    }


def main():
    parser = argparse.ArgumentParser(description="COMB_002 V2 Phase 2A — Horaire Walk-Forward")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None)
    parser.add_argument("--phase1-json", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    p1_file = args.phase1_json or Path(f"COMB002_V2_phase1_{args.asset}_{args.timeframe}_top_params.json")

    if not data_file.exists() or not p1_file.exists():
        print(f"[ERROR] Missing: {data_file if not data_file.exists() else p1_file}")
        sys.exit(1)

    with open(p1_file) as fh:
        p1 = json.load(fh)
    base_params = p1["top"]
    if not base_params:
        print("[ERROR] Phase 1 no produjo ganadores que pasen filtros V2")
        sys.exit(1)

    rows = load_ohlc_csv(str(data_file))
    folds = split_walkforward(rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)

    combos = [(i, label, hours)
              for i in range(len(base_params))
              for label, hours in HORAIRE_BLOCKS.items()]

    print(f"\n=== V2 Phase 2A {args.asset} {args.timeframe} ===")
    print(f"Base params : {len(base_params)}")
    print(f"Horarios    : {len(HORAIRE_BLOCKS)}")
    print(f"Total combos: {len(combos)}\n")

    with Pool(args.workers, initializer=_init_worker, initargs=(folds, base_params)) as pool:
        results = list(pool.imap_unordered(_eval_combo, combos, chunksize=2))

    out_csv = args.out_dir / f"COMB002_V2_phase2a_{args.asset}_{args.timeframe}_results.csv"
    csv_fields = ["base_idx", "smooth_h", "smooth_b", "dist_max_h", "dist_max_l",
                  "horaire_label", "min_pf", "max_pf", "mean_pf", "cv",
                  "min_trades", "passes_filters", "reject_reason"]
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    ok = [r for r in results if r["passes_filters"]]
    ok.sort(key=lambda r: (r["min_pf"], -r["cv"]), reverse=True)
    top3 = ok[:3]

    out_json = args.out_dir / f"COMB002_V2_phase2a_{args.asset}_{args.timeframe}_top_params.json"
    with open(out_json, "w") as fh:
        json.dump({
            "asset": args.asset, "timeframe": args.timeframe,
            "phase": "V2_phase2a_horaire",
            "n_combos": len(combos), "n_passed": len(ok),
            "top": top3,
        }, fh, indent=2)

    print(f"[OK] {out_csv}")
    print(f"[OK] {out_json}")
    print(f"Passed: {len(ok)}/{len(combos)}")
    for r in top3:
        print(f"  horaire={r['horaire_label']:<10} smooth=({r['smooth_h']},{r['smooth_b']}) "
              f"min_pf={r['min_pf']:.3f} cv={r['cv']:.3f}")


if __name__ == "__main__":
    main()
