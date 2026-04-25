"""
COMB_002_IMPULSE Phase 1 - Parallel Pool Runner
Usa multiprocessing.Pool para ejecutar combos en paralelo usando TODOS los cores.

Velocidad estimada vs secuencial:
  BO  (4 cores): 4x más rápido → ~15 min por activo → 4 activos = ~60 min
  TANK (8 cores): 8x más rápido → ~8 min por activo → YM solo = ~8 min

Uso:
  python3 phase1_COMB002_pool_runner.py --asset ES --timeframe 5m
  python3 phase1_COMB002_pool_runner.py --asset YM --timeframe 10m --workers 8
"""

import argparse
import csv
import json
import subprocess
import sys
import os
from itertools import product
from multiprocessing import Pool, cpu_count
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

# ── Grids (COMB_002_IMPULSE_PHASE_CONFIG.json Phase 1) ───────────────────────
SMOOTH_H_RANGE   = [1, 2, 3, 4, 5]
SMOOTH_B_RANGE   = [1, 2, 3, 4, 5]
DISTANCE_H_RANGE = [25, 75, 125, 175, 200]
DISTANCE_L_RANGE = [25, 75, 125, 175, 200]

ROBUSTNESS_THRESHOLD = 0.80
MIN_TRADES_A         = 20

SUPPORTED_ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
SUPPORTED_TIMEFRAMES = ["5m", "10m", "15m"]


