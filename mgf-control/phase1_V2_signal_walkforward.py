"""
COMB_002_IMPULSE V2 — Phase 1: Signal Detection (Walk-Forward Pool Runner)

Diferencias vs V1 Phase 1:
  - Split walk-forward 5 ventanas / 3 folds (NO Phase A/B binario)
  - Score: min(PF_all_folds) en vez de max(PF_B)
  - Filtros V2: min_PF≥1.0 · trades≥20/fold · CV≤0.30
  - VEC: Pool multiprocessing por combos sobre MISMO dataset (cacheo de load)
  - Output incluye breakdown por fold para auditoría

Input : {ASSET}_full_{TF}.csv  (dataset completo, se divide internamente)
Output: COMB002_V2_phase1_{ASSET}_{TF}_results.csv    (todas las combos)
        COMB002_V2_phase1_{ASSET}_{TF}_top_params.json (top-3 que pasan filtros V2)

Uso:
  python3 phase1_V2_signal_walkforward.py --asset ES --timeframe 5m
  python3 phase1_V2_signal_walkforward.py --asset YM --timeframe 10m --workers 4
"""

import argparse
import csv
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
    split_walkforward,
    score_walkforward,
    select_top_n_walkforward,
    V2_N_WINDOWS,
    V2_N_TRAIN_WINDOWS,
)

# ── Grids (iguales a V1 Phase 1) ─────────────────────────────────────────────
SMOOTH_H_RANGE   = [1, 2, 3, 4, 5]
SMOOTH_B_RANGE   = [1, 2, 3, 4, 5]
DISTANCE_H_RANGE = [25, 75, 125, 175, 200]
DISTANCE_L_RANGE = [25, 75, 125, 175, 200]

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

# Worker globals (set en init)
_FOLDS = None


def _init_worker(folds):
    """Inicializa worker con folds compartidos (evita pickle en cada call)."""
    global _FOLDS
    _FOLDS = folds


def _eval_combo(combo):
    """Worker: evalúa UN combo sobre todos los folds walk-forward."""
    smooth_h, smooth_b, dist_h, dist_l = combo

    params = Comb002ImpulseParams(
        stpmt_smooth_h=smooth_h,
        stpmt_smooth_b=smooth_b,
        stpmt_distance_max_h=dist_h,
        stpmt_distance_max_l=dist_l,
        horaire_allowed_hours_utc=list(range(9, 16)),
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

    row = {
        "smooth_h":       smooth_h,
        "smooth_b":       smooth_b,
        "dist_max_h":     dist_h,
        "dist_max_l":     dist_l,
        "min_pf":         score.min_pf,
        "max_pf":         score.max_pf,
        "mean_pf":        score.mean_pf,
        "cv":             score.cv,
        "min_trades":     score.min_trades,
        "passes_filters": score.passes_filters,
        "reject_reason":  score.reject_reason or "",
    }
    for i, pf in enumerate(score.pfs):
        row[f"pf_fold{i}"] = pf
    for i, tr in enumerate(score.trades):
        row[f"trades_fold{i}"] = tr
    return row


def main():
    parser = argparse.ArgumentParser(description="COMB_002 V2 Phase 1 — Signal Walk-Forward")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None,
                        help="Override data file path (default: {asset}_full_{tf}.csv)")
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    if not data_file.exists():
        print(f"[ERROR] Data file not found: {data_file}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"COMB_002 V2 Phase 1 — {args.asset} {args.timeframe}")
    print(f"{'='*80}")
    print(f"Data file   : {data_file}")
    print(f"Workers     : {args.workers}")

    rows = load_ohlc_csv(str(data_file))
    print(f"Loaded rows : {len(rows)}")

    folds = split_walkforward(rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)
    print(f"Folds       : {len(folds)} (n_windows={V2_N_WINDOWS}, n_train={V2_N_TRAIN_WINDOWS})")

    combos = list(product(SMOOTH_H_RANGE, SMOOTH_B_RANGE, DISTANCE_H_RANGE, DISTANCE_L_RANGE))
    print(f"Combos      : {len(combos)}\n")

    with Pool(args.workers, initializer=_init_worker, initargs=(folds,)) as pool:
        results = []
        for i, row in enumerate(pool.imap_unordered(_eval_combo, combos, chunksize=4), 1):
            results.append(row)
            if i % 50 == 0 or i == len(combos):
                ok_count = sum(1 for r in results if r["passes_filters"])
                print(f"  [{i}/{len(combos)}] passed={ok_count}")

    # CSV completo
    out_csv = args.out_dir / f"COMB002_V2_phase1_{args.asset}_{args.timeframe}_results.csv"
    fields = list(results[0].keys())
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {out_csv}")

    # Top-3 ganadores (solo los que pasan filtros V2)
    ok_rows = sorted([r for r in results if r["passes_filters"]],
                     key=lambda r: (r["min_pf"], -r["cv"], r["mean_pf"]),
                     reverse=True)

    top3 = ok_rows[:3]
    out_json = args.out_dir / f"COMB002_V2_phase1_{args.asset}_{args.timeframe}_top_params.json"
    payload = {
        "asset":      args.asset,
        "timeframe":  args.timeframe,
        "phase":      "V2_phase1_signal",
        "n_combos":   len(combos),
        "n_passed":   len(ok_rows),
        "top":        top3,
    }
    with open(out_json, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"[OK] {out_json}")

    print(f"\n{'='*80}")
    print(f"Summary: {len(ok_rows)}/{len(combos)} combos pasan filtros V2")
    if top3:
        print(f"Top-3 min_PF:")
        for r in top3:
            print(f"  smooth=({r['smooth_h']},{r['smooth_b']}) dist=({r['dist_max_h']},{r['dist_max_l']}) "
                  f"min_pf={r['min_pf']:.3f} cv={r['cv']:.3f} trades_min={r['min_trades']}")
    else:
        print("⚠️  NINGÚN combo pasa los filtros V2 — considerar relajar threshold o ampliar data")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
