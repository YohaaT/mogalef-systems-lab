"""
V2 PHASE TEMPLATE — Esqueleto genérico para cualquier estrategia

INSTRUCCIONES:
  1. Copia este archivo → renómbralo: phase1_V2_<NOMBRE_ESTRATEGIA>.py
  2. Completa las 3 secciones marcadas con [ADAPTACIÓN REQUERIDA]
  3. Importa tu strategy_class + params_class
  4. Ejecuta normalmente

SECCIONES A COMPLETAR:
  [A] Imports + Strategy Class + Grids de parámetros
  [B] Función build_params() — cómo construir params desde combo
  [C] Worker function — evalúa UN combo

EJEMPLO CONCRETO para COMB_002 al final de este archivo.
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

# ────────────────────────────────────────────────────────────────────────────
# [ADAPTACIÓN A] IMPORTS + GRIDS
# ────────────────────────────────────────────────────────────────────────────
# TODO: Reemplazar estos imports con tu estrategia

from COMB_002_IMPULSE_V1 import Comb002ImpulseParams, Comb002ImpulseStrategy, load_ohlc_csv
from V2_framework_generic import (
    split_walkforward, score_walkforward, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS,
)

# TODO: Cambiar estos grids según tu estrategia
# Ejemplo: si tu estrategia tiene [param1, param2, param3]
# PARAM1_RANGE = [1, 2, 3, 4, 5]
# PARAM2_RANGE = [10, 20, 30]
# PARAM3_RANGE = [0.5, 1.0, 1.5]

SMOOTH_H_RANGE   = [1, 2, 3, 4, 5]      # CAMBIAR: lista de valores posibles
SMOOTH_B_RANGE   = [1, 2, 3, 4, 5]      # CAMBIAR: según tu estrategia
DISTANCE_H_RANGE = [25, 75, 125, 175, 200]
DISTANCE_L_RANGE = [25, 75, 125, 175, 200]

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]

# Globals para Pool
_FOLDS = None


def _init_worker(folds):
    global _FOLDS
    _FOLDS = folds


# ────────────────────────────────────────────────────────────────────────────
# [ADAPTACIÓN B] BUILD_PARAMS — Constructor de parámetros
# ────────────────────────────────────────────────────────────────────────────
# TODO: Adaptar a tu params_class y parámetros

def build_params(smooth_h, smooth_b, dist_h, dist_l):
    """
    Construye UN conjunto de parámetros desde componentes individuales.

    ENTRADA: valores individuales del grid
    SALIDA: params_class instance (ej: Comb002ImpulseParams)

    Para otra estrategia, cambiar:
      - Nombre de la clase (Comb002ImpulseParams → TuEstrategiaParams)
      - Parámetros pasados al constructor
      - Valores por defecto de otros parámetros
    """
    return Comb002ImpulseParams(
        # Parámetros OPTIMIZADOS en esta phase
        stpmt_smooth_h=smooth_h,
        stpmt_smooth_b=smooth_b,
        stpmt_distance_max_h=dist_h,
        stpmt_distance_max_l=dist_l,

        # Parámetros FIJOS en esta phase (valores por defecto)
        # En phases posteriores, estos cambiarán
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


# ────────────────────────────────────────────────────────────────────────────
# [ADAPTACIÓN C] WORKER FUNCTION — Evaluador de UN combo
# ────────────────────────────────────────────────────────────────────────────
# TODO: Cambiar qué parámetros se optimizan y cómo se evalúan

def _eval_combo(combo):
    """
    Worker: Evalúa UN combo de parámetros sobre todos los folds walk-forward.

    ENTRADA: tuple de valores del grid
    SALIDA: dict con métricas + flags

    Adapt steps:
      1. Desempacar combo → variables individuales
      2. Llamar a build_params() con esas variables
      3. score_walkforward() se encarga del rest
      4. Retornar dict con resultados
    """
    # Desempacar combo (debe coincidir con itertools.product(RANGE1, RANGE2, ...))
    smooth_h, smooth_b, dist_h, dist_l = combo

    # Construir params (usa tu build_params())
    params = build_params(smooth_h, smooth_b, dist_h, dist_l)

    # Evaluar sobre todos los folds (genérico, no cambiar)
    score = score_walkforward(Comb002ImpulseStrategy, params, _FOLDS)

    # Retornar row para CSV (agregar campos según necesites)
    return {
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


# ────────────────────────────────────────────────────────────────────────────
# MAIN — No cambiar (genérico)
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="V2 Phase Template — Walk-Forward Pool")
    parser.add_argument("--asset", required=True, choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True, choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument("--data-file", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    data_file = args.data_file or Path(f"{args.asset}_full_{args.timeframe}.csv")
    if not data_file.exists():
        print(f"[ERROR] {data_file} not found")
        sys.exit(1)

    rows = load_ohlc_csv(str(data_file))
    folds = split_walkforward(rows, V2_N_WINDOWS, V2_N_TRAIN_WINDOWS)

    # Generar todas las combinaciones del grid (producto cartesiano)
    combos = list(product(SMOOTH_H_RANGE, SMOOTH_B_RANGE, DISTANCE_H_RANGE, DISTANCE_L_RANGE))

    print(f"\n{'='*80}")
    print(f"V2 Phase Template — {args.asset} {args.timeframe}")
    print(f"{'='*80}")
    print(f"Rows     : {len(rows)}")
    print(f"Folds    : {len(folds)}")
    print(f"Combos   : {len(combos)}")
    print(f"Workers  : {args.workers}\n")

    # Ejecutar en paralelo
    with Pool(args.workers, initializer=_init_worker, initargs=(folds,)) as pool:
        results = []
        for i, row in enumerate(pool.imap_unordered(_eval_combo, combos, chunksize=4), 1):
            results.append(row)
            if i % 50 == 0 or i == len(combos):
                ok_count = sum(1 for r in results if r["passes_filters"])
                print(f"  [{i}/{len(combos)}] passed={ok_count}")

    # Guardar resultados
    out_csv = args.out_dir / f"COMB002_V2_phase1_{args.asset}_{args.timeframe}_results.csv"
    fields = list(results[0].keys())
    with open(out_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {out_csv}")

    # Top-3 ganadores
    ok_rows = sorted([r for r in results if r["passes_filters"]],
                     key=lambda r: (r["min_pf"], -r["cv"], r["mean_pf"]),
                     reverse=True)
    top3 = ok_rows[:3]
    out_json = args.out_dir / f"COMB002_V2_phase1_{args.asset}_{args.timeframe}_top_params.json"
    with open(out_json, "w") as fh:
        json.dump({
            "asset": args.asset,
            "timeframe": args.timeframe,
            "phase": "V2_phase1_template",
            "n_combos": len(combos),
            "n_passed": len(ok_rows),
            "top": top3,
        }, fh, indent=2)
    print(f"[OK] {out_json}")

    print(f"\nSummary: {len(ok_rows)}/{len(combos)} passed V2 filters")
    if top3:
        print("Top-3:")
        for r in top3:
            print(f"  smooth=({r['smooth_h']},{r['smooth_b']}) dist=({r['dist_max_h']},{r['dist_max_l']}) "
                  f"min_pf={r['min_pf']:.3f} cv={r['cv']:.3f}")


if __name__ == "__main__":
    main()


# ════════════════════════════════════════════════════════════════════════════
# REFERENCIA: CÓMO ADAPTAR PARA OTRA ESTRATEGIA
# ════════════════════════════════════════════════════════════════════════════

"""
EJEMPLO: Tu estrategia se llama "TREND_FOLLOW_V1" con estos parámetros:
  - sma_period: int (10..50, paso 5)
  - atr_multiple: float (1.0..3.0, paso 0.5)
  - stop_loss_pct: float (0.01..0.05, paso 0.01)