# ── Worker function (runs ONE combo, called by Pool) ──────────────────────────
def run_single_combo(args):
    """Evaluate one parameter combo on Phase A and Phase B data."""
    smooth_h, smooth_b, dist_h, dist_l, phase_a_rows, phase_b_rows = args

    params = Comb002ImpulseParams(
        stpmt_smooth_h=smooth_h,
        stpmt_smooth_b=smooth_b,
        stpmt_distance_max_h=dist_h,
        stpmt_distance_max_l=dist_l,
        # ── Phase 1: all other components at defaults ──────────────────────
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

    strategy = Comb002ImpulseStrategy(params)
    result_a = strategy.run(phase_a_rows)
    result_b = strategy.run(phase_b_rows)

    robustness = (result_b.profit_factor / result_a.profit_factor
                  if result_a.profit_factor > 0 else 0.0)

    return {
        "smooth_h":       smooth_h,
        "smooth_b":       smooth_b,
        "dist_max_h":     dist_h,
        "dist_max_l":     dist_l,
        "phase_a_pf":     round(result_a.profit_factor, 4),
        "phase_a_wr":     round(result_a.win_rate, 4),
        "phase_a_trades": len(result_a.trades),
        "phase_a_equity": round(result_a.equity_points, 2),
        "phase_b_pf":     round(result_b.profit_factor, 4),
        "phase_b_wr":     round(result_b.win_rate, 4),
        "phase_b_trades": len(result_b.trades),
        "phase_b_equity": round(result_b.equity_points, 2),
        "robustness":     round(robustness, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE Phase 1 — Pool parallel runner"
    )
    parser.add_argument("--asset",     required=True,  choices=SUPPORTED_ASSETS)
    parser.add_argument("--timeframe", required=True,  choices=SUPPORTED_TIMEFRAMES)
    parser.add_argument(
        "--workers", type=int, default=None,
        help="Parallel workers (default: all CPU cores)"
    )
    args = parser.parse_args()

    asset     = args.asset
    timeframe = args.timeframe
    workers   = args.workers or cpu_count()

    phase_a_file = f"{asset}_phase_A_{timeframe}.csv"
    phase_b_file = f"{asset}_phase_B_{timeframe}.csv"

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE | Phase 1 Signal | {asset} {timeframe}")
    print(f"{'='*80}")
    print(f"Workers (parallel cores): {workers}")
    print(f"Grid: {len(SMOOTH_H_RANGE)}×{len(SMOOTH_B_RANGE)}×"
          f"{len(DISTANCE_H_RANGE)}×{len(DISTANCE_L_RANGE)} = 625 combos")
    print(f"Phase A: {phase_a_file}")
    print(f"Phase B: {phase_b_file}")

    if not Path(phase_a_file).exists():
        print(f"[ERROR] {phase_a_file} not found. Run from mgf-control directory.")
        sys.exit(1)
    if not Path(phase_b_file).exists():
        print(f"[ERROR] {phase_b_file} not found.")
        sys.exit(1)

    print("\nLoading data...")
    phase_a_rows = load_ohlc_csv(phase_a_file)
    phase_b_rows = load_ohlc_csv(phase_b_file)
    print(f"Phase A: {len(phase_a_rows):,} bars | Phase B: {len(phase_b_rows):,} bars")

    # ── Build full combo list ─────────────────────────────────────────────────
    all_combos = [
        (h, b, dh, dl, phase_a_rows, phase_b_rows)
        for h, b, dh, dl in product(
            SMOOTH_H_RANGE, SMOOTH_B_RANGE,
            DISTANCE_H_RANGE, DISTANCE_L_RANGE
        )
    ]
    total = len(all_combos)
    print(f"Total combos: {total}")
    print(f"\nLaunching Pool({workers})...\n")
    sys.stdout.flush()

    # ── Run in parallel ───────────────────────────────────────────────────────
    results = []
    completed = 0
    best_rob = 0.0
    best_row = None

    with Pool(processes=workers) as pool:
        for row in pool.imap_unordered(run_single_combo, all_combos, chunksize=5):
            results.append(row)
            completed += 1

            if row["robustness"] > best_rob:
                best_rob = row["robustness"]
                best_row = row
                flag = ">>> PASS <<<" if best_rob >= ROBUSTNESS_THRESHOLD else ""
                print(
                    f"  [{completed:>3}/{total}] NEW BEST {flag}: "
                    f"h={row['smooth_h']} b={row['smooth_b']} "
                    f"dh={row['dist_max_h']} dl={row['dist_max_l']} | "
                    f"Rob={best_rob:.4f} | "
                    f"PF_A={row['phase_a_pf']:.3f} PF_B={row['phase_b_pf']:.3f} | "
                    f"T_A={row['phase_a_trades']} T_B={row['phase_b_trades']}"
                )
                sys.stdout.flush()

            if completed % 50 == 0:
                print(f"  Progress: {completed}/{total} | "
                      f"Best rob so far: {best_rob:.4f}")
                sys.stdout.flush()

    # ── Sort & export ─────────────────────────────────────────────────────────
    results.sort(key=lambda x: x["robustness"], reverse=True)

    # Add metadata columns
    for r in results:
        r["asset"]     = asset
        r["timeframe"] = timeframe

    # Full log
    log_file = f"COMB002_phase1_{asset}_{timeframe}_full_log.csv"
    fields = ["asset", "timeframe", "smooth_h", "smooth_b", "dist_max_h", "dist_max_l",
              "phase_a_pf", "phase_a_wr", "phase_a_trades", "phase_a_equity",
              "phase_b_pf", "phase_b_wr", "phase_b_trades", "phase_b_equity",
              "robustness"]
    with open(log_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {log_file}")

    # Top 10
    top10_file = f"COMB002_phase1_{asset}_{timeframe}_top10.csv"
    with open(top10_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results[:10])
    print(f"[OK] {top10_file}")

    # Best params JSON
    if best_row:
        best_params = {
            "strategy":              "COMB_002_IMPULSE",
            "asset":                 asset,
            "timeframe":             timeframe,
            "phase":                 1,
            "stpmt_smooth_h":        best_row["smooth_h"],
            "stpmt_smooth_b":        best_row["smooth_b"],
            "stpmt_distance_max_h":  best_row["dist_max_h"],
            "stpmt_distance_max_l":  best_row["dist_max_l"],
            "robustness":            best_rob,
            "phase_a_pf":            best_row["phase_a_pf"],
            "phase_b_pf":            best_row["phase_b_pf"],
            "phase_a_trades":        best_row["phase_a_trades"],
            "phase_b_trades":        best_row["phase_b_trades"],
            "robustness_pass":       best_rob >= ROBUSTNESS_THRESHOLD,
            "min_trades_pass":       best_row["phase_a_trades"] >= MIN_TRADES_A,
        }
        best_file = f"COMB002_phase1_{asset}_{timeframe}_best_params.json"
        with open(best_file, "w") as fh:
            json.dump(best_params, fh, indent=2)
        print(f"[OK] {best_file}")

        status = ">>> PASS <<<" if best_rob >= ROBUSTNESS_THRESHOLD else "!!! FAIL !!!"
        print(f"\n{'='*80}")
        print(f"PHASE 1 DONE: {asset} {timeframe} [{status}]")
        print(f"  stpmt_smooth_h       = {best_params['stpmt_smooth_h']}")
        print(f"  stpmt_smooth_b       = {best_params['stpmt_smooth_b']}")
        print(f"  stpmt_distance_max_h = {best_params['stpmt_distance_max_h']}")
        print(f"  stpmt_distance_max_l = {best_params['stpmt_distance_max_l']}")
        print(f"  robustness           = {best_rob:.4f}")
        print(f"  phase_a_pf           = {best_params['phase_a_pf']:.4f}")
        print(f"  phase_b_pf           = {best_params['phase_b_pf']:.4f}")
        print(f"{'='*80}\n")

        try:
            repo_root = Path(__file__).resolve().parents[1]
            opt_id = f"OPT-COMB002-{asset}-{timeframe}-PH1-{__import__('datetime').date.today().strftime('%Y%m%d')}"
            subprocess.run(["git", "add", f"mgf-control/{best_file}"],
                cwd=repo_root, check=True)
            msg = (f"PH1 DONE - {asset} {timeframe} | {opt_id} | "
                   f"Rob={best_rob:.4f} {'PASS' if best_rob >= ROBUSTNESS_THRESHOLD else 'FAIL'}")
            subprocess.run(["git", "commit", "-m", msg], cwd=repo_root, check=True)
            subprocess.run(["git", "push"], cwd=repo_root, check=True)
            print(f"[GIT] Pushed: {msg}")
        except subprocess.CalledProcessError as e:
            print(f"[GIT WARNING] Push failed: {e} — results saved locally")


if __name__ == "__main__":
    main()
