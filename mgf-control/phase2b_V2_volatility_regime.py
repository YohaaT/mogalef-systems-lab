"""
COMB_002_IMPULSE V2 — Phase 2B: Volatility + Regime Clustering (Pool Runner)

**FASE CLAVE V2**: Aquí se separa la data por RÉGIMEN DE VOLATILIDAD
y se optimizan params DISTINTOS para cada régimen.

Flujo:
  1. Carga data completa
  2. Calcula thresholds de régimen sobre TODA la data (percentiles 33/67 del ATR)
  3. Para cada régimen (low_vol / med_vol / high_vol):
       a. Filtra rows que caen en ese régimen (ventana deslizante)
       b. Divide ese subset en walk-forward 5/3
       c. Optimiza volatility_atr_min/max + mantiene top de Phase 2A
       d. Aplica filtros V2 → selecciona top-3
  4. Output: top-3 POR RÉGIMEN (hasta 9 candidatos totales)

Input : {ASSET}_full_{TF}.csv
        COMB002_V2_phase2a_{ASSET}_{TF}_top_params.json
Output: COMB002_V2_phase2b_{ASSET}_{TF}_top_params_by_regime.json

Uso:
  python3 phase2b_V2_volatility_regime.py --asset ES --timeframe 5m
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
    compute_regime_thresholds,
    filter_rows_by_regime,
    REGIME_LABELS,
    V2_N_WINDOWS,
    V2_N_TRAIN_WINDOWS,
    V2_MIN_TRADES_PER_WINDOW,
)

# ── Grids volatility band ────────────────────────────────────────────────────
ATR_MIN_RANGE = [0.0, 5.0, 10.0, 20.0]
ATR_MAX_RANGE = [50.0, 100.0, 200.0, 500.0]

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

_FOLDS = None
_BASE = None


def _init_worker(folds, base):
    global _FOLDS, _BASE
    _FOLDS = folds
    _BASE = base


def _eval_combo(combo):
    base_idx, atr_min, atr_max = combo
    base = _BASE[base_idx]

    if atr_min >= atr_max:
        return None

    params = Comb002ImpulseParams(
        stpmt_smooth_h=base["smooth_h"],
        stpmt_smooth_b=base["smooth_b"],
        stpmt_distance_max_h=base["dist_max_h"],
        stpmt_distance_max_l=base["dist_max_l"],
        horaire_allowed_hours_utc=base["horaire_hours"],
        volatility_atr_min=atr_min,
        volatility_atr_max=atr_max,
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
        "base_idx": base_idx,
        "smooth_h": base["smooth_h"], "smooth_b": base["smooth_b"],
        "dist_max_h": base["dist_max_h"], "dist_max_l": base["dist_max_l"],
        "horaire_label": base["horaire_label"],
        "horaire_hours": base["horaire_hours"],
        "atr_min": atr_min, "atr_max": atr_max,
        "min_pf": score.min_pf, "max_pf": score.max_pf, "mean_pf": score.mean_pf,
        "cv": score.cv, "min_trades": score.min_trades,
        "pfs": score.pfs, "trades": score.trades,
        "passes_filters": score.passes_filters,
        "reject_reason": score.reject_reason or "",
    }


def optimize_regime(regime_label: str, regime_rows: list, base_params: list,
                    workers: int) -> list:
    """Corre la grid completa sobre la data filtrada por régimen."""
    if len(regime_rows) < V2_N_WINDOWS * 100:
        print(f"  [{regime_label}] insufficient data ({len(regime_rows)} rows) — skipping")
        return []

    try:
        folds = split_walkforward(regime_rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)
    except ValueError as e:
        print(f"  [{regime_label}] {e} — skipping")
        return []

    combos = [(i, amin, amax)
              for i in range(len(base_params))
              for amin, amax in product(ATR_MIN_RANGE, ATR_MAX_RANGE)]

    with Pool(workers, initializer=_init_worker, initargs=(folds, base_params)) as pool:
        raw = list(pool.imap_unordered(_eval_combo, combos, chunksize=2))

    results = [r for r in raw if r is not None]
    ok = [r for r in results if r["passes_filters"]]
    ok.sort(key=lambda r: (r["min_pf"], -r["cv"]), reverse=True)
    return ok[:3]


def main():
    parser = argparse.ArgumentParser(description="COMB_002 V2 Phase 2B — Volatility × Regime")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None)
    parser.add_argument("--phase2a-json", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--regime-window", type=int, default=500,
                        help="Barras para clasificar régimen local (default: 500)")
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    p2a_file = args.phase2a_json or Path(f"COMB002_V2_phase2a_{args.asset}_{args.timeframe}_top_params.json")

    if not data_file.exists() or not p2a_file.exists():
        print(f"[ERROR] Missing file")
        sys.exit(1)

    with open(p2a_file) as fh:
        p2a = json.load(fh)
    base_params = p2a["top"]
    if not base_params:
        print("[ERROR] Phase 2A no produjo ganadores")
        sys.exit(1)

    rows = load_ohlc_csv(str(data_file))
    thresholds = compute_regime_thresholds(rows)

    print(f"\n=== V2 Phase 2B {args.asset} {args.timeframe} ===")
    print(f"Total rows     : {len(rows)}")
    print(f"ATR thresholds : low<{thresholds.atr_low:.2f} · high≥{thresholds.atr_high:.2f}")
    print(f"Base params    : {len(base_params)}")

    by_regime = {}
    for regime in REGIME_LABELS:
        regime_rows = filter_rows_by_regime(rows, thresholds, regime,
                                            window_size=args.regime_window)
        print(f"\n  [{regime}] filtered rows: {len(regime_rows)} ({100*len(regime_rows)/len(rows):.1f}%)")
        top = optimize_regime(regime, regime_rows, base_params, args.workers)
        by_regime[regime] = {
            "n_rows": len(regime_rows),
            "n_top": len(top),
            "top": top,
        }
        for r in top:
            print(f"    atr=({r['atr_min']},{r['atr_max']}) "
                  f"horaire={r['horaire_label']:<10} "
                  f"min_pf={r['min_pf']:.3f} cv={r['cv']:.3f}")

    out_json = args.out_dir / f"COMB002_V2_phase2b_{args.asset}_{args.timeframe}_top_params_by_regime.json"
    with open(out_json, "w") as fh:
        json.dump({
            "asset": args.asset, "timeframe": args.timeframe,
            "phase": "V2_phase2b_volatility_regime",
            "atr_thresholds": {"low": thresholds.atr_low, "high": thresholds.atr_high},
            "regime_window_bars": args.regime_window,
            "by_regime": by_regime,
        }, fh, indent=2)
    print(f"\n[OK] {out_json}")


if __name__ == "__main__":
    main()