PASOS:

1. Reemplaza [ADAPTACIÓN A]:
   ────────────────────────────────────────────
   from MY_STRATEGIES import TrendFollowV1, TrendFollowV1Params, load_ohlc_csv

   SMA_PERIOD_RANGE = [10, 15, 20, 25, 30, 35, 40, 45, 50]
   ATR_MULTIPLE_RANGE = [1.0, 1.5, 2.0, 2.5, 3.0]
   STOP_LOSS_RANGE = [0.01, 0.02, 0.03, 0.04, 0.05]

2. Reemplaza [ADAPTACIÓN B]:
   ────────────────────────────────────────────
   def build_params(sma_period, atr_multiple, stop_loss_pct):
       return TrendFollowV1Params(
           sma_period=sma_period,
           atr_multiple=atr_multiple,
           stop_loss_pct=stop_loss_pct,
           # Otros parámetros fijos (defaults de tu estrategia)
           use_adx_filter=True,
           adx_threshold=25.0,
           max_daily_loss=0.02,
       )

3. Reemplaza [ADAPTACIÓN C]:
   ────────────────────────────────────────────
   def _eval_combo(combo):
       sma_period, atr_multiple, stop_loss_pct = combo

       params = build_params(sma_period, atr_multiple, stop_loss_pct)
       score = score_walkforward(TrendFollowV1, params, _FOLDS)

       return {
           "sma_period": sma_period,
           "atr_multiple": atr_multiple,
           "stop_loss_pct": stop_loss_pct,
           "min_pf": score.min_pf,
           "max_pf": score.max_pf,
           "mean_pf": score.mean_pf,
           "cv": score.cv,
           "min_trades": score.min_trades,
           "passes_filters": score.passes_filters,
           "reject_reason": score.reject_reason or "",
       }

4. Actualiza main() si necesitas cambiar nombres de archivos o grids.

¡LISTO! El rest es genérico y no cambia.
"""
